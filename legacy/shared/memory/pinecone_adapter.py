"""
"""
    """
    """
            raise RuntimeError("PINECONE_API_KEY not configured.")
        pinecone_env = environment or settings.pinecone_environment or "us-west1-gcp"
        pinecone.init(api_key=api_key, environment=pinecone_env)
        self.index_name = index_name
        self.namespace = namespace
        self.dimension = dimension
        self._index = None

    async def connect(self):
        """Connect to Pinecone index (idempotent)."""
            logger.info(f"Connected to Pinecone index: {self.index_name}")

    async def upsert_vectors(self, vectors: List[Dict[str, Any]], batch_size: int = 100):
        """
        """
            ids = [v["id"] for v in batch]
            values = [v["values"] for v in batch]
            metadata = [v.get("metadata", {}) for v in batch]
            # Pinecone expects list of (id, vector, metadata)
            upsert_batch = [(ids[j], values[j], metadata[j]) for j in range(len(batch))]
            try:

                pass
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._index.upsert(upsert_batch, namespace=self.namespace),
                )
                logger.info(f"Upserted batch {i}-{i+len(batch)-1} to Pinecone.")
            except Exception:

                pass
                logger.error(f"Pinecone upsert failed for batch {i}-{i+len(batch)-1}: {e}")

    async def query(
        self,
        vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        """
            matches = result.get("matches", [])
            return [{"id": m["id"], "score": m["score"], "metadata": m.get("metadata", {})} for m in matches]
        except Exception:

            pass
            logger.error(f"Pinecone query failed: {e}")
            return []

    async def delete(self, ids: List[str]):
        """Delete vectors by IDs."""
            logger.info(f"Deleted {len(ids)} vectors from Pinecone.")
        except Exception:

            pass
            logger.error(f"Pinecone delete failed: {e}")
