"""
AI Persona Collaboration Framework for Orchestra AI

This module implements a structured dialogue system that enables Cherry, Sophia, and Karen personas
to collaborate on complex tasks by sharing context, exchanging insights, and building on each other's work.
"""

from typing import Dict, List, Optional, Any, Tuple
import uuid
from datetime import datetime
from enum import Enum

class PersonaType(str, Enum):
    CHERRY = "cherry"
    SOPHIA = "sophia"
    KAREN = "karen"

class CollaborationRole(str, Enum):
    LEAD = "lead"
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"

class HandoffType(str, Enum):
    QUESTION = "question"
    REFINEMENT = "refinement"
    EXPANSION = "expansion"
    CRITIQUE = "critique"
    VERIFICATION = "verification"

class CollaborationMessage:
    """Represents a message in the collaboration dialogue."""
    
    def __init__(
        self,
        content: str,
        persona: PersonaType,
        message_type: str = "contribution",
        references: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        self.id = str(uuid.uuid4())
        self.content = content
        self.persona = persona
        self.message_type = message_type
        self.references = references or []
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary representation."""
        return {
            "id": self.id,
            "content": self.content,
            "persona": self.persona,
            "message_type": self.message_type,
            "references": self.references,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollaborationMessage':
        """Create message from dictionary representation."""
        message = cls(
            content=data["content"],
            persona=data["persona"],
            message_type=data["message_type"],
            references=data["references"],
            metadata=data["metadata"]
        )
        message.id = data["id"]
        message.timestamp = data["timestamp"]
        return message

class CollaborationSession:
    """Manages a collaboration session between multiple AI personas."""
    
    def __init__(
        self,
        task_description: str,
        primary_persona: PersonaType,
        session_id: Optional[str] = None
    ):
        self.session_id = session_id or str(uuid.uuid4())
        self.task_description = task_description
        self.primary_persona = primary_persona
        self.messages: List[CollaborationMessage] = []
        self.persona_roles: Dict[PersonaType, CollaborationRole] = {
            primary_persona: CollaborationRole.LEAD
        }
        self.shared_context: Dict[str, Any] = {}
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.status = "active"
    
    def add_message(self, message: CollaborationMessage) -> str:
        """Add a message to the collaboration session."""
        self.messages.append(message)
        self.updated_at = datetime.now().isoformat()
        return message.id
    
    def get_messages(self, persona: Optional[PersonaType] = None) -> List[CollaborationMessage]:
        """Get all messages, optionally filtered by persona."""
        if persona:
            return [m for m in self.messages if m.persona == persona]
        return self.messages
    
    def assign_role(self, persona: PersonaType, role: CollaborationRole) -> None:
        """Assign a role to a persona in this collaboration."""
        self.persona_roles[persona] = role
    
    def get_role(self, persona: PersonaType) -> CollaborationRole:
        """Get the role assigned to a persona."""
        return self.persona_roles.get(persona, CollaborationRole.CONTRIBUTOR)
    
    def update_shared_context(self, key: str, value: Any) -> None:
        """Update a value in the shared context."""
        self.shared_context[key] = value
        self.updated_at = datetime.now().isoformat()
    
    def get_shared_context(self, key: Optional[str] = None) -> Any:
        """Get a value or all values from the shared context."""
        if key:
            return self.shared_context.get(key)
        return self.shared_context
    
    def create_handoff(
        self,
        from_persona: PersonaType,
        to_persona: PersonaType,
        handoff_type: HandoffType,
        content: str,
        context_keys: List[str] = None
    ) -> str:
        """Create a handoff from one persona to another."""
        # Prepare relevant context for the handoff
        handoff_context = {}
        if context_keys:
            for key in context_keys:
                if key in self.shared_context:
                    handoff_context[key] = self.shared_context[key]
        
        # Create the handoff message
        handoff_message = CollaborationMessage(
            content=content,
            persona=from_persona,
            message_type="handoff",
            metadata={
                "handoff_type": handoff_type,
                "to_persona": to_persona,
                "context": handoff_context
            }
        )
        
        return self.add_message(handoff_message)
    
    def respond_to_handoff(
        self,
        handoff_message_id: str,
        responding_persona: PersonaType,
        content: str
    ) -> str:
        """Respond to a handoff message."""
        # Find the original handoff message
        handoff_message = next((m for m in self.messages if m.id == handoff_message_id), None)
        if not handoff_message or handoff_message.message_type != "handoff":
            raise ValueError(f"Invalid handoff message ID: {handoff_message_id}")
        
        # Verify the responding persona is the intended recipient
        if handoff_message.metadata.get("to_persona") != responding_persona:
            raise ValueError(
                f"Persona {responding_persona} is not the intended recipient of this handoff"
            )
        
        # Create the response message
        response_message = CollaborationMessage(
            content=content,
            persona=responding_persona,
            message_type="handoff_response",
            references=[handoff_message_id],
            metadata={
                "handoff_type": handoff_message.metadata.get("handoff_type"),
                "from_persona": handoff_message.persona
            }
        )
        
        return self.add_message(response_message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary representation."""
        return {
            "session_id": self.session_id,
            "task_description": self.task_description,
            "primary_persona": self.primary_persona,
            "messages": [m.to_dict() for m in self.messages],
            "persona_roles": {k.value: v.value for k, v in self.persona_roles.items()},
            "shared_context": self.shared_context,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollaborationSession':
        """Create session from dictionary representation."""
        session = cls(
            task_description=data["task_description"],
            primary_persona=data["primary_persona"],
            session_id=data["session_id"]
        )
        session.messages = [CollaborationMessage.from_dict(m) for m in data["messages"]]
        session.persona_roles = {
            PersonaType(k): CollaborationRole(v) for k, v in data["persona_roles"].items()
        }
        session.shared_context = data["shared_context"]
        session.created_at = data["created_at"]
        session.updated_at = data["updated_at"]
        session.status = data["status"]
        return session

class CollaborationManager:
    """Manages collaboration sessions between AI personas."""
    
    def __init__(self):
        self.sessions: Dict[str, CollaborationSession] = {}
    
    def create_session(
        self,
        task_description: str,
        primary_persona: PersonaType
    ) -> CollaborationSession:
        """Create a new collaboration session."""
        session = CollaborationSession(task_description, primary_persona)
        self.sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """Get a collaboration session by ID."""
        return self.sessions.get(session_id)
    
    def list_sessions(self, status: Optional[str] = None) -> List[CollaborationSession]:
        """List all collaboration sessions, optionally filtered by status."""
        if status:
            return [s for s in self.sessions.values() if s.status == status]
        return list(self.sessions.values())
    
    def close_session(self, session_id: str) -> bool:
        """Close a collaboration session."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.status = "closed"
        session.updated_at = datetime.now().isoformat()
        return True
    
    def get_persona_sessions(self, persona: PersonaType) -> List[CollaborationSession]:
        """Get all sessions involving a specific persona."""
        return [
            s for s in self.sessions.values()
            if persona in s.persona_roles
        ]
    
    def get_active_handoffs(self, to_persona: PersonaType) -> List[Tuple[CollaborationSession, CollaborationMessage]]:
        """Get all active handoffs directed to a specific persona."""
        active_handoffs = []
        
        for session in self.sessions.values():
            if session.status != "active":
                continue
            
            # Find handoff messages to this persona that don't have responses
            handoff_messages = [
                m for m in session.messages
                if m.message_type == "handoff" and m.metadata.get("to_persona") == to_persona
            ]
            
            # Check which handoffs don't have responses
            for handoff in handoff_messages:
                has_response = any(
                    m.message_type == "handoff_response" and handoff.id in m.references
                    for m in session.messages
                )
                
                if not has_response:
                    active_handoffs.append((session, handoff))
        
        return active_handoffs
