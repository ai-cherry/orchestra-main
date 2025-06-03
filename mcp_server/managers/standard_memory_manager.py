#!/usr/bin/env python3
"""
"""
    """Manages token budgets for different tools."""
        """Initialize with token budgets for each tool."""
        """Estimate the number of tokens for a memory entry using a more accurate approach."""
        words = re.findall(r"\w+", content_str)
        whitespace_count = len(re.findall(r"\s", content_str))
        punctuation_count = len(re.findall(r"[^\w\s]", content_str))

        # Calculate estimated tokens
        word_tokens = len(words) * 1.3
        whitespace_tokens = whitespace_count * 0.25
        punctuation_tokens = punctuation_count * 0.5

        # Add base overhead for JSON structure if content is a dict
        overhead = 4 if isinstance(entry.content, dict) else 0

        return int(word_tokens + whitespace_tokens + punctuation_tokens + overhead)

    def can_fit_entry(self, entry: MemoryEntry, tool: str) -> bool:
        """Check if an entry can fit in a tool's token budget."""
        """Add an entry to a tool's token usage."""
        """Remove an entry from a tool's token usage."""
        """Get the available token budget for a tool."""
    """Handles memory compression and decompression."""
        """Compress a memory entry based on its compression level."""
                    compressed_entry.content = entry.content[:900] + "... [compressed]"

            elif entry.compression_level == CompressionLevel.MEDIUM:
                # Medium compression: extract key sentences
                if len(entry.content) > 500:
                    sentences = entry.content.split(". ")
                    if len(sentences) > 5:
                        important_sentences = sentences[:2] + ["..."] + sentences[-2:]
                        compressed_entry.content = ". ".join(important_sentences)

            elif entry.compression_level == CompressionLevel.HIGH:
                # High compression: keep only first and last paragraph
                if len(entry.content) > 300:
                    paragraphs = entry.content.split("\n\n")
                    if len(paragraphs) > 2:
                        compressed_entry.content = (
                            paragraphs[0] + "\n\n... [highly compressed] ...\n\n" + paragraphs[-1]
                        )

            elif entry.compression_level == CompressionLevel.EXTREME:
                # Extreme compression: keep only first paragraph
                if len(entry.content) > 100:
                    paragraphs = entry.content.split("\n\n")
                    compressed_entry.content = paragraphs[0] + " ... [extremely compressed]"

            elif entry.compression_level == CompressionLevel.REFERENCE_ONLY:
                # Reference only: keep only a reference to the original content
                compressed_entry.content = f"[Reference: memory with hash {entry.metadata.content_hash}]"

        elif isinstance(entry.content, dict):
            if entry.compression_level == CompressionLevel.LIGHT:
                # For dictionaries, keep only key fields
                important_keys = set(list(entry.content.keys())[:5])
                compressed_entry.content = {k: v for k, v in entry.content.items() if k in important_keys}
                if len(entry.content) > len(compressed_entry.content):
                    compressed_entry.content["_compressed"] = True

            elif entry.compression_level == CompressionLevel.MEDIUM:
                # Keep only 3 key fields
                important_keys = set(list(entry.content.keys())[:3])
                compressed_entry.content = {k: v for k, v in entry.content.items() if k in important_keys}
                compressed_entry.content["_compressed"] = True

            elif entry.compression_level in [
                CompressionLevel.HIGH,
                CompressionLevel.EXTREME,
                CompressionLevel.REFERENCE_ONLY,
            ]:
                # Keep only key names for higher compression levels
                compressed_entry.content = {
                    "_compressed": True,
                    "_keys": list(entry.content.keys()),
                }

        return compressed_entry

