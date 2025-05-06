# Using Phidata Agents with PostgreSQL/PGVector Storage

This guide explains how to configure and use Phidata agents and teams with the PostgreSQL/PGVector storage backend after completing the initial setup described in the `PHIDATA_POSTGRES_SETUP_GUIDE.md`.

## Agent Configuration

### Registering a Single Agent

The following example demonstrates how to register a single Phidata agent with PostgreSQL storage:

```python
from packages.agent_registry import register_agent
from packages.agent_types import AGENT_TYPE_PHIDATA
import os

# Define agent configuration
agent_config = {
    "id": "pg-agent-1",
    "name": "PostgreSQL Research Assistant",
    "description": "Research assistant with PostgreSQL/PGVector storage",
    "type": AGENT_TYPE_PHIDATA,

    # Phidata-specific configuration
    "phidata_agent_class": "agno.agent.Agent",  # Use full import path
    "llm_ref": "gpt-4-turbo",  # Reference to LLM model in Portkey client
    "markdown": True,
    "show_tool_calls": True,

    # CloudSQL configuration
    "cloudsql_config": {
        "project_id": os.environ.get("GCP_PROJECT_ID"),
        "region": os.environ.get("GCP_REGION"),
        "instance_connection_name": os.environ.get("CLOUD_SQL_INSTANCE_CONNECTION_NAME"),
        "database": os.environ.get("CLOUD_SQL_DATABASE"),
        "user": os.environ.get("CLOUD_SQL_USER"),
        "use_iam_auth": os.environ.get("CLOUD_SQL_USE_IAM_AUTH", "false").lower() == "true",
        "password_secret_name": os.environ.get("CLOUD_SQL_PASSWORD_SECRET_NAME")
    },

    # Storage configuration
    "storage": {
        "table_name": "pg_agent_1_storage",  # PostgreSQL table name for agent storage
        "schema_name": "llm"  # PostgreSQL schema name
    },

    # Memory configuration with PGVector
    "memory": {
        "table_name": "pg_agent_1_memory",  # PostgreSQL table name for vector memory
        "schema_name": "llm",  # PostgreSQL schema name
        "vector_dimension": 768  # Dimension for textembedding-gecko@003
    },

    # Agent instructions (system prompt)
    "instructions": [
        "You are a helpful AI assistant with access to PostgreSQL database storage.",
        "You can remember conversations and use vector memory for semantic search.",
        "You provide clear, accurate, and helpful responses."
    ]
}

# Register the agent
register_agent(agent_config)
```

### Registering a Team of Agents

For more complex tasks, you can register a team of agents that collaborate:

```python
from packages.agent_registry import register_agent
from packages.agent_types import AGENT_TYPE_PHIDATA
import os

# Define team configuration
team_config = {
    "id": "research-team",
    "name": "Research Team",
    "description": "Team of experts that collaborate on research tasks",
    "type": AGENT_TYPE_PHIDATA,

    # Phidata-specific configuration
    "phidata_agent_class": "agno.team.Team",  # Use Team class
    "llm_ref": "gpt-4-turbo",  # Default LLM for team members
    "team_model_ref": "gpt-4-turbo",  # LLM for team coordinator
    "markdown": True,
    "show_tool_calls": True,

    # Team settings
    "team_mode": "coordinate",  # Options: coordinate, collaborate, delegate
    "team_success_criteria": "The task is considered complete when all facts are verified and a comprehensive response is provided.",
    "team_instructions": [
        "You are a team of AI agents working together to solve complex problems.",
        "Coordinate with your team members to provide the most accurate and helpful responses."
    ],

    # CloudSQL configuration
    "cloudsql_config": {
        "project_id": os.environ.get("GCP_PROJECT_ID"),
        # ...other connection details...
    },

    # Storage configuration for the team
    "storage": {
        "table_name": "research_team_storage",
        "schema_name": "llm"
    },

    # Memory configuration for the team
    "memory": {
        "table_name": "research_team_memory",
        "schema_name": "llm",
        "vector_dimension": 768
    },

    # Team members configuration
    "members": [
        {
            "name": "Researcher",
            "role": "Researches facts and gathers information",
            "model_ref": "gpt-4-turbo",
            "instructions": [
                "You are a research specialist who excels at finding accurate information.",
                "Your role is to thoroughly investigate topics and verify facts."
            ],
            # Member-specific storage
            "storage": {
                "table_name": "research_team_researcher_storage"
            }
        },
        {
            "name": "Writer",
            "role": "Crafts clear and well-structured content",
            "model_ref": "gpt-4-turbo",
            "instructions": [
                "You are a content specialist who excels at clear communication.",
                "Your role is to organize information into well-structured, easy-to-understand content."
            ],
            "storage": {
                "table_name": "research_team_writer_storage"
            }
        }
        # Add more team members as needed
    ]
}

# Register the team
register_agent(team_config)
```

## Using Agents with PostgreSQL Storage

### Getting an Agent Instance

```python
from packages.agent_registry import get_agent_instance

# Get an instance of a registered agent
agent = get_agent_instance("pg-agent-1")

# Check agent health
import asyncio
health_result = asyncio.run(agent.health_check())
if health_result:
    print(f"Agent 'pg-agent-1' is healthy and ready!")
```

### Running an Agent

