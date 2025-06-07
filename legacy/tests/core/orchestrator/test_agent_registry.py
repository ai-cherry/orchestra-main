"""Tests for the simplified agent registry."""
    registry_mod = import_module("core.conductor.src.agents.simplified_agent_registry")  # type: ignore
    llm_agent_type = registry_mod.DEFAULT_AGENT_TYPE  # type: ignore[attr-defined]
    assert llm_agent_type == "llm", "LLM agent is not set as default"
