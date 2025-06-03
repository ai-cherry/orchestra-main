# TODO: Consider adding connection pooling configuration
"""
"""
    """MCP server for memory management using PostgreSQL and Weaviate."""
        self.server = Server("memory")
        self.setup_database()
        self.setup_handlers()

    def setup_database(self):
        """Setup unified database connection."""
        self.db = UnifiedDatabase(postgres_url=os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/orchestra"))

    def setup_handlers(self):
        """Setup MCP handlers."""
            """List available tools."""
                    "name": "store_memory",
                    "description": "Store agent memory in Weaviate",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "string", "description": "Agent ID"},
                            "content": {"type": "string", "description": "Memory content"},
                            "memory_type": {"type": "string", "description": "Type of memory", "default": "general"},
                            "context": {"type": "string", "description": "Additional context"},
                            "importance": {"type": "number", "description": "Importance score (0-1)", "default": 0.5},
                        },
                        "required": ["agent_id", "content"],
                    },
                },
                {
                    "name": "search_memories",
                    "description": "Search agent memories using semantic search",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "string", "description": "Agent ID"},
                            "query": {"type": "string", "description": "Search query"},
                            "memory_type": {"type": "string", "description": "Filter by memory type"},
                            "limit": {"type": "integer", "default": 10},
                        },
                        "required": ["agent_id", "query"],
                    },
                },
                {
                    "name": "get_recent_memories",
                    "description": "Get recent memories for an agent",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "string", "description": "Agent ID"},
                            "limit": {"type": "integer", "default": 20},
                            "memory_type": {"type": "string", "description": "Filter by memory type"},
                        },
                        "required": ["agent_id"],
                    },
                },
                {
                    "name": "store_conversation",
                    "description": "Store conversation message",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Session ID"},
                            "agent_id": {"type": "string", "description": "Agent ID"},
                            "user_id": {"type": "string", "description": "User ID", "default": "anonymous"},
                            "message": {"type": "string", "description": "Message content"},
                            "role": {"type": "string", "enum": ["user", "assistant"], "description": "Message role"},
                        },
                        "required": ["session_id", "agent_id", "message", "role"],
                    },
                },
                {
                    "name": "get_conversation_history",
                    "description": "Get conversation history for a session",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Session ID"},
                            "limit": {"type": "integer", "default": 50},
                        },
                        "required": ["session_id"],
                    },
                },
                {
                    "name": "search_conversations",
                    "description": "Search conversations using semantic search",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "agent_id": {"type": "string", "description": "Filter by agent ID"},
                            "user_id": {"type": "string", "description": "Filter by user ID"},
                            "limit": {"type": "integer", "default": 20},
                        },
                        "required": ["query"],
                    },
                },
                {
                    "name": "create_session",
                    "description": "Create a new session",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "User ID"},
                            "agent_id": {"type": "string", "description": "Agent ID"},
                            "ttl_hours": {"type": "integer", "description": "Session TTL in hours", "default": 24},
                        },
                        "required": ["user_id"],
                    },
                },
                {
                    "name": "get_session",
                    "description": "Get session with conversation history",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"session_id": {"type": "string", "description": "Session ID"}},
                        "required": ["session_id"],
                    },
                },
                {
                    "name": "add_knowledge",
                    "description": "Add item to knowledge base",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Knowledge title"},
                            "content": {"type": "string", "description": "Knowledge content"},
                            "category": {"type": "string", "description": "Knowledge category"},
                            "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"},
                            "source": {"type": "string", "description": "Source of knowledge"},
                        },
                        "required": ["title", "content", "category"],
                    },
                },
                {
                    "name": "search_knowledge",
                    "description": "Search knowledge base",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "category": {"type": "string", "description": "Filter by category"},
                            "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                            "limit": {"type": "integer", "default": 10},
                        },
                        "required": ["query"],
                    },
                },
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
                if name == "store_memory":
                    memory_id = self.db.weaviate.store_memory(
                        agent_id=arguments["agent_id"],
                        content=arguments["content"],
                        memory_type=arguments.get("memory_type", "general"),
                        context=arguments.get("context"),
                        importance=arguments.get("importance", 0.5),
                    )
                    return [TextContent(type="text", text=f"✅ Memory stored successfully with ID: {memory_id}")]

                elif name == "search_memories":
                    memories = self.db.weaviate.search_memories(
                        agent_id=arguments["agent_id"],
                        query=arguments["query"],
                        memory_type=arguments.get("memory_type"),
                        limit=arguments.get("limit", 10),
                    )

                    if not memories:
                        return [TextContent(type="text", text="No memories found matching the query.")]

                    result = f"Found {len(memories)} memories:\n\n"
                    for i, mem in enumerate(memories, 1):
                        result += f"{i}. {mem.get('content', 'N/A')}\n"
                        result += f"   Type: {mem.get('memory_type', 'N/A')}, "
                        result += f"Importance: {mem.get('importance', 0):.2f}, "
                        result += f"Certainty: {mem.get('_additional', {}).get('certainty', 0):.2f}\n\n"

                    return [TextContent(type="text", text=result)]

                elif name == "get_recent_memories":
                    memories = self.db.weaviate.get_recent_memories(
                        agent_id=arguments["agent_id"],
                        limit=arguments.get("limit", 20),
                        memory_type=arguments.get("memory_type"),
                    )

                    if not memories:
                        return [TextContent(type="text", text="No recent memories found.")]

                    result = f"Recent {len(memories)} memories:\n\n"
                    for i, mem in enumerate(memories, 1):
                        result += f"{i}. {mem.get('content', 'N/A')}\n"
                        result += f"   Type: {mem.get('memory_type', 'N/A')}, "
                        result += f"Time: {mem.get('timestamp', 'N/A')}\n\n"

                    return [TextContent(type="text", text=result)]

                elif name == "store_conversation":
                    conv_id = self.db.weaviate.store_conversation(
                        session_id=arguments["session_id"],
                        agent_id=arguments["agent_id"],
                        user_id=arguments.get("user_id", "anonymous"),
                        message=arguments["message"],
                        role=arguments["role"],
                    )
                    return [TextContent(type="text", text=f"✅ Conversation message stored with ID: {conv_id}")]

                elif name == "get_conversation_history":
                    history = self.db.weaviate.get_conversation_history(
                        session_id=arguments["session_id"], limit=arguments.get("limit", 50)
                    )

                    if not history:
                        return [TextContent(type="text", text="No conversation history found.")]

                    result = f"Conversation history ({len(history)} messages):\n\n"
                    for msg in history:
                        role = msg.get("role", "unknown")
                        message = msg.get("message", "N/A")
                        timestamp = msg.get("timestamp", "N/A")
                        result += f"[{timestamp}] {role.upper()}: {message}\n\n"

                    return [TextContent(type="text", text=result)]

                elif name == "search_conversations":
                    conversations = self.db.weaviate.search_conversations(
                        query=arguments["query"],
                        agent_id=arguments.get("agent_id"),
                        user_id=arguments.get("user_id"),
                        limit=arguments.get("limit", 20),
                    )

                    if not conversations:
                        return [TextContent(type="text", text="No conversations found matching the query.")]

                    result = f"Found {len(conversations)} conversation messages:\n\n"
                    for i, conv in enumerate(conversations, 1):
                        result += f"{i}. [{conv.get('role', 'N/A')}] {conv.get('message', 'N/A')}\n"
                        result += f"   Session: {conv.get('session_id', 'N/A')}, "
                        result += f"Certainty: {conv.get('_additional', {}).get('certainty', 0):.2f}\n\n"

                    return [TextContent(type="text", text=result)]

                elif name == "create_session":
                    session_id = str(uuid.uuid4())
                    session = self.db.create_session(
                        session_id=session_id,
                        user_id=arguments["user_id"],
                        agent_id=arguments.get("agent_id"),
                        ttl_hours=arguments.get("ttl_hours", 24),
                    )
                    return [
                        TextContent(
                            type="text",
                            text=f"✅ Session created successfully\nID: {session_id}\nExpires: {session['expires_at']}",
                        )
                    ]

                elif name == "get_session":
                    session = self.db.get_session_with_history(arguments["session_id"])

                    if not session:
                        return [TextContent(type="text", text="Session not found or expired.")]

                    data = json.loads(session["data"]) if isinstance(session["data"], str) else session["data"]
                    result = f"Session ID: {session['id']}\n"
                    result += f"User ID: {data.get('user_id', 'N/A')}\n"
                    result += f"Agent ID: {data.get('agent_id', 'N/A')}\n"
                    result += f"Created: {data.get('created_at', 'N/A')}\n"
                    result += f"Last Activity: {data.get('last_activity', 'N/A')}\n"
                    result += f"Expires: {session.get('expires_at', 'N/A')}\n\n"

                    history = session.get("conversation_history", [])
                    if history:
                        result += f"Conversation History ({len(history)} messages):\n"
                        for msg in history[-10:]:  # Show last 10 messages
                            result += f"  [{msg.get('role', 'N/A')}] {msg.get('message', 'N/A')[:100]}...\n"

                    return [TextContent(type="text", text=result)]

                elif name == "add_knowledge":
                    knowledge_id = self.db.add_to_knowledge_base(
                        title=arguments["title"],
                        content=arguments["content"],
                        category=arguments["category"],
                        tags=arguments.get("tags"),
                        source=arguments.get("source"),
                    )
                    return [TextContent(type="text", text=f"✅ Knowledge added successfully with ID: {knowledge_id}")]

                elif name == "search_knowledge":
                    results = self.db.search_knowledge(
                        query=arguments["query"],
                        category=arguments.get("category"),
                        tags=arguments.get("tags"),
                        limit=arguments.get("limit", 10),
                    )

                    if not results:
                        return [TextContent(type="text", text="No knowledge found matching the query.")]

                    result = f"Found {len(results)} knowledge items:\n\n"
                    for i, item in enumerate(results, 1):
                        result += f"{i}. {item.get('title', 'N/A')}\n"
                        result += f"   Category: {item.get('category', 'N/A')}\n"
                        result += f"   Tags: {', '.join(item.get('tags', []))}\n"
                        result += f"   Content: {item.get('content', 'N/A')[:200]}...\n"
                        result += f"   Certainty: {item.get('_additional', {}).get('certainty', 0):.2f}\n\n"

                    return [TextContent(type="text", text=result)]

                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]

            except Exception:


                pass
                return [TextContent(type="text", text=f"❌ Error executing {name}: {str(e)}")]

    async def run(self):
        """Run the MCP server."""
        if not health["overall"]:
            print(f"⚠️  Database health check failed: {health}")
        else:
            print("✅ Database connections healthy")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, {})

if __name__ == "__main__":
    server = MemoryServer()
    asyncio.run(server.run())
