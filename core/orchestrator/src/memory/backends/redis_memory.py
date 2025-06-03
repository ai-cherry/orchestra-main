"""
"""
    """Redis-based memory implementation for short-term storage."""
        prefix: str = "orchestra:",
    ):
        """Initialize Redis memory."""
        logger.info(f"RedisMemory initialized with host={host}, port={port}")

    async def store(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store an item in Redis."""
            full_key = f"{self.prefix}{key}"
            self.client.set(full_key, json.dumps(value), ex=ttl or self.ttl)
            return True
        except Exception:

            pass
            logger.error(f"Error storing item in Redis: {e}")
            return False

    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve an item from Redis."""
            full_key = f"{self.prefix}{key}"
            value = self.client.get(full_key)
            if value:
                return json.loads(value)
            return None
        except Exception:

            pass
            logger.error(f"Error retrieving item from Redis: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """Delete an item from Redis."""
            full_key = f"{self.prefix}{key}"
            result = self.client.delete(full_key)
            if result:
                return True
            return False
        except Exception:

            pass
            logger.error(f"Error deleting item from Redis: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if an item exists in Redis."""
            full_key = f"{self.prefix}{key}"
            return bool(self.client.exists(full_key))
        except Exception:

            pass
            logger.error(f"Error checking if item exists in Redis: {e}")
            return False

    async def set_ttl(self, key: str, ttl: int) -> bool:
        """Set TTL for an item in Redis."""
            full_key = f"{self.prefix}{key}"
            if self.client.exists(full_key):
                self.client.expire(full_key, ttl)
                return True
            return False
        except Exception:

            pass
            logger.error(f"Error setting TTL for item in Redis: {e}")
            return False

    async def get_ttl(self, key: str) -> Optional[int]:
        """Get TTL for an item in Redis."""
            full_key = f"{self.prefix}{key}"
            ttl = self.client.ttl(full_key)
            if ttl >= 0:
                return ttl
            return None
        except Exception:

            pass
            logger.error(f"Error getting TTL for item in Redis: {e}")
            return None

    async def search(self, field: str, value: Any, operator: str = "==", limit: int = 10) -> List[Dict[str, Any]]:
        """
        """
            pattern = "*"  # Default to all keys

            # If the field is "key", we can use it for pattern matching
            if field == "key" and operator == "==":
                pattern = f"{value}"

            # Get all keys matching the pattern
            full_pattern = f"{self.prefix}{pattern}"
            keys = self.client.keys(full_pattern)

            # Limit the number of keys to process
            keys = keys[: limit * 2]  # Get more keys than needed to account for filtering

            # Process results
            results = []
            for key in keys:
                # Remove prefix from key
                key_without_prefix = key[len(self.prefix) :]

                # Get the value
                value_str = self.client.get(key)
                if not value_str:
                    continue

                try:


                    pass
                    data = json.loads(value_str)

                    # Add the key to the data
                    data["id"] = key_without_prefix

                    # Filter based on field and value if not searching by key
                    if field != "key":
                        if field not in data:
                            continue

                        # Apply operator
                        if operator == "==" and data[field] != value:
                            continue
                        elif operator == "!=" and data[field] == value:
                            continue
                        elif operator == ">" and not (data[field] > value):
                            continue
                        elif operator == ">=" and not (data[field] >= value):
                            continue
                        elif operator == "<" and not (data[field] < value):
                            continue
                        elif operator == "<=" and not (data[field] <= value):
                            continue

                    results.append(data)

                    # Check if we have enough results
                    if len(results) >= limit:
                        break

                except Exception:


                    pass
                    continue

            return results
        except Exception:

            pass
            logger.error(f"Error searching in Redis: {e}")
            return []

    async def store_hash(self, key: str, value: Dict[str, Any]) -> bool:
        """Store a hash in Redis."""
            full_key = f"{self.prefix}{key}"
            # Convert all values to strings
            string_dict = {k: json.dumps(v) for k, v in value.items()}
            self.client.hset(full_key, mapping=string_dict)
            self.client.expire(full_key, self.ttl)
            return True
        except Exception:

            pass
            logger.error(f"Error storing hash in Redis: {e}")
            return False

    async def retrieve_hash(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a hash from Redis."""
            full_key = f"{self.prefix}{key}"
            value = self.client.hgetall(full_key)
            if value:
                # Convert all values from strings back to objects
                result = {k: json.loads(v) for k, v in value.items()}
                return result
            return None
        except Exception:

            pass
            logger.error(f"Error retrieving hash from Redis: {e}")
            return None

    async def clear_all(self) -> bool:
        """Clear all items with the prefix from Redis."""
            keys = self.client.keys(f"{self.prefix}*")
            if keys:
                self.client.delete(*keys)
            return True
        except Exception:

            pass
            logger.error(f"Error clearing items from Redis: {e}")
            return False
