# TODO: Consider adding connection pooling configuration
"""
Orchestra AI - Database Models
This module contains Pydantic models for database entities.
"""

from typing import List, Dict, Any, Optional, Union
from uuid import uuid4, UUID
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator

""
    """Exception raised when metadata validation fails."""
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
        """
        """
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

                        pass
                        validated_metadata[field] = cls.field_validators[field](value)
                    except Exception:

                        pass
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
        """Validate data classification."""
            raise ValueError(f"Invalid privacy level: {value}. Must be one of: {', '.join(valid_levels)}")

    @staticmethod
    def validate_retention_period(value: int) -> int:
        """Validate retention period."""
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
    """
    """
    """
    """
    """
    """
    """
    if "created_at" not in result:
        result["created_at"] = datetime.utcnow()

    # Update modified timestamp
    result["modified_at"] = datetime.utcnow()

    # Add system version if available
    try:

        pass
        from packages.shared.src.version import VERSION

        result["system_version"] = VERSION
    except Exception:

        pass
        result["system_version"] = "unknown"

    return result
