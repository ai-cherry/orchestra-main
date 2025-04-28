# Phidata (Agno) UI Dashboard

This is a simple setup for the Phidata UI Dashboard, which allows you to interact with and test AI agents with different capabilities and tools.

## Getting Started

### Prerequisites

The following packages have been installed:
- `phidata`: Core package for creating and managing AI agents
- `fastapi[standard]`: Web framework for hosting the dashboard
- `sqlalchemy`: For database management and agent conversation history

### Running the Basic Dashboard

To run the basic Phidata UI Dashboard with a single web search agent:

```bash
# Make the script executable (if not already)
chmod +x run_phidata_dashboard.sh

# Run the dashboard
./run_phidata_dashboard.sh
```

The script will prompt you to enter your OpenAI API key if it's not already set as an environment variable.

The dashboard will be available at http://localhost:7777

### Running the Advanced Dashboard

An advanced setup with multiple specialized agents is also available:

```bash
# Set your OpenAI API key if not already set
export OPENAI_API_KEY=your_key_here

# Run the advanced dashboard
python advanced_playground.py
```

This will start a dashboard with three agents:
1. Web Search Agent - uses DuckDuckGo to search the web
2. Research Assistant - uses Wikipedia to provide in-depth information
3. Math Helper - uses Calculator tool to perform calculations

## Understanding the Dashboard

### Key Features

- **Agent Selection**: Switch between different agents using the dropdown menu
- **Chat Interface**: Interact with the selected agent through a familiar chat UI
- **Session History**: View and continue past conversations
- **Tool Visibility**: See when and how tools are being used by the agent
- **Local Storage**: All your conversations are stored locally in a SQLite database

### Dashboard Components

- **Agent Configuration**: Shows the current agent's settings and tools
- **Chat Window**: The main interface for interacting with agents
- **Tool Usage Panel**: Displays real-time information about tool calls
- **Session Management**: Create new sessions or continue previous ones

## Customizing Agents

You can customize existing agents or create new ones by modifying the Python files:

### Basic Structure of an Agent

```python
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.storage.agent.sqlite import SqlAgentStorage

my_custom_agent = Agent(
    name="Custom Agent Name",
    model=OpenAIChat(id="model_name"),  # e.g., "gpt-4o", "gpt-3.5-turbo"
    tools=[],  # Add tools here
    instructions=["List of instructions for the agent"],
    storage=SqlAgentStorage(table_name="agent_name", db_file="agents.db"),
    add_history_to_messages=True,
    markdown=True,
)
```

### Available Tools

The Phidata package includes many built-in tools:

- `DuckDuckGo()`: Web search capability
- `Wikipedia()`: Fetch information from Wikipedia
- `Calculator()`: Perform mathematical calculations
- `Weather()`: Get weather information
- `TableProcessor()`: Process tabular data
- `PDFReader()`: Extract text from PDFs
- ... and many more

To use a tool, simply import it and add it to the agent's tools list:

```python
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.calculator import Calculator

my_agent = Agent(
    # ... other parameters
    tools=[DuckDuckGo(), Calculator()],
    # ...
)
```

### Advanced Configuration

For more advanced configuration, you can:

1. Use different models:
   ```python
   from phi.model.anthropic import Claude
   model = Claude(id="claude-3-opus-20240229")
   ```

2. Use different storage backends:
   ```python
   from phi.storage.agent.postgres import PostgresAgentStorage
   storage = PostgresAgentStorage(
       table_name="my_agent",
       connection_string="postgresql://user:password@localhost/dbname"
   )
   ```

3. Enable streaming for real-time responses:
   ```python
   agent = Agent(
       # ... other parameters
       streaming=True
   )
   ```

## Troubleshooting

### API Key Issues

If you encounter errors related to the OpenAI API key:

1. Ensure the API key is correctly set in your environment:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

2. Verify that your API key is valid and has sufficient credits.

### Server Connection Issues

If you're having trouble connecting to the dashboard:

1. Make sure the server is running and check console for any error messages.
2. The default port is 7777. If you need to change it:
   ```python
   serve_playground_app("playground:app", reload=True, port=8000)
   ```

### Tool-related Issues

If tools aren't working properly:

1. For DuckDuckGo or other web search tools, ensure you have internet connectivity.
2. For specialized tools like PDF processing, make sure you have the required dependencies installed.

## Next Steps

- Explore other Phidata tools and integrations
- Create agents with custom tools specific to your use case
- Integrate with other data sources or APIs
- Implement authentication for production deployments

For more information, visit the [Phidata documentation](https://docs.phidata.com/).
