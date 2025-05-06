"""
Constants for Firestore storage adapters in the AI Orchestration System.

This module defines constants used by the Firestore storage adapters,
such as collection names, field names, and query limitations.
"""

# Collection names
MEMORY_ITEMS_COLLECTION = "memory_items"
AGENT_DATA_COLLECTION = "agent_data"
USER_SESSIONS_COLLECTION = "user_sessions"
VECTOR_EMBEDDINGS_COLLECTION = "vector_embeddings"

# Field names
ID_FIELD = "id"
USER_ID_FIELD = "user_id"
AGENT_ID_FIELD = "agent_id"
SESSION_ID_FIELD = "session_id"
TIMESTAMP_FIELD = "timestamp"
ITEM_TYPE_FIELD = "item_type"
PERSONA_FIELD = "persona_active"
CONTENT_FIELD = "text_content"
EMBEDDING_FIELD = "embedding"
METADATA_FIELD = "metadata"
EXPIRATION_FIELD = "expiration"

# Special fields
CONTENT_HASH_FIELD = "content_hash"
EMBEDDING_DIM_FIELD = "embedding_dim"

# Query limitations
MAX_BATCH_SIZE = 400  # Firestore limit is 500, but we use a lower number for safety
MAX_IN_QUERY_ITEMS = 10  # Firestore has a limit on 'in' queries
