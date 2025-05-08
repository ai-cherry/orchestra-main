"""
Example script demonstrating Roo integration with MCP.

This script shows how to use the Roo integration with MCP to manage
mode transitions and memory access for AI agents.
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp_server.storage.in_memory_storage import InMemoryStorage
from mcp_server.managers.standard_memory_manager import StandardMemoryManager
from mcp_server.roo.modes import get_mode
from mcp_server.roo.transitions import ModeTransitionManager
from mcp_server.roo.memory_hooks import BoomerangOperation, RooMemoryManager
from mcp_server.roo.rules import create_rule_engine
from mcp_server.roo.adapters.gemini_adapter import GeminiRooAdapter


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("roo-mcp-example")


async def setup_memory_system():
    """Set up the memory system."""
    # Create storage backend
    storage = InMemoryStorage()
    await storage.initialize()
    
    # Create memory manager
    memory_manager = StandardMemoryManager(storage)
    await memory_manager.initialize()
    
    return memory_manager


async def simulate_mode_transition(adapter: GeminiRooAdapter):
    """Simulate a mode transition from code to architect."""
    # Start in code mode
    current_mode = "code"
    logger.info(f"Starting in {current_mode} mode")
    
    # Create a request
    request = {
        "request_id": "req-123",
        "type": "code_review",
        "content": "Please review this code for performance issues."
    }
    
    # Process the request
    processed_request = await adapter.process_request(current_mode, request)
    logger.info(f"Processed request in {current_mode} mode")
    
    # Simulate a response that requests a mode transition
    response = {
        "content": "I need to analyze the architecture. Let me switch to architect mode.",
        "mode_transition": {
            "target_mode": "architect",
            "reason": "Need to analyze architecture",
            "context_data": {
                "code_file": "app.py",
                "issue": "performance"
            }
        }
    }
    
    # Process the response
    processed_response = await adapter.process_response(current_mode, processed_request, response)
    logger.info(f"Processed response with transition request")
    
    # Check if transition was successful
    if "transition" in processed_response and processed_response["transition"]["success"]:
        transition_id = processed_response["transition"]["id"]
        logger.info(f"Transition prepared: {current_mode} -> architect (ID: {transition_id})")
        
        # Switch to architect mode
        current_mode = "architect"
        
        # Create a new request in architect mode with the transition context
        architect_request = {
            "request_id": "req-124",
            "type": "architecture_analysis",
            "content": "Analyze the architecture for performance issues.",
            "transition_id": transition_id
        }
        
        # Process the request in architect mode
        processed_architect_request = await adapter.process_request(current_mode, architect_request)
        logger.info(f"Processed request in {current_mode} mode with transition context")
        
        # Simulate a response from architect mode
        architect_response = {
            "content": "I've analyzed the architecture and found some issues.",
            "analysis": {
                "issues": ["Database connection pooling not configured", "Missing caching layer"],
                "recommendations": ["Add connection pooling", "Implement Redis cache"]
            }
        }
        
        # Process the response
        processed_architect_response = await adapter.process_response(
            current_mode, 
            processed_architect_request, 
            architect_response
        )
        
        # Complete the transition back to code mode
        transition_result = await adapter.handle_mode_transition(
            transition_id,
            {
                "analysis_result": architect_response["analysis"]
            }
        )
        
        if transition_result["success"]:
            logger.info(f"Transition completed: architect -> code")
            logger.info(f"Transition context preserved: {json.dumps(transition_result['transition']['metadata'], indent=2)}")
        else:
            logger.error(f"Failed to complete transition: {transition_result.get('error')}")
    else:
        logger.error(f"Failed to prepare transition: {processed_response.get('transition', {}).get('error')}")


async def simulate_boomerang_operation(adapter: GeminiRooAdapter):
    """Simulate a boomerang operation through multiple modes."""
    # Start in code mode
    initial_mode = "code"
    logger.info(f"Starting boomerang operation from {initial_mode} mode")
    
    # Define the operation
    operation_result = await adapter.start_boomerang_operation(
        initial_mode=initial_mode,
        target_modes=["debug", "reviewer", "architect"],
        operation_data={
            "task": "Fix performance issues in the database layer",
            "files": ["database.py", "models.py"]
        },
        return_mode="code"
    )
    
    if not operation_result["success"]:
        logger.error(f"Failed to start boomerang operation: {operation_result.get('error')}")
        return
        
    operation_id = operation_result["operation_id"]
    logger.info(f"Started boomerang operation: {operation_id}")
    
    # Simulate going through each mode
    current_mode = initial_mode
    
    # First transition to debug mode
    debug_request = {
        "request_id": "req-debug-1",
        "type": "debug_analysis",
        "content": "Analyze performance issues in the database layer",
        "operation_id": operation_id
    }
    
    # Process the request in debug mode
    processed_debug_request = await adapter.process_request("debug", debug_request)
    logger.info(f"Processed request in debug mode as part of boomerang operation")
    
    # Simulate a response from debug mode
    debug_response = {
        "content": "I've identified the performance bottlenecks.",
        "issues": ["N+1 query problem", "Missing indexes"],
        "complete_operation": {
            "operation_id": operation_id,
            "result": {
                "debug_findings": ["N+1 query problem", "Missing indexes"],
                "suggested_fixes": ["Use join queries", "Add indexes on foreign keys"]
            }
        }
    }
    
    # Process the response and advance the operation
    processed_debug_response = await adapter.process_response(
        "debug", 
        processed_debug_request, 
        debug_response
    )
    
    if "operation_result" in processed_debug_response:
        next_mode = processed_debug_response["operation_result"]["next_mode"]
        logger.info(f"Operation advanced to {next_mode} mode")
        
        # Continue with reviewer mode (simplified for example)
        logger.info(f"Simulating reviewer mode step...")
        
        # Simulate completing the entire operation
        # In a real implementation, you would go through each mode
        
        # Get the final results
        operation_results = await adapter.boomerang.get_operation_results(operation_id)
        if operation_results:
            logger.info(f"Boomerang operation completed with results:")
            logger.info(json.dumps(operation_results, indent=2))
        else:
            logger.error(f"Failed to get operation results")
    else:
        logger.error(f"Failed to advance operation")


async def main():
    """Main function."""
    # Set up memory system
    memory_manager = await setup_memory_system()
    
    # Create transition manager
    transition_manager = ModeTransitionManager(memory_manager)
    
    # Create rule engine
    rule_engine = create_rule_engine()
    
    # Create Gemini adapter
    adapter = GeminiRooAdapter(memory_manager, transition_manager, rule_engine)
    
    # Simulate a mode transition
    await simulate_mode_transition(adapter)
    
    print("\n" + "-" * 50 + "\n")
    
    # Simulate a boomerang operation
    await simulate_boomerang_operation(adapter)
    
    # Demonstrate memory access
    roo_memory = RooMemoryManager(memory_manager)
    
    # Store a user preference
    await roo_memory.store_user_preference("theme", "dark")
    
    # Retrieve the user preference
    theme = await roo_memory.get_user_preference("theme")
    logger.info(f"User preference - theme: {theme}")
    
    # Store a code change
    await roo_memory.store_code_change(
        "database.py",
        "update",
        {
            "before": "def get_user(id):",
            "after": "def get_user(id: int) -> User:",
            "description": "Added type hints"
        },
        "code"
    )
    
    # Get recent changes for the file
    changes = await roo_memory.get_recent_changes_for_file("database.py")
    logger.info(f"Recent changes for database.py:")
    logger.info(json.dumps(changes, indent=2))


if __name__ == "__main__":
    asyncio.run(main())