# Agent Communication System Guide

This guide explains the agent communication system implemented in AI Orchestra, which enables robust multi-agent coordination and collaboration.

## Overview

The agent communication system provides several mechanisms for agents to communicate with each other:

1. **In-Memory Message Queue**: For fast, local communication between agents in the same process
2. **PubSub-Based Messaging**: For distributed communication across multiple instances
3. **Workflow State Machine**: For coordinating complex multi-agent workflows
4. **Distributed Task Queue**: For reliable task distribution and processing

These mechanisms can be used together or independently, depending on your deployment scenario and requirements.

## Communication Patterns

The system supports several communication patterns:

1. **Direct Messaging**: One agent sends a message to another specific agent
2. **Broadcast**: One agent sends a message to all agents
3. **Request-Response**: One agent sends a request and waits for a response
4. **Publish-Subscribe**: Agents subscribe to specific message types or topics
5. **Task Distribution**: Tasks are assigned to agents based on capabilities
6. **Workflow Coordination**: Complex multi-step processes involving multiple agents

## Message Protocol

All agent communication uses a standardized message protocol defined in `core/orchestrator/src/protocols/agent_protocol.py`. The protocol defines:

- Message types (query, response, notification, etc.)
- Standard message format with sender, recipient, content, etc.
- Content models for different message types

Example message types:

- `QUERY`: A question or request from one agent to another
- `RESPONSE`: A response to a query
- `NOTIFICATION`: A broadcast notification
- `TASK`: A task assignment
- `RESULT`: The result of a task
- `MEMORY`: A memory operation
- `WORKFLOW`: A workflow state change

## Using the In-Memory Message Queue

The in-memory message queue is implemented in `core/orchestrator/src/services/message_queue.py`. It provides:

- Fast, reliable message passing between agents
- Support for direct messaging and broadcast
- Request-response pattern with timeout
- Message handlers for asynchronous processing

### Example: Sending a Message

```python
from core.orchestrator.src.services.message_queue import get_message_queue, AgentMessage

# Get the message queue
message_queue = get_message_queue()

# Create a message
message = AgentMessage(
    sender_id="agent1",
    recipient_id="agent2",
    message_type="query",
    content={"query": "What is the weather?"}
)

# Send the message
await message_queue.send_message(message)
```

### Example: Receiving Messages

```python
# Receive a message with timeout
message = await message_queue.receive_message("agent2", timeout=5.0)
if message:
    print(f"Received message: {message.content}")
```

### Example: Using Message Handlers

```python
# Define a message handler
async def handle_query(message):
    print(f"Handling query: {message.content}")
    # Process the query...

# Register the handler
message_queue.register_handler("agent2", handle_query)
```

## Using the PubSub-Based Messaging

The PubSub-based messaging system is implemented in `core/orchestrator/src/services/pubsub_client.py` and `core/orchestrator/src/services/agent_communication.py`. It provides:

- Distributed communication across multiple instances
- Topic-based messaging
- Filtering capabilities
- Reliable delivery with retries

### Example: Initializing the Communication Service

```python
from core.orchestrator.src.services.agent_communication import get_agent_communication

# Initialize the communication service
communication = await get_agent_communication(
    agent_id="agent1",
    conversation_id="conversation1"
)
```

### Example: Publishing Events

```python
# Publish an event
await communication.publish_event(
    event_type="agent_message",
    data={"message": "Hello from agent1!"},
    recipient_id="agent2"  # or "all" for broadcast
)
```

### Example: Publishing Tasks

```python
# Publish a task
await communication.publish_task(
    task_type="process_query",
    data={"query": "What is the weather?"},
    agent_id="agent2"
)
```

### Example: Handling Events and Tasks

```python
# Register event handler
communication.register_event_handler(
    "agent_message",
    async_handler_function
)

# Register task handler
communication.register_task_handler(
    "process_query",
    async_task_handler
)
```

## Using the Workflow State Machine

The workflow state machine is implemented in `core/orchestrator/src/workflows/state_machine.py`. It provides:

- State-based workflow management
- Condition-based transitions
- Action execution on transitions
- Event-based monitoring

### Example: Defining a Workflow

