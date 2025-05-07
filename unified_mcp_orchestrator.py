#!/usr/bin/env python3
"""
unified_mcp_orchestrator.py - Unified Model Context Protocol (MCP) Orchestration System

This script provides a unified interface for orchestrating AI assistants (Roo, Cline, etc.)
through a common Model Context Protocol (MCP) framework. It ensures consistent memory 
management, context preservation, and task execution across different AI tools.

Key features:
- Unified memory management via MCP
- Cross-tool orchestration
- Consistent context window handling
- Tool-agnostic workflows
- MCP server management
"""

import os
import sys
import json
import logging
import importlib
import subprocess
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
from enum import Enum

# Import tool-specific modules
try:
    from roo_workflow_manager import MemoryBank as RooMemoryBank
    from roo_workflow_manager import RooModeManager, MODE_MAP as ROO_MODE_MAP
    roo_available = True
except ImportError:
    roo_available = False

try:
    from cline_integration import ClineMemoryBank, ClineModeManager, CLINE_MODE_MAP
    cline_available = True
except ImportError:
    cline_available = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("unified-mcp-orchestrator")

class AITool(Enum):
    """Enumeration of supported AI tools."""
    ROO = "roo"
    CLINE = "cline"
    GEMINI = "gemini"
    AGNO = "agno"  # Phidata implementation
    COPILOT = "copilot"

class MemoryScope(Enum):
    """Enumeration of memory scopes."""
    USER = "user"      # User-specific memory
    SESSION = "session"  # Current session only
    GLOBAL = "global"    # Global/shared memory
    PROJECT = "project"  # Project-specific memory

class UnifiedMemoryManager:
    """Manages unified memory across different AI tools."""
    
    def __init__(self, default_tool: AITool = None):
        self.default_tool = default_tool or (
            AITool.ROO if roo_available else 
            AITool.CLINE if cline_available else 
            None
        )
        if not self.default_tool:
            logger.warning("No AI tools available for memory management")
    
    def get_memory_manager(self, tool: Optional[AITool] = None) -> Any:
        """Get the appropriate memory manager for the specified tool."""
        tool = tool or self.default_tool
        
        if tool == AITool.ROO and roo_available:
            return RooMemoryBank
        elif tool == AITool.CLINE and cline_available:
            return ClineMemoryBank
        else:
            logger.error(f"Memory manager not available for {tool}")
            return None
    
    def save(self, key: str, content: str, 
             scope: Optional[MemoryScope] = MemoryScope.SESSION,
             tool: Optional[AITool] = None) -> bool:
        """Save content to memory with the specified scope."""
        tool = tool or self.default_tool
        memory_manager = self.get_memory_manager(tool)
        
        if not memory_manager:
            return False
        
        scoped_key = f"{scope.value}:{key}" if scope != MemoryScope.SESSION else key
        return memory_manager.save(scoped_key, content)
    
    def retrieve(self, key: str, 
                scope: Optional[MemoryScope] = MemoryScope.SESSION,
                tool: Optional[AITool] = None) -> Optional[str]:
        """Retrieve content from memory with the specified scope."""
        tool = tool or self.default_tool
        memory_manager = self.get_memory_manager(tool)
        
        if not memory_manager:
            return None
        
        scoped_key = f"{scope.value}:{key}" if scope != MemoryScope.SESSION else key
        return memory_manager.retrieve(scoped_key)
    
    def update(self, key: str, content: str,
              scope: Optional[MemoryScope] = MemoryScope.SESSION,
              tool: Optional[AITool] = None) -> bool:
        """Update content in memory with the specified scope."""
        tool = tool or self.default_tool
        memory_manager = self.get_memory_manager(tool)
        
        if not memory_manager:
            return False
        
        scoped_key = f"{scope.value}:{key}" if scope != MemoryScope.SESSION else key
        return memory_manager.update(scoped_key, content)
    
    def sync_between_tools(self, key: str, 
                         source_tool: AITool,
                         target_tool: AITool,
                         scope: Optional[MemoryScope] = MemoryScope.SESSION) -> bool:
        """Sync memory content between different AI tools."""
        source_manager = self.get_memory_manager(source_tool)
        target_manager = self.get_memory_manager(target_tool)
        
        if not source_manager or not target_manager:
            return False
        
        scoped_key = f"{scope.value}:{key}" if scope != MemoryScope.SESSION else key
        content = source_manager.retrieve(scoped_key)
        
        if content:
            return target_manager.save(scoped_key, content)
        
        return False

