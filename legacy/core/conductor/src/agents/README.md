# AI cherry_ai Agent Architecture

This directory contains the implementation of the AI cherry_ai agent architecture, which provides a flexible and extensible framework for building AI agents with different capabilities.

## Core Components

The agent architecture consists of several core components:

### 1. Base Agent Interface

The `Agent` abstract base class in `agent_base.py` defines the interface that all agents must implement. It provides methods for processing user input, determining if an agent can handle a specific context, and managing agent lifecycle.

Key methods:

- `process(context: AgentContext) -> AgentResponse`: Process user input and generate a response
- `can_handle(context: AgentContext) -> float`: Determine if this agent can handle the given context
- `initialize()`: Initialize the agent
- `close()`: Close the agent and release resources

### 2. Agent Context and Response

The `AgentContext` and `AgentResponse` classes in `agent_base.py` provide structured containers for agent input and output:

- `AgentContext`: Contains user input, conversation history, persona information, and metadata
- `AgentResponse`: Contains the agent's response text, confidence score, and metadata

### 3. Enhanced Agent Types

Several enhanced agent types extend the base `Agent` class with additional capabilities:

- **StatefulAgent** (`stateful_agent.py`): Maintains state between interactions using Pydantic models
- **ObservableAgent** (`observable_agent.py`): Adds error handling and observability features
- **ToolUsingAgent** (`tools/base.py`): Enables agents to use tools to accomplish tasks
- **PersonaAwareAgent** (`persona_agent.py`): Adapts responses based on persona traits

### 4. Memory Management

The memory management system in `memory/` provides a unified interface for storing and retrieving memory items across different storage backends:

- **MemoryStore**: Abstract base class for memory stores
- **RedisMemoryStore**: Redis-based implementation for short-term memory
- **FirestoreMemoryStore**: Firestore-based implementation for long-term memory
- **VertexVectorMemoryStore**: Vertex AI Vector Search-based implementation for semantic memory
- **LayeredMemoryManager**: Manages multiple memory stores with different priorities

### 5. Tool Integration

The tool integration framework in `tools/` provides a standardized way to define and use tools with agents:

- **Tool**: Abstract base class for tools
- **ToolRegistry**: Registry for managing available tools
- **ToolUsingAgent**: Mixin for agents that can use tools

### 6. Agent Teams

The agent team coordination system in `teams/` enables multiple agents to work together to solve complex tasks:

- **AgentTeam**: Coordinates a team of specialized agents
- **TeamCoordinator**: Agent that creates execution plans for teams
- **ExecutionPlan**: Plan for executing a task with multiple agents

## Usage Examples

See `examples/agent_usage_example.py` for examples of how to use the different agent types and components.

### Basic Agent Usage

```python
# Create an agent
agent = SimpleTextAgent()

# Create context
context = AgentContext(
    user_input="Hello, how are you?",
    user_id="user123",
    persona=PersonaConfig(name="Helper", interaction_style="friendly")
)

# Process input
response = await agent.process(context)

# Use response
print(response.text)
```

### Tool-Using Agent

```python
# Create tools
calculator_tool = CalculatorTool()
weather_tool = WeatherTool()

# Create tool-using agent
agent = ToolUsingAgent(tools=[calculator_tool, weather_tool])

# Use a tool
result = await agent.use_tool("calculator", expression="2 + 2")
print(f"2 + 2 = {result}")
```

### Agent with Memory

```python
# Set up memory manager
memory_manager = await get_memory_manager()

# Create stateful agent
agent = StatefulAgent()

# Remember something
memory_id = await agent.remember(
    context=context,
    text="Important information to remember",
    metadata={"type": "note"}
)

# Recall relevant memories
memories = await agent.recall(context=context, query="important information")
```

### Agent Team

```python
# Create agents
tool_agent = ToolUsingAgent(tools=[...])
llm_agent = LLMAgent()
memory_agent = StatefulAgent()

# Create coordinator
coordinator = TeamCoordinator()

# Create team
team = AgentTeam(
    coordinator=coordinator,
    agents={
        "tool_agent": tool_agent,
        "llm_agent": llm_agent,
        "memory_agent": memory_agent
    },
    team_mode=TeamMode.COLLABORATE
)

# Process with team
response = await team.process(context)
```

## Design Principles

The agent architecture is designed with the following principles in mind:

1. **Modularity**: Components are designed to be modular and composable, allowing for flexible agent configurations.

2. **Extensibility**: The architecture is easily extensible with new agent types, tools, memory stores, etc.

3. **Observability**: Built-in support for metrics, logging, and error handling makes it easier to monitor and debug agents.

4. **State Management**: Structured state management using Pydantic models ensures type safety and consistency.

5. **Async-First**: All operations are designed to be asynchronous, enabling efficient handling of concurrent requests.

6. **Memory-Centric**: The architecture is built around a sophisticated memory system that supports different types of memory (short-term, long-term, semantic).

7. **Tool Integration**: First-class support for tools enables agents to interact with external systems and APIs.

8. **Team Coordination**: Support for agent teams enables complex tasks to be broken down and handled by specialized agents.

## Integration with External Frameworks

The agent architecture is designed to integrate with external agent frameworks like LangChain, AutoGen, and PhiData. Adapter classes can be created to wrap agents from these frameworks and use them within the AI cherry_ai system.

## Future Directions

Planned enhancements to the agent architecture include:

1. **Workflow Integration**: Integration with the workflow system for complex multi-step tasks.

2. **Enhanced Semantic Memory**: Improved semantic memory capabilities using Vertex AI Vector Search.

3. **Multi-Modal Support**: Support for multi-modal inputs and outputs (images, audio, etc.).

4. **Agent Learning**: Mechanisms for agents to learn from interactions and improve over time.

5. **Distributed Execution**: Support for distributed execution of agent teams across multiple machines.

6. **Framework Adapters**: Ready-to-use adapters for popular agent frameworks (LangChain, AutoGen, etc.).
