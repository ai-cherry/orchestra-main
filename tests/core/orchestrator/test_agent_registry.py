"""Tests for the simplified agent registry."""

from importlib import import_module

def test_llm_agent_is_default() -> None:
    registry_mod = import_module("core.orchestrator.src.agents.simplified_agent_registry")  # type: ignore
    llm_agent_type = registry_mod.DEFAULT_AGENT_TYPE  # type: ignore[attr-defined]
    assert llm_agent_type == "llm", "LLM agent is not set as default"
