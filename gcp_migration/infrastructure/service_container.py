"""
Service container for dependency injection.

This module provides a dependency injection container that manages service
creation and lifecycle, ensuring consistent configuration and optimized
resource usage across the application.
"""

import asyncio
import inspect
import logging
from enum import Enum, auto
from typing import Any, Callable, Dict, Generic, Optional, Set, Type, TypeVar, cast

from gcp_migration.domain.exceptions_fixed import (
    ConfigurationError, DependencyError, MigrationError
)
from gcp_migration.domain.protocols import (
    IGCPServiceCore, IGCPSecretManager, IGCPStorage, IGCPFirestore, 
    IGCPVertexAI, IExtendedGCPService
)
from gcp_migration.infrastructure.adapters import (
    AdapterFactory, FirestoreAdapter, SecretManagerAdapter, 
    StorageAdapter, VertexAIAdapter
)
from gcp_migration.infrastructure.connection import (
    ConnectionPool, ConnectionPoolManager, create_connection_pool
)
from gcp_migration.infrastructure.gcp_service import GCPService
from gcp_migration.infrastructure.service_factory import GCPServiceFactory

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for generic service resolution
T = TypeVar('T')
TImpl = TypeVar('TImpl')


class ServiceLifetime(Enum):
    """Service lifetime options for the container."""
    
    TRANSIENT = auto()  # New instance created each time
    SCOPED = auto()     # Same instance used within a scope
    SINGLETON = auto()  # Same instance used across all scopes


class ServiceRegistration(Generic[T]):
    """
    Information about a registered service.
    
    This class stores metadata about a service registration including
    its implementation type and lifetime.
    """
    
    def __init__(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type] = None,
        factory: Optional[Callable[['ServiceContainer'], T]] = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        condition: Optional[Callable[[], bool]] = None
    ):
        """
        Initialize a service registration.
        
        Args:
            service_type: The type/interface being registered
            implementation_type: The concrete implementation type
            factory: Factory function to create the service
            lifetime: Service lifetime
            condition: Optional condition for conditional registration
        """
        if implementation_type is None and factory is None:
            raise ConfigurationError(
                "Either implementation_type or factory must be provided"
            )
            
        self.service_type = service_type
        self.implementation_type = implementation_type
        self.factory = factory
        self.lifetime = lifetime
        self.condition = condition


