#!/usr/bin/env python3
"""
"""
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("cherry_ai_API_KEY", "4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd")

# Test commands
TEST_COMMANDS = [
    # Agent control
    "Show me agent status",
    "Start the system agent",
    "Stop the analyzer agent",
    # Queries
    "What's the current system status?",
    "Show me recent activities",
    "List all available resources",
    # Workflows
    "Process pending items",
    "Generate status report",
    "Analyze system performance",
    # Help
    "Help",
    "What can you do?",
]

async def test_text_command(text: str) -> Dict[str, Any]:
    """Test a text command"""
                f"{API_URL}/api/nl/text", headers={"X-API-Key": API_KEY}, json={"text": text}, timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except Exception:

            pass
            return {"error": str(e)}

async def test_websocket():
    """Test WebSocket connection"""
    print("\n📡 WebSocket test (placeholder)")
    print("WebSocket endpoint available at: ws://localhost:8000/api/nl/stream")

async def main():
    """Run all tests"""
    print("🧪 Testing Natural Language Interface")
    print("=" * 50)
    print(f"API URL: {API_URL}")
    print(f"API Key: {API_KEY[:10]}...")
    print("=" * 50)

    # Test each command
    for i, command in enumerate(TEST_COMMANDS, 1):
        print(f"\n📝 Test {i}/{len(TEST_COMMANDS)}: '{command}'")
        result = await test_text_command(command)

        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Response: {result.get('text', 'No response text')}")

            if result.get("actions_taken"):
                print(f"   Actions: {json.dumps(result['actions_taken'], indent=2)}")

            if result.get("suggestions"):
                print(f"   Suggestions: {', '.join(result['suggestions'])}")

    # Test WebSocket
    await test_websocket()

    print("\n✅ All tests completed!")

if __name__ == "__main__":
    # Check if the API is running
    try:

        pass
        import requests

        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API is not responding. Please start the API first:")
            print("   make dev-start")
            sys.exit(1)
    except Exception:

        pass
        print(f"❌ Cannot connect to API at {API_URL}")
        print("   Please start the API first: make dev-start")
        sys.exit(1)

    # Run tests
    asyncio.run(main())
