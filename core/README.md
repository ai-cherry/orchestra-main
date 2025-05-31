# Orchestra AI Core - Modular Architecture

## Overview

This is a clean, modular implementation of the Orchestra AI core system, designed with elegance and maintainability in mind. The architecture follows best practices for separation of concerns, dependency injection, and event-driven communication.

## Architecture

### Phase 1: Infrastructure Foundation 🏗️

#### 1. Deployment Module (`infrastructure/deployment/`)
- **base.py**: Cloud-agnostic deployment abstractions
- **digitalocean.py**: DigitalOcean-specific implementation
- Supports multiple environments (dev, staging, prod)
- Resource sizing and configuration management

#### 2. Service Connectivity (`infrastructure/connectivity/`)
- **base.py**: Service connection interfaces with health checks
- **postgres.py**: PostgreSQL connection with retry logic
- **dragonfly.py**: DragonflyDB (Redis-compatible) connection
- Connection pooling and failover support
- Unified health check system

#### 3. Configuration Management (`infrastructure/config/`)
- **settings.py**: Centralized configuration using Pydantic
- Environment-based configuration
- Type-safe settings with validation
- Feature flags for gradual rollout

### Phase 2: Core Services 🧠

#### 1. Memory Service (`services/memory/`)
- **Layered Architecture**:
  - Short-term: DragonflyDB (hot cache)
  - Mid-term: PostgreSQL (document storage)
  - Long-term: Weaviate (vector search)
- **Smart Policies**:
  - Automatic promotion based on access patterns
  - TTL-based eviction
  - Layer selection based on content type

#### 2. Event Bus (`services/events/`)
- **Decoupled Communication**:
  - Publish/subscribe pattern
  - Priority-based event handling
  - Wildcard subscriptions
  - Event history and statistics

#### 3. Agent Registry (Coming Soon)
- Dynamic agent registration
- Capability-based routing
- Load balancing
- Shadow testing support

## Key Design Principles

### 1. **Single Responsibility**
Each module has one clear purpose:
- Deployment handles infrastructure
- Connectivity manages external services
- Memory handles data persistence
- Events handle communication

### 2. **Dependency Injection**
```python
# Services are injected, not created
memory_service = get_memory_service(service_registry)
```

### 3. **Interface-Based Design**
```python
# All components implement clear interfaces
class MemoryStore(ABC):
    async def store(self, item: MemoryItem) -> bool
    async def retrieve(self, item_id: str) -> Optional[MemoryItem]
```

### 4. **Event-Driven Architecture**
```python
# Components communicate through events
await event_bus.publish("core.initialized", {"services": [...]})
```

## Usage

### Basic Setup

```python
from core.main import get_orchestra_core

# Initialize and run the core
core = get_orchestra_core()
await core.run()
```

### Memory Service

```python
from core.services.memory.unified_memory import get_memory_service

# Store data
item_id = await memory_service.store(
    content={"message": "Hello, Orchestra!"},
    metadata={"user": "alice"},
    layer=MemoryLayer.SHORT_TERM
)

# Retrieve data
item = await memory_service.retrieve(item_id)

# Search across layers
results = await memory_service.search("Hello", limit=10)
```

### Event Bus

```python
from core.services.events.event_bus import get_event_bus

event_bus = get_event_bus()

# Subscribe to events
async def handle_message(event):
    print(f"Received: {event.data}")

event_bus.subscribe("message.received", handle_message)

# Publish events
await event_bus.publish("message.received", {"text": "Hello!"})
```

### Service Registry

```python
from core.infrastructure.connectivity.base import ServiceRegistry

registry = ServiceRegistry()

# Register services
registry.register_service("mongodb", mongodb_connection)

# Health check all services
health_status = await registry.health_check_all()
```

## Configuration

Create a `.env` file:

```env
# Environment
ENVIRONMENT=dev
SECRET_KEY=your-secret-key

# PostgreSQL
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=orchestra

# DragonflyDB
DRAGONFLY_URI=redis://localhost:6379

# Weaviate
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your-api-key

# Feature Flags
FF_USE_NEW_MEMORY_SERVICE=true
FF_ENABLE_COST_OPTIMIZATION=true
```

## Testing

Run tests with pytest:

```bash
pytest tests/test_infrastructure.py -v
```

## Project Structure

```
core/
├── infrastructure/          # Infrastructure layer
│   ├── deployment/         # Cloud deployment
│   ├── connectivity/       # Service connections
│   └── config/            # Configuration
├── services/              # Core services
│   ├── memory/           # Memory management
│   ├── agents/           # Agent system
│   └── events/           # Event bus
├── main.py               # Main entry point
└── README.md            # This file
```

## Next Steps

1. **Agent System**: Implement the agent registry and routing
2. **API Layer**: Add FastAPI endpoints
3. **Monitoring**: Add Prometheus metrics
4. **Tracing**: Add OpenTelemetry support
5. **Admin UI**: Create React dashboard

## Benefits of This Architecture

1. **Modularity**: Each component can be developed and tested independently
2. **Scalability**: Services can be scaled individually
3. **Maintainability**: Clear boundaries and interfaces
4. **Testability**: Easy to mock and test components
5. **Flexibility**: Easy to add new services or replace existing ones

## Contributing

When adding new features:
1. Follow the existing patterns
2. Add appropriate interfaces
3. Include comprehensive tests
4. Update documentation
5. Use type hints throughout

## License

[Your License Here]

## Deployment (Vultr Single Node)

Run the unified stack using Pulumi and Docker Compose:

```bash
pulumi preview --stack=vultr-dev
docker compose -f deploy/docker-compose.vultr.yml config --quiet
```
