# Agentic Retrieval

This feature introduces a `RetrieverAgent` powered by LlamaIndex. The agent decides which index to query and can iteratively refine results.

The `/api/query` endpoint invokes this agent. If the agent exceeds four retrieval steps or runs longer than 25 seconds the orchestrator falls back to a single ACORN search.
