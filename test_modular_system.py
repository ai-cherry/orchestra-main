"""
Test script for the modular Orchestra AI system.

This script tests the core functionality of the modular architecture.
"""

import asyncio
import logging

from core.business.personas.base import PersonaConfig, PersonaTrait, ResponseStyle, get_persona_manager
from core.business.workflows.examples import register_example_workflows
from core.main import OrchestraSystem
from core.services.agents.examples import register_example_agents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_system():
    """Test the modular Orchestra AI system."""
    logger.info("Starting modular system test...")

    # Initialize Orchestra system
    orchestra = OrchestraSystem()
    await orchestra.initialize()
    logger.info("✓ Orchestra system initialized")

    # Register workflows
    register_example_workflows()
    logger.info("✓ Example workflows registered")

    # Register agents
    register_example_agents()
    logger.info("✓ Example agents registered")

    # Register personas
    persona_manager = get_persona_manager()
    persona_manager.register_persona(
        PersonaConfig(
            id="test_assistant",
            name="Test Assistant",
            description="A test AI assistant",
            traits=[PersonaTrait.HELPFUL, PersonaTrait.CONCISE],
            style=ResponseStyle.TECHNICAL,
        )
    )
    logger.info("✓ Test persona registered")

    # Test workflow execution
    from core.business.workflows.base import get_workflow_engine

    workflow_engine = get_workflow_engine()

    logger.info("\nTesting document analysis workflow...")
    try:
        context = await workflow_engine.execute_workflow(
            workflow_name="document_analysis",
            inputs={
                "document_id": "test_doc_1",
                "document": "This is a test document about artificial intelligence and machine learning. It discusses various algorithms and their applications in modern technology.",
            },
        )
        logger.info("✓ Workflow completed successfully")
        logger.info(f"  Summary: {context.outputs.get('summary', 'N/A')[:100]}...")
        logger.info(f"  Keywords: {context.outputs.get('keywords', [])}")
    except Exception as e:
        logger.error(f"✗ Workflow failed: {e}")

    # Test agent communication
    from core.services.agents.base import get_agent_manager

    agent_manager = get_agent_manager()

    logger.info("\nStarting agents...")
    await agent_manager.start_all_agents()
    logger.info("✓ All agents started")

    # List agents
    agents = agent_manager.list_agents()
    logger.info(f"\nRegistered agents ({len(agents)}):")
    for agent in agents:
        logger.info(f"  - {agent.name} ({agent.id}): {', '.join(cap.value for cap in agent.capabilities)}")

    # Test memory service
    from core.services.memory.unified_memory import get_memory_service

    memory_service = get_memory_service()

    logger.info("\nTesting memory service...")
    await memory_service.store(
        key="test:item",
        value={"data": "test value", "timestamp": "2024-01-01"},
        metadata={"type": "test"},
    )

    retrieved = await memory_service.get("test:item")
    logger.info(f"✓ Memory store/retrieve: {retrieved}")

    # Test event bus
    from core.services.events.event_bus import Event, get_event_bus

    event_bus = get_event_bus()

    logger.info("\nTesting event bus...")
    test_event_received = False

    async def test_handler(event: Event):
        nonlocal test_event_received
        test_event_received = True
        logger.info(f"✓ Event received: {event.type}")

    await event_bus.subscribe("test.event", test_handler)
    await event_bus.publish(Event(type="test.event", data={"test": "data"}))
    await asyncio.sleep(0.1)  # Give time for async processing

    if test_event_received:
        logger.info("✓ Event bus working correctly")
    else:
        logger.error("✗ Event bus test failed")

    # Shutdown
    logger.info("\nShutting down...")
    await agent_manager.stop_all_agents()
    await orchestra.shutdown()
    logger.info("✓ System shut down successfully")

    logger.info("\n=== All tests completed ===")

if __name__ == "__main__":
    asyncio.run(test_system())
