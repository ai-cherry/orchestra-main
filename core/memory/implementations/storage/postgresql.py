"""
"""
    """
    """
        table_name: str = "memory_items",
        compression_enabled: bool = True,
        compression_threshold: int = 1024
    ):
        self.tier = tier
        self.config = config
        self.table_name = table_name
        self.compression_enabled = compression_enabled
        self.compression_threshold = compression_threshold
        
        self._pool: Optional[Pool] = None
        self._prepared_statements: Dict[str, str] = {}
        
        logger.info(
            f"Initialized PostgreSQLStorage for tier {tier.value} "
            f"with table {table_name}"
        )
    
    async def initialize(self) -> None:
        """Initialize PostgreSQL connection pool and schema."""
            logger.info(f"PostgreSQL storage initialized for tier {self.tier.value}")
            
        except Exception:

            
            pass
            raise MemoryConnectionError(
                backend="postgresql",
                host=self.config.host,
                port=self.config.port,
                reason=str(e),
                cause=e
            )
    
    async def _create_schema(self) -> None:
        """Create the memory items table if it doesn't exist."""
            await conn.execute(f"""
            """
        """Prepare common SQL statements for performance."""
            self._prepared_statements['get'] = await conn.prepare(f"""
            """
            self._prepared_statements['update_access'] = await conn.prepare(f"""
            """
            self._prepared_statements['set'] = await conn.prepare(f"""
            """
            self._prepared_statements['delete'] = await conn.prepare(f"""
            """
            self._prepared_statements['exists'] = await conn.prepare(f"""
            """
        """Create optimized indexes based on access patterns."""
            await conn.execute(f"""
            """
            await conn.execute(f"""
            """
            await conn.execute(f"ANALYZE {self.table_name}")
    
    async def get(self, key: str) -> Optional[MemoryItem]:
        """Retrieve an item from PostgreSQL."""
                    row = await conn.fetchrow(f"""
                    """
                    await conn.execute(f"""
                    """
                operation="get",
                timeout_seconds=self.config.command_timeout,
                key=key
            )
        except Exception:

            pass
            logger.error(f"Failed to get item {key}: {str(e)}")
            raise MemoryStorageError(
                operation="get",
                storage_backend="postgresql",
                reason=str(e),
                key=key,
                cause=e
            )
    
    async def set(self, item: MemoryItem) -> bool:
        """Store an item in PostgreSQL."""
                    await conn.execute(f"""
                    """
                operation="set",
                timeout_seconds=self.config.command_timeout,
                key=item.key
            )
        except Exception:

            pass
            logger.error(f"Failed to set item {item.key}: {str(e)}")
            raise MemoryStorageError(
                operation="set",
                storage_backend="postgresql",
                reason=str(e),
                key=item.key,
                cause=e
            )
    
    async def delete(self, key: str) -> bool:
        """Delete an item from PostgreSQL."""
                    result = await conn.execute(f"""
                    """
            logger.error(f"Failed to delete item {key}: {str(e)}")
            raise MemoryStorageError(
                operation="delete",
                storage_backend="postgresql",
                reason=str(e),
                key=key,
                cause=e
            )
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in PostgreSQL."""
                    row = await conn.fetchrow(f"""
                    """
            logger.error(f"Failed to check existence of {key}: {str(e)}")
            return False
    
    async def get_batch(self, keys: List[str]) -> Dict[str, Optional[MemoryItem]]:
        """Get multiple items in a single query."""
                rows = await conn.fetch(f"""
                """
                await conn.execute(f"""
                """
            logger.error(f"Failed to get batch: {str(e)}")
            raise MemoryStorageError(
                operation="get_batch",
                storage_backend="postgresql",
                reason=str(e),
                cause=e
            )
    
    async def set_batch(self, items: List[MemoryItem]) -> Dict[str, bool]:
        """Set multiple items in a single transaction."""
                    await conn.executemany(f"""
                    """
            logger.error(f"Failed to set batch: {str(e)}")
            # Return partial results
            return results
    
    async def search(
        self,
        pattern: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[MemoryItem]:
        """Search for items using pattern matching and metadata filters."""
                query = f"""
                """
                    query += f" AND key LIKE ${param_count}"
                    params.append(pattern.replace('*', '%'))
                
                # Add metadata filters
                if metadata_filter:
                    for key, value in metadata_filter.items():
                        param_count += 1
                        query += f" AND metadata->>${param_count - 1} = ${param_count}"
                        params.extend([key, json.dumps(value)])
                
                # Add order and limit
                query += f" ORDER BY accessed_at DESC LIMIT ${param_count + 1}"
                params.append(limit)
                
                # Execute query
                rows = await conn.fetch(query, *params)
                
                # Build results
                results = []
                for row in rows:
                    value = self._deserialize_value(row['value'], row['compressed'])
                    results.append(MemoryItem(
                        key=row['key'],
                        value=value,
                        metadata=dict(row['metadata']),
                        tier=MemoryTier(row['tier']),
                        created_at=row['created_at'],
                        accessed_at=row['accessed_at'],
                        access_count=row['access_count'],
                        size_bytes=row['size_bytes'],
                        ttl_seconds=row['ttl_seconds'],
                        checksum=row['checksum']
                    ))
                
                return results
                
        except Exception:

                
            pass
            logger.error(f"Failed to search: {str(e)}")
            raise MemoryStorageError(
                operation="search",
                storage_backend="postgresql",
                reason=str(e),
                cause=e
            )
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
                stats = await conn.fetchrow(f"""
                """
                tier_dist = await conn.fetch(f"""
                """
                    "tier": self.tier.value,
                    "total_items": stats['total_items'] or 0,
                    "total_size_bytes": stats['total_size'] or 0,
                    "avg_access_count": float(stats['avg_access_count'] or 0),
                    "last_access": stats['last_access'],
                    "tier_distribution": {
                        row['tier']: row['count'] for row in tier_dist
                    },
                    "pool_size": self._pool.get_size() if self._pool else 0,
                    "pool_free": self._pool.get_idle_size() if self._pool else 0,
                }
                
        except Exception:

                
            pass
            logger.error(f"Failed to get stats: {str(e)}")
            return {}
    
    async def cleanup_expired(self) -> int:
        """Remove expired items."""
                result = await conn.execute(f"""
                """
                    await conn.execute(f"VACUUM ANALYZE {self.table_name}")
                    logger.info(f"Cleaned up {count} expired items from {self.tier.value}")
                
                return count
                
        except Exception:

                
            pass
            logger.error(f"Failed to cleanup expired items: {str(e)}")
            return 0
    
    async def close(self) -> None:
        """Close PostgreSQL connections."""
            logger.info(f"PostgreSQL storage closed for tier {self.tier.value}")
    
    # Private helper methods
    
    def _serialize_value(self, value: Any) -> Tuple[bytes, bool]:
        """Serialize and optionally compress value."""
                operation="serialize",
                key="",
                value_type=type(value).__name__,
                reason=str(e),
                cause=e
            )
    
    def _deserialize_value(self, data: bytes, compressed: bool) -> Any:
        """Deserialize and optionally decompress value."""
                operation="deserialize",
                key="",
                value_type="unknown",
                reason=str(e),
                cause=e
            )