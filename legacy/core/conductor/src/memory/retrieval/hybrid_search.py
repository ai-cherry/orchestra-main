"""
"""
T = TypeVar("T", bound=Dict[str, Any])

class QueryType(str, Enum):
    """Types of queries for hybrid search."""
    FACTUAL = "factual"  # Prioritize exact matches
    CONCEPTUAL = "conceptual"  # Prioritize semantic matches
    CONVERSATIONAL = "conversational"  # Balance between exact and semantic
    UNKNOWN = "unknown"  # Default type

class HybridSearchConfig(BaseModel):
    """
    """
    fusion_method: str = "weighted_sum"  # "weighted_sum", "reciprocal_rank_fusion"

    # RRF constant for reciprocal rank fusion
    rrf_k: int = 60

    # Minimum scores
    min_keyword_score: float = 0.1
    min_semantic_score: float = 0.1

    # Timeout settings
    keyword_timeout: float = 3.0
    semantic_timeout: float = 5.0

class HybridSearchEngine:
    """
    """
        """
        """
        logger.info(f"HybridSearchEngine initialized with {len(layers)} layers")

    async def search(
        self,
        query: str,
        limit: int = 10,
        layers: Optional[List[str]] = None,
        query_type: Optional[QueryType] = None,
    ) -> List[SearchResult]:
        """
        """

        # Adjust weights based on query type
        keyword_weight = self.config.keyword_weight
        semantic_weight = self.config.semantic_weight

        if query_type == QueryType.FACTUAL:
            keyword_weight *= self.config.factual_keyword_boost
            semantic_weight *= self.config.factual_semantic_boost
        elif query_type == QueryType.CONCEPTUAL:
            keyword_weight *= self.config.conceptual_keyword_boost
            semantic_weight *= self.config.conceptual_semantic_boost
        elif query_type == QueryType.CONVERSATIONAL:
            keyword_weight *= self.config.conversational_keyword_boost
            semantic_weight *= self.config.conversational_semantic_boost

        # Execute keyword and semantic searches in parallel
        keyword_task = self._execute_keyword_search(query, limit * 2, layers)
        semantic_task = self._execute_semantic_search(query, limit * 2, layers)

        keyword_results, semantic_results = await asyncio.gather(keyword_task, semantic_task, return_exceptions=True)

        # Handle except Exception:
     pass
            logger.error(f"Keyword search failed: {keyword_results}")
            keyword_results = []

        if isinstance(semantic_results, Exception):
            logger.error(f"Semantic search failed: {semantic_results}")
            semantic_results = []

        # Apply minimum scores
        keyword_results = [r for r in keyword_results if r.score >= self.config.min_keyword_score]
        semantic_results = [r for r in semantic_results if r.score >= self.config.min_semantic_score]

        # Combine results using the configured fusion method
        if self.config.fusion_method == "reciprocal_rank_fusion":
            combined_results = self._reciprocal_rank_fusion(
                keyword_results, semantic_results, keyword_weight, semantic_weight
            )
        else:  # Default to weighted sum
            combined_results = self._weighted_sum_fusion(
                keyword_results, semantic_results, keyword_weight, semantic_weight
            )

        # Sort by score (descending) and limit results
        combined_results.sort(key=lambda x: x.score, reverse=True)
        limited_results = combined_results[:limit]

        # Log performance metrics
        total_time = (time.time() - start_time) * 1000
        logger.debug(
            f"Hybrid search completed in {total_time:.2f}ms, "
            f"found {len(limited_results)} results "
            f"(keyword: {len(keyword_results)}, semantic: {len(semantic_results)})"
        )

        return limited_results

    async def _execute_keyword_search(self, query: str, limit: int, layers: Optional[List[str]]) -> List[SearchResult]:
        """
        """
            # Use "contains" operator for keyword search
            results = await asyncio.wait_for(
                self.retriever.search(
                    field="content",
                    value=query,
                    operator="contains",
                    limit=limit,
                    layers=layers,
                ),
                timeout=self.config.keyword_timeout,
            )

            # If no results in content field, try text field
            if not results:
                results = await asyncio.wait_for(
                    self.retriever.search(
                        field="text",
                        value=query,
                        operator="contains",
                        limit=limit,
                        layers=layers,
                    ),
                    timeout=self.config.keyword_timeout,
                )

            # Tag results as keyword search
            for result in results:
                result.item["search_type"] = "keyword"

            return results
        except Exception:

            pass
            logger.warning(f"Keyword search timed out after {self.config.keyword_timeout}s")
            return []
        except Exception:

            pass
            logger.error(f"Error in keyword search: {e}")
            return []

    async def _execute_semantic_search(self, query: str, limit: int, layers: Optional[List[str]]) -> List[SearchResult]:
        """
        """
                result.item["search_type"] = "semantic"

            return results
        except Exception:

            pass
            logger.warning(f"Semantic search timed out after {self.config.semantic_timeout}s")
            return []
        except Exception:

            pass
            logger.error(f"Error in semantic search: {e}")
            return []

    def _weighted_sum_fusion(
        self,
        keyword_results: List[SearchResult],
        semantic_results: List[SearchResult],
        keyword_weight: float,
        semantic_weight: float,
    ) -> List[SearchResult]:
        """
        """
            item_id = result.item.get("id", result.item.get("memory_key", ""))
            if not item_id:
                continue

            score = result.score * keyword_weight
            combined_scores[item_id] = (result, score)

        # Process semantic results
        for result in semantic_results:
            item_id = result.item.get("id", result.item.get("memory_key", ""))
            if not item_id:
                continue

            score = result.score * semantic_weight

            if item_id in combined_scores:
                # Item exists in both result sets, combine scores
                existing_result, existing_score = combined_scores[item_id]
                combined_score = existing_score + score

                # Update with combined score and mark as hybrid
                result.score = combined_score
                result.item["search_type"] = "hybrid"
                combined_scores[item_id] = (result, combined_score)
            else:
                # New item
                combined_scores[item_id] = (result, score)

        # Extract results and update scores
        results = []
        for item_id, (result, score) in combined_scores.items():
            result.score = score
            results.append(result)

        return results

    def _reciprocal_rank_fusion(
        self,
        keyword_results: List[SearchResult],
        semantic_results: List[SearchResult],
        keyword_weight: float,
        semantic_weight: float,
    ) -> List[SearchResult]:
        """
        """
            item_id = result.item.get("id", result.item.get("memory_key", ""))
            if not item_id:
                continue

            # RRF formula: 1 / (rank + k)
            rank = i + 1  # 1-based ranking
            score = (1.0 / (rank + self.config.rrf_k)) * keyword_weight
            combined_scores[item_id] = (result, score)

        # Process semantic results with RRF formula
        for i, result in enumerate(semantic_results):
            item_id = result.item.get("id", result.item.get("memory_key", ""))
            if not item_id:
                continue

            # RRF formula: 1 / (rank + k)
            rank = i + 1  # 1-based ranking
            score = (1.0 / (rank + self.config.rrf_k)) * semantic_weight

            if item_id in combined_scores:
                # Item exists in both result sets, combine scores
                existing_result, existing_score = combined_scores[item_id]
                combined_score = existing_score + score

                # Update with combined score and mark as hybrid
                result.score = combined_score
                result.item["search_type"] = "hybrid"
                combined_scores[item_id] = (result, combined_score)
            else:
                # New item
                combined_scores[item_id] = (result, score)

        # Extract results and update scores
        results = []
        for item_id, (result, score) in combined_scores.items():
            result.score = score
            results.append(result)

        return results

    def _default_query_classifier(self, query: str) -> QueryType:
        """
        """
            "what is",
            "who is",
            "when did",
            "where is",
            "how many",
            "define",
            "explain",
            "list",
            "tell me about",
            "find",
        ]

        # Check for conceptual query indicators
        conceptual_indicators = [
            "why",
            "how does",
            "what if",
            "compare",
            "contrast",
            "analyze",
            "evaluate",
            "similar to",
            "difference between",
            "relationship",
            "concept",
            "theory",
            "principle",
        ]

        # Check for conversational query indicators
        conversational_indicators = [
            "can you",
            "could you",
            "would you",
            "i want",
            "i need",
            "help me",
            "please",
            "thanks",
            "thank you",
            "hi",
            "hello",
        ]

        # Count matches for each type
        factual_count = sum(1 for indicator in factual_indicators if indicator in query)
        conceptual_count = sum(1 for indicator in conceptual_indicators if indicator in query)
        conversational_count = sum(1 for indicator in conversational_indicators if indicator in query)

        # Determine the type with the most matches
        if factual_count > conceptual_count and factual_count > conversational_count:
            return QueryType.FACTUAL
        elif conceptual_count > factual_count and conceptual_count > conversational_count:
            return QueryType.CONCEPTUAL
        elif conversational_count > 0:
            return QueryType.CONVERSATIONAL

        # Default to unknown if no clear indicators
        return QueryType.UNKNOWN
