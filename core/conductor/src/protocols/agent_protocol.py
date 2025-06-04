"""
"""
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
    """Response to a query"""
    """Notification message"""
    """Status update from an agent"""
    """Error message"""
    """Task assignment"""
    """Task result"""
    """Memory operation"""
    operation: str  # "store", "retrieve", "update", "delete"
    key: str
    value: Optional[Any] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WorkflowEvent(BaseModel):
    """Workflow state change event"""
    """
    """
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
