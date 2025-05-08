# MCP Memory System

This package implements a Model Context Protocol (MCP) memory system that enables bidirectional memory synchronization between different AI tools including GitHub Copilot and Google Gemini.

## Overview

The MCP Memory System provides a unified framework for managing memory across different AI tools, allowing them to share context and collaborate effectively. Key features include:

- **Unified Memory Schema**: Standardized memory representation across all tools
- **Bidirectional Synchronization**: Memory changes in one tool are automatically reflected in others
- **Context Window Management**: Smart handling of token limits and compression
- **Tool-Specific Adapters**: Adapters for GitHub Copilot and Google Gemini
- **Extensible Architecture**: Easy to add support for additional tools

## Architecture

The system follows a clean architecture with clear interfaces and responsibilities:

```
┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐ 
│   Copilot Tool  │      │   Gemini Tool   │     │    Other Tools  │ 
└────────┬────────┘      └────────┬────────┘     └────────┬────────┘ 
         │                        │                       │          
         ▼                        ▼                       ▼          
┌────────┴────────┐      ┌────────┴────────┐     ┌────────┴────────┐ 
│ Copilot Adapter │      │ Gemini Adapter  │     │  Other Adapters │ 
└────────┬────────┘      └────────┬────────┘     └────────┬────────┘ 
         │                        │                       │          
         └────────────────┬───────┴───────────────┬──────┘          
                          │                       │                 
                          ▼                       ▼                 
              ┌───────────┴───────────┐ ┌─────────┴─────────┐       
              │  Memory Manager       │ │ Token Budget Mgr   │       
              └───────────┬───────────┘ └─────────┬─────────┘       
                          │                       │                 
                          └───────────┬───────────┘                 
                                      │                             
                                      ▼                             
                          ┌───────────┴───────────┐                 
                          │     Storage Layer     │                 
                          └───────────────────────┘                 
```

## Components

### Interfaces

- `IMemoryStorage`: Interface for all storage implementations
- `IMemoryManager`: Interface for memory managers
- `IToolAdapter`: Interface for tool-specific adapters

### Models

- `MemoryEntry`: Represents a single memory entry with metadata
- `MemoryMetadata`: Contains metadata about memory entries
- Various enums for memory types, scopes, compression levels, etc.

### Storage Implementations

- `InMemoryStorage`: In-memory storage implementation

### Managers

- `StandardMemoryManager`: Memory manager implementation that handles synchronization

### Tool Adapters

- `CopilotAdapter`: Adapter for GitHub Copilot
- `GeminiAdapter`: Adapter for Google Gemini

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/example/mcp-server.git
cd mcp-server

# Install dependencies
pip install -e .
```

### Basic Usage

```python
import asyncio
from mcp_server.storage.in_memory_storage import InMemoryStorage
from mcp_server.managers.standard_memory_manager import StandardMemoryManager
from mcp_server.adapters.copilot_adapter import CopilotAdapter
from mcp_server.adapters.gemini_adapter import GeminiAdapter
from mcp_server.models.memory import MemoryEntry, MemoryType, MemoryScope, MemoryMetadata

async def main():
    # Initialize storage
    storage = InMemoryStorage()
    
    # Initialize memory manager
    memory_manager = StandardMemoryManager(storage)
    
    # Initialize tool adapters
    copilot_adapter = CopilotAdapter()
    gemini_adapter = GeminiAdapter()
    
    # Register adapters with the memory manager
    memory_manager.register_tool(copilot_adapter)
    memory_manager.register_tool(gemini_adapter)
    
    # Initialize everything
    await memory_manager.initialize()
    
    # Create a memory entry from Copilot
    entry = MemoryEntry(
        memory_type=MemoryType.SHARED,
        scope=MemoryScope.SESSION,
        priority=5,
        compression_level=0,
        ttl_seconds=3600,
        content="This is a memory from Copilot",
        metadata=MemoryMetadata(
            source_tool="copilot",
            last_modified=0.0,  # Will be set by manager
        )
    )
    
    # Save the memory
    await memory_manager.create_memory("test_memory", entry, "copilot")
    
    # Retrieve the memory from Gemini
    gemini_entry = await memory_manager.get_memory("test_memory", "gemini")
    print(f"Content retrieved by Gemini: {gemini_entry.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Running the Demo

The system includes a demonstration application that shows the main features:

```bash
python -m mcp_server.main
```

## Configuration

The system can be configured using a JSON configuration file:

```json
{
  "storage": {
    "type": "in_memory"
  },
  "copilot": {
    "token_limit": 5000
  },
  "gemini": {
    "model": "gemini-pro",
    "token_limit": 200000
  }
}
```

Pass the configuration file to the demo:

```bash
python -m mcp_server.main --config config.json
```

## Extending the System

### Adding a New Tool Adapter

To add support for a new AI tool, create a new adapter that implements the `IToolAdapter` interface:

```python
from mcp_server.interfaces.tool_adapter import IToolAdapter

class NewToolAdapter(IToolAdapter):
    """Adapter for a new AI tool."""
    
    @property
    def tool_name(self) -> str:
        return "new_tool"
    
    @property
    def context_window_size(self) -> int:
        return 10000  # Adjust based on the tool's actual limit
    
    # Implement all required methods...
```

### Adding a New Storage Backend

To add a new storage backend, create a class that implements the `IMemoryStorage` interface:

```python
from mcp_server.interfaces.storage import IMemoryStorage

class NewStorage(IMemoryStorage):
    """New storage implementation."""
    
    # Implement all required methods...
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
