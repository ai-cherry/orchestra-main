# Orchestra Agent Framework Integrations

This document provides comprehensive information about integrating Orchestra with modern agent frameworks including SuperAGI, AutoGen, LangChain, and
## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Integration Components](#integration-components)
3. [Setup Instructions](#setup-instructions)
4. [Configuration Options](#configuration-options)
5. [Usage Examples](#usage-examples)
6. [Gemini 1.5 Context Window](#gemini-15-context-window)
7. [Infrastructure Setup](#infrastructure-setup)
8. [Troubleshooting](#troubleshooting)

## Architecture Overview

The integration architecture enhances Orchestra's agent capabilities by connecting to specialized frameworks:

```
┌─────────────────────────────────────┐
│         Orchestra Core              │
└───────────┬──────────────┬──────────┘
            │              │
┌───────────▼──────┐ ┌─────▼───────────┐
│ Memory System    │ │ Agent Framework │
└───────┬───┬──────┘ └────┬────┬───────┘
        │   │             │    │
┌───────▼───▼──────┐ ┌────▼────▼───────┐
│ GeminiContext    │ │ Integration     │
│ Manager (2M)     │ │ Adapters        │
└──┬────┬────┬─────┘ └─┬───┬────┬──────┘
   │    │    │         │   │    │
┌──▼────▼────▼─────────▼───▼────▼──────┐
│                                      │
│  ┌──────────┐  ┌────────┐  ┌───────┐ │
│  │ SuperAGI │  │AutoGen │  │Vertex │ │
│  │ Cloud    │  │Multi-  │  │AI     │ │
│  │ Agents   │  │Agent   │  │Agent  │ │
│  └──────────┘  └────────┘  │Builder│ │
│                            └───────┘ │
│  ┌──────────┐                        │
│  │LangChain │                        │
│  │Memory    │                        │
│  └──────────┘                        │
│                                      │
└──────────────────────────────────────┘
```

## Integration Components

### 1. Gemini Context Manager

Leverages Gemini 1.5's large token context window for cross-agent memory sharing.

**Key Features:**

- Maintains a shared 2M token context pool
- Priority-based memory management
- Intelligent context pruning
- Token-aware memory allocation

### 2. SuperAGI Integration

Connects Orchestra to SuperAGI's cloud agent management platform.

**Key Features:**

- Advanced agent lifecycle management
- Tool discovery and registry mapping
- Resource optimization
- Agent monitoring and analytics

### 3. AutoGen Integration

Implements AutoGen's multi-agent conversation protocols.

**Key Features:**

- Structured multi-agent dialogues
- Group reasoning capabilities
- Advanced agent specialization
- Sophisticated conversation flows

### 4. LangChain Memory Adapter

Enhances Orchestra's memory system with LangChain's specialized memory modules.

**Key Features:**

- Entity extraction and memory
- Conversation summarization
- Structured knowledge bases
- Enhanced semantic search

### 5.
Provides enterprise-grade agent management via Google's
**Key Features:**

- Enterprise compliance features
- Advanced analytics and monitoring
- A/B testing for agent optimization
- Secure deployment and scaling

## Setup Instructions

### Prerequisites

- Python 3.8+
- - Terraform (optional, for infrastructure)
- Access to relevant API keys

### Installation

1. Run the setup script:

```bash
./scripts/setup_integrations.sh
```

This script will:

- Install required dependencies
- Set up configuration files
- Enable - Test the Gemini Context Manager
- Create environment variable scripts

2. Source the environment variables:

```bash
source ./set_integration_env.sh
```

3. Update the configuration file at `./config/integrations.yaml` as needed.

4. For infrastructure deployment (optional):

```bash
cd terraform
terraform init
terraform apply
```

### Enabling Specific Integrations

Edit the `./config/integrations.yaml` file to enable specific integrations:

```yaml
# Enable SuperAGI integration
superagi:
  enabled: true
  api_url: "https://api.superagi.com/v1"
```

## Configuration Options

### Gemini Context Manager

```yaml
gemini_context_manager:
  enabled: true
  model: "gemini-2.5-pro"
  max_tokens: 2000000 # 2M tokens
  token_estimator: "transformers" # Use transformers library for token estimation
  priority_threshold: 0.7 # Threshold for high-priority items preservation
```

### SuperAGI Integration

```yaml
superagi:
  enabled: true
  api_url: "https://api.superagi.com/v1"
  organization_id: "your-org-id" # Optional
```

### AutoGen Integration

```yaml
autogen:
  enabled: true
  default_llm: "gpt-4o" # Default model
  max_rounds: 10 # Maximum conversation rounds
  speaker_selection: "auto" # auto, round_robin, or random
  use_manager: true # Use GroupChatManager
```

### LangChain Memory Adapter

```yaml
langchain:
  enabled: true
  use_entity_memory: true # Enable entity extraction
  use_summary_memory: true # Enable conversation summarization
  use_vectorstore: true # Enable vector storage
  collection_name: "orchestra_memories" # Collection name
  embedding_model: "textembedding-gecko@latest" # Embedding model
```

###
```yaml
vertex_ai:
  enabled: true
  model: "gemini-2.5-pro" # Model to use
  project_id: "your-project-id" # Optional, uses current project by default
  region: "us-central1" # Region
```

## Usage Examples

### Gemini Context Manager

```python
from packages.shared.src.memory.gemini_context_manager import GeminiContextManager

# Initialize the context manager
config = {"max_tokens": 2000000, "priority_threshold": 0.7}
context_manager = GeminiContextManager(config)
await context_manager.initialize()

# Add memory to context
await context_manager.add_to_context(memory_item, priority=0.8)

# Retrieve relevant context
memories = await context_manager.get_relevant_context(
    query="What happened in the previous conversation?",
    user_id="user123",
    session_id="session456",
    limit=10
)
```

### SuperAGI Integration

```python
from packages.shared.src.integrations.superagi.agent_provider import SuperAGIAgentProvider

# Initialize SuperAGI provider
provider = SuperAGIAgentProvider(config={"api_key": "your-api-key"})
await provider.initialize()

# Create an agent
agent_config = {
    "name": "Research Assistant",
    "description": "Helps with research tasks",
    "goal": ["Find information", "Summarize findings"],
    "tools": [{"name": "web_search", "description": "Search the web"}]
}
agent_id = await provider.create_agent(agent_config)

# Run the agent
result = await provider.run_agent(
    agent_id=agent_id,
    input_data="Find information about quantum computing"
)
```

### AutoGen Integration

```python
from packages.shared.src.integrations.autogen.team_adapter import AutoGenTeamAdapter

# Initialize AutoGen team adapter
adapter = AutoGenTeamAdapter(
    agent_config={
        "autogen_team": {
            "agents": [
                {
                    "name": "Researcher",
                    "type": "assistant",
                    "system_message": "You are a research expert."
                },
                {
                    "name": "Writer",
                    "type": "assistant",
                    "system_message": "You are a technical writer."
                }
            ],
            "max_rounds": 10
        }
    }
)
await adapter.initialize()

# Run the team conversation
result = await adapter.run(
    prompt="Write a technical article about neural networks.",
    session_id="session123",
    user_id="user456"
)
```

### LangChain Memory Adapter

```python
from packages.shared.src.integrations.langchain.memory_adapter import LangChainMemoryAdapter

# Initialize LangChain memory adapter
adapter = LangChainMemoryAdapter(config={
    "use_entity_memory": True,
    "use_summary_memory": True,
    "gemini_model": "gemini-2.5-flash"
})
await adapter.initialize()

# Add memory
memory_id = await adapter.add_memory(memory_item)

# Retrieve memories with semantic search
memories = await adapter.get_memories(
    user_id="user123",
    session_id="session456",
    query="What did we discuss about machine learning?",
    limit=5
)
```

###
```python
from packages.shared.src.integrations.vertex_ai.agent_builder import VertexAIAgentBuilder

# Initialize builder = VertexAIAgentBuilder(config={
    "project_id": "your-project-id",
    "region": "us-central1"
})
await builder.initialize()

# Create an agent
agent_id = await builder.create_agent(
    agent_config={
        "name": "Customer Support Agent",
        "description": "Handles customer inquiries"
    },
    tools=[{
        "name": "lookup_order",
        "description": "Look up order information",
        "parameters": [
            {"name": "order_id", "type": "string", "required": True}
        ]
    }]
)

# Deploy the agent
await builder.deploy_agent(agent_id, "production")

# Run the agent
response = await builder.run_agent(
    agent_id=agent_id,
    prompt="I need help with my order #12345"
)
```

## Gemini 1.5 Context Window

The Gemini Context Manager leverages Gemini 1.5's large token context window for efficient cross-agent memory sharing. This extensive context window enables:

1. **Long-Term Conversation Tracking**: Maintain context across lengthy agent interactions without frequent pruning.

2. **Cross-Agent Knowledge Sharing**: Allow multiple agents to share a unified context pool.

3. **Prioritized Memory Management**: Keep the most important information in context using intelligent prioritization:

   - High-priority items are preserved even when context approaches capacity
   - Low-priority items are pruned first when space is needed
   - Recency and access frequency influence priority calculation

4. **Contextual Relevance**: Retrieve the most relevant memories for any given query across the entire context window.

### Memory Prioritization

The system uses a prioritization algorithm based on:

- Explicit priority assignment (0.0-1.0)
- Access count and frequency
- Recency of information
- Content importance (based on semantic relevance)

## Infrastructure Setup

The integration components are supported by
- **Memory System Infrastructure**

  - Redis for real-time caching layer
  - AlloyDB with vector extension for persistent storage
  -
- **Security Infrastructure**

  -   - Workload Identity Federation for GitHub Actions
  - IAM permissions for secure access

- **Monitoring and Optimization**
  - Cloud Monitoring alerts
  - Budget tracking and alerts
  - Performance metrics

To deploy the infrastructure:

```bash
cd terraform
terraform init
terraform apply
```

### Infrastructure Diagram

```
┌──────────────────┐      ┌──────────────────┐
│  Redis Cache     │◄────►│  AlloyDB Cluster │
│  (Memory Cache)  │      │  (Persistent)    │
└────────┬─────────┘      └─────────┬────────┘
         │                          │
         │                          │
┌────────▼──────────────────────────▼────────┐
│                                            │
│             Orchestra Application          │
│                                            │
└────────┬──────────────────────────┬────────┘
         │                          │
┌────────▼────────┐        ┌────────▼────────┐
│  └─────────────────┘        └─────────────────┘
```

## Troubleshooting

### Common Issues

#### 1. API Authentication Failures

**Problem**: "Failed to authenticate with [Service] API"

**Solution**:

- Verify API keys are correctly set in - Check if API key has necessary permissions
- Confirm the API is enabled in
#### 2. Integration Initialization Failures

**Problem**: "Failed to initialize [Integration] adapter"

**Solution**:

- Check if all dependencies are installed
- Verify configuration values in `integrations.yaml`
- Check logs for specific error messages
- Ensure required API services are enabled

#### 3. Infrastructure Deployment Issues

**Problem**: Terraform deployment fails

**Solution**:

- Check project permissions
- Verify quota limits for resources
- Review error messages in Terraform output
- Try deploying specific modules separately

#### 4. Context Window Limitations

**Problem**: "Could not add to context: not enough space"

**Solution**:

- Lower the priority threshold to allow more aggressive pruning
- Reduce the token count of items being added
- Monitor the context window usage metrics

### Checking Integration Status

Run the test script to verify integration status:

```bash
python3 scripts/test_integrations.py
```

### Support Resources

- Check logs in `./logs/integrations.log`
- Review the configuration files in `./config/`
- Consult
