# TODO: Consider adding connection pooling configuration
"""
"""
T = TypeVar("T")


class MemoryQuery(BaseModel):
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
        """
        """
        """
        """
        """
        """
        except Exception:

            pass
            self.db = None

class RedisMemoryStore(MemoryStore):
    """
    """
        """Initialize the Redis memory store."""
            host = self.config.get("host", "localhost")
            port = self.config.get("port", 6379)
            db = self.config.get("db", 0)
            password = self.config.get("password")

            # Create Redis client
            self._client = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True)

            # Test connection
            await self._client.ping()

            # Set initialized flag
            self._initialized = True

            logger.info(f"Redis memory store initialized: {host}:{port}/{db}")
        except Exception:

            pass
            logger.error("Redis package not installed. Install with: pip install redis")
            raise
        except Exception:

            pass
            logger.error(f"Failed to initialize Redis memory store: {e}")
            raise ConnectionError(f"Redis connection failed: {e}")

    async def close(self) -> None:
        """Close the Redis memory store."""

    async def store(self, item: MemoryItem) -> str:
        """Store a memory item in Redis."""
            item_id = item.id or f"mem:{int(time.time() * 1000)}"

            # Prepare item for storage
            item_dict = item.dict()

            # Store in Redis
            key = f"memory:{item_id}"
            await self._client.hset(key, mapping=item_dict)

            # Set TTL if configured
            ttl = self.config.get("ttl")
            if ttl:
                await self._client.expire(key, ttl)

            # Add to index
            await self._client.sadd("memory:index", item_id)

            # Update stats
            storage_time = (time.time() - start_time) * 1000
            item_count = await self._client.scard("memory:index")
            self._update_stats(item_count=item_count, avg_storage_time_ms=storage_time)

            return item_id
        except Exception:

            pass
            logger.error(f"Failed to store item in Redis: {e}")
            raise ConnectionError(f"Redis storage failed: {e}")

    async def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve a memory item from Redis."""
            key = f"memory:{item_id}"
            exists = await self._client.exists(key)
            if not exists:
                return None

            # Retrieve item
            item_dict = await self._client.hgetall(key)

            # Convert to MemoryItem
            item = MemoryItem.parse_obj(item_dict)

            # Update stats
            retrieval_time = (time.time() - start_time) * 1000
            self._update_stats(avg_retrieval_time_ms=retrieval_time)

            return item
        except Exception:

            pass
            logger.error(f"Failed to retrieve item from Redis: {e}")
            raise ConnectionError(f"Redis retrieval failed: {e}")

    async def query(self, query: MemoryQuery) -> List[MemoryItem]:
        """Query for memory items in Redis."""
            item_ids = await self._client.smembers("memory:index")

            # Apply limit and offset
            item_ids = list(item_ids)[query.offset : query.offset + query.limit]

            # Retrieve items
            items = []
            for item_id in item_ids:
                item = await self.retrieve(item_id)
                if item:
                    # Apply metadata filters
                    if query.metadata_filters:
                        match = True
                        for key, value in query.metadata_filters.items():
                            if key not in item.metadata or item.metadata[key] != value:
                                match = False
                                break
                        if not match:
                            continue

                    # Apply text filter
                    if query.text and query.text.lower() not in item.text_content.lower():
                        continue

                    # Apply time range filter
                    if query.time_range:
                        start, end = query.time_range
                        if item.timestamp < start or item.timestamp > end:
                            continue

                    items.append(item)

            # Update stats
            retrieval_time = (time.time() - start_time) * 1000
            self._update_stats(avg_retrieval_time_ms=retrieval_time)

            return items
        except Exception:

            pass
            logger.error(f"Failed to query items from Redis: {e}")
            raise ConnectionError(f"Redis query failed: {e}")

    async def delete(self, item_id: str) -> bool:
        """Delete a memory item from Redis."""
            key = f"memory:{item_id}"
            exists = await self._client.exists(key)
            if not exists:
                return False

            # Delete item
            await self._client.delete(key)

            # Remove from index
            await self._client.srem("memory:index", item_id)

            # Update stats
            item_count = await self._client.scard("memory:index")
            self._update_stats(item_count=item_count)

            return True
        except Exception:

            pass
            logger.error(f"Failed to delete item from Redis: {e}")
            raise ConnectionError(f"Redis deletion failed: {e}")

    async def clear(self) -> int:
        """Clear all memory items from Redis."""
            item_ids = await self._client.smembers("memory:index")
            count = len(item_ids)

            # Delete all items
            for item_id in item_ids:
                key = f"memory:{item_id}"
                await self._client.delete(key)

            # Clear index
            await self._client.delete("memory:index")

            # Update stats
            self._update_stats(item_count=0)

            return count
        except Exception:

            pass
            logger.error(f"Failed to clear items from Redis: {e}")
            raise ConnectionError(f"Redis clear failed: {e}")

    """
    """
            collection = self.config.get("collection", "memory")
            project = self.config.get("project", "cherry-ai-project")

            self._collection = self._client.collection(collection)

            # Set initialized flag
            self._initialized = True

        except Exception:

            pass
            raise
        except Exception:

            pass

    async def close(self) -> None:

    async def store(self, item: MemoryItem) -> str:
            item_id = item.id or f"mem:{int(time.time() * 1000)}"

            # Prepare item for storage
            item_dict = item.dict()


            if item_dict.get("timestamp"):
                item_dict["timestamp"] = item_dict["timestamp"]
            else:
                item_dict["timestamp"] = SERVER_TIMESTAMP

            doc_ref = self._collection.document(item_id)
            await doc_ref.set(item_dict)

            # Update stats
            storage_time = (time.time() - start_time) * 1000
            self._update_stats(avg_storage_time_ms=storage_time)

            # Update item count (this is expensive, so we do it occasionally)
            if storage_time < 100:  # Only if storage was fast
                try:

                    pass
                    count_query = self._collection.count()
                    count = await count_query.get()
                    self._update_stats(item_count=count[0][0])
                except Exception:

                    pass
                    logger.warning(f"Failed to update item count: {count_err}")

            return item_id
        except Exception:

            pass

    async def retrieve(self, item_id: str) -> Optional[MemoryItem]:
            if "timestamp" in item_dict and item_dict["timestamp"]:
                item_dict["timestamp"] = item_dict["timestamp"].isoformat()

            item = MemoryItem.parse_obj(item_dict)

            # Update stats
            retrieval_time = (time.time() - start_time) * 1000
            self._update_stats(avg_retrieval_time_ms=retrieval_time)

            return item
        except Exception:

            pass

    async def query(self, query: MemoryQuery) -> List[MemoryItem]:
                fs_query = fs_query.where(f"metadata.{key}", "==", value)

            # Apply time range filter
            if query.time_range:
                start, end = query.time_range
                fs_query = fs_query.where("timestamp", ">=", start)
                fs_query = fs_query.where("timestamp", "<=", end)

            # Apply limit and offset
            fs_query = fs_query.limit(query.limit).offset(query.offset)

            # Execute query
            docs = await fs_query.get()

            # Convert to MemoryItems
            items = []
            for doc in docs:
                item_dict = doc.to_dict()

                if "timestamp" in item_dict and item_dict["timestamp"]:
                    item_dict["timestamp"] = item_dict["timestamp"].isoformat()

                item = MemoryItem.parse_obj(item_dict)

                if query.text and query.text.lower() not in item.text_content.lower():
                    continue

                items.append(item)

            # Update stats
            retrieval_time = (time.time() - start_time) * 1000
            self._update_stats(avg_retrieval_time_ms=retrieval_time)

            return items
        except Exception:

            pass

    async def delete(self, item_id: str) -> bool:
                logger.warning(f"Failed to update item count: {count_err}")

            return True
        except Exception:

            pass

    async def clear(self) -> int:
