# TODO: Consider adding connection pooling configuration
"""
"""
    """
    """
        """
        """
        super().__init__(mcp_server, droid_config, "knowledge")
        self.supported_methods = [
            "store_knowledge",
            "search_knowledge",
            "generate_documentation",
            "update_embeddings",
            "analyze_knowledge_graph",
            "extract_insights",
        ]
        self.vector_dimension = droid_config.get("vector_dimension", 1536)
        self.embedding_model = droid_config.get("embedding_model", "text-embedding-ada-002")
        self.weaviate_config = droid_config.get("weaviate", {})
        self.cache_embeddings = droid_config.get("cache_embeddings", True)
        self.embedding_cache: Dict[str, List[float]] = {}

    async def translate_to_factory(self, mcp_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        """
        method = mcp_request.get("method", "")
        params = mcp_request.get("params", {})

        # Map MCP methods to Factory AI Knowledge capabilities
        factory_request = {
            "droid": "knowledge",
            "action": self._map_method_to_action(method),
            "context": {
                "content": params.get("content", ""),
                "metadata": params.get("metadata", {}),
                "schema": params.get("schema", {}),
                "existing_knowledge": params.get("existing_knowledge", {}),
                "query": params.get("query", ""),
            },
            "options": {
                "embedding_model": params.get("embedding_model", self.embedding_model),
                "vector_dimension": params.get("vector_dimension", self.vector_dimension),
                "similarity_threshold": params.get("similarity_threshold", 0.7),
                "max_results": params.get("max_results", 10),
                "include_metadata": params.get("include_metadata", True),
                "generate_summary": params.get("generate_summary", True),
            },
        }

        # Handle specific knowledge operations
        if method == "store_knowledge":
            factory_request["context"]["collection"] = params.get("collection", "default")
            factory_request["context"]["document_type"] = params.get("document_type", "general")
            factory_request["options"]["auto_chunk"] = params.get("auto_chunk", True)
            factory_request["options"]["chunk_size"] = params.get("chunk_size", 512)

        elif method == "search_knowledge":
            factory_request["context"]["search_type"] = params.get("search_type", "semantic")
            factory_request["context"]["filters"] = params.get("filters", {})
            factory_request["options"]["rerank"] = params.get("rerank", True)
            factory_request["options"]["explain_scores"] = params.get("explain_scores", False)

        elif method == "generate_documentation":
            factory_request["context"]["doc_type"] = params.get("doc_type", "technical")
            factory_request["context"]["target_audience"] = params.get("target_audience", "developers")
            factory_request["context"]["sections"] = params.get("sections", [])
            factory_request["options"]["format"] = params.get("format", "markdown")

        elif method == "analyze_knowledge_graph":
            factory_request["context"]["graph_type"] = params.get("graph_type", "concept")
            factory_request["context"]["depth"] = params.get("depth", 3)
            factory_request["options"]["visualization"] = params.get("visualization", True)

        return factory_request

    async def translate_to_mcp(self, factory_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        """
        if "error" in factory_response:
            return {
                "error": {
                    "code": -32603,
                    "message": factory_response["error"].get("message", "Unknown error"),
                    "data": factory_response["error"].get("details", {}),
                }
            }

        result = factory_response.get("result", {})
        mcp_response = {
            "result": {
                "status": result.get("status", "success"),
                "data": result.get("data", {}),
                "embeddings": result.get("embeddings", []),
                "search_results": self._format_search_results(result.get("search_results", [])),
                "documentation": result.get("documentation", ""),
                "insights": result.get("insights", []),
                "metadata": {
                    "processing_time": result.get("processing_time", 0),
                    "tokens_processed": result.get("tokens_processed", 0),
                    "knowledge_version": result.get("version", "1.0.0"),
                },
            }
        }

        # Include Weaviate-specific results if present
        if "weaviate_response" in result:
            mcp_response["result"]["weaviate"] = {
                "objects_created": result["weaviate_response"].get("objects_created", 0),
                "objects_updated": result["weaviate_response"].get("objects_updated", 0),
                "schema_changes": result["weaviate_response"].get("schema_changes", []),
            }

        # Include knowledge graph analysis if present
        if "knowledge_graph" in result:
            mcp_response["result"]["knowledge_graph"] = {
                "nodes": result["knowledge_graph"].get("nodes", []),
                "edges": result["knowledge_graph"].get("edges", []),
                "clusters": result["knowledge_graph"].get("clusters", []),
                "visualization": result["knowledge_graph"].get("visualization", ""),
            }

        return mcp_response

    async def _call_factory_droid(self, factory_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        """
                    api_key=self.droid_config.get("api_key"),
                    base_url=self.droid_config.get("base_url", "https://api.factory.ai"),
                )

            # Call the Knowledge droid
            response = await self._factory_client.droids.knowledge.execute(
                action=factory_request["action"],
                context=factory_request["context"],
                options=factory_request["options"],
            )

            # Cache embeddings if enabled
            if self.cache_embeddings and "embeddings" in response:
                content = factory_request["context"].get("content", "")
                if content:
                    self.embedding_cache[content[:100]] = response["embeddings"]

            return {"result": response}

        except Exception:


            pass
            logger.warning("Factory AI SDK not available, using mock response")
            return self._get_mock_response(factory_request)

        except Exception:


            pass
            logger.error(f"Error calling Knowledge droid: {e}", exc_info=True)
            raise

    def _map_method_to_action(self, method: str) -> str:
        """
        """
            "store_knowledge": "store",
            "search_knowledge": "search",
            "generate_documentation": "generate_docs",
            "update_embeddings": "update_vectors",
            "analyze_knowledge_graph": "analyze_graph",
            "extract_insights": "extract",
        }
        return method_mapping.get(method, "store")

    def _format_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        """
                    "rank": idx + 1,
                    "id": result.get("id", ""),
                    "content": result.get("content", ""),
                    "metadata": result.get("metadata", {}),
                    "score": result.get("score", 0.0),
                    "distance": result.get("distance", 0.0),
                    "explanation": result.get("explanation", ""),
                    "highlights": result.get("highlights", []),
                    "related_documents": result.get("related", []),
                }
            )
        return formatted_results

    def _get_mock_response(self, factory_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        """
        action = factory_request["action"]

        if action == "store":
            return {
                "result": {
                    "status": "success",
                    "data": {
                        "document_id": "doc-" + str(hash(factory_request["context"]["content"]))[:8],
                        "chunks_created": 3,
                        "collection": factory_request["context"].get("collection", "default"),
                    },
                    "embeddings": [0.1] * self.vector_dimension,  # Mock embeddings
                    "weaviate_response": {
                        "objects_created": 3,
                        "objects_updated": 0,
                        "schema_changes": [],
                    },
                    "processing_time": 0.5,
                    "tokens_processed": 150,
                    "version": "1.0.0",
                }
            }

        elif action == "search":
            query = factory_request["context"].get("query", "")
            return {
                "result": {
                    "status": "success",
                    "search_results": [
                        {
                            "id": "doc-001",
                            "content": "PostgreSQL connection pooling best practices...",
                            "metadata": {
                                "source": "documentation",
                                "created_at": "2024-01-15",
                                "author": "system",
                            },
                            "score": 0.92,
                            "distance": 0.08,
                            "explanation": f"High semantic similarity to query: '{query}'",
                            "highlights": ["connection pooling", "PostgreSQL"],
                        },
                        {
                            "id": "doc-002",
                            "content": "Weaviate vector search optimization techniques...",
                            "metadata": {
                                "source": "knowledge_base",
                                "category": "performance",
                            },
                            "score": 0.85,
                            "distance": 0.15,
                            "highlights": ["vector search", "optimization"],
                        },
                    ],
                    "processing_time": 0.3,
                    "version": "1.0.0",
                }
            }

        elif action == "generate_docs":
            return {
                "result": {
                    "status": "success",
                    "documentation": """
Generated by Knowledge Droid v1.0.0"""
                    "metadata": {
                        "sections": 5,
                        "word_count": 150,
                        "format": "markdown",
                    },
                    "processing_time": 1.2,
                    "version": "1.0.0",
                }
            }

        elif action == "analyze_graph":
            return {
                "result": {
                    "status": "success",
                    "knowledge_graph": {
                        "nodes": [
                            {
                                "id": "node-1",
                                "label": "PostgreSQL",
                                "type": "technology",
                                "properties": {"category": "database"},
                            },
                            {
                                "id": "node-2",
                                "label": "Weaviate",
                                "type": "technology",
                                "properties": {"category": "vector_db"},
                            },
                            {
                                "id": "node-3",
                                "label": "Connection Pooling",
                                "type": "concept",
                                "properties": {"importance": "high"},
                            },
                        ],
                        "edges": [
                            {
                                "source": "node-1",
                                "target": "node-3",
                                "relationship": "implements",
                                "weight": 0.9,
                            }
                        ],
                        "clusters": [
                            {
                                "id": "cluster-1",
                                "name": "Database Technologies",
                                "nodes": ["node-1", "node-2"],
                            }
                        ],
                        "visualization": "graph TD\n  A[PostgreSQL] --> B[Connection Pooling]\n  C[Weaviate]",
                    },
                    "insights": [
                        "Strong correlation between database technologies",
                        "Connection pooling is a central concept",
                    ],
                    "processing_time": 0.8,
                    "version": "1.0.0",
                }
            }

        return {
            "result": {
                "message": f"Mock response for action: {action}",
                "status": "success",
                "version": "1.0.0",
            }
        }

    async def optimize_embeddings(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        """
            content_key = doc.get("content", "")[:100]
            if content_key in self.embedding_cache:
                cached_count += 1
            else:
                new_embeddings.append(doc)

        if new_embeddings:
            # Process new embeddings
            request = {
                "method": "update_embeddings",
                "params": {
                    "documents": new_embeddings,
                    "batch_size": 100,
                    "use_cache": True,
                },
            }

            result = await self.process_request(request)
        else:
            result = {
                "result": {
                    "status": "success",
                    "message": "All embeddings found in cache",
                }
            }

        result["result"]["cache_stats"] = {
            "cached": cached_count,
            "processed": len(new_embeddings),
            "total": len(documents),
        }

        return result

    async def build_knowledge_index(self, collection: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        """
            "method": "analyze_knowledge_graph",
            "params": {
                "collection": collection,
                "graph_type": "full",
                "depth": options.get("depth", 5),
                "visualization": True,
                "rebuild_index": True,
            },
        }

        return await self.process_request(request)
