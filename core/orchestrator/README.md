# Orchestrator README

## Key Components

### Memory System
The Orchestrator employs a layered memory architecture that leverages **Weaviate for efficient semantic search** and **PostgreSQL for structured, mid-term storage**, while Redis remains the short-term cache.  Current managers include:

- `RedisMemoryManager`: Handles short-term, volatile memory with TTL.
- `WeaviateMemoryManager`: Manages interactions with the Weaviate vector database for long-term semantic memory and search.
- `PostgresMemoryManager`: Manages interactions with PostgreSQL for structured mid-term memory and relational queries.

### Personas System
*(unchanged content)*

### Agents System
*(unchanged content)*

## Future Enhancements
- Enhanced context-window compression for very long conversations.
- Automatic memory consolidation policies.
*(removed obsolete bullet about vector database, all other bullets retained)*

## Getting Started
*(unchanged content)*

