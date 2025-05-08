#!/usr/bin/env python3
"""
mcp_client_lib.py - Unified MCP Client Library for Project Orchestra

This library provides a unified interface for interacting with the Model Context Protocol (MCP)
system, allowing different AI tools (Roo, Cline, Gemini, Co-pilot) to share context and
collaborate effectively.

Key features:
- Direct API client for MCP server
- Standardized memory schema
- Advanced memory operations (search, tagging, etc.)
- Streaming memory updates
- Cross-tool memory access
"""

import os
import json
import time
import logging
import requests
import threading
from enum import Enum
from typing import List, Dict, Any, Optional, Union, Callable
from datetime import datetime
from pathlib import Path
import websocket  # You may need to install this: pip install websocket-client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("mcp-client")

class MemoryType(Enum):
    """Type of memory item."""
    TRANSIENT = "transient"  # Short-lived, not persisted
    SHARED = "shared"        # Shared between tools
    PRIVATE = "private"      # Tool-specific
    SYSTEM = "system"        # System-level memory

class MemoryScope(Enum):
    """Scope of memory item."""
    SESSION = "session"      # Current session only
    USER = "user"            # User-specific
    PROJECT = "project"      # Project-specific
    GLOBAL = "global"        # Global scope

class ToolType(Enum):
    """Type of AI tool."""
    ROO = "roo"
    CLINE = "cline"
    GEMINI = "gemini"
    COPILOT = "copilot"
    AGNO = "agno"

class CompressionLevel(Enum):
    """Level of compression for memory items."""
    NONE = "none"
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"
    EXTREME = "extreme"

class MCPMemoryItem:
    """Standardized memory item for MCP."""
    
    def __init__(
        self, 
        key: str,
        content: Any,
        memory_type: MemoryType = MemoryType.SHARED,
        scope: MemoryScope = MemoryScope.SESSION,
        source_tool: Optional[ToolType] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
        compression_level: CompressionLevel = CompressionLevel.NONE,
        importance: float = 0.5,
        tags: Optional[List[str]] = None
    ):
        self.key = key
        self.content = content
        self.memory_type = memory_type
        self.scope = scope
        self.source_tool = source_tool
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
        self.last_accessed = self.created_at
        self.access_count = 0
        self.ttl = ttl
        self.compression_level = compression_level
        self.importance = importance
        self.tags = tags or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            "key": self.key,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "scope": self.scope.value,
            "source_tool": self.source_tool.value if self.source_tool else None,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "ttl": self.ttl,
            "compression_level": self.compression_level.value,
            "importance": self.importance,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMemoryItem':
        """Create from dictionary."""
        return cls(
            key=data["key"],
            content=data["content"],
            memory_type=MemoryType(data.get("memory_type", "shared")),
            scope=MemoryScope(data.get("scope", "session")),
            source_tool=ToolType(data["source_tool"]) if data.get("source_tool") else None,
            metadata=data.get("metadata", {}),
            ttl=data.get("ttl"),
            compression_level=CompressionLevel(data.get("compression_level", "none")),
            importance=data.get("importance", 0.5),
            tags=data.get("tags", [])
        )