class UnifiedModeManager:
    """Manages modes across different AI tools."""
    
    @staticmethod
    def get_mode_manager(tool: AITool) -> Any:
        """Get the appropriate mode manager for the specified tool."""
        if tool == AITool.ROO and roo_available:
            return RooModeManager
        elif tool == AITool.CLINE and cline_available:
            return ClineModeManager
        else:
            logger.error(f"Mode manager not available for {tool}")
            return None
    
    @staticmethod
    def map_mode(mode: str, source_tool: AITool, target_tool: AITool) -> str:
        """Map a mode from one tool to the equivalent mode in another tool."""
        # Define mode mappings between tools
        mode_mappings = {
            (AITool.ROO, AITool.CLINE): {
                "architect": "plan",
                "code": "act",
                "reviewer": "plan",
                "ask": "plan",
                "strategy": "plan",
                "creative": "plan",
                "debug": "act",
                "orchestrator": "plan"
            },
            (AITool.CLINE, AITool.ROO): {
                "plan": "architect",
                "act": "code"
            }
        }
        
        mapping = mode_mappings.get((source_tool, target_tool))
        if mapping and mode in mapping:
            return mapping[mode]
        
        # Default fallback mappings
        if target_tool == AITool.ROO:
            return "orchestrator"
        elif target_tool == AITool.CLINE:
            return "plan"
        
        return mode
    
    @staticmethod
    def execute_in_mode(tool: AITool, mode: str, prompt: str, context: Optional[str] = None) -> Optional[str]:
        """Execute a prompt in the specified mode with the specified tool."""
        mode_manager = UnifiedModeManager.get_mode_manager(tool)
        
        if not mode_manager:
            logger.error(f"Cannot execute in mode: no mode manager available for {tool}")
            return None
        
        return mode_manager.execute_in_mode(mode, prompt, context)

class MCPWorkflowTemplate:
    """Represents a workflow template that can be executed by any AI tool."""
    
    def __init__(self, name: str, description: str, steps: List[Dict[str, Any]]):
        self.name = name
        self.description = description
        self.steps = steps
    
    def adapt_for_tool(self, tool: AITool) -> List[Dict[str, Any]]:
        """Adapt the workflow template for a specific AI tool."""
        adapted_steps = []
        
        for step in self.steps:
            adapted_step = step.copy()
            
            if "mode" in step:
                if tool == AITool.ROO and step["mode"] not in ROO_MODE_MAP:
                    adapted_step["mode"] = UnifiedModeManager.map_mode(step["mode"], AITool.CLINE, AITool.ROO)
                elif tool == AITool.CLINE and step["mode"] not in CLINE_MODE_MAP:
                    adapted_step["mode"] = UnifiedModeManager.map_mode(step["mode"], AITool.ROO, AITool.CLINE)
            
            adapted_steps.append(adapted_step)
        
        return adapted_steps

# Collection of unified workflow templates
UNIFIED_WORKFLOWS = {
    "mcp_system_review": MCPWorkflowTemplate(
        name="mcp_system_review",
        description="Review and analyze the existing MCP system implementation",
        steps=[
            {
                "type": "mode",
                "mode": "plan",  # Will be mapped to the appropriate mode for each tool
                "task": "Analyze the current MCP system architecture and identify any limitations or bottlenecks. Focus on cross-tool compatibility and integration points."
            },
            {
                "type": "mode",
                "mode": "plan",
                "task": "Review the existing MCP implementation for compliance with best practices. Check for proper error handling, security considerations, and performance optimizations."
            },
            {
                "type": "mode",
                "mode": "plan",
                "task": "Develop a strategy for enhancing the MCP system with improved cross-tool integration. Consider different usage scenarios and reliability requirements."
            }
        ]
    ),
    "cross_tool_memory_sync": MCPWorkflowTemplate(
        name="cross_tool_memory_sync",
        description="Set up and verify cross-tool memory synchronization",
        steps=[
            {
                "type": "mode",
                "mode": "plan",
                "task": "Design a cross-tool memory synchronization approach that ensures consistency between all AI assistants. Consider data formats, synchronization triggers, and conflict resolution."
            },
            {
                "type": "mode",
                "mode": "act",
                "task": "Implement the core memory synchronization components. Create adapters for each AI tool and establish a common data format."
            },
            {
                "type": "mode",
                "mode": "act",
                "task": "Create tests to verify memory synchronization between tools. Test retrieval, updates, and conflict scenarios."
            },
            {
                "type": "mode",
                "mode": "plan",
                "task": "Review the implementation and develop monitoring strategies to ensure ongoing synchronization integrity."
            }
        ]
    ),
    "context_window_management": MCPWorkflowTemplate(
        name="context_window_management",
        description="Optimize context window usage across AI tools",
        steps=[
            {
                "type": "mode",
                "mode": "plan",
                "task": "Analyze context window usage patterns across all AI tools. Identify optimization opportunities for token usage, memory structure, and information priority."
            },
            {
                "type": "mode",
                "mode": "act",
                "task": "Implement context window optimization techniques, including token pruning, context compression, and priority-based memory management."
            },
            {
                "type": "mode",
                "mode": "plan",
                "task": "Evaluate the optimizations and measure the improvements in context window utilization across all tools."
            }
        ]
    )
}

