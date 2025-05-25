#!/usr/bin/env python3
"""
mcp_cli.py - Command-line Interface for the Unified MCP System

This script provides a simplified command-line interface for working with the
unified Model Context Protocol (MCP) system across different AI tools including
Roo, Cline, Gemini, Agno, and Co-pilot.

Usage:
  mcp_cli memory get <key> [--scope=<scope>] [--tool=<tool>]
  mcp_cli memory set <key> <content> [--scope=<scope>] [--tool=<tool>]
  mcp_cli memory sync <key> --from=<source-tool> --to=<target-tool> [--scope=<scope>]
  mcp_cli run <tool> <mode> <prompt> [--context=<context>]
  mcp_cli workflow <workflow-name> [--tool=<tool>]
  mcp_cli cross-tool <workflow-name> [--tools=<tool1,tool2,...>]
  mcp_cli server list
  mcp_cli server status <server-name>
  mcp_cli server start <server-name>
  mcp_cli server stop <server-name>
  mcp_cli server run <server-name> <operation> [--params=<json-params>]
  mcp_cli list [workflows|servers|tools]
  mcp_cli --help

Options:
  --scope=<scope>       Memory scope: 'user', 'session', 'global', or 'project' [default: session]
  --tool=<tool>         AI tool to use: 'roo', 'cline', 'gemini', 'agno', or 'copilot'
  --from=<source-tool>  Source tool for memory sync
  --to=<target-tool>    Target tool for memory sync
  --context=<context>   Additional context for the prompt
  --tools=<tools>       Comma-separated list of tools for cross-tool workflows
  --params=<json-params> JSON parameters for server operations
  --help                Show this help message and exit
"""

import json
import sys
from typing import Any, Dict

# Import unified MCP components
try:
    from cline_integration import CLINE_MODE_MAP as CLINE_MODES
    from unified_mcp_orchestrator import (
        UNIFIED_WORKFLOWS,
        AITool,
        MCPServerManager,
        MemoryScope,
        UnifiedMemoryManager,
        UnifiedModeManager,
        UnifiedWorkflowOrchestrator,
    )

    from roo_workflow_manager import MODE_MAP as ROO_MODES
except ImportError as e:
    print(f"Error importing MCP components: {e}")
    print(
        "Make sure unified_mcp_orchestrator.py, roo_workflow_manager.py, and cline_integration.py are available."
    )
    sys.exit(1)


def parse_args() -> Dict[str, Any]:
    """Parse command-line arguments."""
    import docopt

    return docopt.docopt(__doc__)


def format_output(data: Any) -> str:
    """Format output data for display."""
    if isinstance(data, dict) or isinstance(data, list):
        return json.dumps(data, indent=2)
    return str(data)


def handle_memory_commands(args: Dict[str, Any]) -> None:
    """Handle memory-related commands."""
    memory_manager = UnifiedMemoryManager()

    # Determine tool if specified
    tool = None
    if args["--tool"]:
        try:
            tool = AITool(args["--tool"])
        except ValueError:
            print(f"Invalid tool: {args['--tool']}")
            print(f"Available tools: {', '.join(t.value for t in AITool)}")
            sys.exit(1)

    # Determine scope if specified
    scope = MemoryScope.SESSION
    if args["--scope"]:
        try:
            scope = MemoryScope(args["--scope"])
        except ValueError:
            print(f"Invalid scope: {args['--scope']}")
            print(f"Available scopes: {', '.join(s.value for s in MemoryScope)}")
            sys.exit(1)

    # Memory get command
    if args["get"]:
        key = args["<key>"]
        content = memory_manager.retrieve(key, scope=scope, tool=tool)
        if content:
            print(content)
        else:
            print(f"No content found for key: {key}")
            sys.exit(1)

    # Memory set command
    elif args["set"]:
        key = args["<key>"]
        content = args["<content>"]
        result = memory_manager.save(key, content, scope=scope, tool=tool)
        print(f"Memory set {'succeeded' if result else 'failed'}")

    # Memory sync command
    elif args["sync"]:
        key = args["<key>"]
        source_tool = AITool(args["--from"])
        target_tool = AITool(args["--to"])

        result = memory_manager.sync_between_tools(
            key, source_tool=source_tool, target_tool=target_tool, scope=scope
        )
        print(f"Memory sync {'succeeded' if result else 'failed'}")


def handle_run_command(args: Dict[str, Any]) -> None:
    """Handle the run command to execute a prompt in a specific mode."""
    try:
        tool = AITool(args["<tool>"])
    except ValueError:
        print(f"Invalid tool: {args['<tool>']}")
        print(f"Available tools: {', '.join(t.value for t in AITool)}")
        sys.exit(1)

    mode = args["<mode>"]
    prompt = args["<prompt>"]
    context = args["--context"]

    # Verify mode is valid for the tool
    if tool == AITool.ROO and mode not in ROO_MODES:
        print(f"Invalid mode '{mode}' for Roo.")
        print(f"Available modes: {', '.join(ROO_MODES.keys())}")
        sys.exit(1)
    elif tool == AITool.CLINE and mode not in CLINE_MODES:
        print(f"Invalid mode '{mode}' for Cline.")
        print(f"Available modes: {', '.join(CLINE_MODES.keys())}")
        sys.exit(1)

    # Execute in the specified mode
    result = UnifiedModeManager.execute_in_mode(tool, mode, prompt, context)

    if result:
        print(result)
    else:
        print("Failed to execute in the specified mode")
        sys.exit(1)


