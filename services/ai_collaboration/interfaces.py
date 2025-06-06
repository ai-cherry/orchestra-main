#!/usr/bin/env python3
"""
Interfaces for AI Collaboration Service
Following SOLID principles with Protocol classes for dependency inversion
"""

from typing import Protocol, Dict, Any, List, Optional, runtime_checkable, Callable
from datetime import datetime
from abc import abstractmethod


@runtime_checkable
class IDatabase(Protocol):
    """Database interface for data persistence"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize database connection"""
        ...
    
    @abstractmethod
    async def close(self) -> None:
        """Close database connection"""
        ...
    
    @abstractmethod
    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute query and fetch all results"""
        ...
    
    @abstractmethod
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Execute query and fetch one result"""
        ...
    
    @abstractmethod
    async def execute(self, query: str, *args) -> None:
        """Execute query without returning results"""
        ...
    
    @abstractmethod
    async def insert(self, table: str, **kwargs) -> Any:
        """Insert record and return ID"""
        ...
    
    @abstractmethod
    async def update(self, table: str, conditions: Dict[str, Any], **kwargs) -> int:
        """Update records and return count"""
        ...
    
    @abstractmethod
    async def delete(self, table: str, conditions: Dict[str, Any]) -> int:
        """Delete records and return count"""
        ...
    
    @abstractmethod
    async def transaction(self):
        """Context manager for transactions"""
        ...


@runtime_checkable
class ICache(Protocol):
    """Cache interface for fast data access"""
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to cache service"""
        ...
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from cache service"""
        ...
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        ...
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value with optional TTL in seconds"""
        ...
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key and return if it existed"""
        ...
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        ...
    
    @abstractmethod
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on existing key"""
        ...
    
    @abstractmethod
    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to channel"""
        ...
    
    @abstractmethod
    async def subscribe(self, *channels: str):
        """Subscribe to channels (returns async iterator)"""
        ...
    
    @abstractmethod
    def pubsub(self):
        """Get pub/sub client"""
        ...