class UnifiedWorkflowOrchestrator:
    """Orchestrates workflows across different AI tools."""
    
    def __init__(self):
        self.memory_manager = UnifiedMemoryManager()
        self.execution_history = []
    
    def execute_workflow(self, workflow_name: str, parameters: Dict[str, Any] = None, 
                        tool: Optional[AITool] = None) -> str:
        """Execute a unified workflow using the specified tool."""
        if workflow_name not in UNIFIED_WORKFLOWS:
            return f"Workflow '{workflow_name}' not found"
        
        workflow = UNIFIED_WORKFLOWS[workflow_name]
        
        # Default to Roo if available, otherwise Cline
        tool = tool or (AITool.ROO if roo_available else AITool.CLINE if cline_available else None)
        
        if not tool:
            return "No AI tools available to execute workflow"
        
        # Adapt the workflow for the specific tool
        adapted_steps = workflow.adapt_for_tool(tool)
        
        # Execute the workflow
        if tool == AITool.ROO and roo_available:
            from roo_workflow_manager import SubtaskManager
            manager = SubtaskManager()
            result = manager.orchestrate_workflow(
                main_task=f"Execute workflow: {workflow.description}",
                subtasks=adapted_steps
            )
        elif tool == AITool.CLINE and cline_available:
            from cline_integration import ClineSubtaskManager
            manager = ClineSubtaskManager()
            result = manager.orchestrate_workflow(
                main_task=f"Execute workflow: {workflow.description}",
                subtasks=adapted_steps
            )
        else:
            return f"Cannot execute workflow with {tool}: tool not available"
        
        return result
    
    def execute_cross_tool_workflow(self, workflow_name: str, tools: List[AITool] = None) -> str:
        """Execute parts of a workflow across different tools, sharing context between them."""
        if workflow_name not in UNIFIED_WORKFLOWS:
            return f"Workflow '{workflow_name}' not found"
        
        workflow = UNIFIED_WORKFLOWS[workflow_name]
        
        # Default to all available tools if none specified
        available_tools = []
        if roo_available:
            available_tools.append(AITool.ROO)
        if cline_available:
            available_tools.append(AITool.CLINE)
        
        tools = tools or available_tools
        
        if not tools:
            return "No AI tools available to execute workflow"
        
        # Divide steps among tools
        steps_per_tool = len(workflow.steps) // len(tools)
        tool_assignments = {}
        
        for i, step in enumerate(workflow.steps):
            tool_index = min(i // steps_per_tool, len(tools) - 1)
            tool = tools[tool_index]
            
            if tool not in tool_assignments:
                tool_assignments[tool] = []
            
            tool_assignments[tool].append(step)
        
        # Execute steps for each tool
        results = []
        for tool, steps in tool_assignments.items():
            adapted_steps = workflow.adapt_for_tool(tool)
            
            if tool == AITool.ROO and roo_available:
                from roo_workflow_manager import SubtaskManager
                manager = SubtaskManager()
                task_description = f"Execute part of workflow: {workflow.description}"
                result = manager.orchestrate_workflow(task_description, adapted_steps)
            elif tool == AITool.CLINE and cline_available:
                from cline_integration import ClineSubtaskManager
                manager = ClineSubtaskManager()
                task_description = f"Execute part of workflow: {workflow.description}"
                result = manager.orchestrate_workflow(task_description, adapted_steps)
            else:
                result = f"Cannot execute workflow with {tool}: tool not available"
            
            results.append(f"Results from {tool.value}:\n{result}")
            
            # Save results to shared memory for next tool
            self.memory_manager.save(
                key=f"workflow_{workflow_name}_results_{tool.value}",
                content=result,
                scope=MemoryScope.GLOBAL
            )
        
        # Create unified summary
        summary = f"Cross-tool execution of {workflow_name} workflow:\n\n"
        summary += "\n\n".join(results)
        
        # Save unified summary
        self.memory_manager.save(
            key=f"workflow_{workflow_name}_summary",
            content=summary,
            scope=MemoryScope.GLOBAL
        )
        
        return summary

class MCPServerManager:
    """Manages MCP servers and their interactions."""
    
    @staticmethod
    def list_available_servers() -> List[str]:
        """List all available MCP servers."""
        try:
            # This command would need to be implemented in the MCP system
            cmd = ["mcp-cli", "list-servers"]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            servers = result.stdout.strip().split("\n")
            return servers
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Failed to list MCP servers")
            return []
    
    @staticmethod
    def check_server_status(server_name: str) -> bool:
        """Check if an MCP server is running."""
        try:
            cmd = ["mcp-cli", "status", server_name]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            status = result.stdout.strip()
            return "running" in status.lower()
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error(f"Failed to check status of MCP server: {server_name}")
            return False
    
    @staticmethod
    def start_server(server_name: str) -> bool:
        """Start an MCP server."""
        try:
            cmd = ["mcp-cli", "start", server_name]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error(f"Failed to start MCP server: {server_name}")
            return False
    
    @staticmethod
    def stop_server(server_name: str) -> bool:
        """Stop an MCP server."""
        try:
            cmd = ["mcp-cli", "stop", server_name]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error(f"Failed to stop MCP server: {server_name}")
            return False
    
    @staticmethod
    def execute_server_operation(server_name: str, operation: str, parameters: Dict[str, Any] = None) -> Optional[str]:
        """Execute an operation on an MCP server."""
        try:
            cmd = ["mcp-cli", "execute", server_name, operation]
            
            if parameters:
                cmd.append(json.dumps(parameters))
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error(f"Failed to execute operation on MCP server: {server_name}")
            return None

def main():
    """Command line interface for the unified MCP orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified MCP Orchestrator")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Execute workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Execute a unified workflow")
    workflow_parser.add_argument("--name", required=True, choices=UNIFIED_WORKFLOWS.keys(), 
                                help="Name of the workflow to execute")
    workflow_parser.add_argument("--tool", choices=[t.value for t in AITool], 
                                help="Tool to use for execution")
    
    # Cross-tool workflow command
    cross_tool_parser = subparsers.add_parser("cross-tool", help="Execute a workflow across multiple tools")
    cross_tool_parser.add_argument("--name", required=True, choices=UNIFIED_WORKFLOWS.keys(),
                                 help="Name of the workflow to execute")
    cross_tool_parser.add_argument("--tools", nargs="+", choices=[t.value for t in AITool],
                                 help="Tools to use for execution")
    
    # Memory operations
    memory_parser = subparsers.add_parser("memory", help="Perform memory operations")
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command", help="Memory operation to perform")
    
    # Get memory
    get_memory_parser = memory_subparsers.add_parser("get", help="Get memory content")
    get_memory_parser.add_argument("--key", required=True, help="Memory key")
    get_memory_parser.add_argument("--scope", choices=[s.value for s in MemoryScope], default="session",
                                 help="Memory scope")
    get_memory_parser.add_argument("--tool", choices=[t.value for t in AITool],
                                 help="Tool to use for memory operation")
    
    # Set memory
    set_memory_parser = memory_subparsers.add_parser("set", help="Set memory content")
    set_memory_parser.add_argument("--key", required=True, help="Memory key")
    set_memory_parser.add_argument("--content", required=True, help="Memory content")
    set_memory_parser.add_argument("--scope", choices=[s.value for s in MemoryScope], default="session",
                                 help="Memory scope")
    set_memory_parser.add_argument("--tool", choices=[t.value for t in AITool],
                                 help="Tool to use for memory operation")
    
    # Sync memory
    sync_memory_parser = memory_subparsers.add_parser("sync", help="Sync memory between tools")
    sync_memory_parser.add_argument("--key", required=True, help="Memory key")
    sync_memory_parser.add_argument("--source", required=True, choices=[t.value for t in AITool],
                                  help="Source tool")
    sync_memory_parser.add_argument("--target", required=True, choices=[t.value for t in AITool],
                                  help="Target tool")
    sync_memory_parser.add_argument("--scope", choices=[s.value for s in MemoryScope], default="session",
                                  help="Memory scope")
    
    # Server operations
    server_parser = subparsers.add_parser("server", help="Perform MCP server operations")
    server_subparsers = server_parser.add_subparsers(dest="server_command", help="Server operation to perform")
    
    # List servers
    list_servers_parser = server_subparsers.add_parser("list", help="List available MCP servers")
    
    # Check server status
    status_server_parser = server_subparsers.add_parser("status", help="Check MCP server status")
    status_server_parser.add_argument("--name", required=True, help="Server name")
    
    # Start server
    start_server_parser = server_subparsers.add_parser("start", help="Start MCP server")
    start_server_parser.add_argument("--name", required=True, help="Server name")
    
    # Stop server
    stop_server_parser = server_subparsers.add_parser("stop", help="Stop MCP server")
    stop_server_parser.add_argument("--name", required=True, help="Server name")
    
    # Execute server operation
    execute_server_parser = server_subparsers.add_parser("execute", help="Execute operation on MCP server")
    execute_server_parser.add_argument("--name", required=True, help="Server name")
    execute_server_parser.add_argument("--operation", required=True, help="Operation name")
    execute_server_parser.add_argument("--parameters", help="JSON string of parameters")
    
    # List workflows
    list_workflows_parser = subparsers.add_parser("list-workflows", help="List available unified workflows")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == "workflow":
        tool = AITool(args.tool) if args.tool else None
        orchestrator = UnifiedWorkflowOrchestrator()
        result = orchestrator.execute_workflow(args.name, tool=tool)
        print(result)
    
    elif args.command == "cross-tool":
        tools = [AITool(t) for t in args.tools] if args.tools else None
        orchestrator = UnifiedWorkflowOrchestrator()
        result = orchestrator.execute_cross_tool_workflow(args.name, tools=tools)
        print(result)
    
    elif args.command == "memory":
        memory_manager = UnifiedMemoryManager()
        
        if args.memory_command == "get":
            tool = AITool(args.tool) if args.tool else None
            content = memory_manager.retrieve(
                args.key,
                scope=MemoryScope(args.scope),
                tool=tool
            )
            if content:
                print(content)
            else:
                print(f"No content found for key: {args.key}")
                sys.exit(1)
        
        elif args.memory_command == "set":
            tool = AITool(args.tool) if args.tool else None
            result = memory_manager.save(
                args.key,
                args.content,
                scope=MemoryScope(args.scope),
                tool=tool
            )
            print(f"Memory set {'succeeded' if result else 'failed'}")
        
        elif args.memory_command == "sync":
            result = memory_manager.sync_between_tools(
                args.key,
                source_tool=AITool(args.source),
                target_tool=AITool(args.target),
                scope=MemoryScope(args.scope)
            )
            print(f"Memory sync {'succeeded' if result else 'failed'}")
    
    elif args.command == "server":
        server_manager = MCPServerManager()
        
        if args.server_command == "list":
            servers = server_manager.list_available_servers()
            for server in servers:
                print(server)
        
        elif args.server_command == "status":
            status = server_manager.check_server_status(args.name)
            print(f"Server {args.name} is {'running' if status else 'not running'}")
        
        elif args.server_command == "start":
            result = server_manager.start_server(args.name)
            print(f"Server start {'succeeded' if result else 'failed'}")
        
        elif args.server_command == "stop":
            result = server_manager.stop_server(args.name)
            print(f"Server stop {'succeeded' if result else 'failed'}")
        
        elif args.server_command == "execute":
            parameters = None
            if args.parameters:
                try:
                    parameters = json.loads(args.parameters)
                except json.JSONDecodeError:
                    print(f"Error parsing parameters JSON: {args.parameters}")
                    sys.exit(1)
            
            result = server_manager.execute_server_operation(args.name, args.operation, parameters)
            if result:
                print(result)
            else:
                print("Operation failed")
                sys.exit(1)
    
    elif args.command == "list-workflows":
        print("Available unified workflows:")
        for name, workflow in UNIFIED_WORKFLOWS.items():
            print(f"  - {name}: {workflow.description}")
            print(f"    Steps: {len(workflow.steps)}")
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()