def handle_workflow_command(args: Dict[str, Any]) -> None:
    """Handle the workflow command to execute a predefined workflow."""
    workflow_name = args["<workflow-name>"]

    # Check if workflow exists
    if workflow_name not in UNIFIED_WORKFLOWS:
        print(f"Workflow '{workflow_name}' not found.")
        print(f"Available workflows: {', '.join(UNIFIED_WORKFLOWS.keys())}")
        sys.exit(1)

    tool = None
    if args["--tool"]:
        try:
            tool = AITool(args["--tool"])
        except ValueError:
            print(f"Invalid tool: {args['--tool']}")
            print(f"Available tools: {', '.join(t.value for t in AITool)}")
            sys.exit(1)

    orchestrator = UnifiedWorkflowOrchestrator()
    result = orchestrator.execute_workflow(workflow_name, tool=tool)
    print(result)


def handle_cross_tool_command(args: Dict[str, Any]) -> None:
    """Handle the cross-tool command to execute a workflow across multiple tools."""
    workflow_name = args["<workflow-name>"]

    # Check if workflow exists
    if workflow_name not in UNIFIED_WORKFLOWS:
        print(f"Workflow '{workflow_name}' not found.")
        print(f"Available workflows: {', '.join(UNIFIED_WORKFLOWS.keys())}")
        sys.exit(1)

    tools = None
    if args["--tools"]:
        try:
            tool_names = args["--tools"].split(",")
            tools = [AITool(name) for name in tool_names]
        except ValueError as e:
            print(f"Invalid tool in tools list: {e}")
            print(f"Available tools: {', '.join(t.value for t in AITool)}")
            sys.exit(1)

    orchestrator = UnifiedWorkflowOrchestrator()
    result = orchestrator.execute_cross_tool_workflow(workflow_name, tools=tools)
    print(result)


def handle_server_commands(args: Dict[str, Any]) -> None:
    """Handle server-related commands."""
    server_manager = MCPServerManager()

    # Server list command
    if args["list"]:
        servers = server_manager.list_available_servers()
        if servers:
            print("Available MCP servers:")
            for server in servers:
                print(f"  - {server}")
        else:
            print("No MCP servers found.")

    # Server status command
    elif args["status"]:
        server_name = args["<server-name>"]
        status = server_manager.check_server_status(server_name)
        print(f"Server {server_name} is {'running' if status else 'not running'}")

    # Server start command
    elif args["start"]:
        server_name = args["<server-name>"]
        result = server_manager.start_server(server_name)
        print(f"Server start {'succeeded' if result else 'failed'}")

    # Server stop command
    elif args["stop"]:
        server_name = args["<server-name>"]
        result = server_manager.stop_server(server_name)
        print(f"Server stop {'succeeded' if result else 'failed'}")

    # Server run command
    elif args["run"]:
        server_name = args["<server-name>"]
        operation = args["<operation>"]

        parameters = None
        if args["--params"]:
            try:
                parameters = json.loads(args["--params"])
            except json.JSONDecodeError:
                print(f"Error parsing parameters JSON: {args['--params']}")
                sys.exit(1)

        result = server_manager.execute_server_operation(
            server_name, operation, parameters
        )
        if result:
            print(result)
        else:
            print("Operation failed")
            sys.exit(1)


def handle_list_command(args: Dict[str, Any]) -> None:
    """Handle the list command to display available resources."""
    # List workflows
    if args["workflows"]:
        print("Available unified workflows:")
        for name, workflow in UNIFIED_WORKFLOWS.items():
            print(f"  - {name}: {workflow.description}")
            print(f"    Steps: {len(workflow.steps)}")

    # List servers
    elif args["servers"]:
        server_manager = MCPServerManager()
        servers = server_manager.list_available_servers()
        if servers:
            print("Available MCP servers:")
            for server in servers:
                print(f"  - {server}")
        else:
            print("No MCP servers found.")

    # List tools
    elif args["tools"]:
        print("Available AI tools:")
        for tool in AITool:
            print(f"  - {tool.value}")

        print("\nRoo modes:")
        for mode, display_name in ROO_MODES.items():
            print(f"  - {mode}: {display_name}")

        print("\nCline modes:")
        for mode, display_name in CLINE_MODES.items():
            print(f"  - {mode}: {display_name}")


def main() -> None:
    """Main entry point."""
    try:
        pass
    except ImportError:
        print("docopt package is required. Install it with: pip install docopt")
        sys.exit(1)

    try:
        args = parse_args()

        # Memory commands
        if args["memory"]:
            handle_memory_commands(args)

        # Run command
        elif args["run"]:
            handle_run_command(args)

        # Workflow command
        elif args["workflow"]:
            handle_workflow_command(args)

        # Cross-tool command
        elif args["cross-tool"]:
            handle_cross_tool_command(args)

        # Server commands
        elif args["server"]:
            handle_server_commands(args)

        # List command
        elif args["list"]:
            handle_list_command(args)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
