# Orchestra Tools with Phidata Integration

This module provides tools that can be used by agents within the Orchestra system. The tools are designed to be compatible with Phidata's tool system, allowing them to be used with both Orchestra's native agents and Phidata-based agents.

## Directory Structure

- `src/`: Source code directory
  - `base.py`: Base classes for tools and the tool registry
  - `web_browser.py`: Example implementation of a web browser tool
  - `salesforce.py`: Example implementation of a Salesforce integration tool

## Tool System Architecture

The tool system consists of the following key components:

1. **OrchestraTool**: Abstract base class for all tools in the Orchestra system
2. **ToolRegistry**: Registry that manages tool registration and instantiation
3. **Tool Implementations**: Concrete tool classes that inherit from OrchestraTool

## Phidata Compatibility

Tools can be used with Phidata agents in two ways:

### 1. Using the OrchestraTool Class

The `OrchestraTool` base class provides methods for converting to Phidata-compatible tools:

```python
from packages.tools.src.base import OrchestraTool

class MyTool(OrchestraTool):
    name = "my_tool"
    description = "Description of my tool"
    
    def run(self, **kwargs):
        # Tool implementation here
        return {"result": "success"}
```

The `to_phidata_tool()` method can be called to get a Phidata-compatible tool instance.

### 2. Using Phidata's @tool Decorator (Direct Style)

Alternatively, tools can be defined directly using Phidata's `@tool` decorator:

```python
from phidata.tools import tool

@tool(
    name="my_tool",
    description="Description of my tool",
    parameters={
        "param1": {
            "type": "string",
            "description": "First parameter"
        }
    }
)
def my_tool(param1: str):
    # Tool implementation here
    return {"result": "success"}
```

## Using Tools with PhidataAgentWrapper

The `PhidataAgentWrapper` class in the agents module automatically handles tool initialization and conversion for Phidata agents. It can use tools defined in either style.

### Configuration Example

```python
agent_config = {
    "name": "Phidata Agent",
    "wrapper_type": "phidata",
    "phidata_agent_class": "agno.agent.Agent",
    "llm_ref": "gpt4o",
    "tools": [
        {
            "type": "packages.tools.src.web_browser.WebBrowserTool",
            "params": {
                "timeout": 15,
                "max_content_length": 8000
            }
        },
        {
            "type": "packages.tools.src.salesforce.SalesforceTool",
            "params": {
                "username": "${SALESFORCE_USERNAME}",
                "password": "${SALESFORCE_PASSWORD}",
                "security_token": "${SALESFORCE_SECURITY_TOKEN}"
            }
        }
    ]
}
```

## Creating New Tools

To create a new tool:

1. Create a new file in `packages/tools/src/` for your tool
2. Define a class that inherits from `OrchestraTool`
3. Implement the required methods, especially `run()`
4. (Optional) Override `to_phidata_tool()` if you need custom parameter schemas
5. (Optional) Provide a direct Phidata-style decorator implementation

## Tool Registry

The `ToolRegistry` class provides methods for registering, creating, and retrieving tools:

```python
from packages.tools.src.base import get_registry

# Get the global registry
registry = get_registry()

# Register a tool class
registry.register_tool_class("my_tool", MyTool)

# Create a tool instance
tool = registry.create_tool("tool_id", {
    "type": "my_tool",
    "params": {
        "param1": "value1"
    }
})

# Get all tools as Phidata-compatible tools
phidata_tools = registry.get_phidata_tools()
