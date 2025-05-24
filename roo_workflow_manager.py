#!/usr/bin/env python3
"""
roo_workflow_manager.py - Roo Code Mode Orchestration with Boomerang Tasks for Project Orchestra

This script manages AI model orchestration for Project Orchestra, breaking down complex
tasks into subtasks that can be handled by specialized modes and maintaining context
across the workflow. It integrates with VS Code tasks and GitHub-GCP workflows.

NOTE: This is a Roo Code integration utility and is separate from the main Project Orchestra
implementation. It serves as a bridge between Roo Code AI modes and the Project Orchestra
infrastructure.
"""

import argparse
import json
import logging
import subprocess
import sys
from typing import Any, Dict, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("roo-orchestrator")

# Mode configuration mapping (used for CLI operation)
MODE_MAP = {
    "architect": "🏗 Architect",
    "code": "💻 Code",
    "reviewer": "🕵️ Reviewer",
    "ask": "❓ Ask",
    "strategy": "🧠 Strategy",
    "creative": "🎨 Creative",
    "debug": "🐛 Debug",
    "orchestrator": "🪃 Orchestrator",
}

# VS Code task mapping
VSCODE_TASKS = {
    "terraform_plan": "Terraform Plan",
    "terraform_validate": "Terraform Validate",
    "terraform_apply": "Terraform Apply",
    "deploy_cloud_run": "Deploy to Cloud Run",
    "run_cloud_build": "Run Cloud Build Pipeline",
    "run_data_sync": "Run Data Sync Pipeline",
    "run_migration": "Run Migration Pipeline",
    "github_gcp_init": "GitHub-GCP: Initialize Workspace",
    "github_gcp_pr": "GitHub-GCP: Create PR with Infrastructure Changes",
    "github_gcp_deploy": "GitHub-GCP: Deploy to Cloud Run",
    "github_gcp_sync": "GitHub-GCP: Sync Codespace with GCP Secrets",
    "github_gcp_graph": "GitHub-GCP: Generate Terraform Graph",
    "github_gcp_identity": "GitHub-GCP: Create Workload Identity Federation",
    "github_gcp_import": "GitHub-GCP: Import GCP Resources to Terraform",
}


