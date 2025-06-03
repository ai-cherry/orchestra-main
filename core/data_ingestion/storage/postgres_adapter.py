"""
"""
    """
    """
        """
        """
        self._schema = config.get("schema", "data_ingestion")
        
    async def connect(self) -> bool:
        """Establish connection pool to PostgreSQL."""
                host=self.config["host"],
                port=self.config.get("port", 5432),
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"],
                min_size=self.config.get("pool_size", 10),
                max_size=self.config.get("pool_max_size", 20),
                command_timeout=60,
                server_settings={
                    'search_path': f'{self._schema},public'
                }
            )
            
            # Test connection
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            self._connected = True
            logger.info("PostgreSQL connection established")
            return True
            
        except Exception:

            
            pass
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> bool:
        """Close connection pool."""
            logger.info("PostgreSQL connection closed")
            return True
            
        except Exception:

            
            pass
            logger.error(f"Error disconnecting from PostgreSQL: {e}")
            return False
    
    async def store(
        self, 
        data: Any, 
        key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StorageResult:
        """
        """
                error="Not connected to PostgreSQL"
            )
        
        try:

        
            pass
            # Generate key if not provided
            if not key:
                key = str(uuid.uuid4())
            
            # Determine table and operation based on metadata
            table = metadata.get("table", "parsed_content")
            operation = metadata.get("operation", "insert")
            
            async with self._pool.acquire() as conn:
                async with conn.transaction():
                    if operation == "insert":
                        result = await self._insert_data(
                            conn, table, key, data, metadata
                        )
                    elif operation == "update":
                        result = await self._update_data(
                            conn, table, key, data, metadata
                        )
                    else:
                        return StorageResult(
                            success=False,
                            error=f"Unsupported operation: {operation}"
                        )
            
            return result
            
        except Exception:

            
            pass
            logger.error(f"Error storing data in PostgreSQL: {e}")
            return StorageResult(
                success=False,
                error=str(e)
            )
    
    async def retrieve(
        self, 
        key: str,
        include_metadata: bool = False
    ) -> Optional[Any]:
        """Retrieve data from PostgreSQL by key."""
                query = f"""
                """
                            "id": str(row["id"]),
                            "content": row["content"],
                            "metadata": row["metadata"],
                            "created_at": row["created_at"]
                        }
                    else:
                        return row["content"]
                
                # Try file_imports table
                query = f"""
                """
                            "filename": row["filename"],
                            "source_type": row["source_type"]
                        }
                
                return None
                
        except Exception:

                
            pass
            logger.error(f"Error retrieving data from PostgreSQL: {e}")
            return None
    
    async def delete(self, key: str) -> StorageResult:
        """Delete data from PostgreSQL."""
                error="Not connected to PostgreSQL"
            )
        
        try:

        
            pass
            async with self._pool.acquire() as conn:
                async with conn.transaction():
                    # Delete from parsed_content (cascade will handle related)
                    query = f"""
                    """
                    if result == "DELETE 0":
                        # Try file_imports
                        query = f"""
                        """
                    deleted = result != "DELETE 0"
            
            return StorageResult(
                success=deleted,
                key=key,
                error=None if deleted else "Key not found"
            )
            
        except Exception:

            
            pass
            logger.error(f"Error deleting from PostgreSQL: {e}")
            return StorageResult(
                success=False,
                key=key,
                error=str(e)
            )
    
    async def list(
        self, 
        prefix: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[str]:
        """List keys from PostgreSQL tables."""
                query = f"""
                """
                    query += " WHERE content_type = $1"
                    params.append(prefix)
                
                query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
                params.extend([limit, offset])
                
                rows = await conn.fetch(query, *params)
                
                return [row["id"] for row in rows]
                
        except Exception:

                
            pass
            logger.error(f"Error listing keys from PostgreSQL: {e}")
            return []
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in PostgreSQL."""
                query = f"""
                """
        """Insert data into specified table."""
            if table == "parsed_content":
                query = f"""
                """
                    uuid.UUID(metadata["file_import_id"]) if metadata.get("file_import_id") else None,
                    metadata.get("content_type", "unknown"),
                    metadata.get("source_id"),
                    str(data),
                    json.dumps(metadata.get("metadata", {})),
                    metadata.get("vector_id"),
                    metadata.get("tokens_count")
                )
                
                return StorageResult(
                    success=result is not None,
                    key=str(result) if result else key,
                    metadata={"inserted": result is not None}
                )
                
            elif table == "file_imports":
                query = f"""
                """
                    data.get("filename"),
                    data.get("source_type"),
                    data.get("file_size"),
                    data.get("mime_type"),
                    data.get("s3_key"),
                    json.dumps(metadata or {}),
                    uuid.UUID(data.get("created_by")) if data.get("created_by") else None
                )
                
                return StorageResult(
                    success=True,
                    key=str(result)
                )
            
            else:
                return StorageResult(
                    success=False,
                    error=f"Unsupported table: {table}"
                )
                
        except Exception:

                
            pass
            return StorageResult(
                success=False,
                error=str(e)
            )
    
    async def _update_data(
        self,
        conn: asyncpg.Connection,
        table: str,
        key: str,
        data: Any,
        metadata: Dict[str, Any]
    ) -> StorageResult:
        """Update data in specified table."""
            if table == "file_imports":
                updates = []
                params = [uuid.UUID(key)]
                param_count = 1
                
                if "processing_status" in data:
                    param_count += 1
                    updates.append(f"processing_status = ${param_count}")
                    params.append(data["processing_status"])
                
                if "error_message" in data:
                    param_count += 1
                    updates.append(f"error_message = ${param_count}")
                    params.append(data["error_message"])
                
                if "processing_started_at" in data:
                    param_count += 1
                    updates.append(f"processing_started_at = ${param_count}")
                    params.append(data["processing_started_at"])
                
                if "processing_completed_at" in data:
                    param_count += 1
                    updates.append(f"processing_completed_at = ${param_count}")
                    params.append(data["processing_completed_at"])
                
                if "metadata" in data:
                    param_count += 1
                    updates.append(f"metadata = ${param_count}")
                    params.append(json.dumps(data["metadata"]))
                
                if not updates:
                    return StorageResult(
                        success=False,
                        error="No fields to update"
                    )
                
                query = f"""
                """
                    success=result != "UPDATE 0",
                    key=key
                )
            
            else:
                return StorageResult(
                    success=False,
                    error=f"Update not supported for table: {table}"
                )
                
        except Exception:

                
            pass
            return StorageResult(
                success=False,
                error=str(e)
            )
    
    async def execute_query(
        self,
        query: str,
        params: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a custom query and return results."""
            logger.error(f"Error executing query: {e}")
            return []