#!/usr/bin/env python3
"""
"""
    """
    """
        """
        """
        self.persistence_path = self.config.get("persistence_path")
        self.persist_on_change = self.config.get("persist_on_change", False)
        self.auto_load = self.config.get("auto_load", True)

        # Performance settings
        self.max_keys_per_scope = self.config.get("max_keys_per_scope", 10000)
        self.enable_search_index = self.config.get("enable_search_index", True)

        # Search index (scope -> term -> set of keys)
        self.search_index: Dict[str, Dict[str, Set[str]]] = {}

        # Stats
        self.stats = {
            "stores": 0,
            "retrievals": 0,
            "hits": 0,
            "misses": 0,
            "expirations": 0,
            "deletes": 0,
            "searches": 0,
        }

    async def initialize(self) -> bool:
        """
        """
                logger.info("Initializing optimized memory storage")

                # Create initial data structure
                # No need to acquire lock since we're initializing

                # Auto-load from persistence if configured
                if self.persistence_path and self.auto_load:
                    try:

                        pass
                        await self._load_from_persistence()
                    except Exception:

                        pass
                        logger.warning(f"Could not load data from persistence: {e}")

                self._initialized = True

            duration = time.time() - start_time
            self.perf.record_operation("storage.initialize", duration)
            return True
        except Exception:

            pass
            logger.error(f"Failed to initialize optimized memory storage: {e}")
            duration = time.time() - start_time
            self.perf.record_operation("storage.initialize.error", duration)
            return False

    async def store(self, key: str, entry: Any, scope: str = "default") -> bool:
        """
        """
            self.stats["stores"] += 1

            async with self.lock:
                # Create scope if it doesn't exist
                if scope not in self.data:
                    self.data[scope] = {}
                    self.ttls[scope] = {}
                    if self.enable_search_index:
                        self.search_index[scope] = {}

                # Check if we've reached the max keys limit
                if len(self.data[scope]) >= self.max_keys_per_scope:
                    # Try to clean expired keys first
                    await self._clean_expired_keys(scope)

                    # If still at limit, remove oldest key
                    if len(self.data[scope]) >= self.max_keys_per_scope:
                        oldest_key = next(iter(self.data[scope]))
                        del self.data[scope][oldest_key]
                        if oldest_key in self.ttls[scope]:
                            del self.ttls[scope][oldest_key]
                        # Remove from search index
                        if self.enable_search_index and scope in self.search_index:
                            for term_keys in self.search_index[scope].values():
                                if oldest_key in term_keys:
                                    term_keys.remove(oldest_key)

                # Store the data (make a copy to avoid reference issues)
                if isinstance(entry, dict):
                    self.data[scope][key] = json.loads(json.dumps(entry))
                elif isinstance(entry, (str, int, float, bool, list)):
                    self.data[scope][key] = entry
                else:
                    try:

                        pass
                        self.data[scope][key] = json.loads(json.dumps(entry))
                    except Exception:

                        pass
                        # Fall back to string representation
                        self.data[scope][key] = str(entry)

                # Set TTL if provided
                ttl = None
                if isinstance(entry, dict) and "ttl_seconds" in entry:
                    ttl = entry["ttl_seconds"]
                elif isinstance(entry, MemoryEntry) and entry.metadata.ttl_seconds:
                    ttl = entry.metadata.ttl_seconds

                if ttl:
                    self.ttls[scope][key] = time.time() + ttl
                elif key in self.ttls[scope]:
                    # Remove any existing TTL
                    del self.ttls[scope][key]

                # Update search index
                if self.enable_search_index:
                    await self._update_search_index(key, entry, scope)

            # Persist if configured
            if self.persistence_path and self.persist_on_change:
                await self._persist_to_storage()

            duration = time.time() - start_time
            self.perf.record_operation("storage.store", duration)
            return True
        except Exception:

            pass
            logger.error(f"Failed to store entry: {e}")
            duration = time.time() - start_time
            self.perf.record_operation("storage.store.error", duration)
            return False

    async def retrieve(self, key: str, scope: str = "default") -> Optional[Any]:
        """
        """
            self.stats["retrievals"] += 1

            async with self.lock:
                # Check if scope exists
                if scope not in self.data:
                    self.stats["misses"] += 1
                    return None

                # Check if key exists
                if key not in self.data[scope]:
                    self.stats["misses"] += 1
                    return None

                # Check if key has expired
                if scope in self.ttls and key in self.ttls[scope]:
                    if time.time() > self.ttls[scope][key]:
                        # Key has expired, remove it
                        del self.data[scope][key]
                        del self.ttls[scope][key]

                        # Remove from search index
                        if self.enable_search_index and scope in self.search_index:
                            for term_keys in self.search_index[scope].values():
                                if key in term_keys:
                                    term_keys.remove(key)

                        self.stats["expirations"] += 1
                        self.stats["misses"] += 1
                        return None

                # Return data (make a copy to avoid reference issues)
                self.stats["hits"] += 1
                if isinstance(self.data[scope][key], dict):
                    result = json.loads(json.dumps(self.data[scope][key]))
                else:
                    result = self.data[scope][key]

            duration = time.time() - start_time
            self.perf.record_operation("storage.retrieve", duration)
            return result
        except Exception:

            pass
            logger.error(f"Failed to retrieve entry: {e}")
            duration = time.time() - start_time
            self.perf.record_operation("storage.retrieve.error", duration)
            return None

    async def delete(self, key: str, scope: str = "default") -> bool:
        """
        """
            self.stats["deletes"] += 1

            async with self.lock:
                # Check if scope exists
                if scope not in self.data:
                    return False

                # Check if key exists
                if key not in self.data[scope]:
                    return False

                # Delete the key
                del self.data[scope][key]

                # Delete TTL if exists
                if scope in self.ttls and key in self.ttls[scope]:
                    del self.ttls[scope][key]

                # Remove from search index
                if self.enable_search_index and scope in self.search_index:
                    for term_keys in self.search_index[scope].values():
                        if key in term_keys:
                            term_keys.remove(key)

            # Persist if configured
            if self.persistence_path and self.persist_on_change:
                await self._persist_to_storage()

            duration = time.time() - start_time
            self.perf.record_operation("storage.delete", duration)
            return True
        except Exception:

            pass
            logger.error(f"Failed to delete entry: {e}")
            duration = time.time() - start_time
            self.perf.record_operation("storage.delete.error", duration)
            return False

    async def list_keys(self, scope: str = "default") -> List[str]:
        """
        """
            self.perf.record_operation("storage.list_keys", duration)
            return keys
        except Exception:

            pass
            logger.error(f"Failed to list keys: {e}")
            duration = time.time() - start_time
            self.perf.record_operation("storage.list_keys.error", duration)
            return []

    async def search(self, query: str, scope: str = "default", limit: int = 10) -> List[Dict[str, Any]]:
        """
        """
            self.stats["searches"] += 1

            results = []
            async with self.lock:
                # Check if scope exists
                if scope not in self.data:
                    return []

                # Clean expired keys first
                await self._clean_expired_keys(scope)

                # Use search index if enabled
                if self.enable_search_index and scope in self.search_index:
                    matching_keys = set()
                    # Split query into terms
                    terms = self._get_search_terms(query)

                    for term in terms:
                        if term in self.search_index[scope]:
                            # For first term, initialize the set
                            if not matching_keys:
                                matching_keys = self.search_index[scope][term].copy()
                            else:
                                # For subsequent terms, keep only keys that match all terms
                                matching_keys &= self.search_index[scope][term]

                    # Get data for matching keys
                    for key in list(matching_keys)[:limit]:
                        if key in self.data[scope]:
                            entry = self.data[scope][key]
                            # Add key to entry for reference
                            if isinstance(entry, dict):
                                entry_copy = json.loads(json.dumps(entry))
                                entry_copy["_key"] = key
                                results.append(entry_copy)
                            else:
                                results.append({"_key": key, "value": entry})
                else:
                    # Fallback to simple string matching
                    query_lower = query.lower()
                    for key, entry in self.data[scope].items():
                        if len(results) >= limit:
                            break

                        # Check if query is in key
                        if query_lower in key.lower():
                            if isinstance(entry, dict):
                                entry_copy = json.loads(json.dumps(entry))
                                entry_copy["_key"] = key
                                results.append(entry_copy)
                            else:
                                results.append({"_key": key, "value": entry})
                            continue

                        # Check if query is in values
                        if isinstance(entry, dict):
                            entry_str = json.dumps(entry).lower()
                            if query_lower in entry_str:
                                entry_copy = json.loads(json.dumps(entry))
                                entry_copy["_key"] = key
                                results.append(entry_copy)
                        elif isinstance(entry, str) and query_lower in entry.lower():
                            results.append({"_key": key, "value": entry})

            duration = time.time() - start_time
            self.perf.record_operation("storage.search", duration)
            return results
        except Exception:

            pass
            logger.error(f"Failed to search entries: {e}")
            duration = time.time() - start_time
            self.perf.record_operation("storage.search.error", duration)
            return []

    async def get_health(self) -> Dict[str, Any]:
        """
        """
                    "status": "healthy",
                    "type": "in-memory",
                    "initialized": self._initialized,
                    "scopes": total_scopes,
                    "keys": total_keys,
                    "memory_usage": memory_usage,
                    "stats": self.stats,
                    "persistence": bool(self.persistence_path),
                    "search_index_enabled": self.enable_search_index,
                }

            duration = time.time() - start_time
            self.perf.record_operation("storage.get_health", duration)
            return health
        except Exception:

            pass
            logger.error(f"Failed to get health information: {e}")
            duration = time.time() - start_time
            self.perf.record_operation("storage.get_health.error", duration)
            return {"status": "unhealthy", "error": str(e), "type": "in-memory"}

    async def save(self, key: str, entry: MemoryEntry) -> bool:
        """
        """
        return await self.store(key, entry, getattr(entry, "scope", "default"))

    async def get(self, key: str) -> Optional[MemoryEntry]:
        """
        """
        """
        """
                        if isinstance(value, dict) and value.get("metadata", {}).get("content_hash") == content_hash:
                            entry = await self.retrieve(key)
                            if entry:
                                return entry
            return None
        except Exception:

            pass
            logger.error(f"Error retrieving by hash: {e}")
            return None

    async def health_check(self) -> Dict[str, Any]:
        """
        """
        """
        """
            self.stats["expirations"] += 1

        return len(expired_keys)

    async def _update_search_index(self, key: str, entry: Any, scope: str) -> None:
        """
        """
        """
        """
        elif hasattr(entry, "__dict__"):
            # For objects, use their string representation
            terms.update(self._get_search_terms(str(entry)))

        return terms

    def _get_search_terms(self, text: str) -> Set[str]:
        """
        """
        words = re.sub(r"[^\w\s]", " ", text.lower()).split()

        # Filter out very short words and common stop words
        stop_words = {
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "is",
            "are",
            "was",
            "were",
            "in",
            "on",
            "at",
            "to",
            "for",
            "with",
            "by",
            "of",
        }

        for word in words:
            if len(word) > 2 and word not in stop_words:
                terms.add(word)

        return terms

    async def _persist_to_storage(self) -> bool:
        """
        """
                        "value": value,
                        "ttl_remaining": ttl_remaining,
                    }

            # Write to temporary file first
            temp_path = f"{self.persistence_path}.tmp"
            with open(temp_path, "w") as f:
                json.dump(data_to_persist, f)

            # Rename to actual file (atomic operation)
            os.replace(temp_path, self.persistence_path)

            return True
        except Exception:

            pass
            logger.error(f"Failed to persist data: {e}")
            return False

    async def _load_from_persistence(self) -> bool:
        """
        """
            with open(self.persistence_path, "r") as f:
                persisted_data = json.load(f)

            # Load data
            current_time = time.time()

            for scope, keys in persisted_data.items():
                # Create scope if it doesn't exist
                if scope not in self.data:
                    self.data[scope] = {}
                    self.ttls[scope] = {}
                    if self.enable_search_index:
                        self.search_index[scope] = {}

                for key, data in keys.items():
                    # Extract value and TTL
                    value = data["value"]
                    ttl_remaining = data.get("ttl_remaining")

                    # Store the value
                    self.data[scope][key] = value

                    # Set TTL if available
                    if ttl_remaining is not None and ttl_remaining > 0:
                        self.ttls[scope][key] = current_time + ttl_remaining

                    # Update search index if enabled
                    if self.enable_search_index:
                        await self._update_search_index(key, value, scope)

            logger.info(f"Loaded data from {self.persistence_path}")
            return True
        except Exception:

            pass
            logger.error(f"Failed to load persisted data: {e}")
            return False
