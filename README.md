# Orchestra AI

Orchestra AI is a modular platform for coordinating multiple AI agents with a unified memory layer and streamlined deployment tooling.

## Features
- **Layered Memory** using PostgreSQL and Weaviate
- **Tool Registry** for dynamic agent tooling
- **Admin UI** for monitoring and configuration
- **Pulumi Infrastructure** targeting a single Vultr server

## Quick Start
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements/development.txt
python tools/orchestra_cli.py init
./start_orchestra.sh
```

Copy `env.example` to `.env` and fill in the persona memory variables:

```
REDIS_DB_CHERRY=0
REDIS_DB_SOPHIA=1
REDIS_DB_KAREN=2
POSTGRES_SCHEMA_CHERRY=cherry
POSTGRES_SCHEMA_SOPHIA=sophia
POSTGRES_SCHEMA_KAREN=karen
NEO4J_URL=bolt://localhost:7687
```

See `docs/PROJECT_STRUCTURE.md` and `docs/ORCHESTRA_AI_OPERATIONS_GUIDE.md` for full details.
Additional docs:
- [Architecture](docs/ARCHITECTURE.md)
- [Status](docs/STATUS.md)
- [Unified Vultr Setup](docs/UNIFIED_VULTR_ARCHITECTURE.md)

## Persona Memory Architecture
The codebase implements a four-layer memory stack as described in
[docs/PERSONA_MEMORY_ARCHITECTURE.md](docs/PERSONA_MEMORY_ARCHITECTURE.md).
Queries are routed via the `PersonaMemoryRouter` which isolates Redis and
PostgreSQL resources per persona and can fetch related context through Neo4j.

