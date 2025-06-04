# Weaviate Agents Runtime

To enable Weaviate's built-in Agents runtime, mount `deploy/agents-config.yaml` into the `weaviate` service and ensure the `agents` module is enabled.

The conductor exposes `/api/query` which forwards payloads to `http://weaviate:8080/agent/query`.
