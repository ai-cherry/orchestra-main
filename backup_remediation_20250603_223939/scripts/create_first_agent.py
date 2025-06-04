#!/usr/bin/env python3
"""
"""
    "q1": "A and B",  # Data collection and task automation
    "q2": "A",  # Fully autonomous to start
    "q3": "B then A then C",  # Starting with unstructured text
    "q4": "all",  # All communication methods
    "q5": "A or B",  # Scheduled or event-driven
    "q6": "hybrid",  # Hybrid complexity
    "q7": "all + natural language",  # All with focus on NL
    "q8": "B,C,D",  # Near real-time to flexible
    "q9": "A or B",  # Fail fast or retry
    "q10": "between A and B",  # Short to long term memory
    "q11": "mix",  # Mixed voice personality
    "q12": "A and B",  # Monitor and process/categorize
    # Additional configuration
    "agent_name": "Data Monitor & Processor",
}

# Map the complex answers to simpler values for the factory
SIMPLIFIED_ANSWERS = {
    "q1": "A",  # Primary: Data collection
    "q2": "A",  # Fully autonomous
    "q3": "unstructured",
    "q4": "all",
    "q5": "event_driven",  # More flexible
    "q6": "medium",
    "q7": "natural_language",
    "q8": "near_real_time",
    "q9": "retry",
    "q10": "short_term",  # Start simple
    "q11": "friendly",  # Conversational
    "q12": "monitor",
    "agent_name": "Data Monitor & Processor",
}

async def test_agent():
    """Test the created agent"""
    print("🤖 Creating your first agent based on questionnaire answers...")

    # Create agent from answers
    agent = create_agent_from_answers(SIMPLIFIED_ANSWERS)

    print(f"\n✅ Created agent: {agent.config.name}")
    print(f"   ID: {agent.config.id}")
    print(f"   Capabilities: {[cap.value for cap in agent.config.capabilities]}")
    print(f"   Autonomy: {agent.custom_config.autonomy_level.value}")

    # Register with agent manager
    agent_manager = get_agent_manager()
    agent_manager.register_agent(agent)

    # Start the agent
    print("\n🚀 Starting agent...")
    await agent.start()

    # Test 1: Send a monitoring task
    print("\n📊 Test 1: Monitoring task")
    await agent_manager._event_bus.publish(
        {
            "type": "agent.message",
            "data": {
                "message": {
                    "sender_id": "test_script",
                    "recipient_id": agent.config.id,
                    "content": "Monitor the system metrics",
                    "metadata": {"type": "monitor", "source": "system_metrics"},
                },
                "sender_id": "test_script",
                "recipient_id": agent.config.id,
            },
        }
    )

    # Give agent time to process
    await asyncio.sleep(2)

    # Test 2: Process data task
    print("\n🔧 Test 2: Process data task")
    agent.add_task(
        {
            "type": "process",
            "content": "Process incoming user data",
            "sender": "test_script",
            "metadata": {"priority": "high"},
        }
    )

    # Give agent time to process
    await asyncio.sleep(2)

    # Test 3: Natural language command
    print("\n💬 Test 3: Natural language interaction")
    await agent_manager._event_bus.publish(
        {
            "type": "agent.message",
            "data": {
                "message": {
                    "sender_id": "user",
                    "recipient_id": agent.config.id,
                    "content": "What's the current status of data collection?",
                    "metadata": {"type": "query"},
                },
                "sender_id": "user",
                "recipient_id": agent.config.id,
            },
        }
    )

    # Give agent time to process
    await asyncio.sleep(2)

    # Check agent state
    print(f"\n📈 Agent Status: {agent.state.status.value}")
    print(f"   Active workflows: {len(agent.state.active_workflows)}")
    print(f"   Messages in queue: {len(agent.state.message_queue)}")

    # Stop agent
    print("\n🛑 Stopping agent...")
    await agent.stop()

    print("\n✅ Test completed!")

def main():
    """Main entry point"""
    print("=" * 60)
    print("🎉 Creating Your First Cherry AI Agent")
    print("=" * 60)
    print("\nBased on your answers:")
    print("- Primary focus: Data collection & Task automation")
    print("- Fully autonomous operation")
    print("- Natural language interface with voice support")
    print("- Near real-time response")
    print("=" * 60)

    # Run the test
    asyncio.run(test_agent())

if __name__ == "__main__":
    main()
