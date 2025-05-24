# Claude Assistant Instructions

## Project Overview

This is the Orchestra system - a comprehensive AI orchestration platform with agent management, memory systems, and GCP integration.

## Key Commands to Run

### Linting and Type Checking

Before committing any changes, always run:

```bash
# Python linting
ruff check .

# Python type checking
mypy .

# If frontend changes were made:
cd admin-interface && npm run lint
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_example.py
```

### Development Setup

```bash
# Activate virtual environment
source activate_venv.sh

# Install dependencies
pip install -r requirements.txt
```

## Project Structure

- `/core/orchestrator/` - Main orchestration logic and API
- `/mcp_server/` - MCP (Model Context Protocol) server implementation
- `/admin-interface/` - React-based admin dashboard
- `/config/` - Configuration files for agents, LLM, and modes
- `/docs/` - Documentation files
- `/tests/` - Test suite

## Important Guidelines

1. **Always run linting before commits** - Use `ruff check .` and fix any issues
2. **Follow existing patterns** - Check neighboring files for code style
3. **No hardcoded credentials** - Use environment variables or GCP Secret Manager
4. **Test your changes** - Write and run tests for new functionality
5. **Memory optimization** - This project prioritizes performance and memory efficiency

## Common Tasks

### Adding a New Agent

1. Define agent in `/config/agents.yaml`
2. Implement agent class in `/core/orchestrator/src/agents/`
3. Register in the agent registry
4. Add tests

### Working with Memory System

- Memory managers are in `/mcp_server/managers/`
- Storage backends in `/mcp_server/storage/`
- Always consider performance implications

### API Development

- API endpoints are in `/core/orchestrator/src/api/endpoints/`
- Follow FastAPI patterns
- Add proper error handling

## Environment Variables

Key environment variables to set:

- `GOOGLE_CLOUD_PROJECT` - GCP project ID
- `OPENAI_API_KEY` - For LLM operations
- `REDIS_URL` - Redis connection string (if using Redis backend)

## Deployment

The system can be deployed to:

- Google Cloud Run
- Local Docker containers
- Development server with `uvicorn`

## Troubleshooting

- Check `/docs/TROUBLESHOOTING_GUIDE.md` for common issues
- Ensure all required APIs are enabled in GCP
- Verify credentials are properly configured
