# AI Orchestra MCP & LLM Gateway Integration Guide

## Overview

This guide documents the architecture and best practices for integrating Model Context Protocol (MCP) servers and a unified LLM gateway (LiteLLM) with SuperAGI, MongoDB, and Weaviate in the AI Orchestra project. It also covers modular Pulumi infrastructure, secure CI/CD, and AI-powered development workflows.

---

## Architecture Summary

- **SuperAGI**: Orchestrates multi-agent workflows, deployed as a Kubernetes service.
- **MongoDB**: Used for mid/long-term memory, accessed via MCP server for natural language queries.
- **Weaviate**: Provides semantic search, accessed via MCP server for vector-based queries.
- **DragonflyDB**: Used for ephemeral/short-term memory, accessed directly (no MCP).
- **LiteLLM**: Self-hosted, OpenAI-compatible LLM gateway for unified access to multiple LLM providers.
- **Pulumi**: Manages all infrastructure as code, with modular components for each service.
- **GitHub Actions**: Automates CI/CD, secret injection, and stack deployments.
- **Cursor AI**: Accelerates code generation, debugging, and workflow automation.

---

## LiteLLM Integration

- **LiteLLM Gateway**: Deployed as a Kubernetes deployment/service using a Pulumi component. Provides a unified, OpenAI-compatible API for SuperAGI and other agents.
- **API Keys**: Managed via Pulumi ESC and injected as Kubernetes secrets.
- **SuperAGI Configuration**:
  - The LiteLLM endpoint is injected into the SuperAGI config as the `llm_gateway_url`.
  - Example config snippet:
    ```yaml
    llm_gateway_url: http://litellm:4000
    ```
- **Agent-Side Model Selection**:
  - Agents can select models based on task type, leveraging LiteLLM’s unified API.
  - Example:
    ```python
    import litellm

    class SuperAGIAgent:
        def __init__(self):
            self.model_map = {
                "summarize": "anthropic/claude-3-sonnet",
                "analyze": "openai/gpt-4o",
                "generate": "huggingface/meta-llama-3"
            }

        def select_model(self, task_type):
            return self.model_map.get(task_type, "openai/gpt-4o")

        def run_task(self, task_type, prompt):
            model = self.select_model(task_type)
            response = litellm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response["choices"][0]["message"]["content"]
    ```

---

## MCP Integration

- **MongoDB MCP Server**: Deployed as a Kubernetes deployment/service. SuperAGI is configured to use its endpoint for natural language queries.
- **Weaviate MCP Server**: Deployed similarly, enabling semantic search for agents.
- **DragonflyDB**: Accessed directly for performance; no MCP server required.
- **SuperAGI Configuration**:
  - MCP endpoints are injected into the SuperAGI config via Pulumi.
  - Example config snippet:
    ```yaml
    mcp:
      mongodb:
        enabled: true
        endpoint: http://mcp-mongodb:8080
      weaviate:
        enabled: true
        endpoint: http://mcp-weaviate:8080
    ```

---

## Pulumi Modularization

- Each major service is defined as a Pulumi `ComponentResource` (see `infra/components/`).
- Stacks are separated by environment (`dev`, `prod`) and by function (infrastructure, database, ai-deployment).
- Secrets are managed via Pulumi ESC and injected securely into Kubernetes.
- Example usage:
  ```python
  from components.litellm_component import LiteLLMComponent
  litellm = LiteLLMComponent(
      "orchestra-litellm",
      config={
          "namespace": "superagi",
          "image": "berriai/litellm:latest",
          "replicas": 1,
          "api_keys": {
              "OPENAI_API_KEY": "...",
              "ANTHROPIC_API_KEY": "...",
              "HUGGINGFACE_API_KEY": "...",
          },
          "port": 4000,
      },
      opts=ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
  )
  ```

---

## CI/CD & GitHub Actions

- All deployments are automated via GitHub Actions.
- Pulumi previews run on pull requests; deployments run on merges.
- Secrets are injected via Pulumi ESC and OIDC authentication.
- Branch protection and code review are enforced.

---

## AI Coding with Cursor

- Use Cursor AI for generating Pulumi scripts, MCP integrations, and debugging.
- Always validate AI-generated code and use detailed prompts for best results.
- Example prompt:
  > "Write a Python function to query Weaviate via MCP for semantic search, handling errors and logging results."

---

## Best Practices & Pitfalls

- **Test MCP servers and LiteLLM thoroughly** before production use; they are early-stage.
- **Do not MCP-wrap DragonflyDB** unless standardization is critical.
- **Keep Pulumi stacks modular** to avoid dependency hell.
- **Never store secrets in code or logs**; always use Pulumi ESC.
- **Document all configuration and integration points** for maintainability.

---

## References

- [Pulumi Recommended Patterns](https://www.pulumi.com/blog/recommended-patterns-the-basics/)
- [SuperAGI Documentation](https://superagi.com)
- [Model Context Protocol (MCP)](https://www.anthropic.com/news/model-context-protocol)
- [MongoDB MCP Server](https://www.mongodb.com/blog/post/announcing-mongodb-mcp-server)
- [Weaviate MCP Server](https://pulsemcp.ai/servers/weaviate)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [Cursor AI Guide](https://www.cursor.com/blog/10-practical-examples)

---

For further details, see the code in `infra/components/` and the main stack in `infra/main.py`.
