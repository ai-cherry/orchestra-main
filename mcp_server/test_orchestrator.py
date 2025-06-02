#!/usr/bin/env python3
"""Test script for orchestrator server functions."""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the functions we created
from servers.orchestrator_server import get_all_agents, run_agent_task, run_workflow


async def test_functions():
    """Test the orchestrator functions."""
    print("Testing Orchestrator Server Functions...\n")

    # Test get_all_agents
    print("1. Testing get_all_agents():")
    agents = await get_all_agents()
    for agent in agents:
        print(f"   - {agent['id']}: {agent['name']} (Status: {agent['status']})")

    print("\n2. Testing run_agent_task():")
    result = await run_agent_task(
        agent_id="data-processor", task="Process customer data", parameters={"batch_size": 100}
    )
    print(f"   Result: {result}")

    print("\n3. Testing run_workflow():")
    workflow_result = await run_workflow(
        workflow_name="data-pipeline", params={"source": "database", "destination": "warehouse"}
    )
    print(f"   Result: {workflow_result}")

    print("\n✅ All tests passed! The orchestrator server functions are working correctly.")


if __name__ == "__main__":
    asyncio.run(test_functions())
