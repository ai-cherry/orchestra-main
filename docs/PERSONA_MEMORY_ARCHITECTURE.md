# Persona-Aware Memory Architecture

This document outlines the proposed four-layer memory system and persona routing approach.

## Four-Layer Memory Stack

1. **Episodic Memory – Redis Cluster**
   - Separate databases per persona (Cherry, Sophia, Karen).
   - Short term context with TTL matching domain needs.
2. **Semantic Memory – Weaviate Vector DB**
   - Namespaces per persona with cross references for shared concepts.
3. **Procedural Memory – PostgreSQL**
   - Persona specific schemas storing workflow information.
4. **Meta-Memory – Neo4j**
   - Knowledge graph describing relationships between personas and tasks.

## PersonaMemoryRouter

A new `PersonaMemoryRouter` will route queries across memory layers based on the active persona.

```python
class PersonaMemoryRouter:
    def __init__(self, active_persona: str):
        self.persona = active_persona
        self.episodic = RedisCluster(namespace=active_persona)
        self.semantic = WeaviateClient(class_prefix=active_persona)
        self.procedural = PostgresSchema(schema_name=active_persona)
        self.meta = Neo4jGraph()

    def query(self, query: str, context: dict):
        episodic_results = self.episodic.search(context.get("time_window"))
        semantic_hits = self.semantic.hybrid_search(query)
        procedural_flows = self.procedural.match_workflow(context)
        return self._rank_results(episodic_results, semantic_hits, procedural_flows)
```

## Implementation Tasks

- Consolidate existing memory managers under `core/services/memory/unified_memory.py`.
- Add Neo4j integration for meta-memory and cross-persona queries.
- Extend configuration files to support persona specific Redis DBs and Postgres schemas.
- Update documentation and `.env.example` with new environment variables.
- Provide unit tests ensuring persona isolation and cross-persona queries.