class StandardMemoryManager(IMemoryManager):
    """Standard implementation of memory manager."""
        """Initialize the standard memory manager."""
        """Initialize the memory manager."""
        logger.info("Initializing standard memory manager")

        # Initialize storage
        storage_initialized = await self.storage.initialize()
        if not storage_initialized:
            logger.error("Failed to initialize storage")
            return False

        # Initialize token budget manager
        token_budgets = {}
        for tool_name, adapter in self.tools.items():
            token_budgets[tool_name] = adapter.context_window_size
        self.token_budget_manager = TokenBudgetManager(token_budgets)

        # Initialize tools
        for tool_name, adapter in self.tools.items():
            try:

                pass
                tool_initialized = await adapter.initialize()
                if not tool_initialized:
                    logger.warning(f"Failed to initialize tool adapter: {tool_name}")
            except Exception:

                pass
                logger.error(f"Error initializing tool adapter {tool_name}: {e}")

        self.initialized = True
        logger.info("Standard memory manager initialized")
        return True

    def register_tool(self, adapter: IToolAdapter) -> None:
        """Register a tool with the memory manager."""
        logger.info(f"Registered tool adapter: {tool_name}")

    async def create_memory(self, key: str, entry: MemoryEntry, source_tool: str) -> bool:
        """Create a new memory entry."""
            logger.error("Memory manager not initialized")
            return False

        # Update entry metadata
        entry.metadata.source_tool = source_tool
        entry.metadata.last_modified = time.time()
        entry.update_hash()

        # Save to storage
        save_success = await self.storage.save(key, entry)
        if not save_success:
            logger.error(f"Failed to save memory entry: {key}")
            return False

        # Sync to other tools
        if source_tool in self.tools:
            for tool_name, adapter in self.tools.items():
                if tool_name != source_tool:
                    try:

                        pass
                        # Compress if necessary for the target tool
                        compressed_entry = await self._compress_for_tool(entry, tool_name)
                        sync_success = await adapter.sync_create(key, compressed_entry or entry)
                        if not sync_success:
                            logger.warning(f"Failed to sync memory entry {key} to tool {tool_name}")
                    except Exception:

                        pass
                        logger.error(f"Error syncing memory entry {key} to tool {tool_name}: {e}")

        logger.info(f"Created memory entry: {key} from {source_tool}")
        return True

    async def get_memory(self, key: str, tool: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry for a specific tool."""
            logger.error("Memory manager not initialized")
            return None

        # Get from storage
        entry = await self.storage.get(key)
        if not entry:
            return None

        # If the tool is different from the source, compress if needed
        if tool != entry.metadata.source_tool and tool in self.tools:
            # Check if the entry would fit in the tool's context window
            token_estimate = self.token_budget_manager.estimate_tokens(entry)
            available_budget = self.token_budget_manager.get_available_budget(tool)

            if token_estimate > available_budget:
                # Try to compress
                compressed_entry = await self._compress_for_tool(entry, tool)
                if compressed_entry:
                    return compressed_entry

        return entry

    async def update_memory(self, key: str, entry: MemoryEntry, source_tool: str) -> bool:
        """Update an existing memory entry."""
            logger.error("Memory manager not initialized")
            return False

        # Get the existing entry
        existing = await self.storage.get(key)

        if not existing:
            logger.info(f"Memory entry not found for update, creating new: {key}")
            return await self.create_memory(key, entry, source_tool)

        # Update entry metadata
        entry.metadata.source_tool = source_tool
        entry.metadata.last_modified = time.time()
        entry.metadata.version = existing.metadata.version + 1
        entry.update_hash()

        # Save to storage
        save_success = await self.storage.save(key, entry)
        if not save_success:
            logger.error(f"Failed to update memory entry: {key}")
            return False

        # Sync to other tools
        if source_tool in self.tools:
            for tool_name, adapter in self.tools.items():
                if tool_name != source_tool:
                    try:

                        pass
                        # Compress if necessary for the target tool
                        compressed_entry = await self._compress_for_tool(entry, tool_name)
                        sync_success = await adapter.sync_update(key, compressed_entry or entry)
                        if not sync_success:
                            logger.warning(f"Failed to sync updated memory entry {key} to tool {tool_name}")
                    except Exception:

                        pass
                        logger.error(f"Error syncing updated memory entry {key} to tool {tool_name}: {e}")

        logger.info(f"Updated memory entry: {key} from {source_tool}")
        return True

    async def delete_memory(self, key: str, source_tool: str) -> bool:
        """Delete a memory entry."""
            logger.error("Memory manager not initialized")
            return False

        # Get the existing entry
        existing = await self.storage.get(key)
        if not existing:
            return False

        # Delete from storage
        delete_success = await self.storage.delete(key)
        if not delete_success:
            logger.error(f"Failed to delete memory entry: {key}")
            return False

        # Sync deletion to other tools
        if source_tool in self.tools:
            for tool_name, adapter in self.tools.items():
                if tool_name != source_tool:
                    try:

                        pass
                        sync_success = await adapter.sync_delete(key)
                        if not sync_success:
                            logger.warning(f"Failed to sync deletion of memory entry {key} to tool {tool_name}")
                    except Exception:

                        pass
                        logger.error(f"Error syncing deletion of memory entry {key} to tool {tool_name}: {e}")

        logger.info(f"Deleted memory entry: {key} from {source_tool}")
        return True

    async def search_memory(self, query: str, tool: str, limit: int = 10) -> List[Tuple[str, MemoryEntry, float]]:
        """Search for memory entries for a specific tool."""
            logger.error("Memory manager not initialized")
            return []

        # Search in storage
        search_results = await self.storage.search(query, limit)

        # If tool is different from the source of any entries, compress if needed
        if tool in self.tools:
            compressed_results = []
            for key, entry, score in search_results:
                if tool != entry.metadata.source_tool:
                    compressed_entry = await self._compress_for_tool(entry, tool)
                    if compressed_entry:
                        compressed_results.append((key, compressed_entry, score))
                    else:
                        compressed_results.append((key, entry, score))
                else:
                    compressed_results.append((key, entry, score))
            search_results = compressed_results

        logger.info(f"Search for '{query}' found {len(search_results)} results for {tool}")
        return search_results

    async def optimize_context_window(self, tool: str, required_keys: Optional[List[str]] = None) -> int:
        """Optimize the context window for a specific tool."""
            logger.error("Memory manager not initialized")
            return 0

        if tool not in self.tools:
            logger.error(f"Tool not registered: {tool}")
            return 0

        # Get available budget
        available_budget = self.token_budget_manager.get_available_budget(tool)

        # Get all keys
        all_keys = await self.storage.list_keys()
        entries = []

        # Get entries for required keys first
        if required_keys:
            for key in required_keys:
                if key in all_keys:
                    entry = await self.storage.get(key)
                    if entry and not entry.is_expired():
                        entries.append((key, entry))
                        token_estimate = self.token_budget_manager.estimate_tokens(entry)
                        available_budget -= token_estimate

        # Get other entries within budget
        other_keys = [k for k in all_keys if required_keys is None or k not in required_keys]

        # Sort by priority and relevance
        other_entries = []
        for key in other_keys:
            entry = await self.storage.get(key)
            if entry and not entry.is_expired():
                other_entries.append((key, entry))

        other_entries.sort(key=lambda x: (x[1].priority, x[1].metadata.context_relevance), reverse=True)

        # Add entries until budget is exhausted
        optimized_entries = entries

        for key, entry in other_entries:
            token_estimate = self.token_budget_manager.estimate_tokens(entry)

            if token_estimate <= available_budget:
                # Entry fits as-is
                optimized_entries.append((key, entry))
                available_budget -= token_estimate
            else:
                # Try to compress
                compressed_entry = await self._compress_for_tool(entry, tool)
                if compressed_entry:
                    compressed_tokens = self.token_budget_manager.estimate_tokens(compressed_entry)
                    if compressed_tokens <= available_budget:
                        optimized_entries.append((key, compressed_entry))
                        available_budget -= compressed_tokens

        logger.info(f"Optimized context window for {tool}: {len(optimized_entries)} entries")
        return len(optimized_entries)

    async def get_memory_status(self) -> Dict[str, Any]:
        """Get the status of the memory system."""
            logger.error("Memory manager not initialized")
            return {"status": "not_initialized"}

        storage_health = await self.storage.health_check()

        # Get tool status
        tool_status = {}
        for tool_name, adapter in self.tools.items():
            try:

                pass
                tool_status[tool_name] = await adapter.get_status()
            except Exception:

                pass
                logger.error(f"Error getting status for tool {tool_name}: {e}")
                tool_status[tool_name] = {"status": "error", "error": str(e)}

        # Count entries by type, scope, etc.
        all_keys = await self.storage.list_keys()
        entry_count = len(all_keys)

        tool_counts = {}
        scope_counts = {}
        type_counts = {}

        for key in all_keys:
            entry = await self.storage.get(key)
            if not entry:
                continue

            # Count by source tool
            source_tool = entry.metadata.source_tool
            tool_counts[source_tool] = tool_counts.get(source_tool, 0) + 1

            # Count by scope
            scope = entry.scope
            scope_counts[scope] = scope_counts.get(scope, 0) + 1

            # Count by type
            mem_type = entry.memory_type
            type_counts[mem_type] = type_counts.get(mem_type, 0) + 1

        return {
            "status": ("healthy" if storage_health.get("status") == "healthy" else "unhealthy"),
            "entry_count": entry_count,
            "tool_counts": tool_counts,
            "scope_counts": scope_counts,
            "type_counts": type_counts,
            "storage": storage_health,
            "tools": tool_status,
        }

    async def _compress_for_tool(self, entry: MemoryEntry, tool: str) -> Optional[MemoryEntry]:
        """Compress an entry to fit in a tool's context window."""
        logger.warning(f"Unable to compress entry enough to fit in tool's context window: {tool}")
        return None
