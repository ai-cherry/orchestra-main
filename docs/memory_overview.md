# Memory Sub-System

The Orchestra AI platform abstracts short-term and long-term memory behind a **unified in-process interface** so that agents, tools, and services never need to know _where_ information is ultimately persisted.

```
+-------------------+          +----------------------+        +------------------+
|  LLM / Agent API |  <---->  |  UnifiedMemory (API) |  <----> |  Back-end Driver |
+-------------------+          +----------------------+        +------------------+
                                               |                    |  Weaviate
                                               |                    |  Postgres
                                               |                    |  Redis ➜ Dragonfly
                                               |                    |  MongoDB
                                               |                    +------------------+
                                               |
                                        +----------------+
                                        |  LayeredMemory |
                                        +----------------+
```

## Key Modules

| File | Purpose |
|------|---------|
| `core/orchestrator/src/memory/interface.py` | `@runtime_checkable` Protocol that defines the public surface area (✅ 100% typed). |
| `core/orchestrator/src/memory/unified_memory.py` | Thin façade that proxies every call to the currently-configured driver returned by `factory.get_default_memory()` |
| `core/orchestrator/src/memory/layered_memory.py` | An implementation that delegates **short-term** storage to an in-memory cache (Redis/Dragonfly) and **long-term** storage to a vector DB (Weaviate). |
| `core/orchestrator/src/memory/factory.py` | Central point that decides _which_ concrete back-end to instantiate based on environment variables or Pulumi config. |

All production entrypoints (`core/orchestrator/src/main.py`, FastAPI routers, tools, etc.) **only import `UnifiedMemory`** – never a concrete implementation – ensuring perfect swap-ability.

```python
from orchestrator.memory.unified_memory import UnifiedMemory

conversation = UnifiedMemory.get("session:123")
conversation.append("user", "Hello, world!")
```

## Configuration

The factory checks (in order):

1. **Environment variables** – e.g. `ORCHESTRA_MEMORY_BACKEND=weaviate` and `WEAVIATE_REST_ENDPOINT`.
2. **Pulumi config** – secrets are injected automatically by the GitHub Actions deploy workflow.
3. **Fallback** – a pure-python in-process dictionary, suitable for local dev.

No code changes are required when you switch from local dev ➜ staging ➜ prod.

## Extending

Create a new driver that satisfies `MemoryInterface`, register it in `factory.py`, and expose the config knob via an env-var. That's it.
