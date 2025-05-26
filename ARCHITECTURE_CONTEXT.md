# Orchestra AI Architecture (Post-GCP)

## System Architecture

### Core Services
1. **Orchestrator** (`core/orchestrator/`) - Main coordination service
2. **Memory Manager** - Layered memory system with MongoDB/Redis/Weaviate
3. **Agent System** - Phidata-based agents
4. **API Layer** - FastAPI endpoints

### Memory Architecture
```
┌─────────────────┐
│   Short-term    │ → DragonflyDB (Aiven)
├─────────────────┤
│   Mid-term      │ → MongoDB Atlas
├─────────────────┤
│   Long-term     │ → Weaviate Cloud
└─────────────────┘
```

### External Dependencies
- **LLM Providers**: OpenRouter, OpenAI, Anthropic (via Portkey)
- **Memory Storage**: MongoDB Atlas, DragonflyDB, Weaviate
- **Deployment**: DigitalOcean Droplets

### Development Stack
- Python 3.10
- FastAPI
- Phidata (agent framework)
- Docker Compose (local dev)
- Pulumi (infrastructure as code)
