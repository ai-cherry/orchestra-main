# AI Orchestra - AI Orchestration System

AI Orchestra is a flexible orchestration system for AI agents, designed to manage interactions between users and AI models through a persona-based architecture.

## Overview

The system coordinates multiple AI agents, maintains conversation memory, provides a unified API for client applications, and handles different LLM providers with robust fallback mechanisms.

## Key Features

- **Persona-Based Interactions**: Dynamic personality selection for contextual responses
- **Memory Management**: Conversation history storage with semantic search capabilities
- **LLM Provider Abstraction**: Support for multiple providers with fallback mechanisms
- **Agent Orchestration**: Coordinate multiple specialized AI agents
- **FastAPI Backend**: Modern, asynchronous API implementation

## System Architecture

The system follows a modular design with clearly separated concerns:

- **Core** (`/core/orchestrator/`): Core orchestration logic and API endpoints
- **Packages** (`/packages/`): Shared libraries for memory, agents, and personas
- **Tests** (`/tests/`): Comprehensive test suite for all components
- **Infrastructure** (`/infra/`): Deployment configuration

## Quick Start

1. Set up environment with required API keys:

```bash
cp .env.example .env
# Edit .env to add your API keys
```

2. Start the API server:

```bash
./run_api.sh
```

3. Test the API with sample requests:

```bash
python test_personas_api_manually.py
```

## Documentation

- **API Documentation**: Available at `http://localhost:8000/docs` when running locally
- **Architecture**: See `AI_CONTEXT.md` for a comprehensive system overview
- **Memory System**: Detailed in `packages/shared/src/memory/MEMORY_CONTEXT.md`
- **LLM Providers**: Explained in `core/orchestrator/src/services/llm/LLM_PROVIDER_CONTEXT.md`

## Development

This project is developed using a containerized environment for consistency:
- Python 3.11
- FastAPI for API development
- Pydantic for data validation
- DevContainer configuration for VS Code

For detailed development information, see the `.devcontainer` directory.

## License

This project is proprietary and not licensed for external use or distribution.
