"""
"""
    """
    """
        memory_key: str = "history",
        input_key: Optional[str] = None,
        output_key: Optional[str] = None,
        return_messages: bool = True,
        firestore_config: Optional[Dict[str, Any]] = None,
        qdrant_config: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        **kwargs,
    ):
        """
        """
            raise ImportError("langchain not installed. Install with: pip install langchain")

        super().__init__(**kwargs)

        self.memory_key = memory_key
        self.input_key = input_key
        self.output_key = output_key
        self.return_messages = return_messages
        self.session_id = session_id or "default"

        # Initialize memory tiers
        self.warm_memory = FirestoreEpisodicMemory(firestore_config)
        self.cold_memory = QdrantSemanticMemory(qdrant_config)

        # Message history cache
        self._message_cache: List[BaseMessage] = []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all memory backends."""
                logger.error("Failed to initialize hot memory tier")
            if not warm_ok:
                logger.error("Failed to initialize warm memory tier")
            if not cold_ok:
                logger.warning("Cold memory tier not initialized (stub)")

            self._initialized = hot_ok and warm_ok

            # Load recent messages into cache
            await self._load_recent_messages()

            logger.info("LangChain memory wrapper initialized")

        except Exception:


            pass
            logger.error(f"Failed to initialize LangChain memory: {e}")
            raise

    async def _load_recent_messages(self, limit: int = 100) -> None:
        """Load recent messages from storage into cache."""
            keys = await self.hot_memory.list_keys(prefix=f"{self.session_id}:")

            # Get messages
            messages = []
            for key in keys[-limit:]:  # Get last N keys
                entry = await self.hot_memory.get(key)
                if entry and isinstance(entry.content, dict):
                    msg_type = entry.content.get("type", "human")
                    msg_content = entry.content.get("content", "")

                    if msg_type == "human":
                        messages.append(HumanMessage(content=msg_content))
                    elif msg_type == "ai":
                        messages.append(AIMessage(content=msg_content))

            self._message_cache = messages

        except Exception:


            pass
            logger.error(f"Failed to load recent messages: {e}")

    @property
    def memory_variables(self) -> List[str]:
        """Return memory variables."""
        """Load memory variables for LangChain."""
            messages_str = "\n".join([f"{msg.__class__.__name__}: {msg.content}" for msg in self._message_cache])
            return {self.memory_key: messages_str}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save context to memory (synchronous wrapper)."""
        """Save context to memory asynchronously."""
            human_message = inputs.get(input_key, "")
            ai_message = outputs.get(output_key, "")

            # Create memory entries
            timestamp = datetime.utcnow()

            # Save human message
            if human_message:
                human_entry = MemoryEntry(
                    key=f"{self.session_id}:human:{timestamp.isoformat()}",
                    content={
                        "type": "human",
                        "content": human_message,
                        "timestamp": timestamp.isoformat(),
                        "session_id": self.session_id,
                    },
                    metadata=MemoryMetadata(
                        tags=["conversation", "human", self.session_id],
                        source="langchain",
                        ttl_seconds=3600,  # 1 hour in hot tier
                    ),
                )

                await self.hot_memory.save(human_entry)
                self._message_cache.append(HumanMessage(content=human_message))

            # Save AI message
            if ai_message:
                ai_entry = MemoryEntry(
                    key=f"{self.session_id}:ai:{timestamp.isoformat()}",
                    content={
                        "type": "ai",
                        "content": ai_message,
                        "timestamp": timestamp.isoformat(),
                        "session_id": self.session_id,
                    },
                    metadata=MemoryMetadata(
                        tags=["conversation", "ai", self.session_id],
                        source="langchain",
                        ttl_seconds=3600,  # 1 hour in hot tier
                    ),
                )

                await self.hot_memory.save(ai_entry)
                self._message_cache.append(AIMessage(content=ai_message))

            # Trim cache if too large
            if len(self._message_cache) > 1000:
                self._message_cache = self._message_cache[-500:]

            # Trigger background migration if needed
            asyncio.create_task(self._migrate_old_messages())

        except Exception:


            pass
            logger.error(f"Failed to save context: {e}")

    async def _migrate_old_messages(self) -> None:
        """Migrate old messages from hot to warm tier."""
            keys = await self.hot_memory.list_keys(prefix=f"{self.session_id}:")

            for key in keys:
                entry = await self.hot_memory.get(key)
                if not entry:
                    continue

                # Check if should migrate
                target_tier = self.hot_memory.should_migrate(entry)
                if target_tier == MemoryTier.WARM:
                    # Save to warm tier
                    entry.metadata.tier = MemoryTier.WARM
                    entry.metadata.ttl_seconds = 86400  # 24 hours

                    if await self.warm_memory.save(entry):
                        # Delete from hot tier
                        await self.hot_memory.delete(key)

        except Exception:


            pass
            logger.error(f"Failed to migrate messages: {e}")

    def clear(self) -> None:
        """Clear memory (synchronous wrapper)."""
        """Clear memory asynchronously."""
            hot_count = await self.hot_memory.clear(prefix=f"{self.session_id}:")
            warm_count = await self.warm_memory.clear(prefix=f"{self.session_id}:")
            cold_count = await self.cold_memory.clear(prefix=f"{self.session_id}:")

            # Clear cache
            self._message_cache.clear()

            logger.info(f"Cleared session {self.session_id}: " f"hot={hot_count}, warm={warm_count}, cold={cold_count}")

        except Exception:


            pass
            logger.error(f"Failed to clear memory: {e}")

    async def search_memories(
        self,
        query: str,
        limit: int = 10,
        tiers: Optional[List[MemoryTier]] = None,
    ) -> List[Dict[str, Any]]:
        """
        """
                hot_results = await self.hot_memory.search(query, limit, {"prefix": self.session_id})
                results.extend(
                    [
                        {
                            "tier": "hot",
                            "entry": r.entry,
                            "score": r.score,
                        }
                        for r in hot_results
                    ]
                )

            if MemoryTier.WARM in search_tiers:
                warm_results = await self.warm_memory.search(query, limit, {"tags": [self.session_id]})
                results.extend(
                    [
                        {
                            "tier": "warm",
                            "entry": r.entry,
                            "score": r.score,
                        }
                        for r in warm_results
                    ]
                )

            if MemoryTier.COLD in search_tiers:
                cold_results = await self.cold_memory.search(query, limit, {"tags": [self.session_id]})
                results.extend(
                    [
                        {
                            "tier": "cold",
                            "entry": r.entry,
                            "score": r.score,
                        }
                        for r in cold_results
                    ]
                )

            # Sort by score
            results.sort(key=lambda x: x["score"], reverse=True)

            return results[:limit]

        except Exception:


            pass
            logger.error(f"Failed to search memories: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
                "session_id": self.session_id,
                "message_cache_size": len(self._message_cache),
                "tiers": {
                    "hot": hot_stats,
                    "warm": warm_stats,
                    "cold": cold_stats,
                },
            }

        except Exception:


            pass
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}

