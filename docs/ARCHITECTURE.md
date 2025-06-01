# Orchestra AI Architecture (Unified Vultr Server)

## System Architecture

### Core Services
1. **Orchestrator** (`agent/app/main.py`) – FastAPI application that routes API requests and coordinates agents, memory, and tools.
2. **Memory Layer** – Multi-tier memory (Redis short-term, Postgres mid-term, Weaviate vector long-term).
3. **Agent System** – Async Python agents (phidata style) running in-process workers.
4. **Admin UI** – React/Vite application served by Nginx.

### Memory Architecture (Current)

```
┌──────────────────┐
│ Short-term cache │ → Redis 5 (local)
├──────────────────┤
│ Mid-term store   │ → PostgreSQL 14 (local)
├──────────────────┤
│ Long-term vector │ → Weaviate 1.24 (docker)
└──────────────────┘
```

### External Dependencies
• **LLM Providers:** OpenAI GPT-4o, Anthropic Claude 3 (via Portkey)
• **Storage:** Postgres, Redis, Weaviate (all local to Vultr server)
• **Hosting:** Single Vultr dedicated instance

### Development Stack
- Python 3.10
- FastAPI
- Phidata (agent framework)
- Docker (only for Weaviate)
- Bash scripts for deploy & backup (no Pulumi/terraform in production)
