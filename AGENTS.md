# AGENTS.md

## Orchestra AI Agent Management Guide

This document provides clear, actionable guidance for configuring, registering, and managing agents in the Orchestra AI platform. It is designed for a single-developer/admin context and is kept up-to-date with best practices and new features.

---

## 1. Agent Overview

- **Agents** are modular, autonomous components that perform orchestration, enrichment, or workflow tasks.
- Each agent is registered with the Orchestrator backend and can be managed via the admin interface.
- Agents interact with memory, external APIs, and other agents via well-defined interfaces.

---

## 2. Agent Configuration

- Agent configuration is centralized in `core/env_config.py` and/or `orchestrator/agents/config.py`.
- All environment variables and secrets should be managed via the centralized settings object.
- Example agent configuration block:

```python
from core.env_config import settings

class MyAgentConfig:
    api_key = settings.my_agent_api_key
    endpoint = settings.my_agent_endpoint
    # Add additional agent-specific config here
```

---

## 3. Agent Registration

- Agents are registered at orchestrator startup via the agent registry.
- To register a new agent:
  1. Implement the agent class, inheriting from the base agent interface.
  2. Add the agent to the registry in `orchestrator/agents/registry.py`.
  3. Ensure the agent is included in the orchestrator's startup sequence.

---

## 4. Agent Lifecycle Management

- Agents can be started, stopped, and restarted via the admin interface or orchestrator API.
- Use the `/agents` endpoint for programmatic management.
- Agent health and status are monitored and exposed via `/health` and `/agents/status`.

---

## 5. Best Practices

- **Single Responsibility:** Each agent should have a clear, focused purpose.
- **Statelessness:** Prefer stateless agents; use memory or external stores for persistence.
- **Error Handling:** Implement robust error handling and logging using the centralized logging system.
- **Security:** Store all secrets in the centralized config; never hardcode credentials.
- **Testing:** Provide unit and integration tests for all agent logic.

---

## 6. Example Agent Workflow

1. **Initialization:** Agent loads config and registers with orchestrator.
2. **Execution:** Agent receives a task via API or workflow trigger.
3. **Processing:** Agent interacts with memory, APIs, or other agents as needed.
4. **Result:** Agent returns result/status to orchestrator and logs the operation.

---

## 7. Troubleshooting

- Use the admin interface to view agent logs, status, and recent actions.
- Check centralized logs for errors or warnings.
- Use the `/agents/test` endpoint to validate agent functionality.

---

## 8. Updating This Guide

- Update this file whenever new agent features, patterns, or best practices are introduced.
- Keep examples and references current with the codebase.