class ServiceContainer:
    """
    Dependency injection container for services.
    
    This class provides a centralized registry for services with support for:
    1. Automatic dependency resolution
    2. Service lifetime management (transient, scoped, singleton)
    3. Conditional registration
    4. Lazy initialization
    """
    
    def __init__(self):
        """Initialize the service container."""
        self._registrations: Dict[Type, ServiceRegistration] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[int, Dict[Type, Any]] = {}
        self._current_scope_id = 0
        self._lock = asyncio.Lock()
    
    def register(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type] = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        condition: Optional[Callable[[], bool]] = None
    ) -> None:
        """
        Register a service with its implementation.
        
        Args:
            service_type: The type/interface being registered
            implementation_type: The concrete implementation type
            lifetime: Service lifetime
            condition: Optional condition for conditional registration
        """
        if implementation_type is None:
            # Self-registration
            implementation_type = service_type
            
        registration = ServiceRegistration(
            service_type=service_type,
            implementation_type=implementation_type,
            lifetime=lifetime,
            condition=condition
        )
        
        self._registrations[service_type] = registration
    
    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[['ServiceContainer'], T],
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        condition: Optional[Callable[[], bool]] = None
    ) -> None:
        """
        Register a service with a factory function.
        
        Args:
            service_type: The type/interface being registered
            factory: Factory function to create the service
            lifetime: Service lifetime
            condition: Optional condition for conditional registration
        """
        registration = ServiceRegistration(
            service_type=service_type,
            factory=factory,
            lifetime=lifetime,
            condition=condition
        )
        
        self._registrations[service_type] = registration
    
    def register_instance(
        self,
        service_type: Type[T],
        instance: T
    ) -> None:
        """
        Register an existing instance as a singleton.
        
        Args:
            service_type: The type/interface being registered
            instance: The instance to register
        """
        self._singletons[service_type] = instance
    
    def is_registered(self, service_type: Type[T]) -> bool:
        """
        Check if a service type is registered.
        
        Args:
            service_type: The type to check
            
        Returns:
            True if registered, False otherwise
        """
        return service_type in self._registrations or service_type in self._singletons
    
    def create_scope(self) -> int:
        """
        Create a new scope for scoped services.
        
        Returns:
            Scope ID
        """
        self._current_scope_id += 1
        scope_id = self._current_scope_id
        self._scoped_instances[scope_id] = {}
        return scope_id
    
    def dispose_scope(self, scope_id: int) -> None:
        """
        Dispose a scope and its scoped services.
        
        Args:
            scope_id: ID of the scope to dispose
        """
        if scope_id in self._scoped_instances:
            del self._scoped_instances[scope_id]
    
    async def resolve_async(self, service_type: Type[T], scope_id: Optional[int] = None) -> T:
        """
        Resolve a service asynchronously (supports async factories).
        
        Args:
            service_type: The type to resolve
            scope_id: Optional scope ID for scoped services
            
        Returns:
            An instance of the requested service
            
        Raises:
            DependencyError: If the service cannot be resolved
        """
        try:
            # Check for directly registered instance
            if service_type in self._singletons:
                return self._singletons[service_type]
                
            # Check for registration
            if service_type not in self._registrations:
                raise DependencyError(f"No registration found for {service_type.__name__}")
                
            registration = self._registrations[service_type]
            
            # Check condition
            if registration.condition is not None and not registration.condition():
                raise DependencyError(
                    f"Conditional registration for {service_type.__name__} evaluated to false"
                )
                
            # Handle lifetimes
            if registration.lifetime == ServiceLifetime.SINGLETON:
                # Check if already instantiated
                if service_type in self._singletons:
                    return self._singletons[service_type]
                    
                # Create singleton instance
                async with self._lock:
                    # Check again in case another task created it
                    if service_type in self._singletons:
                        return self._singletons[service_type]
                        
                    # Create the instance
                    instance = await self._create_instance_async(registration)
                    self._singletons[service_type] = instance
                    return instance
                    
            elif registration.lifetime == ServiceLifetime.SCOPED:
                # Ensure scope ID is provided
                if scope_id is None:
                    raise DependencyError(
                        f"Scope ID required for scoped service {service_type.__name__}"
                    )
                    
                # Check if scope exists
                if scope_id not in self._scoped_instances:
                    raise DependencyError(f"Invalid scope ID: {scope_id}")
                    
                # Check if already instantiated in this scope
                scope = self._scoped_instances[scope_id]
                if service_type in scope:
                    return scope[service_type]
                    
                # Create scoped instance
                instance = await self._create_instance_async(registration)
                scope[service_type] = instance
                return instance
                
            else:  # TRANSIENT
                # Always create new instance
                return await self._create_instance_async(registration)
                
        except Exception as e:
            if isinstance(e, DependencyError):
                raise
            raise DependencyError(
                f"Failed to resolve service {service_type.__name__}: {str(e)}"
            ) from e
    
    def resolve(self, service_type: Type[T], scope_id: Optional[int] = None) -> T:
        """
        Resolve a service synchronously (does not support async factories).
        
        Args:
            service_type: The type to resolve
            scope_id: Optional scope ID for scoped services
            
        Returns:
            An instance of the requested service
            
        Raises:
            DependencyError: If the service cannot be resolved
        """
        try:
            # Check for directly registered instance
            if service_type in self._singletons:
                return self._singletons[service_type]
                
            # Check for registration
            if service_type not in self._registrations:
                raise DependencyError(f"No registration found for {service_type.__name__}")
                
            registration = self._registrations[service_type]
            
            # Check condition
            if registration.condition is not None and not registration.condition():
                raise DependencyError(
                    f"Conditional registration for {service_type.__name__} evaluated to false"
                )
                
            # Handle lifetimes
            if registration.lifetime == ServiceLifetime.SINGLETON:
                # Check if already instantiated
                if service_type in self._singletons:
                    return self._singletons[service_type]
                    
                # Create singleton instance - warning: not thread-safe in sync context
                instance = self._create_instance(registration)
                self._singletons[service_type] = instance
                return instance
                    
            elif registration.lifetime == ServiceLifetime.SCOPED:
                # Ensure scope ID is provided
                if scope_id is None:
                    raise DependencyError(
                        f"Scope ID required for scoped service {service_type.__name__}"
                    )
                    
                # Check if scope exists
                if scope_id not in self._scoped_instances:
                    raise DependencyError(f"Invalid scope ID: {scope_id}")
                    
                # Check if already instantiated in this scope
                scope = self._scoped_instances[scope_id]
                if service_type in scope:
                    return scope[service_type]
                    
                # Create scoped instance
                instance = self._create_instance(registration)
                scope[service_type] = instance
                return instance
                
            else:  # TRANSIENT
                # Always create new instance
                return self._create_instance(registration)
                
        except Exception as e:
            if isinstance(e, DependencyError):
                raise
            raise DependencyError(
                f"Failed to resolve service {service_type.__name__}: {str(e)}"
            ) from e
    
    async def _create_instance_async(self, registration: ServiceRegistration) -> Any:
        """
        Create an instance of a service asynchronously.
        
        Args:
            registration: Service registration information
            
        Returns:
            An instance of the service
            
        Raises:
            DependencyError: If the instance cannot be created
        """
        try:
            # Use factory if provided
            if registration.factory is not None:
                factory = registration.factory
                
                # Check if factory is async
                if inspect.iscoroutinefunction(factory):
                    instance = await factory(self)
                else:
                    instance = factory(self)
                    
                return instance
                
            # Otherwise, use implementation type
            assert registration.implementation_type is not None
            implementation_type = registration.implementation_type
            
            # Check if has async constructor (unlikely in Python, but possible with meta-programming)
            # We'll check for a create_async classmethod first
            if hasattr(implementation_type, "create_async") and inspect.iscoroutinefunction(
                implementation_type.create_async
            ):
                return await implementation_type.create_async(self)
                
            # Otherwise, use regular constructor and resolve dependencies
            return self._create_instance_from_type(implementation_type)
            
        except Exception as e:
            if isinstance(e, DependencyError):
                raise
            service_name = (
                registration.service_type.__name__ 
                if hasattr(registration.service_type, "__name__") 
                else str(registration.service_type)
            )
            raise DependencyError(
                f"Failed to create instance of {service_name}: {str(e)}"
            ) from e
    
    def _create_instance(self, registration: ServiceRegistration) -> Any:
        """
        Create an instance of a service synchronously.
        
        Args:
            registration: Service registration information
            
        Returns:
            An instance of the service
            
        Raises:
            DependencyError: If the instance cannot be created
        """
        try:
            # Use factory if provided
            if registration.factory is not None:
                factory = registration.factory
                
                # Ensure factory is not async
                if inspect.iscoroutinefunction(factory):
                    raise DependencyError(
                        "Cannot use async factory in synchronous resolve. " 
                        "Use resolve_async instead."
                    )
                    
                return factory(self)
                
            # Otherwise, use implementation type
            assert registration.implementation_type is not None
            implementation_type = registration.implementation_type
            
            return self._create_instance_from_type(implementation_type)
            
        except Exception as e:
            if isinstance(e, DependencyError):
                raise
            service_name = (
                registration.service_type.__name__ 
                if hasattr(registration.service_type, "__name__") 
                else str(registration.service_type)
            )
            raise DependencyError(
                f"Failed to create instance of {service_name}: {str(e)}"
            ) from e
    
    def _create_instance_from_type(self, implementation_type: Type) -> Any:
        """
        Create an instance of a service by resolving constructor dependencies.
        
        Args:
            implementation_type: Type to instantiate
            
        Returns:
            An instance of the service
            
        Raises:
            DependencyError: If dependencies cannot be resolved
        """
        try:
            # Get constructor parameters
            signature = inspect.signature(implementation_type.__init__)
            params = signature.parameters
            
            # Skip 'self' parameter
            arg_params = list(params.values())[1:]
            
            # Resolve dependencies
            args = []
            for param in arg_params:
                param_type = param.annotation
                
                # Skip if no type annotation or is simple type
                if param_type is inspect.Parameter.empty or param_type in (str, int, float, bool):
                    if param.default is inspect.Parameter.empty:
                        raise DependencyError(
                            f"Cannot resolve parameter {param.name} of type {param_type}"
                        )
                    continue
                
                # Resolve the dependency
                dependency = self.resolve(param_type)
                args.append(dependency)
                
            # Create the instance
            return implementation_type(*args)
            
        except Exception as e:
            if isinstance(e, DependencyError):
                raise
            raise DependencyError(
                f"Failed to create instance of {implementation_type.__name__}: {str(e)}"
            ) from e


