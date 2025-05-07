#!/usr/bin/env python3
"""
cline_integration.py - Cline.bot Integration for Project Orchestra

This script integrates Cline.bot with the Project Orchestra framework, 
providing similar capabilities to Roo while leveraging Cline's unique features.
It serves as a bridge between Cline.bot AI capabilities and Orchestra's infrastructure.

Key features:
- Memory management via MCP
- Task orchestration 
- Integration with VS Code tasks
- Context management
- Tool execution
"""

import os
import sys
import json
import logging
import subprocess
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("cline-orchestrator")

# Mode configuration mapping (used for Cline)
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
    """Handles interaction with Cline MCP Memory Bank."""
    
    @staticmethod
    def save(key: str, content: str) -> bool:
        """Save content to memory MCP."""
        try:
            # Cline CLI memory save command
            cmd = ["cline-cli", "mcp", "memory_bank_write", "--key", key, "--content", content]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Saved to memory: {key}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to save to memory: {e.stdout} / {e.stderr}")
            return False

    @staticmethod
    def retrieve(key: str) -> Optional[str]:
        """Retrieve content from memory MCP."""
        try:
            # Cline CLI memory retrieve command
            cmd = ["cline-cli", "mcp", "memory_bank_read", "--key", key]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Retrieved from memory: {key}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to retrieve from memory: {e.stdout} / {e.stderr}")
            return None
    
    @staticmethod
    def update(key: str, content: str) -> bool:
        """Update content in memory MCP."""
        try:
            # Cline CLI memory update command
            cmd = ["cline-cli", "mcp", "memory_bank_update", "--key", key, "--content", content]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Updated memory: {key}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to update memory: {e.stdout} / {e.stderr}")
            return False
    
    @staticmethod
    def list_keys(prefix: Optional[str] = None) -> List[str]:
        """List all memory keys, optionally filtered by prefix."""
        try:
            # Cline CLI memory list command
            cmd = ["cline-cli", "mcp", "memory_bank_list"]
            if prefix:
                cmd.extend(["--prefix", prefix])
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            keys = result.stdout.strip().split("\n")
            logger.info(f"Listed {len(keys)} memory keys" + (f" with prefix {prefix}" if prefix else ""))
            return keys
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list memory keys: {e.stdout} / {e.stderr}")
            return []

class ClineModeManager:
    """Manages interactions with Cline modes."""
    
    @staticmethod
    def switch_mode(mode: str) -> bool:
        """Switch Cline to the specified mode."""
        try:
            cmd = ["cline-cli", "mode", mode]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Switched to mode: {mode}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to switch mode: {e.stdout} / {e.stderr}")
            return False
    
    @staticmethod
    def execute_in_mode(mode: str, prompt: str, context: Optional[str] = None) -> Optional[str]:
        """Execute a prompt in the specified mode with optional context."""
        try:
            # Apply mode-specific MCP assessment prompts when appropriate
            if mode in CLINE_MCP_PROMPTS and "mcp" in prompt.lower():
                # Add the mode-specific MCP guidance to the context
                mcp_guidance = CLINE_MCP_PROMPTS[mode]
                if context:
                    context = f"{context}\n\n{mcp_guidance}"
                else:
                    context = mcp_guidance
            
            full_prompt = prompt
            if context:
                full_prompt = f"{context}\n\n{prompt}"
            
            # Use MCP to execute in the appropriate mode
            cmd = ["cline-cli", "mcp", "execute", 
                  "--mode", mode, "--prompt", full_prompt]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Parse the JSON response
            response_data = json.loads(result.stdout)
            return response_data.get("result")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to execute in mode {mode}: {e.stdout} / {e.stderr}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Failed to parse response from MCP")
            return None

    @staticmethod
    def get_mcp_workflow_template(template_name: str) -> Optional[List[Dict[str, Any]]]:
        """Get a predefined MCP workflow template by name."""
        return CLINE_MCP_WORKFLOW_TEMPLATES.get(template_name)
    
    @staticmethod
    def run_tool(tool_name: str, parameters: Dict[str, Any]) -> Optional[str]:
        """Run a Cline tool via MCP."""
        try:
            cmd = ["cline-cli", "mcp", "tool", tool_name]
            for key, value in parameters.items():
                cmd.extend([f"--{key}", str(value)])
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Ran tool {tool_name}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to run tool {tool_name}: {e.stdout} / {e.stderr}")
            return None

