#!/usr/bin/env python3
"""
Command-line interface for the Vertex AI Agent Manager.

This script provides a CLI for triggering Vertex AI Agent tasks.
"""

import argparse
import json
import sys
import logging
from typing import Dict, Any, List, Optional

from .vertex_agent_manager import trigger_vertex_task

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Orchestra Vertex AI Agent Manager CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Add task subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # General task parser
    task_parser = subparsers.add_parser("task", help="Execute a generic task")
    task_parser.add_argument("task", help="Task to execute")
    task_parser.add_argument("--params", "-p", type=json.loads, default={}, 
                            help="JSON string of parameters for the task")
    
    # Terraform parser
    terraform_parser = subparsers.add_parser("terraform", help="Apply Terraform configuration")
    terraform_parser.add_argument("workspace", choices=["dev", "stage", "prod"], 
                                help="Terraform workspace")
    
    # Agent team parser
    team_parser = subparsers.add_parser("team", help="Create and deploy an agent team")
    team_parser.add_argument("name", help="Name of the team")
    team_parser.add_argument("--roles", "-r", nargs="+", 
                            default=["planner", "doer", "reviewer"],
                            help="List of roles for the team members")
    
    # Embeddings parser
    embeddings_parser = subparsers.add_parser("embeddings", help="Manage embeddings")
    embeddings_parser.add_argument("index", help="Vector index name")
    embeddings_parser.add_argument("--data", "-d", required=True, 
                                help="Data to embed")
    
    # Game session parser
    game_parser = subparsers.add_parser("game", help="Manage a game session")
    game_parser.add_argument("type", choices=["trivia", "word_game"], 
                            help="Type of game")
    game_parser.add_argument("session", help="Session ID")
    game_parser.add_argument("action", help="Player action")
    
    # Monitoring parser
    subparsers.add_parser("monitor", help="Monitor GCP resources")
    
    # Init script parser
    subparsers.add_parser("init", help="Run initialization script")
    
    # Add global options
    parser.add_argument("--project", help="GCP project ID")
    parser.add_argument("--location", help="GCP region")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Verify that a subcommand was provided
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    return args


def format_result(result: Dict[str, Any], verbose: bool = False) -> str:
    """
    Format the result for display.
    
    Args:
        result: Result dictionary
        verbose: Whether to include verbose output
        
    Returns:
        Formatted result string
    """
    if verbose:
        return json.dumps(result, indent=2)
    else:
        # Simplified output for non-verbose mode
        status = result.get("status", "unknown")
        message = "Success" if status == "success" else result.get("error", "Unknown error")
        
        output = f"Status: {status}\n"
        if status == "success":
            output += f"Message: {message}\n"
            
            # Add specific information based on the result type
            if "workspace" in result:
                output += f"Workspace: {result['workspace']}\n"
            elif "team" in result:
                output += f"Team: {result['team']}\n"
                if "files_created" in result:
                    output += f"Files: {len(result['files_created'])} files created\n"
            elif "session" in result:
                session = result["session"]
                output += f"Game: {session.get('game_type')}\n"
                output += f"Session: {session.get('session_id')}\n"
                output += f"Response: {session.get('response')}\n"
            elif "monitoring_data" in result:
                costs = result["monitoring_data"]["costs"]
                output += f"Daily cost: ${costs.get('estimated_daily')}\n"
                output += f"Monthly cost: ${costs.get('estimated_monthly')}\n"
        else:
            output += f"Error: {message}\n"
            
        return output


def main():
    """Main entry point for the CLI."""
    args = parse_args()
    
    # Set log level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create kwargs for vertex_agent_manager
    manager_kwargs = {}
    if args.project:
        manager_kwargs["project_id"] = args.project
    if args.location:
        manager_kwargs["location"] = args.location
    
    try:
        # Process commands
        if args.command == "task":
            task = args.task
            result = trigger_vertex_task(task, **args.params)
        elif args.command == "terraform":
            task = f"apply terraform {args.workspace}"
            result = trigger_vertex_task(task)
        elif args.command == "team":
            task = f"create agent team {args.name}"
            result = trigger_vertex_task(task, roles=args.roles)
        elif args.command == "embeddings":
            task = f"manage embeddings {args.index}"
            result = trigger_vertex_task(task, data=args.data)
        elif args.command == "game":
            task = f"manage game session {args.type} {args.session} {args.action}"
            result = trigger_vertex_task(task)
        elif args.command == "monitor":
            task = "monitor resources"
            result = trigger_vertex_task(task)
        elif args.command == "init":
            task = "run init script"
            result = trigger_vertex_task(task)
        else:
            logger.error(f"Unknown command: {args.command}")
            sys.exit(1)
        
        # Print result
        print(format_result(result, args.verbose))
        
        # Set exit code based on result status
        if result.get("status") != "success":
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
