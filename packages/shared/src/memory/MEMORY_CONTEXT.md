# Memory System Architecture

This document explains the memory system architecture for AI coding assistants and tools.

## Overview

The memory system is responsible for storing and retrieving conversation history, user preferences, and other contextual information used by the AI orchestration system. It provides a unified interface for memory operations while supporting different storage backends.

## Key Components

### MemoryManager Interface

The base interface that defines standard memory operations:
- Adding memory items
- Retrieving specific items
- Querying conversation history
- Semantic search functionality
- Storage of agent-specific data

### Implementations

1. **InMemoryMemoryManagerStub**
   - Simple in-memory implementation for development and testing
   - Stores memory items in a Python list
   - No persistence between application restarts
   - Includes basic semantic search capabilities (stub)

2. **PatrickMemoryManager**
   - Main implementation used in development
   - Extends the in-memory implementation with additional features
   - User-specific memory management
   - Advanced filtering capabilities

### Core Data Models

1. **MemoryItem**
   ```python
   class MemoryItem(BaseModel):
       id: Optional[str] = None
       user_id: str
       session_id: Optional[str] = None
       timestamp: datetime = datetime.utcnow()
       item_type: str
       persona_active: Optional[str] = None
       text_content: Optional[str] = None
       embedding: Optional[List[float]] = None
       metadata: Dict[str, Any] = {}
       expiration: Optional[datetime] = None
   ```

2. **AgentData**
   ```python
   class AgentData(BaseModel):
       id: Optional[str] = None
       agent_id: str
       timestamp: datetime = datetime.utcnow()
       data_type: str
       content: Any
       metadata: Dict[str, Any] = {}
       expiration: Optional[datetime] = None
   ```

## Key Operations

1. **Adding Memory Items**
   - New conversation turns
   - User preferences
   - System events

2. **Retrieving Conversation History**
   - By user ID
   - By session ID
   - With persona filters
   - Limiting result size

3. **Semantic Search**
   - Finding relevant past conversations
   - Context-aware responses
   - Using vector embeddings for similarity

4. **Memory Cleanup**
   - Automatic expiration of old items
   - Manual cleanup operations
   - Duplicate detection

## Future Extensions

1. **Firestore Memory Manager** (in development)
   - Cloud-based persistent storage
   - Scalable for production use

2. **Vector Database Integration**
   - Enhanced semantic search capabilities
   - Efficient storage of embeddings

3. **Multi-user Memory Isolation**
   - Enhanced privacy features
   - User-specific memory spaces

## Implementation Patterns

When working with the memory system:

1. Use the `get_memory_manager()` function to obtain the appropriate memory manager instance
2. Always check for initialization before operations
3. Handle potential memory retrieval failures gracefully
4. Set appropriate expiration times for temporary data
5. Use content hashing to avoid storing duplicates