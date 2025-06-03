"""
"""
    """Strategies for resolving duplicates."""
    KEEP_EXISTING = "keep_existing"
    REPLACE_WITH_NEW = "replace_with_new"
    MERGE = "merge"
    KEEP_BOTH = "keep_both"
    MANUAL_REVIEW = "manual_review"

class ResolutionAction(Enum):
    """Actions taken during resolution."""
    REJECTED = "rejected"
    REPLACED = "replaced"
    MERGED = "merged"
    KEPT_BOTH = "kept_both"
    QUEUED_FOR_REVIEW = "queued_for_review"

@dataclass
class ResolutionResult:
    """Result of duplicate resolution."""
    resolved_by: str = "system"
    resolution_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
            "action": self.action.value,
            "strategy": self.strategy.value,
            "duplicate_match": self.duplicate_match.to_dict(),
            "new_content_id": self.new_content_id,
            "merged_content_id": self.merged_content_id,
            "resolution_metadata": self.resolution_metadata,
            "resolution_timestamp": self.resolution_timestamp.isoformat(),
            "resolved_by": self.resolved_by,
            "resolution_reason": self.resolution_reason
        }

class DuplicateResolver:
    """
    """
        """
        """
        if "strategies" in self.config:
            for dup_type, strategy in self.config["strategies"].items():
                self.default_strategies[DuplicateType(dup_type)] = ResolutionStrategy(strategy)
        
        # Auto-resolution thresholds
        self.auto_resolve_threshold = self.config.get("auto_resolve_threshold", 0.98)
        self.manual_review_threshold = self.config.get("manual_review_threshold", 0.85)
    
    async def resolve_duplicate(
        self,
        duplicate_match: DuplicateMatch,
        new_content: Dict[str, Any],
        existing_content: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ResolutionResult:
        """
        """
        """
        """
            content_id = new_content.get("id", str(hash(new_content["content"])))
            
            if content_id in duplicate_matches:
                match = duplicate_matches[content_id]
                existing_content = existing_contents.get(match.existing_id, {})
                
                result = await self.resolve_duplicate(
                    match,
                    new_content,
                    existing_content
                )
                
                results[content_id] = result
        
        return results
    
    async def _determine_strategy(
        self,
        duplicate_match: DuplicateMatch,
        new_content: Dict[str, Any],
        existing_content: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ResolutionStrategy:
        """
        """
        if context and "resolution_strategy" in context:
            return ResolutionStrategy(context["resolution_strategy"])
        
        # Auto-resolution for high confidence matches
        if duplicate_match.similarity_score >= self.auto_resolve_threshold:
            # Check timestamps - keep newer for exact matches
            if duplicate_match.duplicate_type == DuplicateType.EXACT:
                new_timestamp = new_content.get("timestamp", datetime.min)
                existing_timestamp = existing_content.get("timestamp", datetime.min)
                
                if isinstance(new_timestamp, str):
                    new_timestamp = datetime.fromisoformat(new_timestamp)
                if isinstance(existing_timestamp, str):
                    existing_timestamp = datetime.fromisoformat(existing_timestamp)
                
                if new_timestamp > existing_timestamp:
                    return ResolutionStrategy.REPLACE_WITH_NEW
                else:
                    return ResolutionStrategy.KEEP_EXISTING
        
        # Manual review for uncertain matches
        if duplicate_match.similarity_score <= self.manual_review_threshold:
            return ResolutionStrategy.MANUAL_REVIEW
        
        # Use default strategy for duplicate type
        return self.default_strategies.get(
            duplicate_match.duplicate_type,
            ResolutionStrategy.MANUAL_REVIEW
        )
    
    async def _keep_existing(
        self,
        duplicate_match: DuplicateMatch,
        new_content: Dict[str, Any],
        existing_content: Dict[str, Any]
    ) -> ResolutionResult:
        """Keep existing content and reject new."""
                "rejected_content": new_content.get("id"),
                "kept_content": existing_content.get("id"),
                "reason": f"Duplicate detected with {duplicate_match.similarity_score:.2%} similarity"
            },
            resolution_reason="Existing content retained due to duplicate detection"
        )
    
    async def _replace_with_new(
        self,
        duplicate_match: DuplicateMatch,
        new_content: Dict[str, Any],
        existing_content: Dict[str, Any]
    ) -> ResolutionResult:
        """Replace existing content with new."""
            new_content_id=new_content.get("id"),
            resolution_metadata={
                "replaced_content": existing_content.get("id"),
                "new_content": new_content.get("id"),
                "reason": "Newer version detected"
            },
            resolution_reason="Existing content replaced with newer version"
        )
    
    async def _merge_content(
        self,
        duplicate_match: DuplicateMatch,
        new_content: Dict[str, Any],
        existing_content: Dict[str, Any]
    ) -> ResolutionResult:
        """Merge new and existing content."""
            **existing_content.get("metadata", {}),
            **new_content.get("metadata", {})
        }
        
        # Merge content (concatenate for partial matches)
        if duplicate_match.duplicate_type == DuplicateType.PARTIAL:
            # Determine which content is longer
            existing_text = existing_content.get("content", "")
            new_text = new_content.get("content", "")
            
            if len(new_text) > len(existing_text):
                merged_content = new_text
            else:
                merged_content = existing_text
        else:
            # For other types, keep existing content but update metadata
            merged_content = existing_content.get("content", "")
        
        # Generate merged ID
        merged_id = f"merged_{existing_content.get('id')}_{new_content.get('id')}"
        
        return ResolutionResult(
            action=ResolutionAction.MERGED,
            strategy=ResolutionStrategy.MERGE,
            duplicate_match=duplicate_match,
            merged_content_id=merged_id,
            resolution_metadata={
                "merged_from": [existing_content.get("id"), new_content.get("id")],
                "merged_content": merged_content,
                "merged_metadata": merged_metadata,
                "merge_type": duplicate_match.duplicate_type.value
            },
            resolution_reason=f"Content merged due to {duplicate_match.duplicate_type.value} match"
        )
    
    async def _keep_both(
        self,
        duplicate_match: DuplicateMatch,
        new_content: Dict[str, Any],
        existing_content: Dict[str, Any]
    ) -> ResolutionResult:
        """Keep both contents as separate entries."""
            new_content_id=new_content.get("id"),
            resolution_metadata={
                "existing_id": existing_content.get("id"),
                "new_id": new_content.get("id"),
                "relationship": "similar_content",
                "similarity_score": duplicate_match.similarity_score
            },
            resolution_reason="Both contents kept due to semantic differences"
        )
    
    async def _queue_for_review(
        self,
        duplicate_match: DuplicateMatch,
        new_content: Dict[str, Any],
        existing_content: Dict[str, Any]
    ) -> ResolutionResult:
        """Queue for manual review."""
                "review_queue_id": f"review_{datetime.utcnow().timestamp()}",
                "new_content": new_content,
                "existing_content": existing_content,
                "similarity_score": duplicate_match.similarity_score,
                "duplicate_type": duplicate_match.duplicate_type.value
            },
            resolution_reason="Manual review required for ambiguous duplicate"
        )
    
    async def apply_manual_resolution(
        self,
        review_queue_id: str,
        resolution_decision: str,
        resolved_by: str,
        resolution_notes: Optional[str] = None
    ) -> ResolutionResult:
        """
        """
                "manual_decision": resolution_decision,
                "notes": resolution_notes
            },
            resolution_reason=f"Manual resolution: {resolution_decision}"
        )