@runtime_checkable
class IMessageQueue(Protocol):
    """Message queue interface for async communication"""
    
    async def publish(self, topic: str, message: Dict[str, Any]) -> None:
        """Publish message to topic"""
        ...
    
    async def subscribe(self, topic: str, handler: Callable) -> None:
        """Subscribe to topic with handler"""
        ...
    
    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from topic"""
        ...


class IVectorStore(Protocol):
    """Vector store interface for semantic search"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize vector store connection"""
        ...
    
    @abstractmethod
    async def index(self, collection: str, data: Dict[str, Any]) -> str:
        """Index data and return ID"""
        ...
    
    @abstractmethod
    async def search(
        self,
        collection: str,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar items"""
        ...
    
    @abstractmethod
    async def delete(self, collection: str, id: str) -> bool:
        """Delete item by ID"""
        ...
    
    @abstractmethod
    async def update(self, collection: str, id: str, data: Dict[str, Any]) -> bool:
        """Update item by ID"""
        ...
    
    @abstractmethod
    async def create_collection(self, name: str, schema: Dict[str, Any]) -> None:
        """Create a new collection"""
        ...
    
    @abstractmethod
    async def delete_collection(self, name: str) -> None:
        """Delete a collection"""
        ...


@runtime_checkable
class IWebSocketAdapter(Protocol):
    """WebSocket adapter interface for real-time communication"""
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to WebSocket endpoint"""
        ...
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from WebSocket"""
        ...
    
    @abstractmethod
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send message through WebSocket"""
        ...
    
    @abstractmethod
    async def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive message from WebSocket"""
        ...
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        ...
    
    @abstractmethod
    async def ping(self) -> bool:
        """Send ping and wait for pong"""
        ...
    
    @abstractmethod
    def set_message_handler(self, handler) -> None:
        """Set handler for incoming messages"""
        ...


@runtime_checkable
class IMetricsCollector(Protocol):
    """Metrics collector interface for performance monitoring"""
    
    @abstractmethod
    async def collect_metric(
        self,
        agent_id: int,
        metric_type: Any,  # MetricType enum
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Collect a metric data point"""
        ...
    
    @abstractmethod
    async def get_metrics(
        self,
        agent_id: Optional[int] = None,
        metric_type: Optional[Any] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get metrics with optional filters"""
        ...
    
    @abstractmethod
    async def aggregate_metrics(
        self,
        agent_id: int,
        metric_type: Any,
        aggregation: str = "avg",
        time_window: int = 300
    ) -> float:
        """Get aggregated metric value"""
        ...
    
    @abstractmethod
    async def flush(self) -> None:
        """Flush any buffered metrics"""
        ...


@runtime_checkable
class ITaskRouter(Protocol):
    """Task router interface for intelligent task assignment"""
    
    @abstractmethod
    async def route_task(self, task: Any) -> int:
        """Route task to appropriate agent and return agent ID"""
        ...
    
    @abstractmethod
    async def get_agent_load(self, agent_id: int) -> Dict[str, Any]:
        """Get current load information for an agent"""
        ...
    
    @abstractmethod
    async def update_routing_rules(self, rules: Dict[str, List[str]]) -> None:
        """Update task routing rules"""
        ...
    
    @abstractmethod
    async def get_routing_metrics(self) -> Dict[str, Any]:
        """Get routing performance metrics"""
        ...


@runtime_checkable
class IEventBus(Protocol):
    """Event bus interface for event-driven architecture"""
    
    @abstractmethod
    async def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event"""
        ...
    
    @abstractmethod
    async def subscribe(self, event_type: str, handler) -> str:
        """Subscribe to event type and return subscription ID"""
        ...
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        ...
    
    @abstractmethod
    async def get_event_history(
        self,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical events"""
        ...


@runtime_checkable
class IHealthChecker(Protocol):
    """Health checker interface for system monitoring"""
    
    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        ...
    
    @abstractmethod
    async def check_component(self, component: str) -> Dict[str, Any]:
        """Check specific component health"""
        ...
    
    @abstractmethod
    async def register_check(self, name: str, check_func) -> None:
        """Register a health check function"""
        ...
    
    @abstractmethod
    async def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health check history"""
        ...


@runtime_checkable
class ICircuitBreaker(Protocol):
    """Circuit breaker interface for fault tolerance"""
    
    @abstractmethod
    async def call(self, func, *args, **kwargs) -> Any:
        """Call function through circuit breaker"""
        ...
    
    @abstractmethod
    def is_open(self) -> bool:
        """Check if circuit is open"""
        ...
    
    @abstractmethod
    def is_closed(self) -> bool:
        """Check if circuit is closed"""
        ...
    
    @abstractmethod
    def get_state(self) -> str:
        """Get current state (open/closed/half-open)"""
        ...
    
    @abstractmethod
    def get_failure_count(self) -> int:
        """Get current failure count"""
        ...
    
    @abstractmethod
    def reset(self) -> None:
        """Reset circuit breaker state"""
        ...


@runtime_checkable
class ILogger(Protocol):
    """Logger interface for structured logging"""
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        ...
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        ...
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        ...
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Log error message"""
        ...
    
    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message"""
        ...
    
    @abstractmethod
    def set_context(self, **kwargs) -> None:
        """Set logging context"""
        ...


@runtime_checkable
class IRepository(Protocol):
    """Generic repository interface for domain entities"""
    
    @abstractmethod
    async def find_by_id(self, id: Any) -> Optional[Any]:
        """Find entity by ID"""
        ...
    
    @abstractmethod
    async def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Find all entities with optional filters"""
        ...
    
    @abstractmethod
    async def save(self, entity: Any) -> Any:
        """Save entity and return it"""
        ...
    
    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """Delete entity by ID"""
        ...
    
    @abstractmethod
    async def exists(self, id: Any) -> bool:
        """Check if entity exists"""
        ...
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filters"""
        ...


# Factory protocols for creating implementations

@runtime_checkable
class IServiceFactory(Protocol):
    """Factory interface for creating service instances"""
    
    @abstractmethod
    def create_database(self) -> IDatabase:
        """Create database instance"""
        ...
    
    @abstractmethod
    def create_cache(self) -> ICache:
        """Create cache instance"""
        ...
    
    @abstractmethod
    def create_vector_store(self) -> IVectorStore:
        """Create vector store instance"""
        ...
    
    @abstractmethod
    def create_websocket_adapter(self) -> IWebSocketAdapter:
        """Create WebSocket adapter instance"""
        ...
    
    @abstractmethod
    def create_metrics_collector(self) -> IMetricsCollector:
        """Create metrics collector instance"""
        ...
    
    @abstractmethod
    def create_task_router(self) -> ITaskRouter:
        """Create task router instance"""
        ...
    
    @abstractmethod
    def create_logger(self, name: str) -> ILogger:
        """Create logger instance"""
        ...