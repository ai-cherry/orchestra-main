#!/usr/bin/env python3
"""
Test script to verify that all required phi imports for the dashboard are working.
"""

import sys
print("Python path:", sys.path)

# Test phi core import
try:
    import phi
    print("✅ Successfully imported phi")
    print("phi version:", phi.__version__ if hasattr(phi, "__version__") else "unknown")
except ImportError as e:
    print(f"❌ Failed to import phi: {e}")
    sys.exit(1)

# Test essential components for dashboard
essential_imports = {
    "phi.agent": "Agent class for creating agents",
    "phi.assistant": "Assistant class (alternative to Agent)",
    "phi.playground": "Playground class for creating the UI dashboard",
    "phi.tools": "Tool classes for agent capabilities",
    "phi.storage.agent.sqlite": "Storage for agent sessions",
    "phi.model.openai": "OpenAI model integration"
}

all_essential_passed = True

print("\nTesting essential dashboard components:")
for module_name, description in essential_imports.items():
    try:
        __import__(module_name)
        print(f"✅ {module_name}: {description}")
    except ImportError as e:
        print(f"❌ {module_name}: {e}")
        all_essential_passed = False

# Test specific tools
tools_to_test = {
    "phi.tools.duckduckgo": "DuckDuckGo search tool",
    "phi.tools.wikipedia": "Wikipedia tool",
    "phi.tools.calculator": "Calculator tool"
}

print("\nTesting agent tools:")
all_tools_passed = True
for module_name, description in tools_to_test.items():
    try:
        __import__(module_name)
        print(f"✅ {module_name}: {description}")
    except ImportError as e:
        print(f"❌ {module_name}: {e}")
        all_tools_passed = False

# Test creating a basic agent
print("\nTesting agent creation:")
try:
    from phi.agent import Agent
    from phi.model.openai import OpenAIChat
    
    # Create a simple agent without executing it
    test_agent = Agent(
        name="Test Agent",
        model=OpenAIChat(id="dummy-model-id")
    )
    print("✅ Successfully created a test agent")
    agent_creation_ok = True
except Exception as e:
    print(f"❌ Error creating test agent: {e}")
    agent_creation_ok = False

# Summary
print("\n📋 Import Test Summary:")
if all_essential_passed and all_tools_passed and agent_creation_ok:
    print("✅ All imports passed! Your Phidata installation appears to be working correctly.")
    print("\nYou can run the dashboard with one of these commands:")
    print("  - Basic dashboard:   ./run_phidata_dashboard.sh")
    print("  - Advanced dashboard: ./run_advanced_dashboard.sh")
else:
    print("❌ Some imports failed. Please check the errors above.")
    
    if not all_essential_passed:
        print("\n🔧 Fix for essential components:")
        print("  pip install -r phidata_requirements.txt")
    
    if not all_tools_passed:
        print("\n🔧 Fix for tools:")
        print("  pip install duckduckgo-search wikipedia")
