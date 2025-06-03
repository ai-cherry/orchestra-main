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
                f"Importance scoring weights sum to {weights_sum}, not 1.0. " "Scores may not be properly normalized."
            )

        logger.info("ImportanceScorer initialized")

    def score_item(self, item: Dict[str, Any], factors: Optional[ImportanceFactors] = None) -> ImportanceScore:
        """
        """
        item_id = item.get("id", item.get("memory_key", str(id(item))))

        # Extract or use provided factors
        if factors is None:
            factors = self._extract_factors(item)

        # Calculate component scores
        recency_score = self._calculate_recency_score(factors)
        usage_score = self._calculate_usage_score(factors)
        content_score = self._calculate_content_score(factors)
        metadata_score = self._calculate_metadata_score(factors)
        relationship_score = self._calculate_relationship_score(factors)
        semantic_score = self._calculate_semantic_score(factors)

        # Calculate overall score (weighted sum)
        overall_score = (
            recency_score * self.config.recency_weight
            + usage_score * self.config.usage_weight
            + content_score * self.config.content_weight
            + metadata_score * self.config.metadata_weight
            + relationship_score * self.config.relationship_weight
            + semantic_score * self.config.semantic_weight
        )

        # Ensure score is in [0, 1] range
        overall_score = max(0.0, min(1.0, overall_score))

        # Create and return score object
        return ImportanceScore(
            item_id=item_id,
            score=overall_score,
            recency_score=recency_score,
            usage_score=usage_score,
            content_score=content_score,
            metadata_score=metadata_score,
            relationship_score=relationship_score,
            semantic_score=semantic_score,
            factors=factors,
        )

    def _extract_factors(self, item: Dict[str, Any]) -> ImportanceFactors:
        """
        """
        created_at = item.get("created_at")
        if isinstance(created_at, (int, float)):
            created_at = datetime.fromtimestamp(created_at)
        elif not isinstance(created_at, datetime):
            created_at = datetime.utcnow()

        # Extract last accessed time
        last_accessed_at = item.get("last_accessed_at")
        if isinstance(last_accessed_at, (int, float)):
            last_accessed_at = datetime.fromtimestamp(last_accessed_at)
        elif not isinstance(last_accessed_at, datetime):
            last_accessed_at = None

        # Extract content
        content = item.get("content", item.get("text_content", ""))
        if not isinstance(content, str):
            content = str(content)

        # Extract metadata
        metadata = item.get("metadata", {})

        # Extract entities
        entities = item.get("entities", [])
        if not isinstance(entities, list):
            entities = []

        # Extract relationships
        relationships = item.get("relationships", [])
        if not isinstance(relationships, list):
            relationships = []

        # Create and return factors
        return ImportanceFactors(
            created_at=created_at,
            last_accessed_at=last_accessed_at,
            access_count=item.get("access_count", 0),
            reference_count=item.get("reference_count", 0),
            content_length=len(content),
            has_entities=len(entities) > 0,
            entity_count=len(entities),
            is_user_marked_important=metadata.get("important", False),
            explicit_importance=metadata.get("importance"),
            connected_item_count=len(relationships),
            semantic_richness=item.get("semantic_richness", 0.0),
        )

    def _calculate_recency_score(self, factors: ImportanceFactors) -> float:
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