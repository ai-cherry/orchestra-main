# AI cherry_ai Memory Layer Configuration

This document describes the structure, configuration, and best practices for memory management in the AI cherry_ai system.

## Memory Layer Architecture

- **Short-term memory:** Fast, ephemeral storage (Redis/DragonflyDB). Used for recent context and rapid access.
- **Mid-term memory:** Structured storage (Firestore). Used for ongoing conversations and agent state.
- **Long-term memory:** Persistent storage (Firestore/MongoDB). Used for historical data and compliance.
- **Semantic memory:** Vector-based storage (Weaviate or Vertex AI). Used for semantic and similarity search.

## Configuration

All memory layers are parameterized via Pulumi config and environment variables. Key parameters include:
- Storage size (e.g., `dragonfly_storage`, `mongodb_storage`)
- Resource requests/limits (CPU, memory)
- TTL (time-to-live) for each layer
- Promotion/demotion policies

## Performance and Scaling

- **Redis/DragonflyDB:** Optimized for low-latency, high-throughput access. Scale vertically for larger working sets.
- **Firestore/MongoDB:** Designed for durability and query flexibility. Use indexes for frequent queries.
- **Weaviate:** Offloads heavy semantic search from application code. Scale horizontally as data grows.

## Observability

- All memory operations are instrumented with timing and error logging.
- Use `get_stats()` to retrieve per-layer statistics at runtime.
- Monitor resource usage and tune limits as needed.

## Best Practices

- Use semantic memory for all similarity and embedding-based queries.
- Set appropriate TTLs to manage memory pressure.
- Monitor logs for slow operations or errors.
- Document any custom layers or configuration changes.

---

For further details, see the code in [`core/conductor/src/memory/layered_memory.py`](core/conductor/src/memory/layered_memory.py) and infrastructure definitions in [`infra/components/database_component.py`](infra/components/database_component.py).