class GCPServiceContainer(ServiceContainer):
    """
    Specialized container for GCP services.
    
    This class provides a pre-configured container for GCP services with 
    optimized connection handling and circuit breaker integration.
    """
    
    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        """
        Initialize the GCP service container.
        
        Args:
            project_id: GCP project ID
            credentials_path: Optional path to credentials file
        """
        super().__init__()
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.connection_pools: Dict[str, ConnectionPool] = {}
        
        # Register services
        self._register_core_services()
    
    async def initialize(self) -> None:
        """
        Initialize the container asynchronously.
        
        This method sets up connection pools and initializes core services.
        """
        # Create connection pools
        await self._initialize_connection_pools()
        
        # Initialize any singletons that require async initialization
        for service_type, instance in self._singletons.items():
            if hasattr(instance, "initialize") and inspect.iscoroutinefunction(
                instance.initialize
            ):
                await instance.initialize()
    
    async def _initialize_connection_pools(self) -> None:
        """Initialize connection pools for GCP services."""
        # Secret Manager connection pool
        self.connection_pools["secretmanager"] = await create_connection_pool(
            name="secretmanager",
            factory=self._create_secret_client,
            closer=self._close_client,
            min_size=1,
            max_size=10
        )
        
        # Storage connection pool
        self.connection_pools["storage"] = await create_connection_pool(
            name="storage",
            factory=self._create_storage_client,
            closer=self._close_client,
            min_size=1,
            max_size=20
        )
        
        # Firestore connection pool
        self.connection_pools["firestore"] = await create_connection_pool(
            name="firestore",
            factory=self._create_firestore_client,
            closer=self._close_client,
            min_size=1,
            max_size=10
        )
        
        # Vertex AI connection pool
        self.connection_pools["vertexai"] = await create_connection_pool(
            name="vertexai",
            factory=self._create_model_client,
            closer=self._close_client,
            min_size=1,
            max_size=5
        )
        
        logger.info(f"Initialized connection pools for {len(self.connection_pools)} services")
    
    def _register_core_services(self) -> None:
        """Register core GCP services in the container."""
        # Register GCP service
        self.register_factory(
            IGCPServiceCore,
            self._create_gcp_service
        )
        
        # Register extended GCP service
        self.register_factory(
            IExtendedGCPService,
            self._create_gcp_service
        )
        
        # Register individual service adapters
        self.register_factory(
            IGCPSecretManager,
            self._create_secret_manager_adapter
        )
        
        self.register_factory(
            IGCPStorage,
            self._create_storage_adapter
        )
        
        self.register_factory(
            IGCPFirestore,
            self._create_firestore_adapter
        )
        
        self.register_factory(
            IGCPVertexAI,
            self._create_vertex_ai_adapter
        )
    
    # Factory methods for services
    
    def _create_gcp_service(self, container: ServiceContainer) -> GCPService:
        """
        Create a GCP service.
        
        Args:
            container: Service container
            
        Returns:
            GCP service
        """
        return GCPService(
            project_id=self.project_id,
            credentials_path=self.credentials_path,
            connection_pools=self.connection_pools
        )
    
    def _create_secret_manager_adapter(self, container: ServiceContainer) -> SecretManagerAdapter:
        """
        Create a Secret Manager adapter.
        
        Args:
            container: Service container
            
        Returns:
            Secret Manager adapter
        """
        client = GCPServiceFactory.create_secret_manager_client(
            project_id=self.project_id,
            credentials_path=self.credentials_path
        )
        
        return SecretManagerAdapter(
            client=client,
            project_id=self.project_id,
            connection_pool=self.connection_pools.get("secretmanager")
        )
    
    def _create_storage_adapter(self, container: ServiceContainer) -> StorageAdapter:
        """
        Create a Storage adapter.
        
        Args:
            container: Service container
            
        Returns:
            Storage adapter
        """
        client = GCPServiceFactory.create_storage_client(
            project_id=self.project_id,
            credentials_path=self.credentials_path
        )
        
        return StorageAdapter(
            client=client,
            project_id=self.project_id,
            connection_pool=self.connection_pools.get("storage")
        )
    
    def _create_firestore_adapter(self, container: ServiceContainer) -> FirestoreAdapter:
        """
        Create a Firestore adapter.
        
        Args:
            container: Service container
            
        Returns:
            Firestore adapter
        """
        client = GCPServiceFactory.create_firestore_client(
            project_id=self.project_id,
            credentials_path=self.credentials_path
        )
        
        return FirestoreAdapter(
            client=client,
            project_id=self.project_id,
            connection_pool=self.connection_pools.get("firestore")
        )
    
    def _create_vertex_ai_adapter(self, container: ServiceContainer) -> VertexAIAdapter:
        """
        Create a Vertex AI adapter.
        
        Args:
            container: Service container
            
        Returns:
            Vertex AI adapter
        """
        model_client = GCPServiceFactory.create_model_client(
            project_id=self.project_id,
            credentials_path=self.credentials_path
        )
        
        prediction_client = GCPServiceFactory.create_prediction_client(
            project_id=self.project_id,
            credentials_path=self.credentials_path
        )
        
        return VertexAIAdapter(
            model_client=model_client,
            prediction_client=prediction_client,
            project_id=self.project_id,
            connection_pool=self.connection_pools.get("vertexai")
        )
    
    # Methods for connection pool factories
    
    async def _create_secret_client(self) -> Any:
        """Create a Secret Manager client for the connection pool."""
        return GCPServiceFactory.create_secret_manager_client(
            project_id=self.project_id,
            credentials_path=self.credentials_path
        )
    
    async def _create_storage_client(self) -> Any:
        """Create a Storage client for the connection pool."""
        return GCPServiceFactory.create_storage_client(
            project_id=self.project_id,
            credentials_path=self.credentials_path
        )
    
    async def _create_firestore_client(self) -> Any:
        """Create a Firestore client for the connection pool."""
        return GCPServiceFactory.create_firestore_client(
            project_id=self.project_id,
            credentials_path=self.credentials_path
        )
    
    async def _create_model_client(self) -> Any:
        """Create a Vertex AI Model client for the connection pool."""
        return GCPServiceFactory.create_model_client(
            project_id=self.project_id,
            credentials_path=self.credentials_path
        )
    
    async def _close_client(self, client: Any) -> None:
        """Close a client instance from the connection pool."""
        if hasattr(client, "close") and callable(client.close):
            try:
                # Some clients might have async close
                if inspect.iscoroutinefunction(client.close):
                    await client.close()
                else:
                    client.close()
            except Exception as e:
                logger.warning(f"Error closing client: {e}")