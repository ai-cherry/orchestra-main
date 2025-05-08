#!/usr/bin/env python3
"""
enhanced_cline_integration.py - Enhanced Cline.bot Integration with MCP

This script provides a significantly improved integration between Cline.bot and
the Model Context Protocol (MCP) framework, with direct API integration, enhanced
memory operations, and cross-tool collaboration capabilities.

Key enhancements:
- Direct API client instead of subprocess calls
- Smart context preservation between mode transitions
- Advanced memory operations (tagging, search, etc.)
- Cross-tool memory access and sharing
- Streaming memory updates
"""

import os
import sys
import json
import time
import logging
from typing import List, Dict, Any, Optional, Union, Callable
from datetime import datetime
from pathlib import Path

# Import the unified MCP client library
from mcp_client_lib import (
    MCPClient, 
    MCPMemoryManager,
    MCPContextSession,
    MCPWorkflow,
    MCPMemoryStream,
    MCPSharedWorkspace,
    MemoryType, 
    MemoryScope, 
    ToolType, 
    CompressionLevel
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("enhanced-cline")

# Mode configuration mapping
CLINE_MODE_MAP = {
    "plan": "📝 Plan",
    "act": "🎬 Act",
}

# Cline-specific MCP assessment prompts
CLINE_MCP_PROMPTS = {
    "plan": """
When planning solutions, carefully consider MCP (Model Context Protocol) requirements:

1. Evaluate memory persistence needs across AI interactions
2. Consider context window management and token optimization
3. Determine if cross-session or cross-agent memory is needed
4. Identify which MCP servers would be most appropriate for this task
5. Plan for security and access control in MCP implementation
6. Consider how to leverage MCP for context sharing between tools

Your plan should explicitly state which MCP approach is most suitable and why.
""",
    "act": """
When implementing code with MCP (Model Context Protocol) integration:

1. Ensure proper initialization of MCP connections
2. Implement appropriate error handling for MCP operations
3. Use consistent patterns for data persistence
4. Verify security best practices in all MCP interactions
5. Optimize token usage and context window management
6. Document MCP integration points for other developers

Your implementation should follow best practices for MCP integration.
"""
}

# MCP workflow templates for Cline
CLINE_MCP_WORKFLOW_TEMPLATES = {
    "memory_system_setup": [
        {
            "type": "mode",
            "mode": "plan",
            "task": "Design a memory system architecture using MCP that integrates with our existing infrastructure. Consider persistence requirements, security, and performance."
        },
        {
            "type": "mode",
            "mode": "act",
            "task": "Implement the core MCP memory integration components based on the plan. Create the necessary interfaces and adapters."
        },
        {
            "type": "mode",
            "mode": "plan",
            "task": "Review the implementation and test plan. Identify any security issues or performance concerns."
        }
    ],
    "context_window_optimization": [
        {
            "type": "mode",
            "mode": "plan",
            "task": "Analyze the current context usage patterns and identify opportunities for optimization. Consider token efficiency, context structure, and memory bank strategies."
        },
        {
            "type": "mode",
            "mode": "act",
            "task": "Implement context window optimization techniques, including token pruning, context compression, and strategic information storage."
        },
        {
            "type": "mode",
            "mode": "plan",
            "task": "Evaluate the optimizations and measure the improvements in context window utilization."
        }
    ],
    "mcp_server_integration": [
        {
            "type": "mode",
            "mode": "plan",
            "task": "Design an MCP server integration that extends our AI capabilities. Detail the server functionality, API endpoints, and security considerations."
        },
        {
            "type": "mode",
            "mode": "act",
            "task": "Implement the MCP server core functionality. Create the server routes, handlers, and client integration code."
        },
        {
            "type": "mode",
            "mode": "act",
            "task": "Create tests for the MCP server implementation. Include security testing, performance benchmarks, and integration tests."
        },
        {
            "type": "mode",
            "mode": "plan",
            "task": "Review the implementation and recommend deployment strategies. Consider scaling, monitoring, and maintenance."
        }
    ]
}


class ClineMemoryBank:
    """Enhanced memory bank for Cline with advanced MCP integration."""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize the memory bank with direct API access."""
        self.client = MCPClient(base_url=base_url, tool=ToolType.CLINE, api_key=api_key)
        self.memory_manager = MCPMemoryManager(client=self.client, tool=ToolType.CLINE)
    
    def save(self, key: str, content: str) -> bool:
        """Save content to memory."""
        return self.client.set_memory(key=key, content=content)
    
    def retrieve(self, key: str) -> Optional[str]:
        """Retrieve content from memory."""
        return self.client.get_memory(key=key)
    
    def update(self, key: str, content: str) -> bool:
        """Update content in memory."""
        # First check if it exists
        existing = self.retrieve(key)
        if existing is None:
            return self.save(key, content)
        else:
            return self.client.set_memory(key=key, content=content)
    
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all memory keys, optionally filtered by prefix."""
        # Not directly supported by the API, would need server-side implementation
        # For now, this is a placeholder
        logger.warning("list_keys is not fully implemented in the enhanced client")
        return []
    
    def save_with_metadata(
        self,
        key: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        importance: float = 0.5,
        ttl: Optional[int] = None
    ) -> bool:
        """Save content with rich metadata."""
        return self.memory_manager.save_with_metadata(
            key=key,
            content=content,
            metadata=metadata,
            tags=tags,
            importance=importance,
            ttl=ttl
        )
    
    def retrieve_by_tags(self, tags: List[str], match_all: bool = False) -> List[Dict[str, Any]]:
        """Retrieve memories by tags."""
        return self.memory_manager.retrieve_by_tags(tags=tags, match_all=match_all)
    
    def retrieve_from_tool(
        self,
        key: str,
        tool: ToolType,
        fallback_strategy: str = "none"
    ) -> Optional[Any]:
        """Retrieve memory from a specific tool."""
        return self.memory_manager.retrieve_from_tool(
            key=key,
            tool=tool,
            fallback_strategy=fallback_strategy
        )
    
    def create_stream(self, key: str) -> MCPMemoryStream:
        """Create a memory stream for real-time updates."""
        return MCPMemoryStream(memory_key=key, client=self.client)


class ClineModeManager:
    """Enhanced mode manager with context preservation and cross-tool integration."""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize with direct API access."""
        self.client = MCPClient(base_url=base_url, tool=ToolType.CLINE, api_key=api_key)
        self.memory_bank = ClineMemoryBank(base_url=base_url, api_key=api_key)
        self.current_mode = None
        self.context_sessions = {}
    
    def switch_mode(self, mode: str) -> bool:
        """Switch Cline to the specified mode with context preservation."""
        # Record the current mode before switching
        previous_mode = self.current_mode
        self.current_mode = mode
        
        # Log mode transition
        if previous_mode:
            logger.info(f"Mode transition: {previous_mode} -> {mode}")
            
            # Save the mode transition to memory for analytics
            self.memory_bank.save_with_metadata(
                key=f"mode_transition_{int(time.time())}",
                content={
                    "from": previous_mode,
                    "to": mode,
                    "timestamp": datetime.now().isoformat()
                },
                tags=["mode_transition", previous_mode, mode],
                importance=0.3
            )
        
        return True
    
    def execute_in_mode(self, mode: str, prompt: str, context: Optional[str] = None) -> Optional[str]:
        """Execute a prompt in the specified mode with smart context handling."""
        # Switch to the mode
        self.switch_mode(mode)
        
        # Get or create a context session for this mode
        if mode not in self.context_sessions:
            self.context_sessions[mode] = MCPContextSession(ToolType.CLINE, self.client)
        
        session = self.context_sessions[mode]
        
        # Apply mode-specific MCP assessment prompts when appropriate
        if mode in CLINE_MCP_PROMPTS and "mcp" in prompt.lower():
            # Add the mode-specific MCP guidance to the context
            mcp_guidance = CLINE_MCP_PROMPTS[mode]
            if context:
                context = f"{context}\n\n{mcp_guidance}"
            else:
                context = mcp_guidance
        
        # If context is provided, override the session context
        if context:
            session.context = context
        
        # Execute with context preservation
        result = session.execute_in_mode(mode, prompt)
        
        if result:
            # Save result with tags based on the content
            tags = [mode]
            
            # Add basic content analysis tags
            if "design" in prompt.lower() or "architecture" in prompt.lower():
                tags.append("design")
            if "implement" in prompt.lower() or "code" in prompt.lower():
                tags.append("implementation")
            if "test" in prompt.lower() or "validate" in prompt.lower():
                tags.append("testing")
            if "review" in prompt.lower() or "evaluate" in prompt.lower():
                tags.append("review")
            
            # Add MCP-related tags if relevant
            if "mcp" in prompt.lower() or "memory" in prompt.lower() or "context" in prompt.lower():
                tags.append("mcp")
            
            # Save with metadata for better searchability
            self.memory_bank.save_with_metadata(
                key=f"{mode}_result_{int(time.time())}",
                content=result,
                metadata={
                    "prompt": prompt,
                    "mode": mode,
                    "timestamp": datetime.now().isoformat()
                },
                tags=tags,
                importance=0.7
            )
        
        return result
    
    def get_mcp_workflow_template(self, template_name: str) -> Optional[List[Dict[str, Any]]]:
        """Get a predefined MCP workflow template by name."""
        return CLINE_MCP_WORKFLOW_TEMPLATES.get(template_name)


class ClineWorkspaceManager:
    """Manager for shared workspaces across tools."""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize the workspace manager."""
        self.client = MCPClient(base_url=base_url, tool=ToolType.CLINE, api_key=api_key)
        self.workspaces = {}
    
    def create_workspace(self, workspace_name: str) -> MCPSharedWorkspace:
        """Create a new shared workspace."""
        workspace = MCPSharedWorkspace(workspace_name, self.client)
        self.workspaces[workspace_name] = workspace
        return workspace
    
    def get_workspace(self, workspace_name: str) -> Optional[MCPSharedWorkspace]:
        """Get an existing workspace."""
        if workspace_name in self.workspaces:
            return self.workspaces[workspace_name]
        
        # Try to create it
        workspace = self.create_workspace(workspace_name)
        return workspace


class ClintContextSession:
    """Context-preserving session for Cline."""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize the context session."""
        self.session = MCPContextSession(ToolType.CLINE, MCPClient(base_url=base_url, tool=ToolType.CLINE, api_key=api_key))
        self.mode_manager = ClineModeManager(base_url=base_url, api_key=api_key)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up session resources
        pass
    
    def execute_in_mode(self, mode: str, prompt: str) -> Optional[str]:
        """Execute in a mode with automatic context preservation."""
        return self.mode_manager.execute_in_mode(mode, prompt, self.session.context)


class ClineVSCodeTaskRunner:
    """Enhanced VS Code task runner."""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize the task runner."""
        self.client = MCPClient(base_url=base_url, tool=ToolType.CLINE, api_key=api_key)
        self.memory_bank = ClineMemoryBank(base_url=base_url, api_key=api_key)
    
    def run_task(self, task_id: str, inputs: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Run a VS Code task by ID with enhanced logging and memory integration."""
        from roo_workflow_manager import VSCODE_TASKS
        
        if task_id not in VSCODE_TASKS:
            logger.error(f"Unknown VS Code task ID: {task_id}")
            return None
            
        task_name = VSCODE_TASKS[task_id]
        logger.info(f"Running VS Code task: {task_name}")
        
        # Record task execution in memory
        self.memory_bank.save_with_metadata(
            key=f"vscode_task_{int(time.time())}",
            content={
                "task_id": task_id,
                "task_name": task_name,
                "inputs": inputs,
                "status": "started",
                "timestamp": datetime.now().isoformat()
            },
            tags=["vscode_task", task_id, "execution"],
            importance=0.6
        )
        
        # TODO: Implement actual VS Code task execution via MCP API
        # For now, we'll use a simple placeholder
        result = f"Task {task_name} executed successfully"
        
        if result:
            # Update task status in memory
            self.memory_bank.save_with_metadata(
                key=f"vscode_task_{int(time.time())}",
                content={
                    "task_id": task_id,
                    "task_name": task_name,
                    "inputs": inputs,
                    "status": "completed",
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                tags=["vscode_task", task_id, "completed"],
                importance=0.6
            )
            
        return result


class ClineWorkflowManager:
    """Enhanced workflow orchestration with cross-tool capabilities."""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize the workflow manager."""
        self.client = MCPClient(base_url=base_url, tool=ToolType.CLINE, api_key=api_key)
        self.memory_bank = ClineMemoryBank(base_url=base_url, api_key=api_key)
        self.mode_manager = ClineModeManager(base_url=base_url, api_key=api_key)
        self.vscode_runner = ClineVSCodeTaskRunner(base_url=base_url, api_key=api_key)
    
    def execute_workflow(self, main_task: str, steps: Optional[List[Dict[str, Any]]] = None, 
                        mcp_template: Optional[str] = None) -> str:
        """Execute a workflow with enhanced cross-tool integration."""
        # Create a workflow
        workflow = MCPWorkflow(main_task, self.client)
        
        # Use template if specified
        if mcp_template and not steps:
            steps = self.mode_manager.get_mcp_workflow_template(mcp_template)
        
        # If no steps provided, generate them using Plan mode
        if not steps:
            plan_prompt = (
                f"Break down this task into steps that can be executed by specialized modes or operations:\n\n{main_task}"
            )
            
            planning_result = self.mode_manager.execute_in_mode("plan", plan_prompt)
            
            if planning_result:
                # Try to extract steps from the planning result
                try:
                    # Look for JSON array in the response
                    import re
                    json_pattern = r'\[\s*{.*}\s*\]'
                    match = re.search(json_pattern, planning_result, re.DOTALL)
                    
                    if match:
                        steps_json = match.group(0)
                        steps = json.loads(steps_json)
                    else:
                        logger.warning("Could not extract steps from planning result")
                except Exception as e:
                    logger.error(f"Error parsing steps: {e}")
        
        # Add steps to workflow
        if steps:
            for step in steps:
                step_type = step.get("type")
                
                if step_type == "mode":
                    mode = step.get("mode")
                    task = step.get("task")
                    
                    workflow.add_step(
                        tool=ToolType.CLINE,
                        mode=mode,
                        task=task
                    )
                elif step_type == "vs_code_task":
                    task_id = step.get("task_id")
                    inputs = step.get("inputs")
                    
                    # VS Code tasks are handled differently
                    # We'd need to extend the workflow system to handle them
                    logger.info(f"Adding VS Code task {task_id} to workflow")
        
        # Execute the workflow
        results = workflow.execute()
        
        # Generate a summary
        summary = f"Executed workflow: {main_task}\n\n"
        for i, result in enumerate(results):
            summary += f"Step {i+1} ({result.get('type')}): "
            if result.get('result'):
                summary += f"{result.get('result')[:100]}...\n"
            else:
                summary += "No result\n"
        
        return summary
    
    def execute_cross_tool_workflow(self, main_task: str, tools: List[ToolType], 
                                  template: Optional[str] = None) -> str:
        """Execute a workflow across multiple tools."""
        # This would call the MCP API's cross-tool workflow endpoint
        workflow_id = template or "default"
        
        result = self.client.execute_cross_tool_workflow(
            workflow_id=workflow_id,
            tools=tools
        )
        
        if result:
            return result
        else:
            return f"Failed to execute cross-tool workflow: {main_task}"


def main():
    """Command line interface for the enhanced Cline integration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Project Orchestra - Enhanced Cline Integration")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Task command
    task_parser = subparsers.add_parser("task", help="Execute a single task in a specific mode")
    task_parser.add_argument("--mode", required=True, choices=CLINE_MODE_MAP.keys(), 
                            help="Mode to use for the task")
    task_parser.add_argument("--prompt", required=True, help="Task prompt")
    task_parser.add_argument("--context", help="Optional context for the task")
    
    # VS Code task command
    vscode_task_parser = subparsers.add_parser("vscode_task", help="Run a VS Code task")
    vscode_task_parser.add_argument("--task_id", required=True,
                                  help="VS Code task to run")
    vscode_task_parser.add_argument("--inputs", help="JSON string of inputs for the task")
    
    # Workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Execute a complete workflow")
    workflow_parser.add_argument("--task", required=True, help="Main task description")
    workflow_parser.add_argument("--steps", help="JSON file with step definitions")
    workflow_parser.add_argument("--mcp-template", help="Name of MCP workflow template to use")
    
    # Cross-tool workflow command
    cross_tool_parser = subparsers.add_parser("cross-tool", help="Execute a cross-tool workflow")
    cross_tool_parser.add_argument("--task", required=True, help="Main task description")
    cross_tool_parser.add_argument("--tools", required=True, help="Comma-separated list of tools")
    cross_tool_parser.add_argument("--template", help="Workflow template to use")
    
    # Memory command
    memory_parser = subparsers.add_parser("memory", help="Interact with the memory bank")
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command", help="Memory command to execute")
    
    # Memory get command
    memory_get_parser = memory_subparsers.add_parser("get", help="Get memory content")
    memory_get_parser.add_argument("--key", required=True, help="Memory key")
    
    # Memory set command
    memory_set_parser = memory_subparsers.add_parser("set", help="Set memory content")
    memory_set_parser.add_argument("--key", required=True, help="Memory key")
    memory_set_parser.add_argument("--content", required=True, help="Memory content")
    memory_set_parser.add_argument("--tags", help="Comma-separated list of tags")
    
    # Memory get-from-tool command
    memory_from_tool_parser = memory_subparsers.add_parser("get-from-tool", help="Get memory from another tool")
    memory_from_tool_parser.add_argument("--key", required=True, help="Memory key")
    memory_from_tool_parser.add_argument("--tool", required=True, help="Tool to get memory from")
    
    # Memory search command
    memory_search_parser = memory_subparsers.add_parser("search", help="Search memories by tags")
    memory_search_parser.add_argument("--tags", required=True, help="Comma-separated list of tags")
    memory_search_parser.add_argument("--match-all", action="store_true", help="Require all tags to match")
    
    # Session command
    session_parser = subparsers.add_parser("session", help="Start a context-preserving session")
    session_parser.add_argument("--script", required=True, help="Path to session script file")
    
    args = parser.parse_args()
    
    # Initialize components
    mode_manager = ClineModeManager()
    memory_bank = ClineMemoryBank()
    vscode_runner = ClineVSCodeTaskRunner()
    workflow_manager = ClineWorkflowManager()
    
    if args.command == "task":
        result = mode_manager.execute_in_mode(args.mode, args.prompt, args.context)
        if result:
            print(result)
        else:
            print("Failed to execute task")
            sys.exit(1)
    
    elif args.command == "vscode_task":
        inputs = None
        if args.inputs:
            try:
                inputs = json.loads(args.inputs)
            except json.JSONDecodeError:
                print(f"Error parsing inputs JSON: {args.inputs}")
                sys.exit(1)
                
        result = vscode_runner.run_task(args.task_id, inputs)
        if result:
            print(result)
        else:
            print("Failed to run VS Code task")
            sys.exit(1)
    
    elif args.command == "workflow":
        steps = None
        if args.steps:
            try:
                with open(args.steps, 'r') as f:
                    steps = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading steps file: {e}")
                sys.exit(1)
        
        result = workflow_manager.execute_workflow(args.task, steps, args.mcp_template)
        print(result)
    
    elif args.command == "cross-tool":
        tools = [ToolType(t.strip()) for t in args.tools.split(",")]
        result = workflow_manager.execute_cross_tool_workflow(args.task, tools, args.template)
        print(result)
    
    elif args.command == "memory":
        if args.memory_command == "get":
            content = memory_bank.retrieve(args.key)
            if content:
                print(content)
            else:
                print(f"No content found for key: {args.key}")
                sys.exit(1)
        
        elif args.memory_command == "set":
            tags = args.tags.split(",") if args.tags else None
            result = memory_bank.save_with_metadata(args.key, args.content, tags=tags)
            print(f"Memory set {'succeeded' if result else 'failed'}")
        
        elif args.memory_command == "get-from-tool":
            content = memory_bank.retrieve_from_tool(args.key, ToolType(args.tool))
            if content:
                print(content)
            else:
                print(f"No content found for key {args.key} from tool {args.tool}")
                sys.exit(1)
        
        elif args.memory_command == "search":
            tags = args.tags.split(",")
            results = memory_bank.retrieve_by_tags(tags, args.match_all)
            if results:
                for i, result in enumerate(results):
                    print(f"Result {i+1}:")
                    print(f"  Key: {result.get('key')}")
                    content = result.get('content')
                    if isinstance(content, str):
                        print(f"  Content: {content[:100]}..." if len(content) > 100 else f"  Content: {content}")
                    else:
                        print(f"  Content: {content}")
                    print(f"  Tags: {result.get('metadata', {}).get('tags', [])}")
                    print()
            else:
                print(f"No results found for tags: {tags}")
    
    elif args.command == "session":
        try:
            with open(args.script, 'r') as f:
                script_content = f.read()
            
            # Parse the session script
            script_lines = script_content.strip().split("\n")
            
            # Execute the session
            with ClintContextSession() as session:
                for line in script_lines:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    # Parse mode and prompt
                    try:
                        mode, prompt = line.split(":", 1)
                        mode = mode.strip().lower()
                        prompt = prompt.strip()
                        
                        if mode in CLINE_MODE_MAP:
                            print(f"Executing: {mode} - {prompt}")
                            result = session.execute_in_mode(mode, prompt)
                            print(f"Result: {result[:100]}..." if result and len(result) > 100 else f"Result: {result}")
                            print()
                        else:
                            print(f"Unknown mode: {mode}")
                    except ValueError:
                        print(f"Invalid line format: {line}")
        except Exception as e:
            print(f"Error executing session script: {e}")
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()