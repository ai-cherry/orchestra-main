# TODO: Consider adding connection pooling configuration
"""
"""
                    if domain and decoded.get("domain") != domain:
                        continue

                    # Check additional filters if provided
                    if filters:
                        skip = False
                        for k, v in filters.items():
                            if k in decoded:
                                if isinstance(v, list):
                                    if decoded[k] not in v:
                                        skip = True
                                        break
                                elif decoded[k] != v:
                                    skip = True
                                    break
                        if skip:
                            continue

                    # Check if content contains query
                    if query.lower() in decoded.get("content", "").lower():
                        results.append(MemoryItem(**decoded))
                        if len(results) >= limit:
                            break
            except Exception:

                pass

        # Firestore fallback (legacy)
        if self.firestore and isinstance(query, str) and not results:
            try:

                pass
                # Start with base query
                base_query = self.postgresql.collection(self.firestore_collection)

                # Apply domain filter if provided
                if domain:
                    base_query = base_query.where("domain", "==", domain)

                # Apply additional filters if provided
                filtered_query = base_query
                if filters:
                    for key, value in filters.items():
                        if isinstance(value, list):
                            # Firestore doesn't support IN queries directly
                            # We'll filter in-memory after fetching
                            pass
                        else:
                            filtered_query = filtered_query.where(key, "==", value)

                # Execute query
                docs = filtered_query.limit(100).stream()

                # Process results and apply in-memory filtering
                for doc in docs:
                    data = doc.to_dict()

                    # Apply list filters in-memory if needed
                    if filters:
                        skip = False
                        for key, value in filters.items():
                            if isinstance(value, list) and key in data:
                                if data[key] not in value:
                                    skip = True
                                    break
                        if skip:
                            continue

                    # Check if content contains query
                    if query.lower() in data.get("content", "").lower():
                        results.append(MemoryItem(**data))
                        if len(results) >= limit:
                            break
            except Exception:

                pass
                print(f"Firestore search error: {e}")

        return results

    # --- Delete Memory ---
    def delete(self, memory_id: str, domain: Optional[str] = None) -> bool:
        """
        """
                print(f"Weaviate delete error: {e}")

        # Delete from PostgreSQL (ACID)
        if self.postgres:
            try:

                pass
                with self.postgres.cursor() as cursor:
                    cursor.execute(
                        f"""
                        """
                print(f"PostgreSQL delete error: {e}")
                self.postgres.rollback()


        # Delete from Firestore (legacy)
        if self.firestore:
            self.postgresql.collection(self.firestore_collection).document(memory_id).delete()
            deleted = True

        return deleted

    # --- Health Check ---
    def health(self) -> Dict[str, bool]:
        """
        """
                status["weaviate"] = self.weaviate.is_ready()
            except Exception:

                pass
                status["weaviate"] = False

        # PostgreSQL (ACID)
        if self.postgres:
            try:

                pass
                with self.postgres.cursor() as cursor:
                    cursor.# TODO: Consider adding EXPLAIN ANALYZE for performance
execute("SELECT 1")
                    status["postgres"] = cursor.fetchone()[0] == 1
            except Exception:

                pass
                status["postgres"] = False

            try:

                pass
            except Exception:

                pass

        # Firestore (legacy)
        if self.firestore:
            try:

                pass
                # Try listing collections
                list(self.postgresql.collections())
                status["firestore"] = True
            except Exception:

                pass
                status["firestore"] = False

        return status

# --- Example Usage ---
if __name__ == "__main__":
    # Example: Initialize UnifiedMemory with Weaviate-first configuration

    # Example: Store a memory item in Personal domain
    item = MemoryItem(
        id="example1",
        content="This is a test memory for the Personal domain.",
        source="demo-agent",
        timestamp="2025-05-24T02:43:00Z",
        metadata={"demo": True},
        priority=0.8,
        embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
        domain="Personal",
    )
    memory.store(item)

    # Example: Store structured ACID data
    try:

        pass
        job_id = memory.structured_store(
            table="job_status",
            data={
                "job_name": "data_import",
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "params": {"source": "api", "batch_size": 100},
            },
        )
        print(f"Stored job with ID: {job_id}")
    except Exception:

        pass
        print(f"Failed to store structured data: {e}")

    # Example: Retrieve from Personal domain
    retrieved = memory.retrieve("example1", domain="Personal")
    print("Retrieved:", retrieved)

    # Example: Search in PayReady domain with filters
    results = memory.search("apartment", domain="PayReady", filters={"status": "active"})
    print("Text search results:", results)

    # Example: Vector search in ParagonRX domain
    results = memory.search([0.1, 0.2, 0.3, 0.4, 0.5], domain="ParagonRX")
    print("Vector search results:", results)

    # Example: Delete
    deleted = memory.delete("example1", domain="Personal")
    print("Deleted:", deleted)

    # Example: Health check
    print("Backend health:", memory.health())