class VSCodeTaskRunner:
    """Handles running VS Code tasks from the orchestrator."""
    
    @staticmethod
    def run_task(task_id: str, inputs: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Run a VS Code task by ID."""
        from roo_workflow_manager import VSCODE_TASKS
        
        if task_id not in VSCODE_TASKS:
            logger.error(f"Unknown VS Code task ID: {task_id}")
            return None
            
        task_name = VSCODE_TASKS[task_id]
        logger.info(f"Running VS Code task: {task_name}")
        
        try:
            # Construct command for VS Code task
            cmd = ["cline-cli", "terminal", "--command", f"Run VS Code task: {task_name}"]
            
            # Add inputs if provided
            if inputs:
                inputs_arg = json.dumps(inputs)
                cmd.extend(["--inputs", inputs_arg])
                
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"VS Code task completed: {task_name}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to run VS Code task: {e.stdout} / {e.stderr}")
            return None

class ClineSubtaskManager:
    """Manages Cline subtasks and their orchestration."""
    
    def __init__(self):
        self.memory = ClineMemoryBank()
        self.mode_manager = ClineModeManager()
        self.vscode_runner = VSCodeTaskRunner()
        self.execution_history = []
    
    def _get_next_subtask_id(self) -> str:
        """Generate a unique ID for the next subtask."""
        return f"subtask_{len(self.execution_history) + 1}"
    
    def _save_subtask_result(self, subtask_id: str, mode: str, task: str, result: str) -> None:
        """Save subtask result to memory and update execution history."""
        # Save to memory bank
        self.memory.save(f"{subtask_id}_result", result)
        
        # Update execution history
        self.execution_history.append({
            "id": subtask_id,
            "mode": mode,
            "task": task,
            "result_summary": result[:100] + "..." if len(result) > 100 else result
        })
        
        # Save updated execution history
        self.memory.update("execution_history", json.dumps(self.execution_history))
    
    def execute_subtask(self, mode: str, task: str, context: Optional[str] = None) -> Optional[str]:
        """Execute a single subtask in the specified mode."""
        subtask_id = self._get_next_subtask_id()
        logger.info(f"Executing subtask {subtask_id} in mode '{mode}': {task[:50]}...")
        
        # Switch to the appropriate mode
        self.mode_manager.switch_mode(mode)
        
        # Execute the task in that mode
        result = self.mode_manager.execute_in_mode(mode, task, context)
        
        if result:
            # Save the result
            self._save_subtask_result(subtask_id, mode, task, result)
            return result
        
        return None
    
    def execute_vs_code_task(self, task_id: str, inputs: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Execute a VS Code task as part of a workflow."""
        subtask_id = self._get_next_subtask_id()
        from roo_workflow_manager import VSCODE_TASKS
        task_name = VSCODE_TASKS.get(task_id, task_id)
        logger.info(f"Executing VS Code task {subtask_id}: {task_name}")
        
        # Run the VS Code task
        result = self.vscode_runner.run_task(task_id, inputs)
        
        if result:
            # Save the result to memory
            self.memory.save(f"{subtask_id}_vs_code_task", result)
            
            # Update execution history
            self.execution_history.append({
                "id": subtask_id,
                "type": "vs_code_task",
                "task": task_name,
                "result_summary": result[:100] + "..." if len(result) > 100 else result
            })
            
            # Save updated execution history
            self.memory.update("execution_history", json.dumps(self.execution_history))
            
            return result
        
        return None
    
    def orchestrate_workflow(self, main_task: str, subtasks: Optional[List[Dict[str, Any]]] = None, 
                            use_mcp_template: Optional[str] = None) -> str:
        """
        Orchestrate a complete workflow with multiple subtasks.
        
        Args:
            main_task: The overall task description
            subtasks: Optional list of task definitions with mode/operation and parameters
            use_mcp_template: Optional name of an MCP workflow template to use
            
        Returns:
            Final consolidated result
        """
        logger.info(f"Starting workflow orchestration for: {main_task}")
        
        # Clear execution history for this workflow
        self.execution_history = []
        
        # Save the main task to memory
        self.memory.save("main_task", main_task)
        
        # Check if we should use an MCP workflow template
        if use_mcp_template and not subtasks:
            logger.info(f"Using MCP workflow template: {use_mcp_template}")
            subtasks = self.mode_manager.get_mcp_workflow_template(use_mcp_template)
            
            if not subtasks:
                logger.warning(f"MCP template '{use_mcp_template}' not found")
        
        # If no subtasks provided, generate them using Plan mode
        if not subtasks:
            logger.info("No subtasks provided, asking Plan mode to break down the task")
            
            plan_prompt = (
                f"Break down this task into subtasks that can be executed by specialized modes or operations:\n\n{main_task}\n\n"
                f"For each subtask, specify:\n"
                f"1. The type (mode, vs_code_task)\n"
                f"2. For mode: specify the mode name (plan, act) and task description\n"
                f"3. For vs_code_task: specify the task_id and any inputs\n\n"
                f"IMPORTANT: If this task involves memory management, data persistence, or cross-component communication, "
                f"explicitly consider Model Context Protocol (MCP) requirements in your breakdown.\n\n"
                f"Format your response as JSON with this structure:\n"
                f"[\n  {{\"type\": \"mode\", \"mode\": \"mode_name\", \"task\": \"detailed task description\"}},\n"
                f"  {{\"type\": \"vs_code_task\", \"task_id\": \"task_name\", \"inputs\": {{\"key\": \"value\"}}}}\n"
                f"  ...\n]"
            )
            
            # Get breakdown from Plan mode
            plan_response = self.execute_subtask("plan", plan_prompt)
            
            if not plan_response:
                return "Failed to break down the task into subtasks."
            
            # Parse the subtasks from the plan response
            try:
                # Try to extract JSON from the response
                json_start = plan_response.find('[')
                json_end = plan_response.rfind(']') + 1
                
                if json_start != -1 and json_end != -1:
                    json_str = plan_response[json_start:json_end]
                    subtasks = json.loads(json_str)
                else:
                    logger.error("Could not find JSON array in Plan mode response")
                    return "Failed to parse subtasks from Plan mode response."
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse subtasks: {e}")
                logger.error(f"Plan response was: {plan_response}")
                return "Failed to parse subtasks from Plan mode response."
        
        # Save the subtasks plan to memory
        self.memory.save("subtasks_plan", json.dumps(subtasks))
        
        # Execute each subtask in sequence
        results = []
        for idx, subtask in enumerate(subtasks):
            subtask_type = subtask.get("type", "mode")  # Default to mode
            
            # Get context from previous result if available
            context = None
            if idx > 0:
                previous_result = self.memory.retrieve(f"subtask_{idx}_result")
                if previous_result:
                    context = f"Context from previous step:\n\n{previous_result}"
            
            # Execute based on subtask type
            result = None
            if subtask_type == "mode":
                mode = subtask.get("mode")
                task = subtask.get("task")
                if mode and task:
                    result = self.execute_subtask(mode, task, context)
            elif subtask_type == "vs_code_task":
                task_id = subtask.get("task_id")
                inputs = subtask.get("inputs")
                if task_id:
                    result = self.execute_vs_code_task(task_id, inputs)
            
            if result:
                results.append({
                    "type": subtask_type,
                    "details": subtask,
                    "result": result
                })
                logger.info(f"Completed subtask {idx+1}/{len(subtasks)}")
            else:
                logger.error(f"Failed to complete subtask {idx+1}/{len(subtasks)}")
        
        # Generate final summary
        summary_prompt = f"Summarize the results of this multi-step workflow: {main_task}\n\n"
        for idx, result in enumerate(results):
            subtask_type = result["type"]
            details = result["details"]
            result_text = result["result"]
            
            if subtask_type == "mode":
                summary_prompt += f"Step {idx+1} ({details.get('mode')} mode): {result_text[:200]}...\n\n"
            else:
                summary_prompt += f"Step {idx+1} ({subtask_type} - {details.get('task_id', '')}): {result_text[:200]}...\n\n"
        
        final_summary = self.execute_subtask("plan", summary_prompt)
        self.memory.save("workflow_summary", final_summary or "Failed to generate summary")
        
        logger.info("Workflow orchestration completed successfully")
        return final_summary or "Workflow completed but failed to generate summary."

def main():
    """Command line interface for the Cline orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Project Orchestra - Cline Orchestrator")
    
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
    workflow_parser.add_argument("--subtasks", help="JSON file with subtask definitions")
    workflow_parser.add_argument("--mcp-template", help="Name of MCP workflow template to use")
    
    # Memory command
    memory_parser = subparsers.add_parser("memory", help="Interact with the memory bank")
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command", help="Memory command to execute")
    
    # Memory list command
    memory_list_parser = memory_subparsers.add_parser("list", help="List memory keys")
    memory_list_parser.add_argument("--prefix", help="Filter keys by prefix")
    
    # Memory get command
    memory_get_parser = memory_subparsers.add_parser("get", help="Get memory content")
    memory_get_parser.add_argument("--key", required=True, help="Memory key")
    
    # Memory set command
    memory_set_parser = memory_subparsers.add_parser("set", help="Set memory content")
    memory_set_parser.add_argument("--key", required=True, help="Memory key")
    memory_set_parser.add_argument("--content", required=True, help="Memory content")
    
    # List MCP templates command
    mcp_templates_parser = subparsers.add_parser("list-mcp-templates", help="List available MCP workflow templates")
    
    args = parser.parse_args()
    
    if args.command == "task":
        mode_manager = ClineModeManager()
        result = mode_manager.execute_in_mode(args.mode, args.prompt, args.context)
        if result:
            print(result)
        else:
            print("Failed to execute task")
            sys.exit(1)
    
    elif args.command == "vscode_task":
        vscode_runner = VSCodeTaskRunner()
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
        subtask_manager = ClineSubtaskManager()
        
        subtasks = None
        if args.subtasks:
            try:
                with open(args.subtasks, 'r') as f:
                    subtasks = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading subtasks file: {e}")
                sys.exit(1)
        
        result = subtask_manager.orchestrate_workflow(args.task, subtasks, args.mcp_template)
        print(result)
    
    elif args.command == "memory":
        memory_bank = ClineMemoryBank()
        
        if args.memory_command == "list":
            keys = memory_bank.list_keys(args.prefix)
            for key in keys:
                print(key)
        
        elif args.memory_command == "get":
            content = memory_bank.retrieve(args.key)
            if content:
                print(content)
            else:
                print(f"No content found for key: {args.key}")
                sys.exit(1)
        
        elif args.memory_command == "set":
            result = memory_bank.save(args.key, args.content)
            print(f"Memory set {'succeeded' if result else 'failed'}")
    
    elif args.command == "list-mcp-templates":
        print("Available MCP workflow templates:")
        for name, template in CLINE_MCP_WORKFLOW_TEMPLATES.items():
            print(f"  - {name}: {len(template)} subtasks")
            for i, subtask in enumerate(template):
                if subtask['type'] == 'mode':
                    print(f"    {i+1}. {subtask['mode']} mode: {subtask['task'][:50]}...")
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()