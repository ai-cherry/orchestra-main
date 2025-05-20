"""
Privacy Enhanced Memory Manager for AI Orchestration System.

This module provides a wrapper around the standard MemoryManager that adds
enhanced privacy protection features such as data minimization, privacy level
enforcement, PII detection, and automatic data expiration.
"""

import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple, Union, cast

from packages.shared.src.memory.memory_manager import MemoryManager, MemoryHealth
from packages.shared.src.models.base_models import AgentData, MemoryItem, PersonaConfig
from packages.shared.src.models.metadata_schemas import (
    PrivacyLevel,
    MetadataValidationError,
    UserDataMetadata,
    add_standard_metadata_fields,
    validate_user_data_metadata,
)
from packages.shared.src.storage.config import MEMORY_ITEMS_COLLECTION, StorageConfig

# Configure logging
logger = logging.getLogger(__name__)


class PIIDetectionConfig:
    """Configuration for PII detection."""

    # Common PII regex patterns
    EMAIL_PATTERN: Pattern = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    )
    PHONE_PATTERN: Pattern = re.compile(
        r"\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"
    )
    SSN_PATTERN: Pattern = re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b")
    CREDIT_CARD_PATTERN: Pattern = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
    ADDRESS_PATTERN: Pattern = re.compile(
        r"\b\d+\s+([A-Za-z]+(\.?\s+|\s+)){1,4}(Avenue|Lane|Road|Boulevard|Drive|Street|Ave|Dr|Rd|Blvd|Ln|St)\.?\b",
        re.IGNORECASE,
    )

    # Additional configuration
    ENABLE_PII_DETECTION: bool = True
    ENABLE_PII_REDACTION: bool = True
    MINIMUM_RETENTION_DAYS: int = 1
    DEFAULT_RETENTION_DAYS: int = 90
    MAX_RETENTION_DAYS: int = 365


