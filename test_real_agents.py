#!/usr/bin/env python3
"""Test real agents directly."""
sys.path.insert(0, ".")

async def test():
    from agent.app.services.real_agents import get_all_agents, run_agent_task

    print("🔍 Testing Real Agents...")

    # Get all agents
    agents = await get_all_agents()
    print(f"\n✅ Found {len(agents)} real agents:")
    for agent in agents:
        print(f"  - {agent['id']}: {agent['name']} ({agent['type']})")

    # Test running a task
    print("\n🚀 Running test task...")
    result = await run_agent_task("sys-001", "check CPU usage")
    print(f"Result: {result['result']}")

    print("\n✅ Real agents are working!")

if __name__ == "__main__":
    asyncio.run(test())