class ConversationSummaryBufferMemoryWrapper(ConversationSummaryBufferMemory):
    """
    """
        moving_summary_buffer: str = "",
        memory_wrapper: Optional[LangChainMemoryWrapper] = None,
        **kwargs,
    ):
        """
        """
        """Save summary to warm tier."""
                key=f"{self.memory_wrapper.session_id}:summary:{datetime.utcnow().isoformat()}",
                content={
                    "type": "summary",
                    "content": summary,
                    "timestamp": datetime.utcnow().isoformat(),
                    "session_id": self.memory_wrapper.session_id,
                    "token_count": len(summary.split()),  # Rough estimate
                },
                metadata=MemoryMetadata(
                    tags=["summary", self.memory_wrapper.session_id],
                    source="langchain_summary",
                    tier=MemoryTier.WARM,
                    ttl_seconds=86400 * 7,  # 7 days
                ),
            )

            await self.memory_wrapper.warm_memory.save(summary_entry)
            logger.info(f"Saved conversation summary ({len(summary)} chars)")

        except Exception:


            pass
            logger.error(f"Failed to save summary: {e}")

    async def aget_relevant_summaries(self, query: str, limit: int = 3) -> List[str]:
        """Retrieve relevant summaries based on query."""
                    "tags": ["summary", self.memory_wrapper.session_id],
                },
            )

            summaries = []
            for result in results:
                if result.entry.content.get("type") == "summary":
                    summaries.append(result.entry.content.get("content", ""))

            return summaries

        except Exception:


            pass
            logger.error(f"Failed to get relevant summaries: {e}")
            return []
