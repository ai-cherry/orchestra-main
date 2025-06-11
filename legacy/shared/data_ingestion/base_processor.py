"""
"""
    """
    """
        """Check if a record with the given fingerprint already exists."""
        """Insert or update a batch of records."""
        """Clean up resources (connections, etc.)."""
    """
    """
        """
        """
        """
        """
                    record["_fingerprint"] = fingerprint
                processed.append(record)
            if processed:
                await self.storage.upsert_batch(processed)
                total += len(processed)
                if progress_cb:
                    progress_cb(total, len(processed))
        return total

    @abc.abstractmethod
    async def batch_generator(self, source: Any) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """
        """
        """
        """
            m.update(str(k).encode("utf-8"))
            m.update(str(v).encode("utf-8"))
        return m.hexdigest()
