# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """MCP server for direct Weaviate operations"""
        self.server = Server("weaviate-direct")
        self.client = None
        self.setup_handlers()
        
    def setup_handlers(self):
        """Setup MCP handlers"""
            """List available Weaviate tools"""
                    name="weaviate_search",
                    description="Search for vectors in Weaviate",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "collection": {"type": "string", "description": "Collection name"},
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "description": "Number of results", "default": 10},
                            "where_filter": {"type": "object", "description": "Optional where filter"}
                        },
                        "required": ["collection", "query"]
                    }
                ),
                Tool(
                    name="weaviate_insert",
                    description="Insert data into Weaviate",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "collection": {"type": "string", "description": "Collection name"},
                            "data": {"type": "object", "description": "Data to insert"},
                            "vector": {"type": "array", "description": "Optional vector"}
                        },
                        "required": ["collection", "data"]
                    }
                ),
                Tool(
                    name="weaviate_create_collection",
                    description="Create a new Weaviate collection",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Collection name"},
                            "properties": {
                                "type": "array",
                                "description": "Collection properties",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "dataType": {"type": "array", "items": {"type": "string"}}
                                    }
                                }
                            },
                            "vectorizer": {"type": "string", "default": "text2vec-openai"}
                        },
                        "required": ["name", "properties"]
                    }
                ),
                Tool(
                    name="weaviate_delete",
                    description="Delete objects from Weaviate",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "collection": {"type": "string", "description": "Collection name"},
                            "id": {"type": "string", "description": "Object ID to delete"}
                        },
                        "required": ["collection", "id"]
                    }
                ),
                Tool(
                    name="weaviate_get_schema",
                    description="Get Weaviate schema",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> Any:
            """Execute Weaviate tool"""
            logger.info(f"Executing tool: {name} with args: {arguments}")
            
            if not self.client:
                await self._connect_to_weaviate()
            
            try:

            
                pass
                if name == "weaviate_search":
                    return await self._search(
                        arguments["collection"],
                        arguments["query"],
                        arguments.get("limit", 10),
                        arguments.get("where_filter")
                    )
                
                elif name == "weaviate_insert":
                    return await self._insert(
                        arguments["collection"],
                        arguments["data"],
                        arguments.get("vector")
                    )
                
                elif name == "weaviate_create_collection":
                    return await self._create_collection(
                        arguments["name"],
                        arguments["properties"],
                        arguments.get("vectorizer", "text2vec-openai")
                    )
                
                elif name == "weaviate_delete":
                    return await self._delete(
                        arguments["collection"],
                        arguments["id"]
                    )
                
                elif name == "weaviate_get_schema":
                    return await self._get_schema()
                
                else:
                    return {"error": f"Unknown tool: {name}"}
                    
            except Exception:

                    
                pass
                logger.error(f"Tool execution failed: {e}")
                return {"error": str(e)}
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available Weaviate resources"""
                    uri="weaviate://schema",
                    name="Weaviate Schema",
                    description="Current Weaviate schema configuration",
                    mimeType="application/json"
                ),
                Resource(
                    uri="weaviate://stats",
                    name="Weaviate Statistics",
                    description="Weaviate database statistics",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read Weaviate resource"""
            if uri == "weaviate://schema":
                schema = await self._get_schema()
                return json.dumps(schema, indent=2)
            
            elif uri == "weaviate://stats":
                stats = await self._get_stats()
                return json.dumps(stats, indent=2)
            
            else:
                return json.dumps({"error": f"Unknown resource: {uri}"})
    
    async def _connect_to_weaviate(self):
        """Connect to Weaviate instance"""
            weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
            weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
            
            auth_config = None
            if weaviate_api_key:
                auth_config = weaviate.auth.AuthApiKey(api_key=weaviate_api_key)
            
            self.client = weaviate.WeaviateClient(
                connection_params=weaviate.connect.ConnectionParams(
                    http=weaviate.connect.ProtocolParams(
                        host=weaviate_url.replace("http://", "").replace("https://", "").split(":")[0],
                        port=int(weaviate_url.split(":")[-1]) if ":" in weaviate_url else 80,
                        secure=weaviate_url.startswith("https")
                    )
                ),
                auth_client_secret=auth_config
            )
            
            self.client.connect()
            logger.info(f"Connected to Weaviate at {weaviate_url}")
            
        except Exception:

            
            pass
            logger.error(f"Failed to connect to Weaviate: {e}")
            raise
    
    async def _search(self, collection: str, query: str, limit: int, where_filter: Optional[Dict] = None) -> Dict:
        """Search in Weaviate collection"""
                "success": True,
                "results": [
                    {
                        "id": str(obj.uuid),
                        "properties": obj.properties,
                        "score": getattr(obj, 'score', None)
                    }
                    for obj in results.objects
                ],
                "count": len(results.objects)
            }
            
        except Exception:

            
            pass
            logger.error(f"Search failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _insert(self, collection: str, data: Dict, vector: Optional[List[float]] = None) -> Dict:
        """Insert data into Weaviate"""
            if "timestamp" not in data:
                data["timestamp"] = datetime.now().isoformat()
            
            # Insert with or without vector
            if vector:
                result = collection_obj.data.insert(
                    properties=data,
                    vector=vector
                )
            else:
                result = collection_obj.data.insert(properties=data)
            
            return {
                "success": True,
                "id": str(result),
                "message": "Data inserted successfully"
            }
            
        except Exception:

            
            pass
            logger.error(f"Insert failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_collection(self, name: str, properties: List[Dict], vectorizer: str) -> Dict:
        """Create a new collection"""
                    "success": False,
                    "error": f"Collection '{name}' already exists"
                }
            
            # Create collection
            self.client.collections.create(
                name=name,
                vectorizer_config=weaviate.classes.config.Configure.Vectorizer.text2vec_openai()
                if vectorizer == "text2vec-openai" else None,
                properties=[
                    weaviate.classes.config.Property(
                        name=prop["name"],
                        data_type=weaviate.classes.config.DataType(prop["dataType"][0])
                    )
                    for prop in properties
                ]
            )
            
            return {
                "success": True,
                "message": f"Collection '{name}' created successfully"
            }
            
        except Exception:

            
            pass
            logger.error(f"Create collection failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _delete(self, collection: str, object_id: str) -> Dict:
        """Delete object from Weaviate"""
                "success": True,
                "message": f"Object {object_id} deleted from {collection}"
            }
            
        except Exception:

            
            pass
            logger.error(f"Delete failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_schema(self) -> Dict:
        """Get Weaviate schema"""
                "collections": [
                    {
                        "name": col.name,
                        "properties": [
                            {
                                "name": prop.name,
                                "dataType": str(prop.data_type)
                            }
                            for prop in col.config.properties
                        ] if hasattr(col.config, 'properties') else []
                    }
                    for col in collections
                ]
            }
            
            return schema
            
        except Exception:

            
            pass
            logger.error(f"Get schema failed: {e}")
            return {"error": str(e)}
    
    async def _get_stats(self) -> Dict:
        """Get Weaviate statistics"""
                "total_collections": len(collections),
                "collections": []
            }
            
            for col in collections:
                try:

                    pass
                    col_obj = self.client.collections.get(col.name)
                    count = col_obj.aggregate.over_all().with_meta_count().do()
                    
                    stats["collections"].append({
                        "name": col.name,
                        "object_count": count.total_count if hasattr(count, 'total_count') else 0
                    })
                except Exception:

                    pass
                    stats["collections"].append({
                        "name": col.name,
                        "object_count": "unknown"
                    })
            
            return stats
            
        except Exception:

            
            pass
            logger.error(f"Get stats failed: {e}")
            return {"error": str(e)}
    
    async def run(self, initialization_options=None):
        """Run the MCP server"""
            port = int(os.getenv("MCP_WEAVIATE_DIRECT_PORT", "8001"))
            logger.info(f"Starting Weaviate Direct MCP server on port {port}")
            
            await self.server.run(
                host="0.0.0.0",
                port=port,
                initialization_options=initialization_options
            )
            
        except Exception:

            
            pass
            logger.error(f"Server failed to start: {e}")
            raise
        finally:
            if self.client:
                self.client.close()


async def main():
    """Main entry point"""
if __name__ == "__main__":
    asyncio.run(main())