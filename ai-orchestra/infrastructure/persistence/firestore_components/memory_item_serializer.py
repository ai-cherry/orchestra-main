"""
Handles serialization and deserialization of MemoryItem objects to and from
Firestore-compatible dictionaries.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from packages.shared.src.models.base_models import MemoryItem

# Using a standard logger for now
logger = logging.getLogger(__name__)

class MemoryItemSerializer:
    """
    Serializes MemoryItem objects to Firestore-compatible dicts and vice-versa.
    """

    def __init__(self):
        logger.info("MemoryItemSerializer initialized.")

    def to_firestore(self, memory_item: MemoryItem) -> Dict[str, Any]:
        """
        Converts a MemoryItem object into a dictionary suitable for Firestore storage.

        Args:
            memory_item: The MemoryItem object to serialize.

        Returns:
            A dictionary representation of the MemoryItem.
        
        Raises:
            TypeError: If the memory_item is not of the expected type.
            ValueError: If essential fields are missing or invalid.
        """
        if not isinstance(memory_item, MemoryItem):
            raise TypeError(f"Expected MemoryItem, got {type(memory_item)}")

        data: Dict[str, Any] = {
            "id": memory_item.id,
            "content": self._serialize_value(memory_item.content),
            "source": memory_item.source,
            "timestamp": memory_item.timestamp,
            "metadata": memory_item.metadata if memory_item.metadata is not None else {},
            "tags": memory_item.tags if memory_item.tags is not None else [],
            "relationships": memory_item.relationships if memory_item.relationships is not None else {},
            "created_at": self._ensure_utc(memory_item.created_at) if memory_item.created_at else None,
            "updated_at": self._ensure_utc(memory_item.updated_at) if memory_item.updated_at else None,
            "expiry": self._ensure_utc(memory_item.expiry) if memory_item.expiry else None,
            "priority": memory_item.priority,
            "embedding": memory_item.embedding,
        }

        logger.debug(f"Serialized MemoryItem '{memory_item.id}' to Firestore dict.")
        return data

    def to_memory_item(self, item_id: str, firestore_data: Dict[str, Any]) -> MemoryItem:
        """
        Converts a dictionary from Firestore into a MemoryItem object.

        Args:
            item_id: The ID of the item (typically the document ID from Firestore snapshot.id).
            firestore_data: The dictionary data retrieved from Firestore (from snapshot.to_dict()).

        Returns:
            A MemoryItem object.

        Raises:
            TypeError: If firestore_data is not a dictionary.
            ValueError: If required fields are missing or data is malformed.
        """
        if not isinstance(firestore_data, dict):
            raise TypeError(f"Expected dict for firestore_data, got {type(firestore_data)}")
        
        # Ensure item_id is present, either passed in or from the data itself
        actual_item_id = item_id or firestore_data.get("id")
        if not actual_item_id:
            raise ValueError("Item ID (key) is missing or not provided.")

        created_at = firestore_data.get("created_at")
        updated_at = firestore_data.get("updated_at")
        expiry = firestore_data.get("expiry")

        memory_item_data = {
            "id": actual_item_id,
            "content": self._deserialize_value(firestore_data.get("content")),
            "source": firestore_data.get("source", "unknown"),
            "timestamp": firestore_data.get("timestamp"),
            "metadata": firestore_data.get("metadata", {}),
            "tags": firestore_data.get("tags", []),
            "relationships": firestore_data.get("relationships", {}),
            "created_at": self._to_datetime(created_at) if created_at else None,
            "updated_at": self._to_datetime(updated_at) if updated_at else None,
            "expiry": self._to_datetime(expiry) if expiry else None,
            "priority": firestore_data.get("priority", 0.5),
            "embedding": firestore_data.get("embedding"),
        }
        
        try:
            item = MemoryItem(**memory_item_data)
            logger.debug(f"Deserialized Firestore dict to MemoryItem '{actual_item_id}'.")
            return item
        except Exception as e: # Catch Pydantic validation errors or others
            logger.error(f"Error deserializing MemoryItem '{actual_item_id}': {e}", exc_info=True)
            raise ValueError(f"Malformed data for MemoryItem '{actual_item_id}': {e}") from e

    def _serialize_value(self, value: Any) -> Any:
        """
        Handles special serialization for the 'value' field if necessary.
        """
        # TODO: Implement custom serialization if memory_item.value can be complex types
        # e.g., other Pydantic models, custom objects not directly storable in Firestore.
        # if isinstance(value, BaseModel):
        #     return value.model_dump(mode="json")
        return value

    def _deserialize_value(self, value: Any) -> Any:
        """
        Handles special deserialization for the 'value' field if necessary.
        """
        # TODO: Implement custom deserialization if memory_item.value needs it.
        # e.g., if complex types were stored as JSON strings or structured dicts.
        return value

    def _ensure_utc(self, dt: datetime) -> datetime:
        """Ensures a datetime object is timezone-aware and in UTC."""
        if not isinstance(dt, datetime):
            logger.warning(f"_ensure_utc expected datetime, got {type(dt)}. Returning as is.")
            return dt # Or raise TypeError
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _to_datetime(self, value: Any) -> Optional[datetime]:
        """
        Converts a value to a datetime object, ensuring UTC.
        Handles Firestore Timestamps (which client lib converts to datetime) and ISO strings.
        """
        if isinstance(value, datetime):
            return self._ensure_utc(value)
        if isinstance(value, str):
            try:
                # Attempt to parse ISO format, including potential Z for UTC
                dt_str = value.upper().replace("Z", "+00:00")
                dt = datetime.fromisoformat(dt_str)
                return self._ensure_utc(dt)
            except ValueError:
                logger.warning(f"Could not parse date string '{value}' to datetime.")
                return None
        
        # Handle direct google.cloud.firestore.SERVER_TIMESTAMP (though client usually converts)
        # This check is a bit indirect as SERVER_TIMESTAMP is a sentinel object.
        if hasattr(value, '__class__') and 'SERVER_TIMESTAMP' in str(value.__class__):
             logger.debug("Encountered Firestore SERVER_TIMESTAMP. Will be set by server.")
             return None # Or a placeholder indicating server will set it
        
        if value is not None:
            logger.warning(f"Unsupported type for datetime conversion: {type(value)}. Value: {value}")
        return None