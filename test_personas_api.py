#!/usr/bin/env python3
"""
"""
os.getenv("API_KEY")
BASE_URL = "http://localhost:8000"

async def test_personas_api():
    """Test the personas admin API endpoints."""
        headers = {"X-API-Key": API_KEY}

        print("Testing Personas Admin API")
        print("=" * 50)

        # Test health check
        print("\n1. Testing health check...")
        try:

            pass
            response = await client.get(f"{BASE_URL}/api/personas/health/status")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
        except Exception:

            pass
            print(f"   Error: {e}")

        # Test list personas
        print("\n2. Testing list personas...")
        try:

            pass
            response = await client.get(f"{BASE_URL}/api/personas/", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Total personas: {data['total']}")
                print(f"   Filtered: {data['filtered']}")
                if data["personas"]:
                    print("   Personas found:")
                    for persona in data["personas"]:
                        print(f"     - {persona['slug']}: {persona['name']}")
        except Exception:

            pass
            print(f"   Error: {e}")

        # Test get specific persona
        print("\n3. Testing get specific persona...")
        try:

            pass
            response = await client.get(f"{BASE_URL}/api/personas/technical-architect", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                persona = response.json()
                print(f"   Name: {persona['name']}")
                print(f"   Status: {persona['status']}")
                print(f"   Description: {persona['description'][:100]}...")
        except Exception:

            pass
            print(f"   Error: {e}")

        # Test validate all
        print("\n4. Testing validate all personas...")
        try:

            pass
            response = await client.get(f"{BASE_URL}/api/personas/validate/all", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Valid: {data['valid']}")
                print(f"   Total personas: {data['total_personas']}")
                print(f"   Personas with issues: {data['personas_with_issues']}")
        except Exception:

            pass
            print(f"   Error: {e}")

        # Test update persona
        print("\n5. Testing update persona...")
        try:

            pass
            update_data = {"temperature": 0.5, "tags": ["updated", "test", "technical"]}
            response = await client.put(
                f"{BASE_URL}/api/personas/technical-architect", headers=headers, json=update_data
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   Update successful!")
        except Exception:

            pass
            print(f"   Error: {e}")

        print("\n" + "=" * 50)
        print("API test completed!")

if __name__ == "__main__":
    # Check if the server is running
    print("Note: Make sure the FastAPI server is running on port 8000")
    print("You can start it with: uvicorn agent.app.main:app --reload")
    print()

    # Run the tests
    asyncio.run(test_personas_api())
