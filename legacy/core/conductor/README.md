# conductor README

## Key Components

### Memory System
The conductor employs a layered memory architecture that leverages **Weaviate for efficient semantic search** and **PostgreSQL for structured, mid-term storage**, while **Redis is used for short-term (hot) and warm cache layers, including semantic caching**. Docker is the preferred way to run the full stack locally and for development.

Current managers include:

- `RedisMemoryManager`: Handles short-term, volatile memory with TTL and semantic cache (using Redis Stack or vector search modules).
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

- Use Docker Compose to run the full stack locally: `docker-compose up --build`
- Redis is required for caching and semantic caching. It is included in the Docker Compose setup.
- For manual setup, ensure Redis, Postgres, and Weaviate are running and accessible to the API.

