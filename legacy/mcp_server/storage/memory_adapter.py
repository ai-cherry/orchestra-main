#!/usr/bin/env python3
"""
"""
    """
    """
        """
        """
        """
        """
        """
        """
        scope = "default"
        if hasattr(entry, "scope") and entry.scope:
            scope = entry.scope

        # Store using the optimized storage
        return await self.storage.store(key, entry, scope)

    async def get(self, key: str) -> Optional[MemoryEntry]:
        """
        """
        """
        """
    async def list_keys(self, prefix: str = "") -> List[str]:
        """
        """
        """
        """
                result_key = results[0].get("key", None)
                if result_key:
                    # Retrieve the full entry
                    return await self.get(result_key)
        return None

    async def search(self, query: str, limit: int = 10) -> List[Tuple[str, MemoryEntry, float]]:
        """
        """
            key = result.get("_key", "unknown")
            # The content might be stored in different formats
            if isinstance(result, dict) and "_key" in result:
                content_dict = dict(result)
                content_dict.pop("_key", None)
                entry = content_dict
            else:
                entry = result

            # Convert to MemoryEntry if it's not already
            if not isinstance(entry, MemoryEntry):
                try:

                    pass
                    # Try to convert to MemoryEntry
                    metadata = MemoryMetadata(
                        source_tool="unknown",
                        last_modified=time.time(),
                        access_count=0,
                        context_relevance=1.0,
                        last_accessed=time.time(),
                        version=1,
                        sync_status={},
                        content_hash=None,
                    )
                    memory_entry = MemoryEntry(content=entry, metadata=metadata)
                except Exception:

                    pass
                    # Fall back to raw entry
                    memory_entry = entry

            converted_results.append((key, memory_entry, 1.0))  # Score is hardcoded for now

        return converted_results

    async def health_check(self) -> Dict[str, Any]:
        """
        """