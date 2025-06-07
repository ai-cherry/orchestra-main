"""
"""
    """
    """
            raise RuntimeError("WEAVIATE_ENDPOINT and WEAVIATE_API_KEY must be configured")
        self.class_name = class_name
        self._client = None

    async def connect(self):
        """Connect to Weaviate instance (idempotent)."""
            logger.info(f"Connected to Weaviate at: {self.endpoint}")

    async def batch_upsert(self, objects: List[Dict[str, Any]], batch_size: int = 100):
        """
        """
                            uuid = get_valid_uuid(obj["id"])
                            batcher.add_data_object(
                                data_object=obj["properties"],
                                class_name=self.class_name,
                                uuid=uuid,
                                vector=obj["vector"],
                            )

                await asyncio.get_event_loop().run_in_executor(None, upsert_batch)
                logger.info(f"Upserted batch {i}-{i+len(batch)-1} to Weaviate.")
            except Exception:

                pass
                logger.error(f"Weaviate upsert failed for batch {i}-{i+len(batch)-1}: {e}")

    async def query(
        self,
        vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        """
                    self._client.query.get(self.class_name, ["_additional { id distance }", "*"])
                    .with_near_vector({"vector": vector})
                    .with_limit(top_k)
                    .with_where(filters)
                    .do()
                )

            result = await asyncio.get_event_loop().run_in_executor(None, do_query)
            matches = result.get("data", {}).get("Get", {}).get(self.class_name, [])
            return [
                {
                    "id": m["_additional"]["id"],
                    "score": 1.0 - m["_additional"]["distance"],  # Weaviate uses distance, convert to similarity
                    "properties": {k: v for k, v in m.items() if k != "_additional"},
                }
                for m in matches
            ]
        except Exception:

            pass
            logger.error(f"Weaviate query failed: {e}")
            return []

    async def delete(self, ids: List[str]):
        """Delete objects by IDs."""
            logger.info(f"Deleted {len(ids)} objects from Weaviate.")
        except Exception:

            pass
            logger.error(f"Weaviate delete failed: {e}")