class MemoryBank:
    """Handles interaction with Roo Code MCP Memory Bank."""

    @staticmethod
    def save(key: str, content: str) -> bool:
        """Save content to memory MCP."""
        try:
            # Roo CLI memory save command
            cmd = [
                "roo-cli",
                "mcp",
                "memory_bank_write",
                "--key",
                key,
                "--content",
                content,
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Saved to memory: {key}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to save to memory: {e.stdout} / {e.stderr}")
            return False

    @staticmethod
    def retrieve(key: str) -> Optional[str]:
        """Retrieve content from memory MCP."""
        try:
            # Roo CLI memory retrieve command
            cmd = ["roo-cli", "mcp", "memory_bank_read", "--key", key]
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
            # Roo CLI memory update command
            cmd = [
                "roo-cli",
                "mcp",
                "memory_bank_update",
                "--key",
                key,
                "--content",
                content,
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Updated memory: {key}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to update memory: {e.stdout} / {e.stderr}")
            return False


class VSCodeTaskRunner:
    """Handles running VS Code tasks from the orchestrator."""

    @staticmethod
    def run_task(task_id: str, inputs: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Run a VS Code task by ID."""
        if task_id not in VSCODE_TASKS:
            logger.error(f"Unknown VS Code task ID: {task_id}")
            return None

        task_name = VSCODE_TASKS[task_id]
        logger.info(f"Running VS Code task: {task_name}")

        try:
            # Construct command for VS Code task
            cmd = ["roo-cli", "terminal", "--command", f"Run VS Code task: {task_name}"]

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


class RooModeManager:
    """Manages interactions with Roo Code modes."""

    @staticmethod
    def switch_mode(mode: str) -> bool:
        """Switch Roo Code to the specified mode."""
        try:
            cmd = ["roo-cli", "mode", mode]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Switched to mode: {mode}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to switch mode: {e.stdout} / {e.stderr}")
            return False

    @staticmethod
    def execute_in_mode(mode: str, prompt: str, context: Optional[str] = None) -> Optional[str]:
        """Execute a prompt in the specified mode with optional context."""
        try:
            full_prompt = prompt
            if context:
                full_prompt = f"{context}\n\n{prompt}"

            # Use MCP to route to the appropriate model
            cmd = [
                "roo-cli",
                "mcp",
                "portkey-router",
                "route_model_request",
                "--mode",
                mode,
                "--prompt",
                full_prompt,
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            # Parse the JSON response from the MCP
            response_data = json.loads(result.stdout)
            return response_data.get("result")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to execute in mode {mode}: {e.stdout} / {e.stderr}")
            return None
        except json.JSONDecodeError:
            logger.error("Failed to parse response from MCP")
            return None


class GithubIntegration:
    """Handles GitHub integration operations."""

    @staticmethod
    def create_branch(branch_name: str, base_branch: str = "main") -> bool:
        """Create a new Git branch for AI-generated changes."""
        try:
            # Check if branch already exists
            check_cmd = ["git", "show-ref", "--verify", f"refs/heads/{branch_name}"]
            branch_exists = subprocess.run(check_cmd, capture_output=True).returncode == 0

            if branch_exists:
                logger.info(f"Branch {branch_name} already exists")
                return True

            # Create and checkout new branch
            subprocess.run(["git", "checkout", "-b", branch_name, base_branch], check=True)
            logger.info(f"Created and checked out branch: {branch_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create branch: {e}")
            return False

    @staticmethod
    def commit_changes(message: str, files: Optional[List[str]] = None) -> bool:
        """Commit changes to the current branch."""
        try:
            # Add files
            if files:
                for file in files:
                    subprocess.run(["git", "add", file], check=True)
            else:
                subprocess.run(["git", "add", "."], check=True)

            # Commit
            subprocess.run(["git", "commit", "-m", message], check=True)
            logger.info(f"Committed changes with message: {message}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit changes: {e}")
            return False

    @staticmethod
    def create_pr(title: str, body: str, base_branch: str = "main") -> Optional[str]:
        """Create a PR for the current branch."""
        try:
            # Get current branch
            branch_cmd = ["git", "branch", "--show-current"]
            result = subprocess.run(branch_cmd, check=True, capture_output=True, text=True)
            current_branch = result.stdout.strip()

            # Create PR
            pr_cmd = [
                "gh",
                "pr",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--base",
                base_branch,
            ]
            result = subprocess.run(pr_cmd, check=True, capture_output=True, text=True)

            logger.info(f"Created PR for branch {current_branch}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create PR: {e.stdout} / {e.stderr}")
            return None


class GCPIntegration:
    """Handles GCP integration operations."""

    @staticmethod
    def get_project_id() -> Optional[str]:
        """Get the current GCP project ID."""
        try:
            cmd = ["gcloud", "config", "get-value", "project"]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            project_id = result.stdout.strip()
            logger.info(f"Current GCP project: {project_id}")
            return project_id
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get GCP project ID: {e.stdout} / {e.stderr}")
            return None

    @staticmethod
    def run_cloud_build(config_path: str) -> Optional[str]:
        """Run a Cloud Build pipeline with the specified config."""
        try:
            cmd = ["gcloud", "builds", "submit", "--config", config_path]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Ran Cloud Build with config: {config_path}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to run Cloud Build: {e.stdout} / {e.stderr}")
            return None

    @staticmethod
    def deploy_to_cloud_run(service_name: str, image: str, region: str = "us-central1") -> Optional[str]:
        """Deploy an image to Cloud Run."""
        try:
            cmd = [
                "gcloud",
                "run",
                "deploy",
                service_name,
                "--image",
                image,
                "--platform",
                "managed",
                "--region",
                region,
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Deployed {image} to Cloud Run service: {service_name}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to deploy to Cloud Run: {e.stdout} / {e.stderr}")
            return None


class TerraformManager:
    """Handles Terraform operations."""

    @staticmethod
    def run_terraform_command(command: str, working_dir: str = "terraform") -> Optional[str]:
        """Run a Terraform command in the specified directory."""
        try:
            cmd = ["terraform", command]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=working_dir)
            logger.info(f"Ran Terraform command '{command}' in {working_dir}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to run Terraform command: {e.stdout} / {e.stderr}")
            return None

    @staticmethod
    def plan(working_dir: str = "terraform", out_file: str = "tfplan") -> Optional[str]:
        """Run Terraform plan and save the plan to a file."""
        try:
            cmd = ["terraform", "plan", "-out", out_file]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=working_dir)
            logger.info(f"Created Terraform plan in {working_dir}/{out_file}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create Terraform plan: {e.stdout} / {e.stderr}")
            return None

    @staticmethod
    def apply(working_dir: str = "terraform", plan_file: Optional[str] = None) -> Optional[str]:
        """Apply Terraform changes."""
        try:
            if plan_file:
                cmd = ["terraform", "apply", "-auto-approve", plan_file]
            else:
                cmd = ["terraform", "apply", "-auto-approve"]

            result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=working_dir)
            logger.info(f"Applied Terraform changes in {working_dir}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to apply Terraform changes: {e.stdout} / {e.stderr}")
            return None

    @staticmethod
    def get_outputs(
        working_dir: str = "terraform", output_name: Optional[str] = None
    ) -> Union[Dict[str, str], Optional[str]]:
        """Get Terraform outputs."""
        try:
            if output_name:
                cmd = ["terraform", "output", "-raw", output_name]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=working_dir)
                logger.info(f"Got Terraform output '{output_name}'")
                return result.stdout.strip()
            else:
                cmd = ["terraform", "output", "-json"]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=working_dir)
                logger.info("Got all Terraform outputs")
                return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get Terraform outputs: {e.stdout} / {e.stderr}")
            return None
        except json.JSONDecodeError:
            logger.error("Failed to parse Terraform outputs JSON")
            return None


class SubtaskManager:
    """Manages Boomerang subtasks and their orchestration."""

    def __init__(self):
        self.memory = MemoryBank()
        self.mode_manager = RooModeManager()
        self.vscode_runner = VSCodeTaskRunner()
        self.gcp = GCPIntegration()
        self.github = GithubIntegration()
        self.terraform = TerraformManager()
        self.execution_history = []

    def _get_next_subtask_id(self) -> str:
        """Generate a unique ID for the next subtask."""
        return f"subtask_{len(self.execution_history) + 1}"

    def _save_subtask_result(self, subtask_id: str, mode: str, task: str, result: str) -> None:
        """Save subtask result to memory and update execution history."""
        # Save to memory bank
        self.memory.save(f"{subtask_id}_result", result)

        # Update execution history
        self.execution_history.append(
            {
                "id": subtask_id,
                "mode": mode,
                "task": task,
                "result_summary": result[:100] + "..." if len(result) > 100 else result,
            }
        )

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
        task_name = VSCODE_TASKS.get(task_id, task_id)
        logger.info(f"Executing VS Code task {subtask_id}: {task_name}")

        # Run the VS Code task
        result = self.vscode_runner.run_task(task_id, inputs)

        if result:
            # Save the result to memory
            self.memory.save(f"{subtask_id}_vs_code_task", result)

            # Update execution history
            self.execution_history.append(
                {
                    "id": subtask_id,
                    "type": "vs_code_task",
                    "task": task_name,
                    "result_summary": result[:100] + "..." if len(result) > 100 else result,
                }
            )

            # Save updated execution history
            self.memory.update("execution_history", json.dumps(self.execution_history))

            return result

        return None

    def run_terraform_operation(self, operation: str, working_dir: str = "terraform", **kwargs) -> Optional[str]:
        """Run a Terraform operation as part of a workflow."""
        subtask_id = self._get_next_subtask_id()
        logger.info(f"Running Terraform operation {subtask_id}: {operation} in {working_dir}")

        # Map operation to method
        result = None
        if operation == "plan":
            out_file = kwargs.get("out_file", "tfplan")
            result = self.terraform.plan(working_dir, out_file)
        elif operation == "apply":
            plan_file = kwargs.get("plan_file")
            result = self.terraform.apply(working_dir, plan_file)
        elif operation == "get_outputs":
            output_name = kwargs.get("output_name")
            result = self.terraform.get_outputs(working_dir, output_name)
            if isinstance(result, dict):
                result = json.dumps(result, indent=2)
        else:
            result = self.terraform.run_terraform_command(operation, working_dir)

        if result:
            # Save the result to memory
            self.memory.save(f"{subtask_id}_terraform", result)

            # Update execution history
            self.execution_history.append(
                {
                    "id": subtask_id,
                    "type": "terraform",
                    "operation": operation,
                    "working_dir": working_dir,
                    "result_summary": result[:100] + "..." if len(result) > 100 else result,
                }
            )

            # Save updated execution history
            self.memory.update("execution_history", json.dumps(self.execution_history))

            return result

        return None

    def run_gcp_operation(self, operation: str, **kwargs) -> Optional[str]:
        """Run a GCP operation as part of a workflow."""
        subtask_id = self._get_next_subtask_id()
        logger.info(f"Running GCP operation {subtask_id}: {operation}")

        # Map operation to method
        result = None
        if operation == "cloud_build":
            config_path = kwargs.get("config_path", "cloudbuild.yaml")
            result = self.gcp.run_cloud_build(config_path)
        elif operation == "deploy_cloud_run":
            service_name = kwargs.get("service_name")
            image = kwargs.get("image")
            region = kwargs.get("region", "us-central1")
            result = self.gcp.deploy_to_cloud_run(service_name, image, region)
        elif operation == "get_project_id":
            result = self.gcp.get_project_id()

        if result:
            # Save the result to memory
            self.memory.save(f"{subtask_id}_gcp", result)

            # Update execution history
            self.execution_history.append(
                {
                    "id": subtask_id,
                    "type": "gcp",
                    "operation": operation,
                    "result_summary": result[:100] + "..." if len(result) > 100 else result,
                }
            )

            # Save updated execution history
            self.memory.update("execution_history", json.dumps(self.execution_history))

            return result

        return None

    def orchestrate_workflow(self, main_task: str, subtasks: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Orchestrate a complete workflow with multiple subtasks.

        Args:
            main_task: The overall task description
            subtasks: Optional list of task definitions with mode/operation and parameters

        Returns:
            Final consolidated result
        """
        logger.info(f"Starting workflow orchestration for: {main_task}")

        # Clear execution history for this workflow
        self.execution_history = []

        # Save the main task to memory
        self.memory.save("main_task", main_task)

        # If no subtasks provided, generate them using Strategy mode
        if not subtasks:
            logger.info("No subtasks provided, asking Strategy mode to break down the task")

            strategy_prompt = (
                f"Break down this task into subtasks that can be executed by specialized modes or operations:\n\n{main_task}\n\n"
                f"The workflow should include steps for designing, implementing, reviewing, and deploying the solution.\n\n"
                f"For each subtask, specify:\n"
                f"1. The type (mode, vs_code_task, terraform, gcp)\n"
                f"2. For mode: specify the mode name (architect, code, reviewer, debug, ask, strategy, creative) and task description\n"
                f"3. For vs_code_task: specify the task_id and any inputs\n"
                f"4. For terraform: specify the operation and working directory\n"
                f"5. For gcp: specify the operation and parameters\n\n"
                f"Format your response as JSON with this structure:\n"
                f'[\n  {{"type": "mode", "mode": "mode_name", "task": "detailed task description"}},\n'
                f'  {{"type": "vs_code_task", "task_id": "task_name", "inputs": {{"key": "value"}}}},\n'
                f'  {{"type": "terraform", "operation": "command", "working_dir": "path"}},\n'
                f'  {{"type": "gcp", "operation": "operation_name", "parameters": {{"key": "value"}}}}\n'
                f"  ...\n]"
            )

            # Get breakdown from Strategy mode
            strategy_response = self.execute_subtask("strategy", strategy_prompt)

            if not strategy_response:
                return "Failed to break down the task into subtasks."

            # Parse the subtasks from the strategy response
            try:
                # Try to extract JSON from the response
                json_start = strategy_response.find("[")
                json_end = strategy_response.rfind("]") + 1

                if json_start != -1 and json_end != -1:
                    json_str = strategy_response[json_start:json_end]
                    subtasks = json.loads(json_str)
                else:
                    logger.error("Could not find JSON array in Strategy mode response")
                    return "Failed to parse subtasks from Strategy mode response."
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse subtasks: {e}")
                logger.error(f"Strategy response was: {strategy_response}")
                return "Failed to parse subtasks from Strategy mode response."

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
            elif subtask_type == "terraform":
                operation = subtask.get("operation")
                working_dir = subtask.get("working_dir", "terraform")
                kwargs = subtask.get("parameters", {})
                if operation:
                    result = self.run_terraform_operation(operation, working_dir, **kwargs)
            elif subtask_type == "gcp":
                operation = subtask.get("operation")
                kwargs = subtask.get("parameters", {})
                if operation:
                    result = self.run_gcp_operation(operation, **kwargs)

            if result:
                results.append({"type": subtask_type, "details": subtask, "result": result})
                logger.info(f"Completed subtask {idx+1}/{len(subtasks)}")
            else:
                logger.error(f"Failed to complete subtask {idx+1}/{len(subtasks)}")

        # Generate final summary using Creative mode
        summary_prompt = f"Summarize the results of this multi-step workflow: {main_task}\n\n"
        for idx, result in enumerate(results):
            subtask_type = result["type"]
            details = result["details"]
            result_text = result["result"]

            if subtask_type == "mode":
                summary_prompt += f"Step {idx+1} ({details.get('mode')} mode): {result_text[:200]}...\n\n"
            else:
                summary_prompt += f"Step {idx+1} ({subtask_type} - {details.get('operation', details.get('task_id', ''))}): {result_text[:200]}...\n\n"

        final_summary = self.execute_subtask("creative", summary_prompt)
        self.memory.save("workflow_summary", final_summary or "Failed to generate summary")

        logger.info("Workflow orchestration completed successfully")
        return final_summary or "Workflow completed but failed to generate summary."


def main():
    """Command line interface for the orchestrator."""
    parser = argparse.ArgumentParser(description="Project Orchestra - Roo Code Orchestrator")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Task command
    task_parser = subparsers.add_parser("task", help="Execute a single task in a specific mode")
    task_parser.add_argument(
        "--mode",
        required=True,
        choices=MODE_MAP.keys(),
        help="Mode to use for the task",
    )
    task_parser.add_argument("--prompt", required=True, help="Task prompt")
    task_parser.add_argument("--context", help="Optional context for the task")

    # VS Code task command
    vscode_task_parser = subparsers.add_parser("vscode_task", help="Run a VS Code task")
    vscode_task_parser.add_argument(
        "--task_id",
        required=True,
        choices=VSCODE_TASKS.keys(),
        help="VS Code task to run",
    )
    vscode_task_parser.add_argument("--inputs", help="JSON string of inputs for the task")

    # Terraform command
    terraform_parser = subparsers.add_parser("terraform", help="Run a Terraform operation")
    terraform_parser.add_argument(
        "--operation",
        required=True,
        help="Terraform operation to run (e.g., plan, apply, init)",
    )
    terraform_parser.add_argument(
        "--working_dir",
        default="terraform",
        help="Directory containing Terraform configuration",
    )
    terraform_parser.add_argument("--parameters", help="JSON string of additional parameters")

    # GCP command
    gcp_parser = subparsers.add_parser("gcp", help="Run a GCP operation")
    gcp_parser.add_argument(
        "--operation",
        required=True,
        help="GCP operation to run (e.g., cloud_build, deploy_cloud_run)",
    )
    gcp_parser.add_argument("--parameters", help="JSON string of operation parameters")

    # GitHub command
    github_parser = subparsers.add_parser("github", help="Run a GitHub operation")
    github_parser.add_argument(
        "--operation",
        required=True,
        choices=["create_branch", "commit_changes", "create_pr"],
        help="GitHub operation to run",
    )
    github_parser.add_argument("--parameters", help="JSON string of operation parameters")

    # Workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Execute a complete workflow")
    workflow_parser.add_argument("--task", required=True, help="Main task description")
    workflow_parser.add_argument("--subtasks", help="JSON file with subtask definitions")

    args = parser.parse_args()

    if args.command == "task":
        mode_manager = RooModeManager()
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

    elif args.command == "terraform":
        terraform_manager = TerraformManager()
        parameters = {}
        if args.parameters:
            try:
                parameters = json.loads(args.parameters)
            except json.JSONDecodeError:
                print(f"Error parsing parameters JSON: {args.parameters}")
                sys.exit(1)

        if args.operation == "plan":
            result = terraform_manager.plan(args.working_dir, parameters.get("out_file", "tfplan"))
        elif args.operation == "apply":
            result = terraform_manager.apply(args.working_dir, parameters.get("plan_file"))
        elif args.operation == "get_outputs":
            result = terraform_manager.get_outputs(args.working_dir, parameters.get("output_name"))
            if isinstance(result, dict):
                result = json.dumps(result, indent=2)
        else:
            result = terraform_manager.run_terraform_command(args.operation, args.working_dir)

        if result:
            print(result)
        else:
            print(f"Failed to run Terraform operation: {args.operation}")
            sys.exit(1)

    elif args.command == "gcp":
        gcp_integration = GCPIntegration()
        parameters = {}
        if args.parameters:
            try:
                parameters = json.loads(args.parameters)
            except json.JSONDecodeError:
                print(f"Error parsing parameters JSON: {args.parameters}")
                sys.exit(1)

        if args.operation == "cloud_build":
            result = gcp_integration.run_cloud_build(parameters.get("config_path", "cloudbuild.yaml"))
        elif args.operation == "deploy_cloud_run":
            result = gcp_integration.deploy_to_cloud_run(
                parameters.get("service_name"),
                parameters.get("image"),
                parameters.get("region", "us-central1"),
            )
        elif args.operation == "get_project_id":
            result = gcp_integration.get_project_id()
        else:
            print(f"Unknown GCP operation: {args.operation}")
            sys.exit(1)

        if result:
            print(result)
        else:
            print(f"Failed to run GCP operation: {args.operation}")
            sys.exit(1)

    elif args.command == "github":
        github_integration = GithubIntegration()
        parameters = {}
        if args.parameters:
            try:
                parameters = json.loads(args.parameters)
            except json.JSONDecodeError:
                print(f"Error parsing parameters JSON: {args.parameters}")
                sys.exit(1)

        if args.operation == "create_branch":
            result = github_integration.create_branch(
                parameters.get("branch_name"), parameters.get("base_branch", "main")
            )
            print(f"Branch creation {'succeeded' if result else 'failed'}")
        elif args.operation == "commit_changes":
            result = github_integration.commit_changes(
                parameters.get("message", "AI-generated changes"),
                parameters.get("files"),
            )
            print(f"Commit {'succeeded' if result else 'failed'}")
        elif args.operation == "create_pr":
            result = github_integration.create_pr(
                parameters.get("title"),
                parameters.get("body"),
                parameters.get("base_branch", "main"),
            )
            if result:
                print(result)
            else:
                print("Failed to create PR")
                sys.exit(1)

    elif args.command == "workflow":
        subtask_manager = SubtaskManager()

        subtasks = None
        if args.subtasks:
            try:
                with open(args.subtasks, "r") as f:
                    subtasks = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading subtasks file: {e}")
                sys.exit(1)

        result = subtask_manager.orchestrate_workflow(args.task, subtasks)
        print(result)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
