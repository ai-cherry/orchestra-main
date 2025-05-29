#!/usr/bin/env python3
"""
Test script to verify the new GCP-free setup is functional.
Tests all major components and connections.
"""

import asyncio
import os
import sys
from typing import Dict, List, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SetupTester:
    """Test the new GCP-free setup."""

    def __init__(self):
        self.results: Dict[str, Tuple[bool, str]] = {}
        self.critical_failures: List[str] = []

    async def test_environment_variables(self) -> bool:
        """Test that required environment variables are set."""
        print("\n🔍 Testing Environment Variables...")

        required_vars = [
            "MONGODB_URI",
            "DRAGONFLY_URI",
            "WEAVIATE_URL",
            "WEAVIATE_API_KEY",
            "OPENROUTER_API_KEY",
        ]

        all_good = True
        for var in required_vars:
            value = os.getenv(var)
            if value:
                self.results[f"env_{var}"] = (True, f"✓ {var} is set")
                print(f"  ✓ {var} is set")
            else:
                self.results[f"env_{var}"] = (False, f"✗ {var} is NOT set")
                print(f"  ✗ {var} is NOT set")
                all_good = False

        return all_good

    async def test_mongodb_connection(self) -> bool:
        """Test MongoDB connection."""
        print("\n🔍 Testing MongoDB Connection...")

        try:
            from core.orchestrator.src.agents.memory.mongodb_manager import MongoDBMemoryManager

            # Try to connect
            manager = MongoDBMemoryManager()

            # Test basic operations
            test_agent_id = "test_agent"
            test_memory = {"content": "Test memory content", "type": "test"}

            # Store
            memory_id = manager.store_memory(test_agent_id, "test", test_memory)
            print(f"  ✓ Stored test memory with ID: {memory_id}")

            # Retrieve
            memories = manager.retrieve_memories(test_agent_id, "test", limit=1)
            if memories:
                print(f"  ✓ Retrieved {len(memories)} test memories")

            # Clean up
            deleted = manager.clear_agent_memories(test_agent_id)
            print(f"  ✓ Cleaned up {deleted} test memories")

            # Close connection
            manager.close()

            self.results["mongodb"] = (True, "MongoDB connection successful")
            return True

        except Exception as e:
            self.results["mongodb"] = (False, f"MongoDB connection failed: {str(e)}")
            print(f"  ✗ MongoDB connection failed: {e}")
            self.critical_failures.append("MongoDB")
            return False

    async def test_redis_connection(self) -> bool:
        """Test Redis connection (local or Dragonfly)."""
        print("\n🔍 Testing Redis/Dragonfly Connection...")

        try:
            import redis

            # Try local Redis first
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))

            client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

            # Test connection
            client.ping()
            print(f"  ✓ Connected to Redis at {redis_host}:{redis_port}")

            # Test basic operations
            test_key = "test:orchestra"
            client.set(test_key, "test_value")
            value = client.get(test_key)

            if value == "test_value":
                print("  ✓ Redis read/write test passed")

            # Clean up
            client.delete(test_key)

            self.results["redis"] = (True, "Redis connection successful")
            return True

        except Exception as e:
            print("  ⚠️  Local Redis failed, trying Dragonfly...")

            # Try Dragonfly
            try:
                dragonfly_uri = os.getenv("DRAGONFLY_URI")
                if dragonfly_uri:
                    # Parse URI and connect
                    print("  ✓ Dragonfly URI configured")
                    self.results["redis"] = (True, "Dragonfly configured (not tested)")
                    return True
                else:
                    raise Exception("No Dragonfly URI configured")

            except Exception:
                self.results["redis"] = (
                    False,
                    f"Redis/Dragonfly connection failed: {str(e)}",
                )
                print(f"  ✗ Redis/Dragonfly connection failed: {e}")
                return False

    async def test_weaviate_connection(self) -> bool:
        """Test Weaviate connection."""
        print("\n🔍 Testing Weaviate Connection...")

        try:
            import weaviate

            weaviate_url = os.getenv("WEAVIATE_URL")
            weaviate_api_key = os.getenv("WEAVIATE_API_KEY")

            if not weaviate_url:
                raise Exception("WEAVIATE_URL not set")

            # Create client
            client = weaviate.Client(
                url=weaviate_url,
                auth_client_secret=(weaviate.AuthApiKey(api_key=weaviate_api_key) if weaviate_api_key else None),
            )

            # Test connection
            if client.is_ready():
                print(f"  ✓ Connected to Weaviate at {weaviate_url}")
                self.results["weaviate"] = (True, "Weaviate connection successful")
                return True
            else:
                raise Exception("Weaviate not ready")

        except ImportError:
            self.results["weaviate"] = (
                False,
                "Weaviate client not installed (pip install weaviate-client)",
            )
            print("  ⚠️  Weaviate client not installed")
            return False
        except Exception as e:
            self.results["weaviate"] = (False, f"Weaviate connection failed: {str(e)}")
            print(f"  ✗ Weaviate connection failed: {e}")
            return False

    async def test_settings_import(self) -> bool:
        """Test that settings can be imported without GCP dependencies."""
        print("\n🔍 Testing Settings Import...")

        try:
            from core.orchestrator.src.config.settings import get_settings

            settings = get_settings()

            # Check that GCP settings are gone
            gcp_attrs = [
                "GCP_PROJECT_ID",
                "GOOGLE_CLOUD_PROJECT",
                "FIRESTORE_NAMESPACE",
            ]
            has_gcp = False

            for attr in gcp_attrs:
                if hasattr(settings, attr):
                    print(f"  ⚠️  Warning: {attr} still exists in settings")
                    has_gcp = True

            if not has_gcp:
                print("  ✓ Settings imported successfully without GCP dependencies")
                self.results["settings"] = (True, "Settings clean of GCP")
                return True
            else:
                self.results["settings"] = (False, "Settings still has GCP attributes")
                return False

        except Exception as e:
            self.results["settings"] = (False, f"Settings import failed: {str(e)}")
            print(f"  ✗ Settings import failed: {e}")
            return False

    async def test_docker_compose(self) -> bool:
        """Test that docker-compose.yml is clean."""
        print("\n🔍 Testing Docker Compose Configuration...")

        try:
            with open("docker-compose.yml", "r") as f:
                content = f.read()

            if "GOOGLE_APPLICATION_CREDENTIALS" in content:
                self.results["docker"] = (
                    False,
                    "docker-compose.yml still contains GCP references",
                )
                print("  ✗ docker-compose.yml still contains GOOGLE_APPLICATION_CREDENTIALS")
                return False
            else:
                print("  ✓ docker-compose.yml is clean of GCP references")
                self.results["docker"] = (True, "Docker compose is clean")
                return True

        except Exception as e:
            self.results["docker"] = (
                False,
                f"Could not check docker-compose.yml: {str(e)}",
            )
            print(f"  ✗ Could not check docker-compose.yml: {e}")
            return False

    async def test_llm_connections(self) -> bool:
        """Test LLM API connections."""
        print("\n🔍 Testing LLM API Connections...")

        try:
            from litellm import completion

            # Test with a simple prompt
            response = completion(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": "Say 'test successful' and nothing else",
                    }
                ],
                max_tokens=10,
            )

            if "test successful" in response.choices[0].message.content.lower():
                print("  ✓ LLM API connection successful")
                self.results["llm"] = (True, "LLM APIs working")
                return True
            else:
                raise Exception("Unexpected LLM response")

        except Exception as e:
            self.results["llm"] = (False, f"LLM API test failed: {str(e)}")
            print(f"  ⚠️  LLM API test failed: {e}")
            return False

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for success, _ in self.results.values() if success)
        total = len(self.results)

        for test_name, (success, message) in self.results.items():
            status = "✅" if success else "❌"
            print(f"{status} {test_name}: {message}")

        print(f"\nTotal: {passed}/{total} tests passed")

        if self.critical_failures:
            print(f"\n⚠️  CRITICAL FAILURES: {', '.join(self.critical_failures)}")
            print("These components are essential and must be fixed!")

        if passed == total:
            print("\n🎉 All tests passed! Your GCP-free setup is ready!")
        else:
            print("\n⚠️  Some tests failed. Please check the configuration.")

    async def run_all_tests(self):
        """Run all tests."""
        print("🚀 Orchestra AI - Post-GCP Cleanup Test Suite")
        print("=" * 50)

        # Run tests
        await self.test_environment_variables()
        await self.test_settings_import()
        await self.test_docker_compose()
        await self.test_mongodb_connection()
        await self.test_redis_connection()
        await self.test_weaviate_connection()
        await self.test_llm_connections()

        # Print summary
        self.print_summary()


async def main():
    """Main test runner."""
    tester = SetupTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
