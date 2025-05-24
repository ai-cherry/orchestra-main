# Roo-MCP Integration Guide

This guide provides comprehensive documentation for the integration between Roo modes and the MCP (Model Context Protocol) working memory system in the AI Orchestra project.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Setup](#setup)
5. [Usage Examples](#usage-examples)
6. [Performance Optimization](#performance-optimization)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)

## Overview

The Roo-MCP integration enables seamless communication between different Roo modes (Code, Architect, Debug, etc.) and the MCP working memory system. This integration allows for:

- Context preservation across mode transitions
- Efficient memory access patterns
- Rule-based constraints on operations
- Complex multi-mode operations through the "Boomerang" pattern

By leveraging this integration, AI agents can maintain context and state across different operational modes, leading to more coherent and effective interactions.

## Architecture

The integration follows a modular architecture with clear separation of concerns:

```
mcp_server/
├── roo/
│   ├── modes.py           # Mode definitions
│   ├── transitions.py     # Mode transition logic
│   ├── memory_hooks.py    # Memory integration points
│   ├── rules.py           # Rule configurations
│   └── adapters/
│       ├── gemini_adapter.py  # Gemini-specific adapter
│       └── ...                # Other adapters
```

### Key Architectural Patterns

1. **Adapter Pattern**: Model-specific adapters that translate between the model's API and the Roo-MCP integration
2. **Strategy Pattern**: Different memory access strategies based on the mode and operation
3. **Observer Pattern**: Rule engine that observes operations and enforces constraints
4. **Command Pattern**: Operations that can be executed, undone, and tracked

## Components

### Mode System

The mode system defines different operational modes for Roo, each with specific capabilities and access levels:

- **Code Mode**: For implementing features and refactoring code
- **Architect Mode**: For designing system architecture
- **Debug Mode**: For troubleshooting and debugging
- **Reviewer Mode**: For code review and quality analysis
- **Orchestrator Mode**: For coordinating complex operations
- **Strategy Mode**: For planning and strategic analysis
- **Creative Mode**: For creative content generation
- **Ask Mode**: For research and information retrieval

Each mode has:

- A unique slug (e.g., "code", "architect")
- A display name (e.g., "💻 Code", "🏗 Architect")
- A description
- A set of capabilities
- Memory access level
- Allowed transitions to other modes
- Default rules

### Transition System

The transition system manages transitions between different modes, preserving context and ensuring smooth handoffs:

- **TransitionContext**: Stores context information during transitions
- **ModeTransitionManager**: Manages the transition process

### Memory Hooks

Memory hooks provide integration points with the MCP working memory system:

- **RooMemoryManager**: Specialized memory manager for Roo operations
- **BoomerangOperation**: Implements the "Boomerang" pattern for complex operations

### Rule Engine

The rule engine defines and enforces constraints on Roo operations:

- **Rule**: Defines a constraint with conditions and actions
- **RuleEngine**: Evaluates rules against operations

### Adapters

Adapters provide model-specific implementations of the Roo-MCP integration:

- **GeminiRooAdapter**: Adapter for Gemini

## Setup

### Prerequisites

- Python 3.11 or higher
- Access to the MCP server
- Required Python packages (see `setup_roo_mcp.py`)

### Installation

1. Run the setup script:

```bash
python setup_roo_mcp.py
```

This script will:

- Check Python version compatibility
- Install required dependencies
- Set up the environment
- Verify the setup

### Configuration

The integration can be configured through environment variables:

- `MCP_SERVER_HOST`: Hostname of the MCP server (default: "localhost")
- `MCP_SERVER_PORT`: Port of the MCP server (default: 8000)
- `PYTHONPATH`: Should include the project root

## Usage Examples

### Basic Usage

```python
from mcp_server.storage.in_memory_storage import InMemoryStorage
from mcp_server.managers.standard_memory_manager import StandardMemoryManager
from mcp_server.roo.modes import get_mode
from mcp_server.roo.transitions import ModeTransitionManager
from mcp_server.roo.memory_hooks import BoomerangOperation, RooMemoryManager
from mcp_server.roo.rules import create_rule_engine
from mcp_server.roo.adapters.gemini_adapter import GeminiRooAdapter

# Set up memory system
storage = InMemoryStorage()
await storage.initialize()
memory_manager = StandardMemoryManager(storage)
await memory_manager.initialize()

# Create transition manager
transition_manager = ModeTransitionManager(memory_manager)

# Create rule engine
rule_engine = create_rule_engine()

# Create Gemini adapter
adapter = GeminiRooAdapter(memory_manager, transition_manager, rule_engine)

# Process a request in code mode
request = {
    "request_id": "req-123",
    "type": "code_review",
    "content": "Please review this code for performance issues."
}
processed_request = await adapter.process_request("code", request)

# Process a response with a mode transition
response = {
    "content": "I need to analyze the architecture. Let me switch to architect mode.",
    "mode_transition": {
        "target_mode": "architect",
        "reason": "Need to analyze architecture",
        "context_data": {
            "code_file": "app.py",
            "issue": "performance"
        }
    }
}
processed_response = await adapter.process_response("code", processed_request, response)
```

### Mode Transitions

```python
# Prepare a transition from code to architect mode
transition = await transition_manager.prepare_transition(
    "code", "architect", "operation-123",
    {"context_data": {"file": "app.py", "issue": "performance"}}
)

# Later, complete the transition with results
await transition_manager.complete_transition(
    transition.id,
    {"analysis_result": {"issues": ["connection pooling", "caching"]}}
)
```

### Boomerang Operations

```python
# Start a complex operation
operation_id = await boomerang.start_operation(
    initial_mode="code",
    target_modes=["debug", "reviewer", "architect"],
    operation_data={"task": "Fix performance issues"},
    return_mode="code"
)

# Advance through each mode
await boomerang.advance_operation(operation_id, result_data)
```

### Memory Operations

```python
# Create a specialized memory manager
roo_memory = RooMemoryManager(memory_manager)

# Store a user preference
await roo_memory.store_user_preference("theme", "dark")

# Retrieve a user preference
theme = await roo_memory.get_user_preference("theme")

# Store a code change
await roo_memory.store_code_change(
    "database.py", "update",
    {"before": "...", "after": "..."},
    "code"
)

# Get file history
changes = await roo_memory.get_recent_changes_for_file("database.py")
```

## Performance Optimization

The integration includes several performance optimizations:

### Memory Access Optimization

- **Caching**: Frequently accessed memory entries are cached
- **Batching**: Multiple memory operations are batched when possible
- **Compression**: Large memory entries are compressed

### Transition Optimization

- **Context Preservation**: Only essential context is preserved during transitions
- **Lazy Loading**: Context is loaded only when needed

### Rule Evaluation Optimization

- **Rule Indexing**: Rules are indexed by type and intent for faster lookup
- **Early Termination**: Rule evaluation stops as soon as a match is found

## Error Handling

The integration includes comprehensive error handling:

### Error Types

- **ModeNotFoundError**: When a mode is not found
- **InvalidTransitionError**: When a transition is not allowed
- **MemoryAccessError**: When memory access fails
- **RuleViolationError**: When a rule is violated

### Error Recovery

- **Retry Logic**: Failed operations are retried with exponential backoff
- **Fallback Strategies**: Alternative strategies are used when primary ones fail
- **Graceful Degradation**: The system continues to function with reduced capabilities when components fail

## Best Practices

### Mode Transitions

- **Minimize Transitions**: Avoid unnecessary mode transitions
- **Preserve Context**: Include all necessary context in transitions
- **Validate Transitions**: Ensure transitions are allowed before attempting them

### Memory Access

- **Use Specialized Methods**: Use the specialized methods in `RooMemoryManager` instead of direct memory access
- **Batch Operations**: Batch multiple memory operations when possible
- **Clean Up**: Remove temporary memory entries when they are no longer needed

### Rule Definition

- **Be Specific**: Define rules with specific conditions
- **Prioritize Rules**: Assign appropriate priorities to rules
- **Document Intent**: Clearly document the intent of each rule

## Troubleshooting

### Common Issues

#### Mode Transition Failures

- **Issue**: Mode transition fails with "Invalid transition"
- **Solution**: Check if the transition is allowed in the mode definition

#### Memory Access Failures

- **Issue**: Memory access fails with "Memory entry not found"
- **Solution**: Check if the memory entry exists and if the key is correct

#### Rule Violations

- **Issue**: Operation fails with "Rule violation"
- **Solution**: Check which rule was violated and why

### Debugging

- **Logging**: Enable debug logging for detailed information
- **Tracing**: Use the `PerformanceMetrics` class to trace operation performance
- **Inspection**: Inspect memory entries and transition contexts

## API Reference

### Modes

```python
class RooMode:
    """Definition of a Roo mode with its capabilities and settings."""
    slug: str
    name: str
    description: str
    role: str
    capabilities: List[RooModeCapability]
    memory_access_level: str
    can_transition_to: List[str]
    default_rules: Dict[str, Any]
    file_patterns: List[str]
    model: str
    temperature: float
```

### Transitions

```python
class TransitionContext:
    """Context information preserved during mode transitions."""
    id: str
    source_mode: str
    target_mode: str
    operation_id: str
    timestamp: float
    memory_keys: List[str]
    metadata: Dict[str, Any]
    completed: bool

class ModeTransitionManager:
    """Manages transitions between Roo modes with context preservation."""
    async def prepare_transition(
        self,
        source_mode: str,
        target_mode: str,
        operation_id: str,
        context_data: Dict[str, Any] = None
    ) -> Optional[TransitionContext]

    async def complete_transition(
        self,
        transition_id: str,
        result_data: Dict[str, Any] = None
    ) -> Optional[TransitionContext]
```

### Memory Hooks

```python
class RooMemoryManager:
    """Specialized memory manager for Roo operations."""
    async def store_mode_context(
        self,
        mode_slug: str,
        context_data: Dict[str, Any],
        ttl_seconds: int = 3600
    ) -> Optional[str]

    async def retrieve_mode_contexts(
        self,
        mode_slug: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]

    async def store_code_change(
        self,
        file_path: str,
        change_type: str,
        content: Dict[str, Any],
        mode_slug: str,
        ttl_seconds: int = 86400
    ) -> Optional[str]

    async def get_recent_changes_for_file(
        self,
        file_path: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]

    async def store_user_preference(
        self,
        preference_type: str,
        value: Any,
        ttl_seconds: int = 2592000
    ) -> Optional[str]

    async def get_user_preference(
        self,
        preference_type: str,
        default_value: Any = None
    ) -> Any

class BoomerangOperation:
    """Implements the boomerang pattern for complex operations."""
    async def start_operation(
        self,
        initial_mode: str,
        target_modes: List[str],
        operation_data: Dict[str, Any],
        return_mode: str
    ) -> Optional[str]

    async def advance_operation(
        self,
        operation_id: str,
        result: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]
```

### Rules

```python
class Rule:
    """A rule that captures developer intent and enforces constraints."""
    id: str
    name: str
    description: str
    type: RuleType
    intent: RuleIntent
    conditions: List[RuleCondition]
    action: str
    enabled: bool
    severity: RuleSeverity
    metadata: Dict[str, Any]

class RuleEngine:
    """Engine for evaluating rules against operations."""
    def register_rule(self, rule: Rule) -> None

    def register_rules(self, rules: List[Rule]) -> None

    def evaluate(self, context: Dict[str, Any]) -> List[Dict[str, Any]]
```

### Adapters

```python
class GeminiRooAdapter:
    """Adapter for integrating Gemini with Roo and MCP."""
    async def process_request(
        self,
        mode_slug: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]

    async def process_response(
        self,
        mode_slug: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any]
    ) -> Dict[str, Any]

    async def handle_mode_transition(
        self,
        transition_id: str,
        result_data: Dict[str, Any] = None
    ) -> Dict[str, Any]
```
