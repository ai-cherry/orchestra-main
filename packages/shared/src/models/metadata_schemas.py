"""
Metadata schema definitions for the AI Orchestration System.

This module provides structured metadata schemas and validation utilities
for different types of data stored in the memory system, ensuring consistency
and proper data classification.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union, cast
import re
import logging

# Configure logging
logger = logging.getLogger(__name__)


class MetadataValidationError(Exception):
    """Exception raised when metadata validation fails."""

    pass


class DevNoteType(str, Enum):
    """Types of development notes."""

    IMPLEMENTATION = "implementation"
    ARCHITECTURE = "architecture"
    ISSUE = "issue"
    DECISION = "decision"
    REFACTORING = "refactoring"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DEPLOYMENT = "deployment"
    DOCUMENTATION = "documentation"


class PrivacyLevel(str, Enum):
    """Privacy levels for data classification."""

    STANDARD = "standard"
    SENSITIVE = "sensitive"
    CRITICAL = "critical"


class MetadataValidator:
    """Base class for metadata validators."""

    required_fields: Set[str] = set()
    optional_fields: Set[str] = set()
    field_validators: Dict[str, callable] = {}

    @classmethod
    def validate(cls, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate metadata against the schema.

        Args:
            metadata: Metadata to validate

        Returns:
            Validated and potentially modified metadata

        Raises:
            MetadataValidationError: If validation fails
        """
        # Check required fields
        missing_fields = cls.required_fields - set(metadata.keys())
        if missing_fields:
            raise MetadataValidationError(f"Missing required metadata fields: {', '.join(missing_fields)}")

        # Check for unknown fields
        allowed_fields = cls.required_fields.union(cls.optional_fields)
        unknown_fields = set(metadata.keys()) - allowed_fields
        if unknown_fields:
            logger.warning(f"Unknown metadata fields will be ignored: {', '.join(unknown_fields)}")

        # Validate individual fields
        validated_metadata = {}
        for field, value in metadata.items():
            if field in allowed_fields:
                # Run field-specific validation if available
                if field in cls.field_validators:
                    try:
                        validated_metadata[field] = cls.field_validators[field](value)
                    except Exception as e:
                        raise MetadataValidationError(f"Validation failed for field '{field}': {e}")
                else:
                    validated_metadata[field] = value

        # Add default values for missing optional fields
        for field in cls.optional_fields:
            if field not in validated_metadata and hasattr(cls, f"default_{field}"):
                default_value = getattr(cls, f"default_{field}")
                if callable(default_value):
                    validated_metadata[field] = default_value()
                else:
                    validated_metadata[field] = default_value

        return validated_metadata


class DevNoteMetadata(MetadataValidator):
    """Validator for development note metadata."""

    required_fields = {
        "component",
        "note_type",
    }

    optional_fields = {
        "visibility",
        "priority",
        "commit_id",
        "related_file_paths",
        "author",
        "tags",
        "ticket_id",
        "expiration",
        "version",
    }

    @staticmethod
    def default_visibility() -> str:
        return "team"

    @staticmethod
    def default_priority() -> str:
        return "normal"

    @staticmethod
    def default_tags() -> List[str]:
        return []

    @staticmethod
    def default_version() -> str:
        return "1.0"

    @staticmethod
    def validate_note_type(value: str) -> str:
        """Validate note type."""
        try:
            return DevNoteType(value).value
        except ValueError:
            valid_types = [t.value for t in DevNoteType]
            raise ValueError(f"Invalid note type: {value}. Must be one of: {', '.join(valid_types)}")

    @staticmethod
    def validate_priority(value: str) -> str:
        """Validate priority level."""
        valid_priorities = ["low", "normal", "high", "critical"]
        if value not in valid_priorities:
            raise ValueError(f"Invalid priority: {value}. Must be one of: {', '.join(valid_priorities)}")
        return value

    @staticmethod
    def validate_commit_id(value: str) -> str:
        """Validate commit ID format."""
        if not re.match(r"^[0-9a-f]{7,40}$", value):
            raise ValueError("Commit ID must be a valid git commit hash")
        return value

    @staticmethod
    def validate_expiration(value: Union[str, datetime]) -> datetime:
        """Validate and convert expiration date."""
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                raise ValueError("Expiration must be a valid ISO format date string")
        elif isinstance(value, datetime):
            return value
        else:
            raise ValueError("Expiration must be a datetime or ISO format string")

    # Register field validators
    field_validators = {
        "note_type": validate_note_type,
        "priority": validate_priority,
        "commit_id": validate_commit_id,
        "expiration": validate_expiration,
    }


