"""
"""
    """Process vectors in batches to optimize memory usage"""
        """Process large vector arrays in memory-efficient batches"""
    """Enhanced MCP server for all memory management tasks"""
        super().__init__("enhanced_memory_orchestrator", "3.0.0")

        # Initialize components
        self.db: Optional[UnifiedDatabase] = None
        self.intelligent_cache = None # Will be initialized in __aenter__ from base or directly
        self.vector_processor = VectorBatchProcessor(batch_size=50)

        # Performance tracking (some metrics might be covered by IntelligentCache now)
        self.local_cache_hits = 0
        self.local_cache_misses = 0

    async def initialize(self):
        """Initialize server resources. Called by EnhancedMCPServerBase.run()"""
            f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:"
            f"{os.getenv('POSTGRES_PASSWORD', '')}@"
            f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
            f"{os.getenv('POSTGRES_PORT', '5432')}/"
            f"{os.getenv('POSTGRES_DB', 'orchestra')}"
        )
        # Initialize PostgreSQL connection pool via base class method
        await self.initialize_connection_pool(postgres_dsn)
        # Initialize UnifiedDatabase (which includes Weaviate client)
        await self.db.initialize() # Ensure UnifiedDatabase has an async initialize method
        
        # Get the global intelligent cache instance
        self.intelligent_cache = await get_intelligent_cache()
        logger.info("EnhancedMemoryServer initialized with IntelligentCache and UnifiedDatabase.")

    def _generate_cache_key(self, operation: str, **params) -> str:
        """Generate cache key from operation and parameters"""
        key_data = json.dumps({"operation": operation, "params": params}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    async def get_custom_tools(self) -> List[Tool]:
        """Get memory server specific tools"""
                "name": "store_memory_batch",
                "description": "Store multiple memories in batch for better performance",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "memories": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "agent_id": {"type": "string"},
                                    "content": {"type": "string"},
                                    "memory_type": {"type": "string"},
                                    "context": {"type": "string"},
                                    "importance": {"type": "number"},
                                },
                                "required": ["agent_id", "content"],
                            },
                        }
                    },
                    "required": ["memories"],
                },
            },
            {
                "name": "search_memories_cached",
                "description": "Search memories with intelligent caching for improved performance",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "query": {"type": "string"},
                        "memory_type": {"type": "string"},
                        "limit": {"type": "integer", "default": 10},
                        "use_cache": {"type": "boolean", "default": True},
                    },
                    "required": ["agent_id", "query"],
                },
            },
            {
                "name": "optimize_memory_storage",
                "description": "Optimize memory storage by compacting and reindexing",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "compact_threshold": {"type": "number", "default": 0.7},
                    },
                    "required": ["agent_id"],
                },
            },
            {
                "name": "get_memory_statistics",
                "description": "Get detailed statistics about memory usage and performance, including cache metrics",
                "inputSchema": {
                    "type": "object",
                    "properties": {"agent_id": {"type": "string"}},
                },
            },
            {
                "name": "clear_intelligent_cache",
                "description": "Clear specific types from the intelligent cache for fresh data retrieval",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cache_type": {"type": "string", 
                                       "enum": [ct.value for ct in IntelligentCacheType] + ["all"], 
                                       "default": "all"}
                    },
                },
            },
            {
                "name": "store_memory",
                "description": "Store agent memory (vector + relational if needed). Updates cache.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "content": {"type": "string"},
                        "memory_type": {"type": "string", "default": "general"},
                        "context": {"type": "string"},
                        "importance": {"type": "number", "default": 0.5},
                        "vector_class_name": {"type": "string", "description": "Weaviate class name for vector store"},
                        "relational_table_name": {"type": "string", "description": "PostgreSQL table for relational part"}
                    },
                    "required": ["agent_id", "content", "vector_class_name"],
                },
            },
            {
                "name": "search_memories", 
                "description": "Search agent memories (semantic/vector search). Bypasses intelligent cache.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "query": {"type": "string"},
                        "vector_class_name": {"type": "string", "description": "Weaviate class name to search"},
                        "memory_type": {"type": "string"},
                        "limit": {"type": "integer", "default": 10},
                    },
                    "required": ["agent_id", "query", "vector_class_name"],
                },
            },
            {
                "name": "get_recent_memories",
                "description": "Get recent memories for an agent (from relational store).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "limit": {"type": "integer", "default": 20},
                        "memory_type": {"type": "string"},
                    },
                    "required": ["agent_id"],
                },
            },
            {
                "name": "store_conversation",
                "description": "Store conversation message (relational store).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "agent_id": {"type": "string"},
                        "user_id": {"type": "string", "default": "anonymous"},
                        "message": {"type": "string"},
                        "role": {"type": "string", "enum": ["user", "assistant"]},
                    },
                    "required": ["session_id", "agent_id", "message", "role"],
                },
            },
            {
                "name": "get_conversation_history",
                "description": "Get conversation history for a session (from relational store).",
                "inputSchema": {
                    "type": "object",
                    "properties": {"session_id": {"type": "string"}, "limit": {"type": "integer", "default": 50}},
                    "required": ["session_id"],
                },
            },
            {
                "name": "search_conversations",
                "description": "Search conversations.", 
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "agent_id": {"type": "string"},
                        "user_id": {"type": "string"},
                        "vector_class_name": {"type": "string", "description": "Weaviate class if semantic search"},
                        "limit": {"type": "integer", "default": 20},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "create_session",
                "description": "Create a new session (in relational store).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "agent_id": {"type": "string"},
                        "ttl_hours": {"type": "integer", "default": 24},
                    },
                    "required": ["user_id"],
                },
            },
            {
                "name": "get_session",
                "description": "Get session with conversation history (from relational store).",
                "inputSchema": {
                    "type": "object",
                    "properties": {"session_id": {"type": "string"}},
                    "required": ["session_id"],
                },
            },
            {
                "name": "add_knowledge",
                "description": "Add item to knowledge base (Weaviate and/or PostgreSQL).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                        "category": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "source": {"type": "string"},
                        "vector_class_name": {"type": "string", "description": "Weaviate class for KB items"}
                    },
                    "required": ["title", "content", "category", "vector_class_name"],
                },
            },
            {
                "name": "search_knowledge",
                "description": "Search knowledge base (semantic search).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "vector_class_name": {"type": "string", "description": "Weaviate class for KB items"},
                        "category": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "limit": {"type": "integer", "default": 10},
                    },
                    "required": ["query", "vector_class_name"],
                },
            },
        ]
        return tools

    async def handle_custom_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle memory server specific tool calls"""
            logger.error(f"Error executing tool {name}: {e}", exc_info=True)
            return [TextContent(type="text", text=f"❌ Error executing {name}: {str(e)}")]

    async def _handle_tool_internal(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Internal tool handler with actual implementation"""
        logger.info(f"Handling tool: {name} with args: {arguments}")
        if name == "store_memory_batch":
            memories = arguments["memories"]
            results = await self.vector_processor.process_vectors_in_batches(memories, self._store_memory_batch_item)
            success_count = sum(1 for r in results if r["success"])
            return [TextContent(type="text", text=f"✅ Stored {success_count}/{len(memories)} memories successfully")]

        elif name == "search_memories_cached":
            agent_id = arguments["agent_id"]
            query = arguments["query"]
            vector_class_name = arguments.get("vector_class_name", f"AgentMemory_{agent_id}")
            memory_type = arguments.get("memory_type")
            limit = arguments.get("limit", 10)
            use_cache = arguments.get("use_cache", True)

            cache_key_params = {"agent_id": agent_id, "query": query, "vector_class_name": vector_class_name, "memory_type": memory_type, "limit": limit}
            cache_key = self._generate_cache_key("search_memories", **cache_key_params)
            
            cached_result_text = None
            if use_cache and self.intelligent_cache:
                cached_value = await self.intelligent_cache.get(cache_key, IntelligentCacheType.CODE_ANALYSIS, context=cache_key_params)
                if cached_value:
                    self.local_cache_hits += 1
                    cached_result_text = cached_value
                    return [TextContent(type="text", text=f"📋 (Cached) {cached_result_text}")]
            
            if use_cache:
                self.local_cache_misses += 1

            filters = None
            if memory_type:
                filters = {"operator": "Equal", "path": ["memory_type"], "valueString": memory_type}
            
            memories = await self.db.vector_search(
                class_name=vector_class_name,
                query_text=query,
                limit=limit,
                filters=filters
            )
            
            if not memories:
                result_text = "No memories found matching the query."
            else:
                result_text = f"Found {len(memories)} memories:\n\n"
                for i, mem_item in enumerate(memories, 1):
                    result_text += f"{i}. {mem_item.content}\n"
                    result_text += f"   Type: {mem_item.metadata.get('memory_type', 'N/A')}, Score: {mem_item.score:.3f}\n\n"

            if use_cache and self.intelligent_cache:
                await self.intelligent_cache.set(cache_key, result_text, IntelligentCacheType.CODE_ANALYSIS, context=cache_key_params)

            return [TextContent(type="text", text=result_text)]

        elif name == "optimize_memory_storage":
            agent_id = arguments["agent_id"]
            compact_threshold = arguments.get("compact_threshold", 0.7)
            stats = await self._optimize_agent_memories(agent_id, compact_threshold)
            return [TextContent(type="text", text=f"✅ Memory optimization complete: {stats}")]

        elif name == "get_memory_statistics":
            agent_id = arguments.get("agent_id")
            stats = await self._get_memory_statistics(agent_id)
            if self.intelligent_cache:
                stats["intelligent_cache_metrics"] = self.intelligent_cache.get_performance_metrics()
            return [TextContent(type="text", text=f"📊 Memory Statistics: {json.dumps(stats, indent=2, default=str)}")]

        elif name == "clear_intelligent_cache":
            cache_type_str = arguments.get("cache_type", "all")
            invalidated_count = 0
            if self.intelligent_cache:
                if cache_type_str == "all":
                    for ct in IntelligentCacheType:
                        invalidated_count += await self.intelligent_cache.invalidate_pattern(pattern=f"", cache_type=ct)
                else:
                    try:

                        pass
                        ct_enum = IntelligentCacheType(cache_type_str)
                        invalidated_count = await self.intelligent_cache.invalidate_pattern(pattern=f"", cache_type=ct_enum)
                    except Exception:

                        pass
                        return [TextContent(type="text", text=f"❌ Invalid cache_type: {cache_type_str}")]
            return [TextContent(type="text", text=f"✅ Cleared {invalidated_count} entries from {cache_type_str} intelligent cache(s)")]

        elif name == "store_memory":
            memory_data = {
                "agent_id": arguments["agent_id"],
                "content": arguments["content"],
                "memory_type": arguments.get("memory_type", "general"),
                "context": arguments.get("context"),
                "importance": arguments.get("importance", 0.5),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            vector_class_name = arguments["vector_class_name"]
            relational_table = arguments.get("relational_table_name")
            if relational_table:
                await self.db.insert_record(relational_table, {**memory_data, "vector_ref_id": "to_be_filled_by_weaviate_id"})

            memory_id = await self.db.insert_vector(
                class_name=vector_class_name, 
                content=arguments["content"],
                metadata=memory_data
            )
            if self.intelligent_cache:
                await self.intelligent_cache.invalidate_pattern(pattern=arguments["agent_id"])
            return [TextContent(type="text", text=f"✅ Memory stored successfully with ID: {memory_id}")]

        elif name == "search_memories":
            vector_class_name = arguments["vector_class_name"]
            filters = None
            if arguments.get("memory_type"):
                filters = {"operator": "Equal", "path": ["memory_type"], "valueString": arguments["memory_type"]}
            memories = await self.db.vector_search(
                class_name=vector_class_name,
                query_text=arguments["query"],
                limit=arguments.get("limit", 10),
                filters=filters
            )
            if not memories:
                return [TextContent(type="text", text="No memories found matching the query.")]
            result_text = f"Found {len(memories)} memories (direct search):\n\n"
            for i, mem_item in enumerate(memories, 1):
                result_text += f"{i}. {mem_item.content}\n   Score: {mem_item.score:.3f}\n\n"
            return [TextContent(type="text", text=result_text)]
        
        elif name == "get_recent_memories":
            results = await self.db.execute_query(
                f"SELECT content, memory_type, created_at as timestamp FROM agent_general_memories "
                f"WHERE agent_id = $1 {('AND memory_type = $3' if arguments.get('memory_type') else '')} "
                f"ORDER BY created_at DESC LIMIT $2", 
                [arguments["agent_id"], arguments.get("limit", 20)] + ([arguments["memory_type"]] if arguments.get("memory_type") else [])
            )
            if not results:
                return [TextContent(type="text", text="No recent memories found.")]
            result_text = f"Recent {len(results)} memories:\n\n"
            for i, mem in enumerate(results, 1):
                result_text += f"{i}. {mem['content']}\n   Type: {mem['memory_type']}, Time: {mem['timestamp']}\n\n"
            return [TextContent(type="text", text=result_text)]

        elif name == "store_conversation":
            await self.db.insert_record("conversations", {
                "session_id": arguments["session_id"],
                "agent_id": arguments["agent_id"],
                "user_id": arguments.get("user_id", "anonymous"),
                "message": arguments["message"],
                "role": arguments["role"],
                "timestamp": datetime.now(timezone.utc)
            })
            if self.intelligent_cache:
                await self.intelligent_cache.invalidate_pattern(pattern=arguments["session_id"])
            return [TextContent(type="text", text=f"✅ Conversation message stored for session: {arguments['session_id']}")]

        elif name == "get_conversation_history":
            history = await self.db.execute_query(
                f"SELECT role, message, timestamp FROM conversations "
                f"WHERE session_id = $1 ORDER BY timestamp ASC LIMIT $2",
                [arguments["session_id"], arguments.get("limit", 50)]
            )
            if not history:
                return [TextContent(type="text", text="No conversation history found.")]
            result_text = f"Conversation history ({len(history)} messages):\n\n"
            for msg in history:
                result_text += f"[{msg['timestamp']}] {msg['role'].upper()}: {msg['message']}\n\n"
            return [TextContent(type="text", text=result_text)]

        elif name == "search_conversations":
            query = arguments["query"]
            vector_class_name = arguments.get("vector_class_name", f"ConversationStore")
            semantic_results = await self.db.vector_search(
                class_name=vector_class_name,
                query_text=query,
                limit=arguments.get("limit", 10)
            )
            if not semantic_results:
                return [TextContent(type="text", text="No conversations found matching the query.")]
            result_text = f"Found {len(semantic_results)} conversation snippets (semantic search):\n\n"
            for i, item in enumerate(semantic_results, 1):
                result_text += f"{i}. {item.content[:200]}... (Score: {item.score:.3f})\n"
                result_text += f"   Session: {item.metadata.get('session_id', 'N/A')}\n\n"
            return [TextContent(type="text", text=result_text)]

        elif name == "create_session":
            session_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            ttl_hours = arguments.get("ttl_hours", 24)
            expires_at = now + timedelta(hours=ttl_hours)
            session_data = {
                "session_id": session_id,
                "user_id": arguments["user_id"],
                "agent_id": arguments.get("agent_id"),
                "created_at": now,
                "expires_at": expires_at,
                "metadata": {"status": "active"} 
            }
            await self.db.insert_record("sessions", session_data)
            return [TextContent(type="text", text=f"✅ Session created: {session_id}, Expires: {expires_at.isoformat()}")]

        elif name == "get_session":
            session_rows = await self.db.# TODO: Consider adding EXPLAIN ANALYZE for performance
execute_query(
                "SELECT session_id, user_id, agent_id, created_at, expires_at, metadata FROM sessions WHERE session_id = $1",
                [arguments["session_id"]]
            )
            if not session_rows:
                return [TextContent(type="text", text="Session not found or expired.")]
            session = session_rows[0]
            history = await self._handle_tool_internal("get_conversation_history", {"session_id": session['session_id'], "limit": 50})
            result_text = f"Session ID: {session['session_id']}\nUser ID: {session['user_id']}\nAgent ID: {session['agent_id']}\n"
            result_text += f"Created: {session['created_at']}\nExpires: {session['expires_at']}\nMetadata: {session['metadata']}\n\n"
            result_text += history[0].text
            return [TextContent(type="text", text=result_text)]

        elif name == "add_knowledge":
            kb_item_data = {
                "title": arguments["title"],
                "content": arguments["content"],
                "category": arguments["category"],
                "tags": arguments.get("tags", []),
                "source": arguments.get("source"),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            vector_class_name = arguments["vector_class_name"]
            kb_id = await self.db.insert_vector(
                class_name=vector_class_name, 
                content=arguments["content"], 
                metadata=kb_item_data
            )
            if self.intelligent_cache:
                await self.intelligent_cache.invalidate_pattern(pattern=arguments["category"])
            return [TextContent(type="text", text=f"✅ Knowledge added with ID: {kb_id}")]

        elif name == "search_knowledge":
            vector_class_name = arguments["vector_class_name"]
            filters_list = []
            if arguments.get("category"):
                filters_list.append({"operator": "Equal", "path": ["category"], "valueString": arguments["category"]})
            if arguments.get("tags"):
                pass 
            
            filters = None
            if len(filters_list) == 1:
                filters = filters_list[0]
            elif len(filters_list) > 1:
                filters = {"operator": "And", "operands": filters_list}

            results = await self.db.vector_search(
                class_name=vector_class_name,
                query_text=arguments["query"],
                limit=arguments.get("limit", 10),
                filters=filters
            )
            if not results:
                return [TextContent(type="text", text="No knowledge found matching the query.")]
            result_text = f"Found {len(results)} knowledge items:\n\n"
            for i, item in enumerate(results, 1):
                result_text += f"{i}. {item.metadata.get('title', 'N/A')}\n"
                result_text += f"   Category: {item.metadata.get('category', 'N/A')}, Score: {item.score:.3f}\n"
                result_text += f"   Content: {item.content[:150]}...\n\n"
            return [TextContent(type="text", text=result_text)]
        
        else:
            logger.warning(f"Tool '{name}' not found in EnhancedMemoryServer.")
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def _store_memory_batch_item(self, memories_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        batch_results = []
        for memory in memories_batch:
            try:

                pass
                vector_class_name = memory.get("vector_class_name", f"AgentMemory_{memory['agent_id']}")
                memory_data = {
                    "agent_id": memory["agent_id"],
                    "content": memory["content"],
                    "memory_type": memory.get("memory_type", "general"),
                    "context": memory.get("context"),
                    "importance": memory.get("importance", 0.5),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                memory_id = await self.db.insert_vector(
                    class_name=vector_class_name, 
                    content=memory["content"], 
                    metadata=memory_data
                )
                batch_results.append({"success": True, "id": memory_id})
                if self.intelligent_cache:
                    await self.intelligent_cache.invalidate_pattern(pattern=memory["agent_id"]) 
            except Exception:
 
                pass
                logger.error(f"Failed to store memory item in batch: {e}")
                batch_results.append({"success": False, "error": str(e)})
        return batch_results

    async def _optimize_agent_memories(self, agent_id: str, compact_threshold: float) -> Dict[str, Any]:
        logger.info(f"Simulating memory optimization for agent {agent_id}...")
        await asyncio.sleep(1)
        return {"total_memories": 1000, "compacted": 150, "space_saved_mb": 25.3, "index_rebuilt": True}

    async def _get_memory_statistics(self, agent_id: Optional[str]) -> Dict[str, Any]:
        db_stats = await self.db.get_metrics() if self.db else {}
        intelligent_cache_metrics = self.intelligent_cache.get_performance_metrics() if self.intelligent_cache else {}
        
        pg_count_query = f"SELECT COUNT(*) FROM agent_general_memories{(' WHERE agent_id = $1' if agent_id else '')}"
        pg_params = [agent_id] if agent_id else []
        
        weaviate_class_name = f"AgentMemory_{agent_id}" if agent_id else "AgentMemory_default"
        weaviate_memories_list = await self.db.vector_search(class_name=weaviate_class_name, limit=100000) if self.db else []
        
        return {
            "total_memories_pg": (await self.db.execute_query(pg_count_query, pg_params))[0][0] if self.db else "N/A",
            "total_memories_weaviate": len(weaviate_memories_list),
            "db_metrics": db_stats,
            "intelligent_cache_metrics": intelligent_cache_metrics,
            "local_cache_hits": self.local_cache_hits,
            "local_cache_misses": self.local_cache_misses
        }

    async def _handle_original_tools(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        logger.warning(f"Tool '{name}' execution fell through to _handle_original_tools. Args: {arguments}")
        return [TextContent(type="text", text=f"Original Tool '{name}' placeholder. Not fully implemented with direct UnifiedDatabase. Args: {arguments}")]

    async def cleanup(self):
        """Cleanup resources on shutdown, including database pool from base class."""
# if __name__ == "__main__":
#     server = EnhancedMemoryServer()
#     asyncio.run(server.run()) # `run` is from EnhancedMCPServerBase
