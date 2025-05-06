import pytest
from core.orchestrator.src.services.agent_manager import AgentManager
from core.orchestrator.src.agents.base_agent import BaseAgent

class MockAgent(BaseAgent):
    pass

def test_register_and_get_agent():
    manager = AgentManager()
    manager.register("mock_agent", MockAgent)
    retrieved_agent = manager.get("mock_agent")
    assert retrieved_agent == MockAgent

def test_get_nonexistent_agent():
    manager = AgentManager()
    with pytest.raises(ValueError):
        manager.get("nonexistent_agent")

def test_register_non_agent_class():
    manager = AgentManager()
    with pytest.raises(ValueError):
        manager.register("non_agent", int)