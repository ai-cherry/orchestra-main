#!/usr/bin/env python3
"""
Test Natural Language Interface and Simple Agent Demo
"""

import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.app.services.natural_language_processor import (
    IntentClassifier, 
    ResponseGenerator,
    IntentCategory
)

# Simple Agent Demo (without full infrastructure)
class SimpleAgent:
    def __init__(self, name="Data Monitor & Processor"):
        self.name = name
        self.id = f"agent_{datetime.now().timestamp()}"
        self.task_history = []
        self.status = "idle"
        
    async def process_task(self, task_type, data):
        """Process a task and return results"""
        self.status = "processing"
        
        if task_type == "monitor":
            result = {
                "status": "success",
                "data": {
                    "cpu_usage": 45.2,
                    "memory_usage": 62.8,
                    "active_connections": 127,
                    "timestamp": datetime.now().isoformat()
                },
                "summary": "System metrics collected successfully"
            }
        elif task_type == "process":
            result = {
                "status": "success", 
                "processed_items": 42,
                "summary": f"Processed {data.get('items', 'data')} successfully"
            }
        else:
            result = {
                "status": "completed",
                "summary": f"General task '{task_type}' completed"
            }
            
        self.task_history.append({
            "task": task_type,
            "result": result,
            "timestamp": datetime.now()
        })
        
        self.status = "idle"
        return result

async def test_natural_language():
    """Test the natural language interface"""
    print("\n🧪 Testing Natural Language Interface")
    print("=" * 50)
    
    # Initialize components
    classifier = IntentClassifier()
    response_gen = ResponseGenerator()
    
    # Test commands
    test_commands = [
        "Show me agent status",
        "Monitor the system metrics",
        "Process the pending invoices",
        "Help",
        "What can you do?"
    ]
    
    for cmd in test_commands:
        print(f"\n📝 Command: '{cmd}'")
        
        # Classify intent
        intent = await classifier.classify(cmd)
        print(f"   Intent: {intent.category.value}")
        print(f"   Action: {intent.action}")
        if intent.entities:
            print(f"   Entities: {intent.entities}")
        
        # Generate response
        mock_result = {"status": "success", "data": {"test": True}}
        response = await response_gen.generate(intent, mock_result)
        print(f"   Response: {response}")

async def test_simple_agent():
    """Test the simple agent"""
    print("\n\n🤖 Testing Simple Agent")
    print("=" * 50)
    
    agent = SimpleAgent()
    print(f"Created agent: {agent.name}")
    print(f"Agent ID: {agent.id}")
    
    # Test 1: Monitor task
    print("\n📊 Test 1: Monitor system metrics")
    result = await agent.process_task("monitor", {"source": "system"})
    print(f"Result: {result['summary']}")
    print(f"Data: {result['data']}")
    
    # Test 2: Process task
    print("\n🔧 Test 2: Process data")
    result = await agent.process_task("process", {"items": "user data"})
    print(f"Result: {result['summary']}")
    print(f"Processed items: {result['processed_items']}")
    
    # Show task history
    print(f"\n📜 Task History ({len(agent.task_history)} tasks):")
    for task in agent.task_history:
        print(f"   - {task['task']}: {task['result']['status']} at {task['timestamp'].strftime('%H:%M:%S')}")

async def test_nl_to_agent():
    """Test natural language commands controlling the agent"""
    print("\n\n🎯 Testing Natural Language to Agent Control")
    print("=" * 50)
    
    classifier = IntentClassifier()
    agent = SimpleAgent()
    
    # Natural language commands
    nl_commands = [
        "Monitor the system performance",
        "Process the incoming data stream",
        "Show me what tasks you've completed"
    ]
    
    for cmd in nl_commands:
        print(f"\n💬 User: '{cmd}'")
        
        # Classify intent
        intent = await classifier.classify(cmd)
        
        # Execute based on intent
        if intent.category == IntentCategory.AGENT_CONTROL and "monitor" in cmd.lower():
            result = await agent.process_task("monitor", {"source": "system"})
            print(f"🤖 Agent: Monitoring complete. {result['summary']}")
            
        elif intent.category == IntentCategory.WORKFLOW and "process" in cmd.lower():
            result = await agent.process_task("process", {"items": "data stream"})
            print(f"🤖 Agent: {result['summary']}")
            
        elif "completed" in cmd.lower():
            print(f"🤖 Agent: I've completed {len(agent.task_history)} tasks:")
            for task in agent.task_history:
                print(f"    - {task['task']}: {task['result']['summary']}")
        else:
            print(f"🤖 Agent: I understood your request about {intent.category.value}")

async def main():
    """Run all tests"""
    print("=" * 60)
    print("🎉 Orchestra AI - Natural Language & Agent Demo")
    print("=" * 60)
    
    # Test natural language processing
    await test_natural_language()
    
    # Test simple agent
    await test_simple_agent()
    
    # Test NL to agent control
    await test_nl_to_agent()
    
    print("\n\n✅ All tests completed!")
    print("\nNext steps:")
    print("1. Add your RESEMBLE_API_KEY to enable voice synthesis")
    print("2. Connect real data sources for monitoring")
    print("3. Implement specific workflows for your use case")

if __name__ == "__main__":
    asyncio.run(main()) 