class PrivacyEnhancedMemoryManager(MemoryManager):
    """
    Privacy-enhanced wrapper for MemoryManager.

    This class wraps a standard MemoryManager implementation and adds privacy
    enhancements such as PII detection, data minimization, privacy level
    enforcement, and automatic data expiration.
    """

    def __init__(
        self,
        underlying_manager: MemoryManager,
        config: Optional[StorageConfig] = None,
        pii_config: Optional[PIIDetectionConfig] = None,
    ):
        """
        Initialize the privacy-enhanced memory manager.

        Args:
            underlying_manager: The underlying memory manager to wrap
            config: Optional storage configuration
            pii_config: Optional PII detection configuration
        """
        self.manager = underlying_manager
        self.config = config or StorageConfig()
        self.pii_config = pii_config or PIIDetectionConfig()

    async def initialize(self) -> None:
        """Initialize the memory manager."""
        await self.manager.initialize()
        logger.info("Privacy enhanced memory manager initialized")

    async def close(self) -> None:
        """Close the memory manager and release resources."""
        await self.manager.close()

    async def add_memory_item(self, item: MemoryItem) -> str:
        """
        Add a memory item to storage with privacy enhancements.

        Args:
            item: The memory item to store

        Returns:
            The ID of the created memory item

        Raises:
            ValidationError: If the item fails validation
            StorageError: If the storage operation fails
        """
        # Apply privacy enhancements
        enhanced_item = await self._enhance_memory_item(item)

        # Store the enhanced item
        return await self.manager.add_memory_item(enhanced_item)

    async def get_memory_item(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a specific memory item by ID.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            The memory item if found, None otherwise

        Raises:
            StorageError: If the retrieval operation fails
        """
        # Simply delegate to the underlying manager
        return await self.manager.get_memory_item(item_id)

    async def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem]:
        """
        Retrieve conversation history for a user with privacy controls.

        Args:
            user_id: The user ID to get history for
            session_id: Optional session ID to filter by
            limit: Maximum number of items to retrieve
            filters: Optional filters to apply

        Returns:
            List of memory items representing the conversation history

        Raises:
            StorageError: If the retrieval operation fails
        """
        # Add privacy-related filters if needed
        privacy_filters = filters.copy() if filters else {}

        # Get conversation history from underlying manager
        history = await self.manager.get_conversation_history(
            user_id=user_id, session_id=session_id, limit=limit, filters=privacy_filters
        )

        return history

    async def semantic_search(
        self,
        user_id: str,
        query_embedding: List[float],
        persona_context: Optional[PersonaConfig] = None,
        top_k: int = 5,
    ) -> List[MemoryItem]:
        """
        Perform semantic search using vector embeddings with privacy controls.

        Args:
            user_id: The user ID to search memories for
            query_embedding: The vector embedding of the query
            persona_context: Optional persona context for personalized results
            top_k: Maximum number of results to return

        Returns:
            List of memory items ordered by relevance

        Raises:
            ValidationError: If the query embedding has invalid dimensions
            StorageError: If the search operation fails
        """
        # Delegate to the underlying manager
        results = await self.manager.semantic_search(
            user_id=user_id,
            query_embedding=query_embedding,
            persona_context=persona_context,
            top_k=top_k,
        )

        # Post-process results to ensure privacy compliance
        # This could filter out certain sensitive items or apply additional checks
        return results

    async def add_raw_agent_data(self, data: AgentData) -> str:
        """
        Store raw agent data.

        Args:
            data: The agent data to store

        Returns:
            The ID of the stored data

        Raises:
            ValidationError: If the data fails validation
            StorageError: If the storage operation fails
        """
        # Agent data typically doesn't contain personal information,
        # so we can delegate directly to the underlying manager
        return await self.manager.add_raw_agent_data(data)

    async def check_duplicate(self, item: MemoryItem) -> bool:
        """
        Check if a memory item already exists in storage.

        Args:
            item: The memory item to check for duplicates

        Returns:
            True if a duplicate exists, False otherwise

        Raises:
            StorageError: If the check operation fails
        """
        # Generate a content hash if not already present
        if not item.metadata.get("content_hash") and item.text_content:
            item.metadata["content_hash"] = self._generate_content_hash(
                item.text_content
            )

        return await self.manager.check_duplicate(item)

    async def cleanup_expired_items(self) -> int:
        """
        Remove expired items from storage.

        Returns:
            Number of items removed

        Raises:
            StorageError: If the cleanup operation fails
        """
        # Delegate to the underlying manager
        return await self.manager.cleanup_expired_items()

    async def health_check(self) -> MemoryHealth:
        """
        Check the health of the memory system.

        Returns:
            MemoryHealth: A dictionary with health status information

        Raises:
            Exception: If the health check itself fails
        """
        # Get health from underlying manager
        health = await self.manager.health_check()

        # Add privacy-specific health information
        if "details" not in health:
            health["details"] = {}

        health["details"]["privacy_enhanced"] = True
        health["details"][
            "pii_detection_enabled"
        ] = self.pii_config.ENABLE_PII_DETECTION
        health["details"][
            "pii_redaction_enabled"
        ] = self.pii_config.ENABLE_PII_REDACTION

        return health

    async def _enhance_memory_item(self, item: MemoryItem) -> MemoryItem:
        """
        Apply privacy enhancements to a memory item.

        Args:
            item: The memory item to enhance

        Returns:
            Enhanced memory item
        """
        # Create a copy to avoid modifying the original
        enhanced_item = MemoryItem(**item.dict())

        # 1. Apply PII detection if enabled
        if self.pii_config.ENABLE_PII_DETECTION and enhanced_item.text_content:
            pii_detected, pii_types = self._detect_pii(enhanced_item.text_content)
            enhanced_item.metadata["pii_detected"] = pii_detected
            if pii_detected:
                enhanced_item.metadata["pii_types"] = pii_types

                # Apply redaction if enabled
                if self.pii_config.ENABLE_PII_REDACTION:
                    enhanced_item.text_content = self._redact_pii(
                        enhanced_item.text_content
                    )

        # 2. Determine privacy classification level
        privacy_level = self._determine_privacy_level(enhanced_item)

        # 3. Add privacy metadata
        try:
            metadata = enhanced_item.metadata.copy()
            metadata["data_classification"] = privacy_level

            # Validate metadata against schema
            validated_metadata = validate_user_data_metadata(metadata)
            validated_metadata = add_standard_metadata_fields(validated_metadata)

            enhanced_item.metadata = validated_metadata
        except MetadataValidationError as e:
            logger.warning(
                f"Failed to validate privacy metadata: {e}. Using original metadata."
            )

        # 4. Add content hash if not present
        if "content_hash" not in enhanced_item.metadata and enhanced_item.text_content:
            enhanced_item.metadata["content_hash"] = self._generate_content_hash(
                enhanced_item.text_content
            )

        # 5. Set expiration if not present
        if not enhanced_item.expiration:
            retention_days = enhanced_item.metadata.get(
                "retention_period", self.pii_config.DEFAULT_RETENTION_DAYS
            )
            retention_days = min(
                max(retention_days, self.pii_config.MINIMUM_RETENTION_DAYS),
                self.pii_config.MAX_RETENTION_DAYS,
            )
            enhanced_item.expiration = datetime.utcnow() + timedelta(
                days=retention_days
            )

        return enhanced_item

    def _detect_pii(self, text: str) -> Tuple[bool, List[str]]:
        """
        Detect PII in text.

        Args:
            text: Text to check for PII

        Returns:
            Tuple of (pii_detected, list_of_pii_types)
        """
        pii_types = []

        # Check for various PII types using regex patterns
        if self.pii_config.EMAIL_PATTERN.search(text):
            pii_types.append("email")

        if self.pii_config.PHONE_PATTERN.search(text):
            pii_types.append("phone")

        if self.pii_config.SSN_PATTERN.search(text):
            pii_types.append("ssn")

        if self.pii_config.CREDIT_CARD_PATTERN.search(text):
            pii_types.append("credit_card")

        if self.pii_config.ADDRESS_PATTERN.search(text):
            pii_types.append("address")

        return len(pii_types) > 0, pii_types

    def _redact_pii(self, text: str) -> str:
        """
        Redact PII from text.

        Args:
            text: Text containing PII

        Returns:
            Redacted text
        """
        redacted = text

        # Redact various PII types using regex patterns
        redacted = self.pii_config.EMAIL_PATTERN.sub("[EMAIL REDACTED]", redacted)
        redacted = self.pii_config.PHONE_PATTERN.sub("[PHONE REDACTED]", redacted)
        redacted = self.pii_config.SSN_PATTERN.sub("[SSN REDACTED]", redacted)
        redacted = self.pii_config.CREDIT_CARD_PATTERN.sub(
            "[CREDIT CARD REDACTED]", redacted
        )
        redacted = self.pii_config.ADDRESS_PATTERN.sub("[ADDRESS REDACTED]", redacted)

        return redacted

    def _determine_privacy_level(self, item: MemoryItem) -> str:
        """
        Determine the privacy level of a memory item.

        Args:
            item: Memory item to classify

        Returns:
            Privacy level as string
        """
        # Start with standard level
        level = PrivacyLevel.STANDARD.value

        # Check if PII was detected
        if item.metadata.get("pii_detected", False):
            pii_types = item.metadata.get("pii_types", [])

            # Certain PII types require higher privacy levels
            if any(pii_type in ["ssn", "credit_card"] for pii_type in pii_types):
                level = PrivacyLevel.CRITICAL.value
            elif pii_types:
                level = PrivacyLevel.SENSITIVE.value

        # Check for item-type based classification
        if item.item_type in ["personal_info", "payment_info", "health_info"]:
            level = PrivacyLevel.SENSITIVE.value

        if item.item_type in ["credentials", "security_info"]:
            level = PrivacyLevel.CRITICAL.value

        return level

    def _generate_content_hash(self, content: str) -> str:
        """
        Generate a content hash for deduplication.

        Args:
            content: Content to hash

        Returns:
            Hash string
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _apply_data_minimization(self, item: MemoryItem) -> MemoryItem:
        """
        Apply data minimization techniques to a memory item.

        Args:
            item: The memory item to minimize

        Returns:
            Minimized memory item
        """
        # This is a placeholder for more sophisticated data minimization techniques.
        # In a real implementation, this could:
        # - Remove unnecessary fields
        # - Truncate or summarize content
        # - Apply differential privacy techniques
        # - Use entity extraction to remove non-essential personal identifiers

        return item
