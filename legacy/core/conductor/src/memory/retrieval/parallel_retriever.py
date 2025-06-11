"""
"""
T = TypeVar("T", bound=Dict[str, Any])

class SearchResult(BaseModel, Generic[T]):
    """
    """
    source_layer: str = "unknown"
    retrieval_time_ms: float = 0.0

class ParallelMemoryRetriever:
    """
    """
        """
        """
            "short_term": 1.0,
            "mid_term": 0.8,
            "long_term": 0.6,
            "semantic": 1.2,  # Higher weight for semantic results
        }
        self.timeout = timeout

        # Default layer hierarchy (for fallback)
        self.layer_hierarchy = ["short_term", "mid_term", "long_term", "semantic"]

        logger.info(f"ParallelMemoryRetriever initialized with layers: {list(layers.keys())}")

    async def search(
        self,
        field: str,
        value: Any,
        operator: str = "==",
        limit: int = 10,
        layers: Optional[List[str]] = None,
        min_score: float = 0.0,
    ) -> List[SearchResult]:
        """
        """
            logger.warning(f"Search timed out after {self.timeout}s")
            results = []

        # Process results
        all_results: List[SearchResult] = []
        for layer_results in results:
            if isinstance(layer_results, Exception):
                logger.error(f"Error in layer search: {layer_results}")
                continue

            all_results.extend(layer_results)

        # Sort by score (descending)
        all_results.sort(key=lambda x: x.score, reverse=True)

        # Apply score threshold
        filtered_results = [r for r in all_results if r.score >= min_score]

        # Limit results
        limited_results = filtered_results[:limit]

        # Log performance metrics
        total_time = (time.time() - start_time) * 1000

        return limited_results

    async def _search_layer(
        self, layer_name: str, field: str, value: Any, operator: str, limit: int
    ) -> List[SearchResult]:
        """
        """
            return results

        except Exception:


            pass
            logger.warning(f"Search in layer {layer_name} timed out after {self.timeout}s")
            return []
        except Exception:

            pass
            logger.error(f"Error searching layer {layer_name}: {e}")
            return []

    async def semantic_search(
        self,
        query: str,
        limit: int = 10,
        layers: Optional[List[str]] = None,
        min_score: float = 0.0,
    ) -> List[SearchResult]:
        """
        """
            if "semantic" in self.layers:
                semantic_results = await self._search_layer("semantic", "semantic", query, "==", limit)

                # If we have enough semantic results, return them
                if len(semantic_results) >= limit:
                    return semantic_results[:limit]

                # Otherwise, search other layers for additional results
                remaining_limit = limit - len(semantic_results)
                other_layers = [l for l in self.layers.keys() if l != "semantic"]

                # Create tasks for other layers
                tasks = []
                for layer_name in other_layers:
                    task = self._search_text_in_layer(layer_name, query, remaining_limit)
                    tasks.append(task)

                # Execute all search tasks in parallel
                other_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results
                all_other_results: List[SearchResult] = []
                for layer_results in other_results:
                    if isinstance(layer_results, Exception):
                        logger.error(f"Error in layer search: {layer_results}")
                        continue
                    all_other_results.extend(layer_results)

                # Combine results
                combined_results = semantic_results + all_other_results

                # Sort by score (descending)
                combined_results.sort(key=lambda x: x.score, reverse=True)

                # Apply score threshold and limit
                filtered_results = [r for r in combined_results if r.score >= min_score]
                limited_results = filtered_results[:limit]

                # Log performance metrics
                total_time = (time.time() - start_time) * 1000
                logger.debug(
                    f"Parallel semantic search completed in {total_time:.2f}ms, found {len(limited_results)} results"
                )

                return limited_results
            else:
                # No semantic layer, search all layers
                search_layers = list(self.layers.keys())
        else:
            search_layers = layers

        # Create tasks for each layer
        tasks = []
        for layer_name in search_layers:
            if layer_name not in self.layers:
                continue

            if layer_name == "semantic":
                task = self._search_layer(layer_name, "semantic", query, "==", limit)
            else:
                task = self._search_text_in_layer(layer_name, query, limit)
            tasks.append(task)

        # Execute all search tasks in parallel
        try:

            pass
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception:

            pass
            logger.warning(f"Semantic search timed out after {self.timeout}s")
            results = []

        # Process results
        all_results: List[SearchResult] = []
        for layer_results in results:
            if isinstance(layer_results, Exception):
                logger.error(f"Error in layer search: {layer_results}")
                continue

            all_results.extend(layer_results)

        # Sort by score (descending)
        all_results.sort(key=lambda x: x.score, reverse=True)

        # Apply score threshold
        filtered_results = [r for r in all_results if r.score >= min_score]

        # Limit results
        limited_results = filtered_results[:limit]

        # Log performance metrics
        total_time = (time.time() - start_time) * 1000

        return limited_results

    async def _search_text_in_layer(self, layer_name: str, query: str, limit: int) -> List[SearchResult]:
        """
        """
                layer.search("content", query, "contains", limit), timeout=self.timeout
            )

            if content_results:
                # Convert to SearchResult objects
                results = []
                layer_weight = self.layer_weights.get(layer_name, 1.0)
                retrieval_time = 0.0  # We don't have the actual time here

                for item in content_results:
                    result = SearchResult(
                        item=item,
                        score=0.7 * layer_weight,  # Lower score for text match
                        source_layer=layer_name,
                        retrieval_time_ms=retrieval_time,
                    )
                    results.append(result)

                return results

            # If no results, try text field
            text_results = await asyncio.wait_for(layer.search("text", query, "contains", limit), timeout=self.timeout)

            # Convert to SearchResult objects
            results = []
            layer_weight = self.layer_weights.get(layer_name, 1.0)
            retrieval_time = 0.0  # We don't have the actual time here

            for item in text_results:
                result = SearchResult(
                    item=item,
                    score=0.6 * layer_weight,  # Even lower score for text field match
                    source_layer=layer_name,
                    retrieval_time_ms=retrieval_time,
                )
                results.append(result)

            return results

        except Exception:


            pass
            logger.warning(f"Text search in layer {layer_name} timed out after {self.timeout}s")
            return []
        except Exception:

            pass
            logger.error(f"Error searching text in layer {layer_name}: {e}")
            return []