class MCPClient:
    """Client for interacting with MCP server."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8080/api",
        tool: ToolType = None,
        api_key: Optional[str] = None
    ):
        self.base_url = base_url
        self.tool = tool
        self.api_key = api_key or os.environ.get("MCP_API_KEY")
        self.session = requests.Session()
        
        # Add API key to all requests if available
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
    
    def get_memory(
        self, 
        key: str, 
        scope: MemoryScope = MemoryScope.SESSION,
        tool: Optional[ToolType] = None
    ) -> Optional[Any]:
        """Get a memory item."""
        tool_str = (tool or self.tool).value if (tool or self.tool) else None
        
        params = {
            "key": key,
            "scope": scope.value
        }
        
        if tool_str:
            params["tool"] = tool_str
        
        response = self.session.get(f"{self.base_url}/memory", params=params)
        
        if response.status_code == 200:
            return response.json().get("content")
        elif response.status_code == 404:
            return None
        else:
            logger.error(f"Error getting memory: {response.text}")
            return None
    
    def set_memory(
        self,
        key: str,
        content: Any,
        scope: MemoryScope = MemoryScope.SESSION,
        tool: Optional[ToolType] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """Set a memory item."""
        tool_str = (tool or self.tool).value if (tool or self.tool) else None
        
        data = {
            "key": key,
            "content": content,
            "scope": scope.value
        }
        
        if tool_str:
            data["tool"] = tool_str
        
        if ttl:
            data["ttl"] = ttl
        
        response = self.session.post(f"{self.base_url}/memory", json=data)
        
        if response.status_code == 200:
            return True
        else:
            logger.error(f"Error setting memory: {response.text}")
            return False
    
    def delete_memory(
        self,
        key: str,
        scope: MemoryScope = MemoryScope.SESSION,
        tool: Optional[ToolType] = None
    ) -> bool:
        """Delete a memory item."""
        tool_str = (tool or self.tool).value if (tool or self.tool) else None
        
        params = {
            "key": key,
            "scope": scope.value
        }
        
        if tool_str:
            params["tool"] = tool_str
        
        response = self.session.delete(f"{self.base_url}/memory", params=params)
        
        if response.status_code == 200:
            return True
        else:
            logger.error(f"Error deleting memory: {response.text}")
            return False
    
    def sync_memory(
        self,
        key: str,
        source_tool: ToolType,
        target_tool: ToolType,
        scope: MemoryScope = MemoryScope.SESSION
    ) -> bool:
        """Sync memory between tools."""
        data = {
            "key": key,
            "source_tool": source_tool.value,
            "target_tool": target_tool.value,
            "scope": scope.value
        }
        
        response = self.session.post(f"{self.base_url}/memory/sync", json=data)
        
        if response.status_code == 200:
            return True
        else:
            logger.error(f"Error syncing memory: {response.text}")
            return False
    
    def execute(
        self,
        tool: ToolType,
        mode: str,
        prompt: str,
        context: Optional[str] = None
    ) -> Optional[str]:
        """Execute a prompt with a specific tool and mode."""
        data = {
            "tool": tool.value,
            "mode": mode,
            "prompt": prompt
        }
        
        if context:
            data["context"] = context
        
        response = self.session.post(f"{self.base_url}/execute", json=data)
        
        if response.status_code == 200:
            return response.json().get("result")
        else:
            logger.error(f"Error executing: {response.text}")
            return None
    
    def execute_workflow(
        self,
        workflow_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        tool: Optional[ToolType] = None
    ) -> Optional[str]:
        """Execute a workflow."""
        tool_str = (tool or self.tool).value if (tool or self.tool) else None
        
        data = {
            "workflow_id": workflow_id
        }
        
        if parameters:
            data["parameters"] = parameters
        
        if tool_str:
            data["tool"] = tool_str
        
        response = self.session.post(f"{self.base_url}/workflows/execute", json=data)
        
        if response.status_code == 200:
            return response.json().get("result")
        else:
            logger.error(f"Error executing workflow: {response.text}")
            return None
    
    def execute_cross_tool_workflow(
        self,
        workflow_id: str,
        tools: List[ToolType]
    ) -> Optional[str]:
        """Execute a cross-tool workflow."""
        data = {
            "workflow_id": workflow_id,
            "tools": [tool.value for tool in tools]
        }
        
        response = self.session.post(f"{self.base_url}/workflows/cross-tool", json=data)
        
        if response.status_code == 200:
            return response.json().get("result")
        else:
            logger.error(f"Error executing cross-tool workflow: {response.text}")
            return None


class MCPMemoryManager:
    """Advanced memory manager for MCP."""
    
    def __init__(
        self,
        client: Optional[MCPClient] = None,
        tool: Optional[ToolType] = None,
        base_url: Optional[str] = None
    ):
        self.client = client or MCPClient(base_url=base_url, tool=tool)
        self.local_cache = {}
    
    def save_with_metadata(
        self,
        key: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        scope: MemoryScope = MemoryScope.SESSION,
        memory_type: MemoryType = MemoryType.SHARED,
        ttl: Optional[int] = None,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        compression_level: CompressionLevel = CompressionLevel.NONE
    ) -> bool:
        """Save memory with rich metadata."""
        memory_item = MCPMemoryItem(
            key=key,
            content=content,
            memory_type=memory_type,
            scope=scope,
            source_tool=self.client.tool,
            metadata=metadata or {},
            ttl=ttl,
            compression_level=compression_level,
            importance=importance,
            tags=tags or []
        )
        
        # Save to local cache
        self.local_cache[key] = memory_item
        
        # Save to MCP server
        return self.client.set_memory(
            key=key,
            content={
                "data": content,
                "metadata": memory_item.to_dict()
            },
            scope=scope,
            ttl=ttl
        )
    
    def retrieve(
        self,
        key: str,
        scope: MemoryScope = MemoryScope.SESSION
    ) -> Optional[Any]:
        """Retrieve memory content."""
        # Check local cache first
        if key in self.local_cache:
            item = self.local_cache[key]
            return item.content
        
        # Otherwise get from server
        result = self.client.get_memory(key=key, scope=scope)
        
        if result and isinstance(result, dict) and "data" in result:
            # If it has the expected structure with metadata
            content = result["data"]
            
            # Update local cache if metadata is available
            if "metadata" in result:
                try:
                    memory_item = MCPMemoryItem.from_dict(result["metadata"])
                    self.local_cache[key] = memory_item
                except:
                    pass
                
            return content
        
        return result
    
    def retrieve_from_tool(
        self,
        key: str,
        tool: ToolType,
        fallback_strategy: str = "none",
        scope: MemoryScope = MemoryScope.SESSION
    ) -> Optional[Any]:
        """Retrieve memory from a specific tool."""
        result = self.client.get_memory(key=key, scope=scope, tool=tool)
        
        if result is None and fallback_strategy == "generate_if_missing":
            # TODO: Implement generation strategy based on tool type
            pass
        
        return result
    
    def retrieve_by_tags(
        self,
        tags: List[str],
        match_all: bool = False,
        scope: MemoryScope = MemoryScope.SESSION
    ) -> List[Dict[str, Any]]:
        """Retrieve memories by tags."""
        # For now, this is a client-side implementation that filters the local cache
        # In a full implementation, this would call a server endpoint
        
        results = []
        
        # Check each item in local cache
        for key, item in self.local_cache.items():
            if match_all:
                # All tags must match
                if all(tag in item.tags for tag in tags):
                    results.append({
                        "key": key,
                        "content": item.content,
                        "metadata": item.to_dict()
                    })
            else:
                # Any tag matches
                if any(tag in item.tags for tag in tags):
                    results.append({
                        "key": key,
                        "content": item.content,
                        "metadata": item.to_dict()
                    })
        
        return results


class MCPMemoryStream:
    """Streaming memory connection for real-time updates."""
    
    def __init__(self, memory_key: str, client: Optional[MCPClient] = None, base_url: Optional[str] = None):
        self.memory_key = memory_key
        self.client = client or MCPClient(base_url=base_url)
        self.websocket_url = self.client.base_url.replace("http", "ws") + "/memory/stream"
        self.ws = None
        self.callbacks = []
        self.running = False
        self.thread = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
    
    def connect(self):
        """Connect to the memory stream."""
        try:
            self.ws = websocket.WebSocketApp(
                f"{self.websocket_url}?key={self.memory_key}",
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            self.running = True
            self.thread = threading.Thread(target=self.ws.run_forever)
            self.thread.daemon = True
            self.thread.start()
            
            # Wait for connection
            time.sleep(0.5)
            
            return True
        except Exception as e:
            logger.error(f"Error connecting to memory stream: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the memory stream."""
        if self.ws:
            self.running = False
            self.ws.close()
            self.ws = None
    
    def on_update(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for memory updates."""
        self.callbacks.append(callback)
    
    def publish(self, data: Any) -> bool:
        """Publish update to the memory stream."""
        if not self.ws:
            logger.error("Not connected to memory stream")
            return False
        
        try:
            self.ws.send(json.dumps({"data": data}))
            return True
        except Exception as e:
            logger.error(f"Error publishing to memory stream: {e}")
            return False
    
    def _on_open(self, ws):
        logger.info(f"Connected to memory stream for {self.memory_key}")
    
    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            # Notify all callbacks
            for callback in self.callbacks:
                callback(data)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _on_error(self, ws, error):
        logger.error(f"Memory stream error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        logger.info(f"Memory stream closed: {close_msg}")
        if self.running:
            # Try to reconnect
            time.sleep(1)
            self.connect()


class MCPWorkflow:
    """Cross-tool workflow manager."""
    
    def __init__(self, name: str, client: Optional[MCPClient] = None):
        self.name = name
        self.client = client or MCPClient()
        self.steps = []
        self.results = []
    
    def add_step(
        self,
        tool: ToolType,
        mode: Optional[str] = None,
        task: Optional[str] = None,
        context_type: Optional[str] = None,
        files: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """Add a step to the workflow."""
        step = {
            "tool": tool,
            "parameters": parameters or {}
        }
        
        if mode and task:
            step["type"] = "mode"
            step["mode"] = mode
            step["task"] = task
        elif context_type and files:
            step["type"] = "context"
            step["context_type"] = context_type
            step["files"] = files
        
        self.steps.append(step)
    
    def execute(self) -> List[Dict[str, Any]]:
        """Execute the full workflow with context preservation."""
        self.results = []
        context = None
        
        for i, step in enumerate(self.steps):
            logger.info(f"Executing workflow step {i+1}/{len(self.steps)}")
            
            tool = step["tool"]
            step_type = step.get("type", "mode")
            
            result = None
            if step_type == "mode":
                mode = step["mode"]
                task = step["task"]
                
                # Execute with context from previous steps
                result = self.client.execute(tool, mode, task, context)
                
                if result:
                    # Save as context for next step
                    context = result
            
            # Save step result
            self.results.append({
                "step": i+1,
                "tool": tool.value,
                "type": step_type,
                "result": result
            })
        
        return self.results


class MCPContextSession:
    """Context-preserving session for mode transitions."""
    
    def __init__(self, tool: ToolType, client: Optional[MCPClient] = None):
        self.tool = tool
        self.client = client or MCPClient(tool=tool)
        self.context = None
        self.session_id = f"session_{int(time.time())}"
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up any session resources
        pass
    
    def execute_in_mode(self, mode: str, prompt: str) -> Optional[str]:
        """Execute in a mode with automatic context preservation."""
        result = self.client.execute(self.tool, mode, prompt, self.context)
        
        if result:
            # Update context for next execution
            self.context = result
            
            # Also save to memory with the session ID
            self.client.set_memory(
                key=f"{self.session_id}:{mode}",
                content=result,
                scope=MemoryScope.SESSION
            )
        
        return result


class MCPSharedWorkspace:
    """Shared workspace for multi-tool collaboration."""
    
    def __init__(self, name: str, client: Optional[MCPClient] = None):
        self.name = name
        self.client = client or MCPClient()
        self.subscribers = {}
    
    def publish_update(self, source_tool: Union[str, ToolType], content: Any) -> bool:
        """Publish an update to the workspace."""
        if isinstance(source_tool, ToolType):
            source_tool = source_tool.value
            
        key = f"workspace:{self.name}:updates"
        
        update = {
            "source": source_tool,
            "timestamp": datetime.now().isoformat(),
            "content": content
        }
        
        # Store the update
        return self.client.set_memory(
            key=key,
            content=update,
            scope=MemoryScope.PROJECT
        )
    
    def subscribe(self, update_type: str, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to workspace updates."""
        # In a real implementation, this would use server-side events or websockets
        # For now, we'll just register the callback
        self.subscribers[update_type] = callback
    
    def query_updates(self, source_tool: Optional[Union[str, ToolType]] = None) -> List[Dict[str, Any]]:
        """Query for updates in the workspace."""
        key = f"workspace:{self.name}:updates"
        
        # Get the updates
        updates = self.client.get_memory(
            key=key,
            scope=MemoryScope.PROJECT
        )
        
        if not updates:
            return []
        
        if source_tool:
            if isinstance(source_tool, ToolType):
                source_tool = source_tool.value
                
            # Filter by source tool
            return [u for u in updates if u.get("source") == source_tool]
        
        return updates