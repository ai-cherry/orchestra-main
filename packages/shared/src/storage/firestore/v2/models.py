"""
Model utilities for Firestore storage in the AI Orchestration System.

This module provides utilities for converting between domain models
and Firestore document data, as well as other model-related operations.
"""

import hashlib
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, cast

try:
    from packages.shared.src.models.base_models import MemoryItem, AgentData, PersonaConfig
except ImportError:
    # For testing/standalone usage
    class MemoryItem:
        """Stub class for MemoryItem when actual models aren't available."""
        pass
        
    class AgentData:
        """Stub class for AgentData when actual models aren't available."""
        pass
        
    class PersonaConfig:
        """Stub class for PersonaConfig when actual models aren't available."""
        pass

from packages.shared.src.storage.firestore.constants import (
    ID_FIELD, USER_ID_FIELD, AGENT_ID_FIELD, SESSION_ID_FIELD,
    TIMESTAMP_FIELD, ITEM_TYPE_FIELD, PERSONA_FIELD, CONTENT_FIELD,
    EMBEDDING_FIELD, METADATA_FIELD, EXPIRATION_FIELD, CONTENT_HASH_FIELD
)


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID for a document.
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        A unique ID string
    """
    # Generate a UUID
    unique_id = str(uuid.uuid4())
    
    # Add prefix if provided
    if prefix:
        return f"{prefix}_{unique_id}"
    
    return unique_id


def compute_content_hash(content: str) -> str:
    """
    Compute a hash of the content for deduplication.
    
    Args:
        content: Content to hash
        
    Returns:
        SHA-256 hash of the content
    """
    # Create a SHA-256 hash
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def memory_item_to_document(item: MemoryItem) -> Dict[str, Any]:
    """
    Convert a MemoryItem to a Firestore document.
    
    Args:
        item: The MemoryItem to convert
        
    Returns:
        Dictionary representation for Firestore
    """
    # Generate ID if not provided
    doc_id = item.id or generate_id("mem")
    
    # Get basic properties
    doc = {
        ID_FIELD: doc_id,
        USER_ID_FIELD: item.user_id,
        ITEM_TYPE_FIELD: item.item_type or "message",
        TIMESTAMP_FIELD: item.timestamp or datetime.utcnow(),
        METADATA_FIELD: dict(item.metadata) if item.metadata else {},
    }
    
    # Add optional properties if they exist
    if item.session_id:
        doc[SESSION_ID_FIELD] = item.session_id
    
    if item.persona_active:
        doc[PERSONA_FIELD] = item.persona_active
        
    if item.text_content:
        doc[CONTENT_FIELD] = item.text_content
        # Compute content hash if content exists
        doc[METADATA_FIELD][CONTENT_HASH_FIELD] = compute_content_hash(item.text_content)
        
    if item.embedding:
        doc[EMBEDDING_FIELD] = item.embedding
        
    if item.expiration:
        doc[EXPIRATION_FIELD] = item.expiration
        
    return doc


def document_to_memory_item(doc: Dict[str, Any]) -> MemoryItem:
    """
    Convert a Firestore document to a MemoryItem.
    
    Args:
        doc: The document data from Firestore
        
    Returns:
        A MemoryItem instance
    """
    # Extract metadata (if any)
    metadata = dict(doc.get(METADATA_FIELD, {}))
    
    # Create MemoryItem
    return MemoryItem(
        id=doc.get(ID_FIELD),
        user_id=doc.get(USER_ID_FIELD),
        session_id=doc.get(SESSION_ID_FIELD),
        timestamp=doc.get(TIMESTAMP_FIELD),
        item_type=doc.get(ITEM_TYPE_FIELD, "message"),
        persona_active=doc.get(PERSONA_FIELD),
        text_content=doc.get(CONTENT_FIELD),
        embedding=doc.get(EMBEDDING_FIELD),
        metadata=metadata,
        expiration=doc.get(EXPIRATION_FIELD)
    )


def agent_data_to_document(data: AgentData) -> Dict[str, Any]:
    """
    Convert AgentData to a Firestore document.
    
    Args:
        data: The AgentData to convert
        
    Returns:
        Dictionary representation for Firestore
    """
    # Generate ID if not provided
    doc_id = data.id or generate_id("agent")
    
    # Get basic properties
    doc = {
        ID_FIELD: doc_id,
        AGENT_ID_FIELD: data.agent_id,
        "data_type": data.data_type,
        "content": data.content,
        TIMESTAMP_FIELD: data.timestamp or datetime.utcnow(),
        METADATA_FIELD: dict(data.metadata) if data.metadata else {},
    }
    
    return doc


def document_to_agent_data(doc: Dict[str, Any]) -> AgentData:
    """
    Convert a Firestore document to AgentData.
    
    Args:
        doc: The document data from Firestore
        
    Returns:
        An AgentData instance
    """
    # Create AgentData
    return AgentData(
        id=doc.get(ID_FIELD),
        agent_id=doc.get(AGENT_ID_FIELD),
        data_type=doc.get("data_type", "log"),
        content=doc.get("content"),
        timestamp=doc.get(TIMESTAMP_FIELD),
        metadata=doc.get(METADATA_FIELD, {})
    )
