"""
Agent Communication Protocol for AI Orchestration System.

This module defines the standard message formats and protocols for
agent communication in the AI Orchestra system.
"""

import time
import uuid
from enum import Enum
from typing import Any, Dict, Optional, Union

# Handle both pydantic v1 and v2
try:
    from pydantic.v1 import BaseModel, Field  # For pydantic v2
except ImportError:
    from pydantic import BaseModel, Field  # For pydantic v1


class MessageType(str, Enum):
    """Types of messages in the agent communication protocol"""

    QUERY = "query"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    STATUS = "status"
    ERROR = "error"
    TASK = "task"
    RESULT = "result"
    MEMORY = "memory"
    WORKFLOW = "workflow"


class AgentQuery(BaseModel):
    """Query from one agent to another"""

    query: str
    context: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Response to a query"""

    response: str
    confidence: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentNotification(BaseModel):
    """Notification message"""

    notification_type: str
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentStatus(BaseModel):
    """Status update from an agent"""

    status: str
    details: Dict[str, Any] = Field(default_factory=dict)


class AgentError(BaseModel):
    """Error message"""

    error_type: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class AgentTask(BaseModel):
    """Task assignment"""

    task_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    deadline: Optional[float] = None


class AgentResult(BaseModel):
    """Task result"""

    result: Dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


class MemoryOperation(BaseModel):
    """Memory operation"""

    operation: str  # "store", "retrieve", "update", "delete"
    key: str
    value: Optional[Any] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowEvent(BaseModel):
    """Workflow state change event"""

    workflow_id: str
    state: str
    transition: str
    data: Dict[str, Any] = Field(default_factory=dict)


# Type for message content
MessageContent = Union[
    AgentQuery,
    AgentResponse,
    AgentNotification,
    AgentStatus,
    AgentError,
    AgentTask,
    AgentResult,
    MemoryOperation,
    WorkflowEvent,
]


def create_protocol_message(
    sender: str,
    recipient: Optional[str],
    content: MessageContent,
    message_type: Optional[str] = None,
    conversation_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    ttl: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create a standardized protocol message.

    Args:
        sender: The sender agent ID
        recipient: The recipient agent ID or None for broadcast
        content: The message content
        message_type: Optional message type (inferred from content if not provided)
        conversation_id: Optional conversation ID
        correlation_id: Optional correlation ID for related messages
        ttl: Optional time-to-live in seconds

    Returns:
        A dictionary representing the protocol message
    """
    # Infer message type from content if not provided
    if message_type is None:
        if isinstance(content, AgentQuery):
            message_type = MessageType.QUERY
        elif isinstance(content, AgentResponse):
            message_type = MessageType.RESPONSE
        elif isinstance(content, AgentNotification):
            message_type = MessageType.NOTIFICATION
        elif isinstance(content, AgentStatus):
            message_type = MessageType.STATUS
        elif isinstance(content, AgentError):
            message_type = MessageType.ERROR
        elif isinstance(content, AgentTask):
            message_type = MessageType.TASK
        elif isinstance(content, AgentResult):
            message_type = MessageType.RESULT
        elif isinstance(content, MemoryOperation):
            message_type = MessageType.MEMORY
        elif isinstance(content, WorkflowEvent):
            message_type = MessageType.WORKFLOW
        else:
            raise ValueError(f"Unknown content type: {type(content)}")

    # Create message ID if needed
    message_id = str(uuid.uuid4())

    # Create conversation ID if needed
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())

    # Create the message
    return {
        "message_id": message_id,
        "sender_id": sender,
        "recipient_id": recipient,
        "message_type": message_type,
        "content": content.dict(),
        "conversation_id": conversation_id,
        "correlation_id": correlation_id,
        "timestamp": time.time(),
        "ttl": ttl,
    }


def validate_protocol_message(message: Dict[str, Any]) -> bool:
    """
    Validate a protocol message.

    Args:
        message: The message to validate

    Returns:
        True if the message is valid

    Raises:
        ValueError: If the message is invalid
    """
    required_fields = ["message_id", "sender_id", "message_type", "content"]

    # Check required fields
    for field in required_fields:
        if field not in message:
            raise ValueError(f"Missing required field: {field}")

    # Check message type
    if message["message_type"] not in [e.value for e in MessageType]:
        raise ValueError(f"Invalid message type: {message['message_type']}")

    # Validate content based on message type
    content = message["content"]
    message_type = message["message_type"]

    if message_type == MessageType.QUERY:
        AgentQuery(**content)
    elif message_type == MessageType.RESPONSE:
        AgentResponse(**content)
    elif message_type == MessageType.NOTIFICATION:
        AgentNotification(**content)
    elif message_type == MessageType.STATUS:
        AgentStatus(**content)
    elif message_type == MessageType.ERROR:
        AgentError(**content)
    elif message_type == MessageType.TASK:
        AgentTask(**content)
    elif message_type == MessageType.RESULT:
        AgentResult(**content)
    elif message_type == MessageType.MEMORY:
        MemoryOperation(**content)
    elif message_type == MessageType.WORKFLOW:
        WorkflowEvent(**content)

    return True
