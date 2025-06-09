# AI Persona Collaboration Framework

## Overview

The AI Persona Collaboration Framework enables Cherry, Sophia, and Karen personas to collaborate on complex tasks through a structured dialogue system. This framework allows multiple AI personas to be assigned to different aspects of a task, exchange insights, and build on each other's work.

## Key Components

### 1. Collaboration Session

A collaboration session represents a task that multiple personas are working on together. Each session has:

- A unique session ID
- A task description
- A primary persona (lead)
- A collection of messages exchanged between personas
- Role assignments for each participating persona
- Shared context that all personas can access and update

### 2. Persona Roles

The framework defines three distinct roles that personas can take in a collaboration:

- **Lead**: The primary persona responsible for the overall task
- **Contributor**: Personas that provide input on specific aspects of the task
- **Reviewer**: Personas that evaluate and provide feedback on the work

### 3. Handoff Mechanism

The handoff feature allows one persona to explicitly request assistance from another with specific context. Types of handoffs include:

- **Question**: Requesting information or clarification
- **Refinement**: Asking for improvements to existing work
- **Expansion**: Requesting additional content or exploration
- **Critique**: Asking for critical evaluation
- **Verification**: Requesting fact-checking or validation

### 4. Shared Context Layer

The shared context allows personas to exchange information and build on each other's work. This includes:

- Key-value pairs for structured data
- References to previous messages
- Metadata about the collaboration

## Implementation Details

The framework is implemented in `src/personas/collaboration_framework.py` with the following key classes:

### CollaborationMessage

Represents a message in the collaboration dialogue:

```python
class CollaborationMessage:
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
```

### CollaborationSession

Manages a collaboration session between multiple AI personas:

```python
class CollaborationSession:
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
```

### CollaborationManager

Manages multiple collaboration sessions:

```python
class CollaborationManager:
    def __init__(self):
        self.sessions: Dict[str, CollaborationSession] = {}
    
    def create_session(
        self,
        task_description: str,
        primary_persona: PersonaType
    ) -> CollaborationSession:
        session = CollaborationSession(task_description, primary_persona)
        self.sessions[session.session_id] = session
        return session
```

## Usage Examples

### Creating a Collaboration Session

```python
from personas.collaboration_framework import CollaborationManager, PersonaType

# Initialize the collaboration manager
manager = CollaborationManager()

# Create a new collaboration session with Cherry as the lead
session = manager.create_session(
    task_description="Research and summarize recent advancements in quantum computing",
    primary_persona=PersonaType.CHERRY
)

# Assign roles to other personas
session.assign_role(PersonaType.SOPHIA, CollaborationRole.CONTRIBUTOR)
session.assign_role(PersonaType.KAREN, CollaborationRole.REVIEWER)
```

### Creating a Handoff Between Personas

```python
# Cherry creates a handoff to Sophia for expansion on a technical topic
handoff_id = session.create_handoff(
    from_persona=PersonaType.CHERRY,
    to_persona=PersonaType.SOPHIA,
    handoff_type=HandoffType.EXPANSION,
    content="Could you expand on the technical details of quantum entanglement?",
    context_keys=["quantum_computing_basics", "current_research"]
)

# Sophia responds to the handoff
response_id = session.respond_to_handoff(
    handoff_message_id=handoff_id,
    responding_persona=PersonaType.SOPHIA,
    content="Quantum entanglement is a phenomenon where two particles become correlated..."
)
```

### Updating Shared Context

```python
# Add information to the shared context
session.update_shared_context(
    "quantum_computing_basics",
    {
        "qubits": "Quantum bits that can exist in superposition",
        "gates": "Operations that manipulate quantum states",
        "measurement": "Process of observing quantum states"
    }
)

# Retrieve information from the shared context
basics = session.get_shared_context("quantum_computing_basics")
```

## Benefits

1. **Leverages Unique Strengths**: Each persona contributes based on their specialized knowledge and communication style
2. **Creates Comprehensive Responses**: Combines multiple perspectives for more nuanced outputs
3. **Structured Collaboration**: Provides a framework for organized multi-persona interactions
4. **Traceable Contributions**: Maintains a record of which persona contributed what information
5. **Flexible Role Assignment**: Allows personas to take different roles based on the task requirements

## Integration with Persona Manager

The Collaboration Framework integrates with the existing Persona Manager (`src/personas/persona_manager.py`) to access persona instances and their capabilities. This allows for seamless collaboration while maintaining the distinct characteristics of each persona.
