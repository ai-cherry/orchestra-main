# TODO: Consider adding connection pooling configuration
"""
"""
    """Metadata for context entries."""
    context_id: str = Field(description="Unique context identifier")
    parent_id: Optional[str] = Field(default=None, description="Parent context ID")
    version: int = Field(default=1, description="Context version number")
    source: str = Field(description="Source system: 'factory' or 'mcp'")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    embeddings: Optional[List[float]] = Field(default=None, description="Vector embeddings")

class ContextVersion(BaseModel):
    """Version history entry for context changes."""
    change_type: str = Field(description="Type: 'create', 'update', 'merge'")

class UnifiedContextManager:
    """
            await manager.store_context("ctx_123", {"data": "value"}, "factory")

            # Retrieve context
            context = await manager.get_context("ctx_123")

            # Search similar contexts
            similar = await manager.search_similar_contexts("query", limit=5)
        ```
    """
        """
        """
        """Async context manager entry."""
        """Async context manager exit."""
        """Start the context manager and background sync."""
        logger.info("UnifiedContextManager started")

    async def stop(self) -> None:
        """Stop the context manager and cleanup."""
        logger.info("UnifiedContextManager stopped")

    async def store_context(
        self,
        context_id: str,
        data: Dict[str, Any],
        source: str,
        parent_id: Optional[str] = None,
        embeddings: Optional[List[float]] = None,
    ) -> ContextMetadata:
        """
        """
            raise ValueError(f"Context size {data_size} exceeds limit {self.max_context_size}")

        # Check if context exists
        existing = await self._get_context_metadata(context_id)

        if existing:
            # Update existing context
            version = existing.version + 1
            change_type = "update"
        else:
            # Create new context
            version = 1
            change_type = "create"

        # Store in PostgreSQL
        metadata = await self._store_context_metadata(context_id, data, source, parent_id, version, embeddings)

        # Store version history
        await self._store_version_history(context_id, version, data, change_type, source)

        # Update cache
        await self.cache.set(f"context:{context_id}", {"metadata": metadata.dict(), "data": data})

        # Store in Weaviate if embeddings provided
        if embeddings:
            await self._store_in_weaviate(context_id, data, embeddings)

        logger.info(f"Stored context {context_id} version {version} from {source}")
        return metadata

    async def get_context(self, context_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        """
        cache_key = f"context:{context_id}"
        if version:
            cache_key += f":v{version}"

        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # Fetch from database
        if version:
            data = await self._get_context_version(context_id, version)
        else:
            metadata = await self._get_context_metadata(context_id)
            if metadata:
                data = await self._get_context_data(context_id)
            else:
                data = None

        if data:
            # Update cache
            await self.cache.set(cache_key, data)

        return data

    async def search_similar_contexts(
        self,
        query_embeddings: List[float],
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        """
                self.weaviate.query.get("FactoryContext", ["contextId", "metadata"])
                .with_near_vector({"vector": query_embeddings, "certainty": threshold})
                .with_limit(limit)
                .do()
            )

            similar_contexts = []
            if results and "data" in results:
                for item in results["data"]["Get"]["FactoryContext"]:
                    context_id = item["contextId"]
                    metadata = item["metadata"]
                    # Calculate similarity score (Weaviate uses certainty)
                    score = item.get("_additional", {}).get("certainty", 0.0)
                    similar_contexts.append((context_id, score, metadata))

            return similar_contexts

        except Exception:


            pass
            logger.error(f"Weaviate search error: {e}")
            return []

    async def merge_contexts(
        self,
        context_ids: List[str],
        merge_strategy: str = "latest",
    ) -> str:
        """
        """
            raise ValueError("No valid contexts found to merge")

        # Apply merge strategy
        if merge_strategy == "latest":
            # Use the most recent context as base
            merged_data = contexts[-1]["data"]
        elif merge_strategy == "union":
            # Combine all unique keys
            merged_data = {}
            for ctx in contexts:
                merged_data.update(ctx["data"])
        elif merge_strategy == "intersection":
            # Keep only common keys
            if contexts:
                merged_data = contexts[0]["data"].copy()
                for ctx in contexts[1:]:
                    merged_data = {k: v for k, v in merged_data.items() if k in ctx["data"]}
            else:
                merged_data = {}
        else:
            raise ValueError(f"Unknown merge strategy: {merge_strategy}")

        # Create new merged context
        new_context_id = f"merged_{uuid4().hex[:8]}"
        await self.store_context(new_context_id, merged_data, "mcp", parent_id=context_ids[0])  # Use first as parent

        logger.info(f"Merged {len(context_ids)} contexts into {new_context_id}")
        return new_context_id

    async def sync_with_factory(self, factory_context: Dict[str, Any]) -> None:
        """
        """
        context_id = factory_context.get("id", str(uuid4()))
        data = factory_context.get("data", {})

        # Generate embeddings if needed
        embeddings = await self._generate_embeddings(data)

        await self.store_context(context_id, data, "factory", embeddings=embeddings)

    async def sync_to_factory(self, context_id: str) -> Dict[str, Any]:
        """
        """
            raise ValueError(f"Context {context_id} not found")

        # Convert to Factory AI format
        factory_format = {
            "id": context_id,
            "data": context["data"],
            "metadata": context.get("metadata", {}),
            "timestamp": datetime.utcnow().isoformat(),
        }

        return factory_format

    async def cleanup_old_versions(self) -> int:
        """
        """
            query = """
            """
                context_id = record["context_id"]
                excess = record["version_count"] - self.version_retention

                # Delete oldest versions
                delete_query = """
                """
            logger.info(f"Cleaned up {total_cleaned} old context versions")
            return total_cleaned

    async def get_metrics(self) -> Dict[str, Any]:
        """
        """
            context_count = await conn.fetchval("SELECT COUNT(*) FROM factory_context_metadata")
            version_count = await conn.fetchval("SELECT COUNT(*) FROM factory_context_versions")

        # Get cache metrics
        cache_metrics = await self.cache.get_metrics()

        return {
            "contexts": {
                "total": context_count,
                "versions": version_count,
                "avg_versions_per_context": version_count / max(context_count, 1),
            },
            "cache": cache_metrics,
            "sync": {"interval": self.sync_interval, "running": self._running},
        }

    # Private helper methods

    async def _sync_loop(self) -> None:
        """Background sync loop."""
                logger.error(f"Sync loop error: {e}")

    async def _get_context_metadata(self, context_id: str) -> Optional[ContextMetadata]:
        """Get context metadata from PostgreSQL."""
            query = """
            """
        """Get latest context data from PostgreSQL."""
            query = """
            """
                return record["data"]
            return None

    async def _get_context_version(self, context_id: str, version: int) -> Optional[Dict[str, Any]]:
        """Get specific context version from PostgreSQL."""
            query = """
            """
                return record["data"]
            return None

    async def _store_context_metadata(
        self,
        context_id: str,
        data: Dict[str, Any],
        source: str,
        parent_id: Optional[str],
        version: int,
        embeddings: Optional[List[float]],
    ) -> ContextMetadata:
        """Store context metadata in PostgreSQL."""
            query = """
            """
                embeddings_vector = f"[{','.join(map(str, embeddings))}]"

            record = await conn.fetchrow(
                query, context_id, parent_id, version, source, json.dumps(data), embeddings_vector, datetime.utcnow()
            )

            return ContextMetadata(**dict(record))

    async def _store_version_history(
        self,
        context_id: str,
        version: int,
        data: Dict[str, Any],
        change_type: str,
        changed_by: str,
    ) -> None:
        """Store version history in PostgreSQL."""
            query = """
            """
        """Store context in Weaviate for vector search."""
                "contextId": context_id,
                "content": content,
                "metadata": data,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Store with vector
            self.weaviate.data_object.create(weaviate_object, "FactoryContext", vector=embeddings)

        except Exception:


            pass
            logger.error(f"Failed to store in Weaviate: {e}")

    async def _generate_embeddings(self, data: Dict[str, Any]) -> List[float]:
        """
        """