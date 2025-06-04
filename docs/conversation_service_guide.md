# Conversation Service Guide

## Overview

The ConversationService is a core component of the AI coordination System, providing a modern, asynchronous API for managing conversations. This service handles the entire conversation lifecycle including starting sessions, recording messages, tracking state, and retrieving history.

## Key Features

- **Asynchronous Operations**: All memory and event operations use non-blocking async/await patterns
- **Persistent Storage**: Conversations and messages are persisted via the MemoryManager
- **Event-Driven**: All operations emit events for system-wide reactivity
- **Session Management**: Tracks active conversation sessions for users with turn counting

## Architecture

The ConversationService follows these architectural principles:

- **Modern Async Patterns**: Uses Python's async/await for all I/O operations
- **Dependency Injection**: Dependencies are injected via factory functions
- **Event-Driven Design**: Key lifecycle events are published via the EventBus
- **Stateful Tracking**: Maintains in-memory state for active conversations

## Usage in FastAPI Applications

### Starting a Conversation

```python
from fastapi import APIRouter
from core.conductor.src.services.conversation_service import get_conversation_service

router = APIRouter()

@router.post("/start")
async def start_conversation_endpoint(user_id: str, persona_name: str = None):
    conversation_service = get_conversation_service()
    session_id = await conversation_service.start_conversation(
        user_id=user_id,
        persona_name=persona_name
    )
    return {"session_id": session_id}
```

### Recording Messages

```python
@router.post("/messages")
async def add_message_endpoint(
    user_id: str,
    session_id: str,
    message: str,
    is_user: bool = True,
    metadata: dict = None
):
    conversation_service = get_conversation_service()
    message_id = await conversation_service.record_message(
        user_id=user_id,
        content=message,
        is_user=is_user,
        metadata=metadata,
        session_id=session_id
    )
    return {"message_id": message_id}
```

### Retrieving Conversation History

```python
@router.get("/history")
async def get_history_endpoint(
    user_id: str,
    session_id: str,
    limit: int = 20
):
    conversation_service = get_conversation_service()
    history = await conversation_service.get_conversation_history(
        user_id=user_id,
        session_id=session_id,
        limit=limit
    )
    return history
```

## API Reference

### Methods

#### `async start_conversation(user_id: str, persona_name: Optional[str] = None) -> str`

Starts a new conversation session for the specified user.

- **Parameters**:
  - `user_id`: String identifier for the user
  - `persona_name`: Optional name of the persona to activate
- **Returns**: A string session ID for the new conversation
- **Events Published**: `conversation_started`

#### `async end_conversation(user_id: str, session_id: Optional[str] = None) -> bool`

Ends an active conversation session.

- **Parameters**:
  - `user_id`: String identifier for the user
  - `session_id`: Optional specific session ID to end (uses active if not provided)
- **Returns**: Boolean indicating success
- **Events Published**: `conversation_ended`

#### `async record_message(user_id: str, content: str, is_user: bool, metadata: Optional[Dict[str, Any]] = None, session_id: Optional[str] = None) -> str`

Records a message in the conversation.

- **Parameters**:
  - `user_id`: String identifier for the user
  - `content`: The message content text
  - `is_user`: Boolean flag indicating if this is a user message (True) or AI message (False)
  - `metadata`: Optional dictionary of metadata
  - `session_id`: Optional specific session ID (uses active if not provided)
- **Returns**: String ID of the recorded message
- **Events Published**: `conversation_message_added`

#### `async get_conversation_history(user_id: str, session_id: Optional[str] = None, limit: int = 20, persona_name: Optional[str] = None) -> List[Dict[str, Any]]`

Retrieves formatted conversation history.

- **Parameters**:
  - `user_id`: String identifier for the user
  - `session_id`: Optional specific session ID (uses active if not provided)
  - `limit`: Maximum number of messages to retrieve
  - `persona_name`: Optional persona name to filter by
- **Returns**: List of formatted message dictionaries

#### `get_active_conversation(user_id: str) -> Optional[ConversationState]`

Gets the currently active conversation for a user.

- **Parameters**:
  - `user_id`: String identifier for the user
- **Returns**: ConversationState object or None if no active conversation

#### `async add_memory_item_async(item: MemoryItem) -> str`

Low-level method to directly add a memory item.

- **Parameters**:
  - `item`: A MemoryItem object
- **Returns**: String ID of the added memory item

## REST API Endpoints

The ConversationService is exposed through FastAPI endpoints at `/api/conversations/`:

- `POST /api/conversations/start` - Start a new conversation
- `POST /api/conversations/{session_id}/end` - End an existing conversation
- `POST /api/conversations/{session_id}/messages` - Add a message
- `GET /api/conversations/{session_id}/history` - Get conversation history
- `GET /api/conversations/active` - Get the user's currently active conversation

See the OpenAPI documentation at `/api/docs` for full details on request/response formats.

## Testing

The ConversationService has a comprehensive test suite using pytest-asyncio. Run tests with:

```bash
cd /workspaces/cherry_ai-main
pytest tests/core/conductor/services/test_conversation_service.py -v
```

## Best Practices

1. **Always use await**: All methods that interact with memory or events are asynchronous.

2. **Error handling**: All service methods include error handling, but API endpoints should add their own error handling as well.

3. **Session tracking**: Use the `get_active_conversation` method to determine if a user has an active session.

4. **Event subscription**: Consider subscribing to conversation events to extend functionality.

## Migration from Older APIs

If you're migrating from older conversation handling code:

1. Replace direct memory storage with `record_message()`
2. Use proper session start/end for better conversation lifecycle management
3. Ensure all callers use async/await syntax