class UserDataMetadata(MetadataValidator):
    """Validator for user data metadata."""

    required_fields = {
        "data_classification",
    }

    optional_fields = {
        "retention_period",
        "source",
        "session_context",
        "pii_detected",
        "content_hash",
        "access_control",
        "consent_reference",
        "data_subject_rights",
        "expiration",
        "legal_basis",
    }

    @staticmethod
    def default_data_classification() -> str:
        return PrivacyLevel.STANDARD.value

    @staticmethod
    def default_pii_detected() -> bool:
        return False

    @staticmethod
    def default_retention_period() -> int:
        """Default retention period in days."""
        return 90

    @staticmethod
    def validate_data_classification(value: str) -> str:
        """Validate data classification."""
        try:
            return PrivacyLevel(value).value
        except ValueError:
            valid_levels = [l.value for l in PrivacyLevel]
            raise ValueError(f"Invalid privacy level: {value}. Must be one of: {', '.join(valid_levels)}")

    @staticmethod
    def validate_retention_period(value: int) -> int:
        """Validate retention period."""
        if not isinstance(value, int) or value < 1:
            raise ValueError("Retention period must be a positive integer")
        return value

    @staticmethod
    def validate_content_hash(value: str) -> str:
        """Validate content hash format."""
        if not re.match(r"^[0-9a-f]{32,128}$", value):
            raise ValueError("Content hash must be a valid hash string")
        return value

    @staticmethod
    def validate_expiration(value: Union[str, datetime]) -> datetime:
        """Validate and convert expiration date."""
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                raise ValueError("Expiration must be a valid ISO format date string")
        elif isinstance(value, datetime):
            return value
        else:
            raise ValueError("Expiration must be a datetime or ISO format string")

    # Register field validators
    field_validators = {
        "data_classification": validate_data_classification,
        "retention_period": validate_retention_period,
        "content_hash": validate_content_hash,
        "expiration": validate_expiration,
    }


def validate_metadata(metadata: Dict[str, Any], validator_class: type) -> Dict[str, Any]:
    """
    Validate metadata using the specified validator class.

    Args:
        metadata: Metadata to validate
        validator_class: Validator class to use

    Returns:
        Validated metadata

    Raises:
        MetadataValidationError: If validation fails
    """
    return validator_class.validate(metadata)


def validate_dev_note_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate development note metadata.

    Args:
        metadata: Metadata to validate

    Returns:
        Validated metadata

    Raises:
        MetadataValidationError: If validation fails
    """
    return validate_metadata(metadata, DevNoteMetadata)


def validate_user_data_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate user data metadata.

    Args:
        metadata: Metadata to validate

    Returns:
        Validated metadata

    Raises:
        MetadataValidationError: If validation fails
    """
    return validate_metadata(metadata, UserDataMetadata)


def add_standard_metadata_fields(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add standard metadata fields like timestamps and system version.

    Args:
        metadata: Original metadata

    Returns:
        Enhanced metadata with standard fields
    """
    result = metadata.copy()

    # Add created timestamp if not present
    if "created_at" not in result:
        result["created_at"] = datetime.utcnow()

    # Update modified timestamp
    result["modified_at"] = datetime.utcnow()

    # Add system version if available
    try:
        from packages.shared.src.version import VERSION

        result["system_version"] = VERSION
    except ImportError:
        result["system_version"] = "unknown"

    return result
