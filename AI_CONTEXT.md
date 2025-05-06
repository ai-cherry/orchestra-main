# AI Orchestra - System Context for AI Coding Assistants

This document provides context for AI coding assistants working with this codebase.

## Project Overview

AI Orchestra is an AI Orchestration System designed to manage interactions between users and AI models through a flexible persona-based architecture. The system coordinates multiple AI agents, maintains conversation memory, and provides a unified API for client applications.

## System Architecture

### Core Components

1. **API Layer** (`/core/orchestrator/src/api/`)
   - FastAPI-based REST endpoints for interaction
   - Request/response models and validation
   - Authentication and middleware

2. **Persona System** (`/packages/personas/` and `/core/orchestrator/src/personas/`)
   - Manages different AI personalities and response styles
   - Template-based persona configuration
   - Dynamic persona selection

3. **Memory Management** (`/packages/shared/src/memory/`)
   - Conversation history storage
   - Semantic search for relevant context
   - Session-based memory organization
   - Expiration and cleanup mechanisms

4. **LLM Provider Interface** (`/core/orchestrator/src/services/llm/`)
   - Abstraction for different LLM providers (OpenRouter, Portkey)
   - Fallback mechanisms between providers
   - Error handling and retry logic

5. **Agent System** (`/packages/agents/` and `/core/orchestrator/src/agents/`)
   - Task-specific agent implementations
   - Agent orchestration and coordination
   - Tool usage and function calling

6. **Configuration System** (`/core/orchestrator/src/config/`)
   - Environment-based configuration
   - Settings management
   - Feature flags

### Data Models

Key data models are defined in `/packages/shared/src/models/`:

1. `MemoryItem` - Stores conversation history and context
2. `PersonaConfig` - Defines persona traits and behavior
3. `AgentData` - Contains agent state and processing information

## Key Design Patterns

1. **Registry Pattern** - Service and component registration
2. **Dependency Injection** - Services are provided through DI
3. **Repository Pattern** - Abstraction for data storage
4. **Factory Pattern** - Dynamic creation of components
5. **Strategy Pattern** - Swappable implementations of interfaces

## Memory System

The memory system is designed to maintain conversation context and user preferences:

1. `MemoryManager` interface defines standard operations
2. `InMemoryMemoryManagerStub` provides a simple in-memory implementation
3. `PatrickMemoryManager` offers a more specialized implementation

The memory system stores:
- User interactions (messages, commands)
- Session information
- Persona-specific preferences
- Semantic embeddings for context matching

## Environment Setup

The project is configured to run in a development container with:

1. Python 3.11 as the base runtime
2. FastAPI for the web framework
3. Various LLM integrations (OpenAI, Anthropic, etc.)

## Key Workflows

1. **User Interaction Flow**:
   - Request comes through API
   - Persona is selected or continued
   - Memory context is loaded
   - LLM generates response with persona template
   - Response is stored in memory
   - Formatted response returned to user

2. **Agent Orchestration Flow**:
   - Task is analyzed by orchestrator
   - Appropriate agents are selected
   - Subtasks are assigned to agents
   - Results are collected and synthesized
   - Final response is generated

## Codebase Organization

- `/core/` - Core system components
- `/packages/` - Shared libraries and modules
- `/tests/` - Test suites and mocks
- `/docs/` - Documentation
- `/infra/` - Infrastructure as code for deployment
- `/future/` - Upcoming features in development

## Development Practices

1. Dependency management through requirements files
2. Environment variables for configuration
3. FastAPI for API development
4. Pydantic for data validation
5. Comprehensive logging
6. Error handling with specific exception types
7. Automated testing through pytest

## Key Integrations

1. LLM Providers
   - OpenRouter (primary)
   - Portkey (fallback)
   - Direct provider integrations

2. Cloud Services
   - GCP for deployment
   - Cloud Run for containerized services
   - Vertex AI for specialized ML workloads

## Advanced Features

1. **Enhanced Interaction** - Template-based persona responses
2. **Semantic Search** - Finding relevant context in conversation history
3. **Multi-provider Fallback** - Graceful degradation between LLM providers
4. **Session Management** - Maintaining conversational context
5. **Error Recovery** - Robust error handling and fallback mechanisms

## Common Tasks and Patterns

When developing for this system:

1. Use the registry pattern for new services
2. Follow the established error handling patterns
3. Validate inputs with Pydantic models
4. Update memory context appropriately
5. Add proper logging at appropriate levels
6. Follow existing patterns for LLM interaction

This document should be updated as the system evolves to maintain an accurate reference for AI coding assistants.