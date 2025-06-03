# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""Test script to check what data MCP servers have access to"""
os.environ["POSTGRES_USER"] = "orchestrator"
os.environ["POSTGRES_PASSWORD"] = "orch3str4_2024"
os.environ["POSTGRES_DB"] = "orchestrator"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"

from shared.database import UnifiedDatabase
import json
from datetime import datetime

def check_mcp_data():
    print("🔍 Checking MCP Database Content...")
    print("=" * 50)

    try:


        pass
        db = UnifiedDatabase()

        # Check PostgreSQL data
        print("\n📊 PostgreSQL Data:")

        # Sessions
        print("\n🗂️  Sessions:")
        sessions = db.postgres.# TODO: Consider adding EXPLAIN ANALYZE for performance
execute_query("SELECT id, data, created_at FROM orchestra.sessions LIMIT 5")
        if sessions:
            for s in sessions:
                data = json.loads(s["data"]) if isinstance(s["data"], str) else s["data"]
                print(f"  - Session {s['id'][:8]}... User: {data.get('user_id', 'N/A')}")
        else:
            print("  - No sessions found")

        # API Keys
        print("\n🔑 API Keys:")
        keys = db.postgres.execute_query("SELECT name, created_at, last_used FROM orchestra.api_keys LIMIT 5")
        if keys:
            for k in keys:
                print(f"  - {k['name']}: Last used: {k['last_used'] or 'Never'}")
        else:
            print("  - No API keys found")

        # Knowledge Base
        print("\n📚 Knowledge Base:")
        kb = db.postgres.execute_query("SELECT id, title, category, created_at FROM orchestra.knowledge_base LIMIT 5")
        if kb:
            for item in kb:
                print(f"  - {item['title']} ({item['category']})")
        else:
            print("  - No knowledge base entries found")

        # Agents
        print("\n🤖 Agents:")
        agents = db.postgres.list_agents(limit=5)
        if agents:
            for agent in agents:
                print(f"  - {agent['name']}: {agent['description'][:50]}...")
        else:
            print("  - No agents found")

        # Check Weaviate data
        print("\n🧠 Weaviate Vector Data:")

        # Try to get memories
        try:

            pass
            memories = db.weaviate.search_memories(agent_id="test", query="test", limit=5)
            if memories:
                print(f"  - Found {len(memories)} memories")
                for m in memories[:3]:
                    print(f"    • {m.get('content', 'N/A')[:50]}...")
            else:
                print("  - No memories found")
        except Exception:

            pass
            print(f"  - Error accessing memories: {str(e)}")

        # Try to get conversation history
        try:

            pass
            conversations = db.weaviate.search_conversations(query="hello", limit=5)
            if conversations:
                print(f"\n💬 Conversations: Found {len(conversations)} messages")
                for c in conversations[:3]:
                    print(f"    • [{c.get('role', 'N/A')}] {c.get('message', 'N/A')[:50]}...")
            else:
                print("\n💬 Conversations: No conversations found")
        except Exception:

            pass
            print(f"\n💬 Conversations: Error accessing - {str(e)}")

        # Add some test data if empty
        print("\n" + "=" * 50)
        print("💾 Adding test data for MCP to use...")

        # Add a test knowledge entry
        try:

            pass
            kb_id = db.add_to_knowledge_base(
                title="MCP Test Pattern",
                content="This is a test pattern added to verify MCP functionality. The MCP servers can search and retrieve this content.",
                category="testing",
                tags=["mcp", "test", "verification"],
            )
            print(f"✅ Added test knowledge base entry: {kb_id}")
        except Exception:

            pass
            print(f"⚠️  Could not add knowledge base entry: {e}")

        # Add a test memory
        try:

            pass
            memory_id = db.weaviate.store_memory(
                agent_id="mcp_test",
                content="MCP servers are configured and working. PostgreSQL and Weaviate are both accessible.",
                memory_type="system_check",
                importance=0.9,
            )
            print(f"✅ Added test memory: {memory_id}")
        except Exception:

            pass
            print(f"⚠️  Could not add memory: {e}")

        # Create a test session
        try:

            pass
            session_id = "test-mcp-" + datetime.now().strftime("%Y%m%d%H%M%S")
            session = db.create_session(session_id=session_id, user_id="mcp_tester", ttl_hours=24)
            print(f"✅ Created test session: {session_id}")
        except Exception:

            pass
            print(f"⚠️  Could not create session: {e}")

        # Create a test agent
        try:

            pass
            agent = db.postgres.create_agent(
                {
                    "name": "MCP Test Agent",
                    "description": "Agent created to verify MCP functionality",
                    "capabilities": {"test": True, "mcp": True},
                    "autonomy_level": 0.5,
                    "model_config": {"model": "gpt-4", "temperature": 0.7},
                }
            )
            print(f"✅ Created test agent: {agent['name']} (ID: {agent['id']})")
        except Exception:

            pass
            print(f"⚠️  Could not create agent: {e}")

        print("\n✨ MCP servers can now access this test data!")
        print("   Use @orchestra-memory in Cursor to search for 'MCP test'")

        # Summary
        print("\n" + "=" * 50)
        print("📊 Summary - MCP can access:")
        print("  • PostgreSQL: Sessions, Agents, Knowledge Base, API Keys")
        print("  • Weaviate: Memories, Conversations, Vector Search")
        print("\n💡 Test in Cursor:")
        print('  @orchestra-memory search_memories "MCP test"')
        print('  @orchestra-memory search_knowledge "test pattern"')

    except Exception:


        pass
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running: sudo systemctl status postgresql")
        print("  2. Weaviate is running: docker ps | grep weaviate")
        print("  3. Run: orchestra-status")

if __name__ == "__main__":
    check_mcp_data()
