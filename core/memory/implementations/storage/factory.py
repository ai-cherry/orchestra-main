"""
Storage Factory

Factory pattern implementation for creating storage backends based on configuration.
"""

from typing import Dict, Type, Optional
import logging

from ...interfaces import IMemoryStorage, MemoryTier
from ...config import MemoryConfig, PostgreSQLConfig, WeaviateConfig, RedisConfig
from ...exceptions import MemoryConfigurationError

logger = logging.getLogger(__name__)

class MemoryStorageFactory:
    """
    Factory for creating storage backend instances.
    
    This factory implements the Abstract Factory pattern to create
    appropriate storage backends based on tier and configuration.
    """
    
    # Registry of storage implementations
    _storage_classes: Dict[MemoryTier, Type[IMemoryStorage]] = {}
    
    @classmethod
    def register_storage(
        cls,
        tier: MemoryTier,
        storage_class: Type[IMemoryStorage]
    ) -> None:
        """
        Register a storage implementation for a tier.
        
        Args:
            tier: The memory tier
            storage_class: The storage class to use for this tier
        """
        cls._storage_classes[tier] = storage_class
        logger.info(f"Registered {storage_class.__name__} for tier {tier.value}")
    
    @classmethod
    def create_storage(
        cls,
        tier: MemoryTier,
        config: MemoryConfig
    ) -> IMemoryStorage:
        """
        Create a storage instance for the specified tier.
        
        Args:
            tier: The memory tier to create storage for
            config: The memory system configuration
            
        Returns:
            An initialized storage instance
            
        Raises:
            MemoryConfigurationError: If no storage is registered for the tier
        """
        if tier not in cls._storage_classes:
            raise MemoryConfigurationError(
                config_section="storage_factory",
                parameter="tier",
                value=tier.value,
                reason=f"No storage implementation registered for tier {tier.value}"
            )
        
        storage_class = cls._storage_classes[tier]
        
        # Get tier-specific configuration
        tier_config = config.tiers.get(tier.value)
        if not tier_config or not tier_config.enabled:
            raise MemoryConfigurationError(
                config_section="storage_factory",
                parameter="tier_config",
                value=tier.value,
                reason=f"Tier {tier.value} is not enabled in configuration"
            )
        
        # Create storage instance with appropriate config
        logger.info(f"Creating {storage_class.__name__} for tier {tier.value}")
        
        try:
            if tier == MemoryTier.L0_CPU_CACHE:
                from .inmemory import InMemoryStorage
                return InMemoryStorage(
                    tier=tier,
                    max_size_bytes=tier_config.max_size_bytes,
                    max_items=tier_config.max_items,
                    eviction_policy=tier_config.eviction_policy
                )
                
            elif tier == MemoryTier.L1_PROCESS_MEMORY:
                from .inmemory import InMemoryStorage
                return InMemoryStorage(
                    tier=tier,
                    max_size_bytes=tier_config.max_size_bytes,
                    max_items=tier_config.max_items,
                    eviction_policy=tier_config.eviction_policy
                )
                
            elif tier == MemoryTier.L2_SHARED_MEMORY:
                from .shared import SharedMemoryStorage
                return SharedMemoryStorage(
                    tier=tier,
                    max_size_bytes=tier_config.max_size_bytes,
                    redis_config=config.redis
                )
                
            elif tier == MemoryTier.L3_POSTGRESQL:
                from .postgresql import PostgreSQLStorage
                return PostgreSQLStorage(
                    tier=tier,
                    config=config.postgresql,
                    table_name="memory_items"
                )
                
            elif tier == MemoryTier.L4_WEAVIATE:
                from .weaviate import WeaviateStorage
                return WeaviateStorage(
                    tier=tier,
                    config=config.weaviate
                )
                
            else:
                raise MemoryConfigurationError(
                    config_section="storage_factory",
                    parameter="tier",
                    value=tier.value,
                    reason=f"Unknown tier: {tier.value}"
                )
                
        except Exception as e:
            logger.error(f"Failed to create storage for tier {tier.value}: {str(e)}")
            raise MemoryConfigurationError(
                config_section="storage_factory",
                parameter="storage_creation",
                value=tier.value,
                reason=f"Failed to create storage: {str(e)}",
                cause=e
            )
    
    @classmethod
    def create_all_storages(
        cls,
        config: MemoryConfig
    ) -> Dict[MemoryTier, IMemoryStorage]:
        """
        Create storage instances for all enabled tiers.
        
        Args:
            config: The memory system configuration
            
        Returns:
            Dictionary mapping tiers to storage instances
        """
        storages = {}
        
        for tier in MemoryTier:
            tier_config = config.tiers.get(tier.value)
            if tier_config and tier_config.enabled:
                try:
                    storage = cls.create_storage(tier, config)
                    storages[tier] = storage
                    logger.info(f"Created storage for tier {tier.value}")
                except Exception as e:
                    logger.warning(
                        f"Failed to create storage for tier {tier.value}: {str(e)}"
                    )
                    # Continue with other tiers
        
        if not storages:
            raise MemoryConfigurationError(
                config_section="storage_factory",
                parameter="enabled_tiers",
                value="none",
                reason="No storage tiers are enabled in configuration"
            )
        
        return storages
    
    @classmethod
    def validate_storage_config(
        cls,
        tier: MemoryTier,
        config: MemoryConfig
    ) -> bool:
        """
        Validate that required configuration exists for a tier.
        
        Args:
            tier: The memory tier
            config: The memory system configuration
            
        Returns:
            True if configuration is valid
        """
        try:
            # Check tier config exists and is enabled
            tier_config = config.tiers.get(tier.value)
            if not tier_config or not tier_config.enabled:
                return False
            
            # Check backend-specific config
            if tier == MemoryTier.L2_SHARED_MEMORY:
                config.redis.validate()
            elif tier == MemoryTier.L3_POSTGRESQL:
                config.postgresql.validate()
            elif tier == MemoryTier.L4_WEAVIATE:
                config.weaviate.validate()
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed for tier {tier.value}: {str(e)}")
            return False

# Auto-registration of default storage implementations
def _register_default_storages():
    """Register default storage implementations."""
    try:
        from .inmemory import InMemoryStorage
        from .shared import SharedMemoryStorage
        from .postgresql import PostgreSQLStorage
        from .weaviate import WeaviateStorage
        
        MemoryStorageFactory.register_storage(MemoryTier.L0_CPU_CACHE, InMemoryStorage)
        MemoryStorageFactory.register_storage(MemoryTier.L1_PROCESS_MEMORY, InMemoryStorage)
        MemoryStorageFactory.register_storage(MemoryTier.L2_SHARED_MEMORY, SharedMemoryStorage)
        MemoryStorageFactory.register_storage(MemoryTier.L3_POSTGRESQL, PostgreSQLStorage)
        MemoryStorageFactory.register_storage(MemoryTier.L4_WEAVIATE, WeaviateStorage)
        
    except ImportError as e:
        logger.warning(f"Failed to register default storages: {str(e)}")

# Register defaults on module import
_register_default_storages()