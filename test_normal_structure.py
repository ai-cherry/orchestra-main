"""
Test script to verify the normalized structure works properly.
"""
import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

async def test_imports_and_functionality():
    """Test that imports work and basic functionality is operational."""
    try:
        logger.info("Testing imports...")
        
        # Test importing base models
        from shared.models.base_models import MemoryItem, AgentData, PersonaConfig
        logger.info("✓ Imported shared.models.base_models successfully")
        
        # Test importing memory manager
        from shared.memory.memory_manager import MemoryManager, InMemoryMemoryManager
        logger.info("✓ Imported shared.memory.memory_manager successfully")
        
        # Test importing memory stubs
        from shared.memory.stubs import PatrickMemoryManager
        logger.info("✓ Imported shared.memory.stubs successfully")
        
        # Test importing agent base classes
        from packages.agents.base import BaseAgent
        logger.info("✓ Imported packages.agents.base successfully")
        
        # Test importing agent registry
        from orchestrator.agents.agent_registry import (
            get_registry, register_agent, register_default_agents
        )
        logger.info("✓ Imported orchestrator.agents.agent_registry successfully")
        
        # Test importing echo agent
        from orchestrator.agents.echo_agent import EchoAgent
        logger.info("✓ Imported orchestrator.agents.echo_agent successfully")
        
        # Test creating and using an echo agent
        echo = EchoAgent("test-echo", "Test Echo")
        result = await echo.run({"input_text": "Hello, world!"})
        assert "Echo: Hello, world!" in result["response"]
        logger.info(f"✓ Echo agent response: {result['response']}")
        
        # Test creating and using memory manager
        memory = InMemoryMemoryManager()
        memory_item = MemoryItem(
            id="test1",
            content="Test memory item",
            timestamp=1234567890.0,
            metadata={"test": True}
        )
        await memory.store(memory_item)
        retrieved = await memory.retrieve("test1")
        assert retrieved and retrieved.content == "Test memory item"
        logger.info(f"✓ Memory retrieval works: {retrieved.content}")
        
        # Test registering agents
        register_agent(echo)
        registry = get_registry()
        assert registry.get_agent("test-echo") == echo
        logger.info("✓ Agent registry works")
        
        logger.info("All tests passed! The normalized structure is working correctly.")
        return True
        
    except ImportError as e:
        logger.error(f"Import Error: {e}")
        logger.error(f"Python path: {sys.path}")
        return False
    
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Running structure verification tests...")
    result = asyncio.run(test_imports_and_functionality())
    sys.exit(0 if result else 1)
