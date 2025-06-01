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

See `docs/PROJECT_STRUCTURE.md` and `docs/ORCHESTRA_AI_OPERATIONS_GUIDE.md` for full details.
Additional docs:
- [Architecture](docs/ARCHITECTURE.md)
- [Status](docs/STATUS.md)
- [Unified Vultr Setup](docs/UNIFIED_VULTR_ARCHITECTURE.md)

## Persona Memory Architecture
See [docs/PERSONA_MEMORY_ARCHITECTURE.md](docs/PERSONA_MEMORY_ARCHITECTURE.md) for the proposed four-layer memory system and routing approach.

