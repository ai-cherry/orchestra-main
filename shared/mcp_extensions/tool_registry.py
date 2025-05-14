"""
Tool Registry for AI Orchestra

This module implements a Tool Registry that allows AI agents to discover 
available tools through the MCP (Model Context Protocol) memory system.
The ToolRegistry class manages tool registration, discovery, and permissions
across environments, enabling seamless tool access for AI agents like
Gemini, Vertex AI, Roo, and Cline.

Example:
    # Initialize the registry with MCP client
    from tool_registry import ToolRegistry
    from mcp_client import MCPClient
    
    mcp_client = MCPClient()
    registry = ToolRegistry(mcp_client)
    
    # Register a tool
    registry.register_tool(
        name="summarize_text",
        description="Generate a concise summary of any text",
        provider="gemini",
        parameters={"text": "string", "max_length": "integer"}
    )
    
    # Discover tools
    tools = registry.discover_tools(provider="gemini")
"""

import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Set, Union

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("tool_registry")

class ToolRegistry:
    """Registry for AI tools in the MCP memory system.
    
    This class manages tool registration, discovery, and permissions across
    environments, enabling seamless tool access for AI agents like
    Gemini, Vertex AI, Roo, and Cline.
    """
    
    # MCP memory keys
    REGISTRY_KEY = "ai:tool_registry"
    PERMISSIONS_KEY = "ai:tool_permissions"
    USAGE_STATS_KEY = "ai:tool_usage_stats"
    
    def __init__(self, mcp_client):
        """Initialize the Tool Registry.
        
        Args:
            mcp_client: An instance of MCPClient for accessing shared memory
        """
        self.mcp_client = mcp_client
        self._initialize_registry()
    
    def _initialize_registry(self) -> None:
        """Initialize the registry in MCP memory if it doesn't exist."""
        try:
            registry = self.mcp_client.get(self.REGISTRY_KEY)
            if not registry:
                logger.info("Initializing new tool registry in MCP memory")
                self.mcp_client.set(self.REGISTRY_KEY, {
                    "tools": {},
                    "updated_at": time.time(),
                    "version": "1.0.0"
                })
            
            permissions = self.mcp_client.get(self.PERMISSIONS_KEY)
            if not permissions:
                logger.info("Initializing tool permissions in MCP memory")
                self.mcp_client.set(self.PERMISSIONS_KEY, {
                    "default": {"allow_all": True},
                    "environments": {
                        "codespaces": {"allow_all": True},
                        "gcp_workstation": {"allow_all": True}
                    },
                    "agents": {}
                })
            
            usage_stats = self.mcp_client.get(self.USAGE_STATS_KEY)
            if not usage_stats:
                logger.info("Initializing tool usage stats in MCP memory")
                self.mcp_client.set(self.USAGE_STATS_KEY, {
                    "tools": {},
                    "last_reset": time.time()
                })
        except Exception as e:
            logger.error(f"Failed to initialize registry: {e}")
            raise
    
    def register_tool(
        self,
        name: str,
        description: str,
        provider: str,
        parameters: Dict[str, str],
        environment: Optional[str] = None,
        version: str = "1.0.0",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Register a new tool in the registry.
        
        Args:
            name: Tool name (unique identifier)
            description: Human-readable description
            provider: AI provider (gemini, vertex, roo, cline, etc.)
            parameters: Dictionary of parameter names and types
            environment: Optional environment restriction
            version: Tool version
            tags: Optional list of tags for categorization
            
        Returns:
            The registered tool information
        """
        tool_id = f"{provider}:{name}"
        
        try:
            registry = self.mcp_client.get(self.REGISTRY_KEY)
            if not registry:
                raise ValueError("Registry not initialized")
            
            tools = registry.get("tools", {})
            
            # Create tool entry
            tool_info = {
                "id": tool_id,
                "name": name,
                "description": description,
                "provider": provider,
                "parameters": parameters,
                "version": version,
                "registered_at": time.time(),
                "updated_at": time.time(),
                "environment": environment,
                "tags": tags or []
            }
            
            # Update registry
            tools[tool_id] = tool_info
            registry["tools"] = tools
            registry["updated_at"] = time.time()
            
            self.mcp_client.set(self.REGISTRY_KEY, registry)
            logger.info(f"Registered tool: {tool_id}")
            
            # Initialize usage stats for the tool
            self._initialize_tool_stats(tool_id)
            
            return tool_info
            
        except Exception as e:
            logger.error(f"Failed to register tool {name}: {e}")
            raise
    
    def unregister_tool(self, tool_id: str) -> bool:
        """Remove a tool from the registry.
        
        Args:
            tool_id: Tool ID to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            registry = self.mcp_client.get(self.REGISTRY_KEY)
            if not registry:
                return False
            
            tools = registry.get("tools", {})
            if tool_id not in tools:
                logger.warning(f"Tool {tool_id} not found in registry")
                return False
            
            # Remove the tool
            del tools[tool_id]
            registry["tools"] = tools
            registry["updated_at"] = time.time()
            
            self.mcp_client.set(self.REGISTRY_KEY, registry)
            logger.info(f"Unregistered tool: {tool_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister tool {tool_id}: {e}")
            return False
    
    def discover_tools(
        self, 
        provider: Optional[str] = None,
        environment: Optional[str] = None,
        agent_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Discover available tools based on criteria.
        
        Args:
            provider: Optional provider filter
            environment: Optional environment filter
            agent_id: Optional agent ID for permission check
            tags: Optional list of tags to filter by
            
        Returns:
            List of matching tool information dictionaries
        """
        try:
            registry = self.mcp_client.get(self.REGISTRY_KEY)
            if not registry:
                return []
            
            tools = registry.get("tools", {}).values()
            result = []
            
            for tool in tools:
                # Apply provider filter
                if provider and tool["provider"] != provider:
                    continue
                    
                # Apply environment filter
                if environment:
                    tool_env = tool.get("environment")
                    if tool_env and tool_env != environment:
                        continue
                
                # Apply tag filter
                if tags:
                    tool_tags = set(tool.get("tags", []))
                    if not all(tag in tool_tags for tag in tags):
                        continue
                
                # Check permissions if agent_id is provided
                if agent_id and not self._check_permission(agent_id, tool["id"]):
                    continue
                
                result.append(tool)
            
            # Log usage for discovery
            if agent_id:
                self._log_discovery(agent_id, len(result))
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to discover tools: {e}")
            return []
    
    def invoke_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        agent_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Record tool invocation and track usage statistics.
        
        Note: This does not actually execute the tool; it only
        tracks that it was used. The actual execution happens in
        the AI agent or its execution environment.
        
        Args:
            tool_id: Tool ID to invoke
            parameters: Parameters passed to the tool
            agent_id: Optional ID of the invoking agent
            context: Optional context information
            
        Returns:
            Dictionary with invocation ID and timestamp
        """
        try:
            registry = self.mcp_client.get(self.REGISTRY_KEY)
            if not registry or tool_id not in registry.get("tools", {}):
                raise ValueError(f"Tool {tool_id} not found in registry")
            
            # Check permissions if agent_id is provided
            if agent_id and not self._check_permission(agent_id, tool_id):
                raise PermissionError(f"Agent {agent_id} not allowed to use tool {tool_id}")
            
            # Record usage stats
            invocation_id = str(uuid.uuid4())
            self._record_usage(tool_id, agent_id, invocation_id)
            
            return {
                "invocation_id": invocation_id,
                "timestamp": time.time(),
                "tool_id": tool_id,
                "agent_id": agent_id
            }
            
        except Exception as e:
            logger.error(f"Failed to invoke tool {tool_id}: {e}")
            raise
    
    def _initialize_tool_stats(self, tool_id: str) -> None:
        """Initialize usage statistics for a tool.
        
        Args:
            tool_id: Tool ID to initialize stats for
        """
        try:
            stats = self.mcp_client.get(self.USAGE_STATS_KEY)
            if not stats:
                return
            
            tools = stats.get("tools", {})
            if tool_id not in tools:
                tools[tool_id] = {
                    "total_invocations": 0,
                    "last_invocation": None,
                    "invocations_by_agent": {},
                    "discovery_count": 0
                }
                
                stats["tools"] = tools
                self.mcp_client.set(self.USAGE_STATS_KEY, stats)
                
        except Exception as e:
            logger.error(f"Failed to initialize tool stats for {tool_id}: {e}")
    
    def _record_usage(
        self, 
        tool_id: str, 
        agent_id: Optional[str], 
        invocation_id: str
    ) -> None:
        """Record tool usage statistics.
        
        Args:
            tool_id: Tool ID that was used
            agent_id: Agent ID that used the tool
            invocation_id: Unique ID for this invocation
        """
        try:
            stats = self.mcp_client.get(self.USAGE_STATS_KEY)
            if not stats:
                return
            
            tools = stats.get("tools", {})
            if tool_id not in tools:
                self._initialize_tool_stats(tool_id)
                tools = stats.get("tools", {})
            
            # Update tool stats
            tool_stats = tools.get(tool_id, {})
            tool_stats["total_invocations"] = tool_stats.get("total_invocations", 0) + 1
            tool_stats["last_invocation"] = time.time()
            
            # Update agent-specific stats
            if agent_id:
                agent_stats = tool_stats.get("invocations_by_agent", {})
                agent_stats[agent_id] = agent_stats.get(agent_id, 0) + 1
                tool_stats["invocations_by_agent"] = agent_stats
            
            tools[tool_id] = tool_stats
            stats["tools"] = tools
            
            self.mcp_client.set(self.USAGE_STATS_KEY, stats)
            
        except Exception as e:
            logger.error(f"Failed to record tool usage for {tool_id}: {e}")
    
    def _log_discovery(self, agent_id: str, count: int) -> None:
        """Log tool discovery activity.
        
        Args:
            agent_id: Agent ID that discovered tools
            count: Number of tools discovered
        """
        try:
            # Record discovery event (simplified for now)
            pass
        except Exception as e:
            logger.error(f"Failed to log discovery for agent {agent_id}: {e}")
    
    def _check_permission(self, agent_id: str, tool_id: str) -> bool:
        """Check if an agent has permission to use a tool.
        
        Args:
            agent_id: Agent ID to check
            tool_id: Tool ID to check access for
            
        Returns:
            True if allowed, False otherwise
        """
        try:
            permissions = self.mcp_client.get(self.PERMISSIONS_KEY)
            if not permissions:
                return True  # Default to allowing if no permission system
            
            # Check agent-specific permissions
            agent_perms = permissions.get("agents", {}).get(agent_id)
            if agent_perms:
                # Check if agent has a specific permission for this tool
                if tool_id in agent_perms.get("allowed_tools", []):
                    return True
                if tool_id in agent_perms.get("denied_tools", []):
                    return False
                # Check if agent has allow_all permission
                if agent_perms.get("allow_all", False):
                    return True
            
            # Default permission fallback
            return permissions.get("default", {}).get("allow_all", True)
            
        except Exception as e:
            logger.error(f"Permission check failed for {agent_id}, {tool_id}: {e}")
            return False  # Fail closed (deny by default on error)
    
    def get_tool_info(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific tool.
        
        Args:
            tool_id: Tool ID to get information for
            
        Returns:
            Tool information dictionary or None if not found
        """
        try:
            registry = self.mcp_client.get(self.REGISTRY_KEY)
            if not registry:
                return None
            
            tools = registry.get("tools", {})
            return tools.get(tool_id)
            
        except Exception as e:
            logger.error(f"Failed to get tool info for {tool_id}: {e}")
            return None
    
    def get_usage_stats(
        self, 
        tool_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get usage statistics for tools.
        
        Args:
            tool_id: Optional tool ID to filter stats
            agent_id: Optional agent ID to filter stats
            
        Returns:
            Dictionary of usage statistics
        """
        try:
            stats = self.mcp_client.get(self.USAGE_STATS_KEY)
            if not stats:
                return {}
            
            tools_stats = stats.get("tools", {})
            
            # Filter by tool_id if provided
            if tool_id:
                return {tool_id: tools_stats.get(tool_id, {})}
            
            # Filter by agent_id if provided
            if agent_id:
                result = {}
                for tid, tool_stat in tools_stats.items():
                    agent_invocations = tool_stat.get("invocations_by_agent", {}).get(agent_id)
                    if agent_invocations:
                        result[tid] = {
                            "total_invocations": agent_invocations,
                            "last_invocation": tool_stat.get("last_invocation")
                        }
                return result
            
            # Return all stats if no filters
            return tools_stats
            
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {}
