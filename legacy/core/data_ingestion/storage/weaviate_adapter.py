# TODO: Consider adding connection pooling configuration
"""
"""
    """
    """
        """
        """
        self._class_name = config.get("class_name", "DataContent")
        self._vectorizer = config.get("vectorizer", "text2vec-openai")
        
    async def connect(self) -> bool:
        """Establish connection to Weaviate."""
            if self.config.get("api_key"):
                auth_config = weaviate.AuthApiKey(api_key=self.config["api_key"])
            
            self._client = weaviate.Client(
                url=self.config["url"],
                auth_client_secret=auth_config,
                timeout_config=(
                    self.config.get("timeout", 30),
                    self.config.get("timeout", 30)
                )
            )
            
            # Test connection
            if not self._client.is_ready():
                raise Exception("Weaviate is not ready")
            
            # Ensure schema exists
            await self._ensure_schema()
            
            self._connected = True
            logger.info("Weaviate connection established")
            return True
            
        except Exception:

            
            pass
            logger.error(f"Failed to connect to Weaviate: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> bool:
        """Close connection to Weaviate."""
            logger.info("Weaviate connection closed")
            return True
            
        except Exception:

            
            pass
            logger.error(f"Error disconnecting from Weaviate: {e}")
            return False
    
    async def store(
        self, 
        data: Any, 
        key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StorageResult:
        """
        """
                error="Not connected to Weaviate"
            )
        
        try:

        
            pass
            # Generate UUID if not provided
            if not key:
                key = str(uuid.uuid4())
            
            # Prepare data object
            data_object = self._prepare_data_object(data, metadata)
            
            # Add vector if provided
            vector = metadata.get("vector") if metadata else None
            
            # Store in Weaviate
            if vector is not None:
                # Store with pre-computed vector
                result = self._client.data_object.create(
                    data_object=data_object,
                    class_name=self._class_name,
                    uuid=key,
                    vector=vector
                )
            else:
                # Let Weaviate compute the vector
                result = self._client.data_object.create(
                    data_object=data_object,
                    class_name=self._class_name,
                    uuid=key
                )
            
            return StorageResult(
                success=True,
                key=result,
                metadata={"vectorized": vector is None}
            )
            
        except Exception:

            
            pass
            logger.error(f"Weaviate error storing data: {e}")
            return StorageResult(
                success=False,
                error=str(e)
            )
        except Exception:

            pass
            logger.error(f"Error storing data in Weaviate: {e}")
            return StorageResult(
                success=False,
                error=str(e)
            )
    
    async def retrieve(
        self, 
        key: str,
        include_metadata: bool = False
    ) -> Optional[Any]:
        """Retrieve object from Weaviate by UUID."""
                return result.get("properties", {})
                
        except Exception:

                
            pass
            logger.error(f"Error retrieving from Weaviate: {e}")
            return None
    
    async def delete(self, key: str) -> StorageResult:
        """Delete object from Weaviate."""
                error="Not connected to Weaviate"
            )
        
        try:

        
            pass
            # Delete by UUID
            self._client.data_object.delete(
                uuid=key,
                class_name=self._class_name
            )
            
            return StorageResult(
                success=True,
                key=key
            )
            
        except Exception:

            
            pass
            logger.error(f"Error deleting from Weaviate: {e}")
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
        """List object UUIDs from Weaviate."""
                ["_additional { id }"]
            )
            
            # Add filter if prefix provided (assuming prefix is source_type)
            if prefix:
                query = query.with_where({
                    "path": ["sourceType"],
                    "operator": "Equal",
                    "valueString": prefix
                })
            
            # Add pagination
            query = query.with_limit(limit).with_offset(offset)
            
            # Execute query
            result = query.do()
            
            # Extract UUIDs
            objects = result.get("data", {}).get("Get", {}).get(self._class_name, [])
            return [obj["_additional"]["id"] for obj in objects]
            
        except Exception:

            
            pass
            logger.error(f"Error listing from Weaviate: {e}")
            return []
    
    async def exists(self, key: str) -> bool:
        """Check if object exists in Weaviate."""
        """Ensure the required schema exists in Weaviate."""
                c["class"] == self._class_name 
                for c in schema.get("classes", [])
            )
            
            if not class_exists:
                # Create class schema
                class_schema = {
                    "class": self._class_name,
                    "description": "Unified content from all data sources",
                    "vectorizer": self._vectorizer,
                    "properties": [
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "The actual content text"
                        },
                        {
                            "name": "sourceType",
                            "dataType": ["string"],
                            "description": "Source system (slack, gong, salesforce, etc.)"
                        },
                        {
                            "name": "contentType",
                            "dataType": ["string"],
                            "description": "Type of content (message, transcript, record)"
                        },
                        {
                            "name": "timestamp",
                            "dataType": ["date"],
                            "description": "Original timestamp from source"
                        },
                        {
                            "name": "metadata",
                            "dataType": ["object"],
                            "description": "Additional metadata from source",
                            "nestedProperties": [
                                {
                                    "name": "user",
                                    "dataType": ["string"]
                                },
                                {
                                    "name": "channel",
                                    "dataType": ["string"]
                                },
                                {
                                    "name": "filename",
                                    "dataType": ["string"]
                                }
                            ]
                        },
                        {
                            "name": "fileImportId",
                            "dataType": ["string"],
                            "description": "Reference to PostgreSQL file_imports"
                        },
                        {
                            "name": "sourceId",
                            "dataType": ["string"],
                            "description": "Original ID from source system"
                        }
                    ]
                }
                
                self._client.schema.create_class(class_schema)
                logger.info(f"Created Weaviate class: {self._class_name}")
                
        except Exception:

                
            pass
            logger.error(f"Error ensuring Weaviate schema: {e}")
            raise
    
    def _prepare_data_object(
        self, 
        data: Any, 
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare data object for Weaviate storage."""
            obj = {"content": data}
        else:
            obj = {"content": str(data)}
        
        # Add metadata fields
        if metadata:
            # Map metadata to schema properties
            if "source_type" in metadata:
                obj["sourceType"] = metadata["source_type"]
            if "content_type" in metadata:
                obj["contentType"] = metadata["content_type"]
            if "timestamp" in metadata:
                # Convert to RFC3339 format for Weaviate
                if isinstance(metadata["timestamp"], datetime):
                    obj["timestamp"] = metadata["timestamp"].isoformat() + "Z"
                else:
                    obj["timestamp"] = metadata["timestamp"]
            if "file_import_id" in metadata:
                obj["fileImportId"] = metadata["file_import_id"]
            if "source_id" in metadata:
                obj["sourceId"] = metadata["source_id"]
            
            # Nested metadata
            nested_metadata = {}
            for key in ["user", "channel", "filename"]:
                if key in metadata:
                    nested_metadata[key] = metadata[key]
            
            if nested_metadata:
                obj["metadata"] = nested_metadata
        
        return obj
    
    async def search_similar(
        self,
        query: Union[str, List[float]],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        return_distance: bool = True
    ) -> List[Dict[str, Any]]:
        """
        """
                "content",
                "sourceType",
                "contentType",
                "timestamp",
                "fileImportId",
                "sourceId",
                "metadata { user channel filename }"
            ]
            
            if return_distance:
                properties.append("_additional { id distance }")
            else:
                properties.append("_additional { id }")
            
            query_builder = self._client.query.get(
                self._class_name,
                properties
            )
            
            # Add vector search
            if isinstance(query, str):
                # Text search
                query_builder = query_builder.with_near_text({
                    "concepts": [query]
                })
            else:
                # Vector search
                query_builder = query_builder.with_near_vector({
                    "vector": query
                })
            
            # Add filters if provided
            if filters:
                where_filter = self._build_where_filter(filters)
                query_builder = query_builder.with_where(where_filter)
            
            # Add limit
            query_builder = query_builder.with_limit(limit)
            
            # Execute query
            result = query_builder.do()
            
            # Extract and format results
            objects = result.get("data", {}).get("Get", {}).get(self._class_name, [])
            
            formatted_results = []
            for obj in objects:
                formatted_obj = {
                    "id": obj["_additional"]["id"],
                    **obj
                }
                
                if return_distance:
                    formatted_obj["distance"] = obj["_additional"].get("distance", 0)
                
                # Remove _additional from main object
                formatted_obj.pop("_additional", None)
                
                formatted_results.append(formatted_obj)
            
            return formatted_results
            
        except Exception:

            
            pass
            logger.error(f"Error searching in Weaviate: {e}")
            return []
    
    def _build_where_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build Weaviate where filter from filters dict."""
        if "source_type" in filters:
            return {
                "path": ["sourceType"],
                "operator": "Equal",
                "valueString": filters["source_type"]
            }
        
        return {}