```python
from core.orchestrator.src.workflows.state_machine import (
    WorkflowDefinition, WorkflowState, WorkflowTransition, get_workflow_engine
)

# Define a workflow
workflow = WorkflowDefinition(
    workflow_id="query_workflow",
    name="Query Processing Workflow",
    states=[
        WorkflowState.CREATED,
        WorkflowState.RUNNING,
        WorkflowState.COMPLETED
    ],
    transitions=[
        WorkflowTransition(
            from_state=WorkflowState.CREATED,
            to_state=WorkflowState.RUNNING
        ),
        WorkflowTransition(
            from_state=WorkflowState.RUNNING,
            to_state=WorkflowState.COMPLETED,
            action_name="process_query"
        )
    ]
)

# Register the workflow
engine = get_workflow_engine()
engine.register_workflow(workflow)
```

### Example: Running a Workflow

```python
# Define an action
async def process_query(context):
    # Process the query...
    return {"result": "processed"}

# Register the action
engine.register_action("process_query", process_query)

# Create and start a workflow instance
instance_id = await engine.create_instance(
    "query_workflow",
    {"query": "What is the weather?"}
)
await engine.start_instance(instance_id)
```

## Using the Distributed Task Queue

The distributed task queue is implemented in `core/orchestrator/src/services/distributed_task_queue.py`. It provides:

- Redis-backed task distribution
- Priority-based queuing
- Automatic retries
- Dead-letter handling

### Example: Enqueuing a Task

```python
from core.orchestrator.src.services.distributed_task_queue import (
    get_task_queue, TaskDefinition
)

# Get the task queue
task_queue = await get_task_queue()

# Define a task
task = TaskDefinition(
    task_type="process_query",
    parameters={"query": "What is the weather?"},
    priority=10
)

# Enqueue the task
instance_id = await task_queue.enqueue_task(task)
```

### Example: Processing Tasks

```python
# Define a task handler
async def handle_process_query(task_instance):
    # Process the query...
    return {"result": "processed"}

# Register the handler
await task_queue.register_handler("process_query", handle_process_query)

# Start workers
await task_queue.start_workers(num_workers=5)
```

## Integrating with Agents

The `MessageHandlerMixin` class in `core/orchestrator/src/agents/message_handler_mixin.py` provides a convenient way to add message handling capabilities to agents:

```python
from core.orchestrator.src.agents.agent_base import Agent
from core.orchestrator.src.agents.message_handler_mixin import MessageHandlerMixin

class MyAgent(Agent, MessageHandlerMixin):
    def __init__(self, config=None):
        Agent.__init__(self, config)
        MessageHandlerMixin.__init__(self)

        # Register message handlers
        self.register_message_handler("query", self._handle_query)

    async def initialize_async(self):
        # Start message processing
        await self.start_message_processing()

    async def close_async(self):
        # Stop message processing
        await self.stop_message_processing()

    async def _handle_query(self, message):
        # Handle query messages
        # ...
```

For a complete example, see `core/orchestrator/src/agents/examples/pubsub_agent_example.py`.

## Infrastructure Setup

The communication system requires the following infrastructure:

1. **Redis**: For distributed task queue and short-term memory
2. **PubSub**: For distributed messaging
3. **MongoDB

The Terraform modules in `terraform/modules/redis` and `terraform/modules/pubsub` provide the necessary infrastructure. To deploy:

```bash
cd terraform
terraform init
terraform apply -target=module.redis -target=module.pubsub
```

## Best Practices

1. **Use the right communication mechanism** for your needs:

   - In-memory queue for local, fast communication
   - PubSub for distributed, reliable communication
   - Workflow state machine for complex processes
   - Distributed task queue for background processing

2. **Handle errors gracefully** in message and task handlers

3. **Use correlation IDs** to track related messages

4. **Set appropriate timeouts** for request-response patterns

5. **Use message filtering** to reduce processing overhead

6. **Monitor the communication system** using the event bus

## Troubleshooting

Common issues and solutions:

1. **Messages not being delivered**:

   - Check that the recipient agent exists and is listening
   - Verify that PubSub topics and subscriptions are correctly set up
   - Check for filtering rules that might be blocking messages

2. **Tasks not being processed**:

   - Ensure task handlers are registered for the task type
   - Check Redis connection and configuration
   - Verify that workers are running

3. **Workflows stuck in a state**:
   - Check for missing or failing conditions
   - Verify that actions are properly registered
   - Look for exceptions in action execution

## Extending the System

The communication system is designed to be extensible:

1. **Add new message types** in `agent_protocol.py`
2. **Create new workflow definitions** for specific use cases
3. **Implement custom task handlers** for specialized processing
4. **Add monitoring and metrics** using the event bus

## Conclusion

The agent communication system provides a robust foundation for building complex multi-agent systems. By using standardized protocols and multiple communication mechanisms, it enables flexible and reliable agent coordination.