```python
from packages.core.src.models import AgentInput
import asyncio

# Create input for the agent
agent_input = AgentInput(
    request_id="request-123",
    prompt="Tell me about PostgreSQL's advantages for vector storage?",
    user_id="user-456",
    session_id="session-789"
)

# Run the agent
response = asyncio.run(agent.run(agent_input))

# Process the response
print(f"Agent Response:\n{response.content}")
```

### Using Agent with Memory

The agent automatically uses the configured PGVector memory for:

1. Storing conversation history
2. Retrieving relevant context through vector similarity search
3. Maintaining a persistent memory across sessions

```python
# Example using agent with a follow-up question that relies on memory
follow_up_input = AgentInput(
    request_id="request-124",
    prompt="What were the key advantages you mentioned earlier?",
    user_id="user-456",
    session_id="session-789"  # Same session ID to maintain conversation context
)

# The agent will use PGVector memory to recall the earlier conversation
response = asyncio.run(agent.run(follow_up_input))
```

## Agent Configuration Options

### Storage Configuration

```python
"storage": {
    "table_name": "agent_storage_table",  # Table name in PostgreSQL
    "schema_name": "llm",                 # Schema name in PostgreSQL
    "partitioning_field": "agent_id"      # Field to partition data by (optional)
}
```

### Memory Configuration

```python
"memory": {
    "table_name": "agent_memory_table",   # Table name for vector storage
    "schema_name": "llm",                 # Schema name
    "vector_dimension": 768,              # Embedding vector dimension
    "similarity_threshold": 0.7,          # Similarity threshold for retrieval
    "max_results": 5                      # Maximum number of similar items to retrieve
}
```

### CloudSQL Connection Options

```python
"cloudsql_config": {
    "project_id": "your-gcp-project-id",
    "region": "us-central1",
    "instance_connection_name": "project:region:instance",
    "database": "phidata",
    "user": "postgres",
    
    # Option 1: Use IAM authentication
    "use_iam_auth": true,
    
    # Option 2: Use password authentication via Secret Manager
    "use_iam_auth": false,
    "password_secret_name": "cloudsql-postgres-password",
    
    # Optional: Additional database settings
    "pool_size": 5,
    "max_overflow": 2,
    "pool_timeout": 30,
    "pool_recycle": 1800
}
```

### Team Modes

For team agents, you can use different collaboration modes:

```python
"team_mode": "coordinate"  # Team coordinator assigns tasks and synthesizes results
"team_mode": "collaborate" # All team members work together equally
"team_mode": "delegate"    # Tasks are delegated to specific team members based on expertise
```

## Tools Integration

You can add tools to agents or specific team members:

```python
"tools": [
    {
        "type": "phi.tools.web.WebSearch",
        "params": {
            "api_key": os.environ.get("SEARCH_API_KEY"),
            "search_engine_id": os.environ.get("SEARCH_ENGINE_ID")
        }
    },
    {
        "type": "phi.tools.database.SqlQueryTool",
        "params": {
            "connection_string": "postgresql+psycopg2://user:pass@host/db",
            "description": "Run SQL queries against a database"
        }
    }
]
```

## Testing and Debugging

### Running a Health Check

```python
import asyncio
from packages.agent_registry import get_agent_instance

agent = get_agent_instance("pg-agent-1")
health_result = asyncio.run(agent.health_check())
print(f"Agent health: {'Healthy' if health_result else 'Unhealthy'}")
```

### Testing Memory Retrieval

```python
import asyncio
from packages.phidata.src.cloudsql_pgvector import get_pgvector_memory

# Get the memory store with user context
memory = get_pgvector_memory(user_id="user-456")

# Add something to memory
asyncio.run(memory.add(
    text="PostgreSQL with pgvector is great for AI applications due to its scalability and ACID compliance.",
    metadata={"source": "test", "importance": "high"}
))

# Retrieve related items
results = asyncio.run(memory.search(
    text="What database is good for AI vector storage?",
    limit=3
))

for item in results:
    print(f"Text: {item['text']}")
    print(f"Metadata: {item['metadata']}")
    print(f"Score: {item.get('score', 'N/A')}")
```

## Common Issues and Solutions

### Connection Problems

If you encounter connection issues:

```
Error: Your default credentials were not found.
```

Ensure your GCP service account key is properly set:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-key.json
export GCP_SA_KEY_PATH=/path/to/your-key.json
```

### Memory Not Persisting

If agent memory doesn't seem to persist between sessions:

1. Verify you're using the same `session_id` for related conversations
2. Check that the PostgreSQL schema and tables are created correctly
3. Ensure the connection to the database is working properly

### Team Collaboration Issues

If team agents aren't collaborating effectively:

1. Review the team member "role" and "instructions" to ensure clear responsibilities
2. Try different team_mode settings to find the most effective collaboration pattern
3. Ensure the team_success_criteria is specific and measurable

## Monitoring and Maintenance

### Checking Database Tables

You can query the PostgreSQL database to see the stored agent data:

```sql
-- Check agent storage tables
SELECT * FROM llm.agent_storage_table LIMIT 10;

-- Check vector memory tables
SELECT * FROM llm.agent_memory_table LIMIT 10;

-- Count memory entries by user
SELECT user_id, COUNT(*) FROM llm.agent_memory_table GROUP BY user_id;
```

### Performance Optimization

For larger deployments:

1. Consider adding indexes to frequently queried fields
2. Increase the connection pool size for high-traffic applications
3. Use table partitioning for multi-user applications
4. Monitor query performance and adjust PGVector indexes as needed
