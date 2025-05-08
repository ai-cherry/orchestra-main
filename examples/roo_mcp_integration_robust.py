#!/usr/bin/env python3
"""
Robust example script demonstrating Roo integration with MCP.

This script shows how to use the Roo integration with MCP to manage
mode transitions and memory access for AI agents, with proper error
handling, performance optimization, and comprehensive logging.
"""

import asyncio
import json
import logging
import sys
import os
import time
import traceback
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from mcp_server.storage.in_memory_storage import InMemoryStorage
    from mcp_server.managers.standard_memory_manager import StandardMemoryManager
    from mcp_server.roo.modes import get_mode, RooMode, RooModeCapability
    from mcp_server.roo.transitions import ModeTransitionManager, TransitionContext
    from mcp_server.roo.memory_hooks import BoomerangOperation, RooMemoryManager, OperationContext
    from mcp_server.roo.rules import create_rule_engine, Rule, RuleType, RuleIntent
    from mcp_server.roo.adapters.gemini_adapter import GeminiRooAdapter
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please run setup_roo_mcp.py first to set up the environment.")
    sys.exit(1)


# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("roo_mcp_integration.log")
    ]
)
logger = logging.getLogger("roo-mcp-example")


class PerformanceMetrics:
    """Helper class to track and report performance metrics."""
    
    def __init__(self):
        self.operations: Dict[str, List[float]] = {}
    
    def start_operation(self, name: str) -> float:
        """Start tracking an operation."""
        start_time = time.time()
        return start_time
    
    def end_operation(self, name: str, start_time: float) -> float:
        """End tracking an operation and record its duration."""
        duration = time.time() - start_time
        
        if name not in self.operations:
            self.operations[name] = []
        
        self.operations[name].append(duration)
        return duration
    
    def get_average(self, name: str) -> Optional[float]:
        """Get the average duration of an operation."""
        if name not in self.operations or not self.operations[name]:
            return None
        
        return sum(self.operations[name]) / len(self.operations[name])
    
    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """Get a summary of all operations."""
        summary = {}
        
        for name, durations in self.operations.items():
            if not durations:
                continue
                
            summary[name] = {
                "avg": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
                "count": len(durations)
            }
        
        return summary
    
    def print_summary(self) -> None:
        """Print a summary of all operations."""
        summary = self.get_summary()
        
        if not summary:
            logger.info("No performance metrics recorded.")
            return
        
        logger.info("Performance Metrics Summary:")
        for name, stats in summary.items():
            logger.info(f"  {name}:")
            logger.info(f"    Average: {stats['avg']*1000:.2f} ms")
            logger.info(f"    Min: {stats['min']*1000:.2f} ms")
            logger.info(f"    Max: {stats['max']*1000:.2f} ms")
            logger.info(f"    Count: {stats['count']}")


async def setup_memory_system() -> Tuple[StandardMemoryManager, PerformanceMetrics]:
    """
    Set up the memory system with performance tracking.
    
    Returns:
        Tuple containing the memory manager and performance metrics.
    """
    metrics = PerformanceMetrics()
    
    # Create storage backend
    start_time = metrics.start_operation("storage_initialization")
    try:
        storage = InMemoryStorage()
        await storage.initialize()
        logger.info("Storage backend initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize storage backend: {e}")
        raise
    finally:
        duration = metrics.end_operation("storage_initialization", start_time)
        logger.debug(f"Storage initialization took {duration*1000:.2f} ms")
    
    # Create memory manager
    start_time = metrics.start_operation("memory_manager_initialization")
    try:
        memory_manager = StandardMemoryManager(storage)
        await memory_manager.initialize()
        logger.info("Memory manager initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize memory manager: {e}")
        raise
    finally:
        duration = metrics.end_operation("memory_manager_initialization", start_time)
        logger.debug(f"Memory manager initialization took {duration*1000:.2f} ms")
    
    return memory_manager, metrics


async def simulate_mode_transition(
    adapter: GeminiRooAdapter, 
    metrics: PerformanceMetrics
) -> Optional[Dict[str, Any]]:
    """
    Simulate a mode transition from code to architect with error handling.
    
    Args:
        adapter: The GeminiRooAdapter instance
        metrics: Performance metrics tracker
        
    Returns:
        Transition result if successful, None otherwise
    """
    try:
        # Start in code mode
        current_mode = "code"
        logger.info(f"Starting in {current_mode} mode")
        
        # Create a request
        request = {
            "request_id": f"req-{int(time.time())}",
            "type": "code_review",
            "content": "Please review this code for performance issues."
        }
        
        # Process the request
        start_time = metrics.start_operation("process_request")
        try:
            processed_request = await adapter.process_request(current_mode, request)
            logger.info(f"Processed request in {current_mode} mode")
        except Exception as e:
            logger.error(f"Failed to process request in {current_mode} mode: {e}")
            return None
        finally:
            duration = metrics.end_operation("process_request", start_time)
            logger.debug(f"Request processing took {duration*1000:.2f} ms")
        
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
        start_time = metrics.start_operation("process_response")
        try:
            processed_response = await adapter.process_response(current_mode, processed_request, response)
            logger.info(f"Processed response with transition request")
        except Exception as e:
            logger.error(f"Failed to process response with transition request: {e}")
            return None
        finally:
            duration = metrics.end_operation("process_response", start_time)
            logger.debug(f"Response processing took {duration*1000:.2f} ms")
        
        # Check if transition was successful
        if "transition" in processed_response and processed_response["transition"]["success"]:
            transition_id = processed_response["transition"]["id"]
            logger.info(f"Transition prepared: {current_mode} -> architect (ID: {transition_id})")
            
            # Switch to architect mode
            current_mode = "architect"
            
            # Create a new request in architect mode with the transition context
            architect_request = {
                "request_id": f"req-{int(time.time())}",
                "type": "architecture_analysis",
                "content": "Analyze the architecture for performance issues.",
                "transition_id": transition_id
            }
            
            # Process the request in architect mode
            start_time = metrics.start_operation("process_architect_request")
            try:
                processed_architect_request = await adapter.process_request(current_mode, architect_request)
                logger.info(f"Processed request in {current_mode} mode with transition context")
            except Exception as e:
                logger.error(f"Failed to process request in {current_mode} mode: {e}")
                return None
            finally:
                duration = metrics.end_operation("process_architect_request", start_time)
                logger.debug(f"Architect request processing took {duration*1000:.2f} ms")
            
            # Simulate a response from architect mode
            architect_response = {
                "content": "I've analyzed the architecture and found some issues.",
                "analysis": {
                    "issues": ["Database connection pooling not configured", "Missing caching layer"],
                    "recommendations": ["Add connection pooling", "Implement Redis cache"]
                }
            }
            
            # Process the response
            start_time = metrics.start_operation("process_architect_response")
            try:
                processed_architect_response = await adapter.process_response(
                    current_mode, 
                    processed_architect_request, 
                    architect_response
                )
                logger.info(f"Processed response in {current_mode} mode")
            except Exception as e:
                logger.error(f"Failed to process response in {current_mode} mode: {e}")
                return None
            finally:
                duration = metrics.end_operation("process_architect_response", start_time)
                logger.debug(f"Architect response processing took {duration*1000:.2f} ms")
            
            # Complete the transition back to code mode
            start_time = metrics.start_operation("complete_transition")
            try:
                transition_result = await adapter.handle_mode_transition(
                    transition_id,
                    {
                        "analysis_result": architect_response["analysis"]
                    }
                )
                
                if transition_result["success"]:
                    logger.info(f"Transition completed: architect -> code")
                    logger.info(f"Transition context preserved: {json.dumps(transition_result['transition']['metadata'], indent=2)}")
                    return transition_result
                else:
                    logger.error(f"Failed to complete transition: {transition_result.get('error')}")
                    return None
            except Exception as e:
                logger.error(f"Failed to complete transition: {e}")
                return None
            finally:
                duration = metrics.end_operation("complete_transition", start_time)
                logger.debug(f"Transition completion took {duration*1000:.2f} ms")
        else:
            logger.error(f"Failed to prepare transition: {processed_response.get('transition', {}).get('error')}")
            return None
    except Exception as e:
        logger.error(f"Error in simulate_mode_transition: {e}")
        logger.debug(traceback.format_exc())
        return None


async def simulate_boomerang_operation(
    adapter: GeminiRooAdapter,
    metrics: PerformanceMetrics
) -> Optional[Dict[str, Any]]:
    """
    Simulate a boomerang operation through multiple modes with error handling.
    
    Args:
        adapter: The GeminiRooAdapter instance
        metrics: Performance metrics tracker
        
    Returns:
        Operation results if successful, None otherwise
    """
    try:
        # Start in code mode
        initial_mode = "code"
        logger.info(f"Starting boomerang operation from {initial_mode} mode")
        
        # Define the operation
        start_time = metrics.start_operation("start_boomerang_operation")
        try:
            operation_result = await adapter.start_boomerang_operation(
                initial_mode=initial_mode,
                target_modes=["debug", "reviewer", "architect"],
                operation_data={
                    "task": "Fix performance issues in the database layer",
                    "files": ["database.py", "models.py"]
                },
                return_mode="code"
            )
        except Exception as e:
            logger.error(f"Failed to start boomerang operation: {e}")
            return None
        finally:
            duration = metrics.end_operation("start_boomerang_operation", start_time)
            logger.debug(f"Starting boomerang operation took {duration*1000:.2f} ms")
        
        if not operation_result["success"]:
            logger.error(f"Failed to start boomerang operation: {operation_result.get('error')}")
            return None
            
        operation_id = operation_result["operation_id"]
        logger.info(f"Started boomerang operation: {operation_id}")
        
        # Simulate going through each mode
        current_mode = initial_mode
        
        # First transition to debug mode
        debug_request = {
            "request_id": f"req-debug-{int(time.time())}",
            "type": "debug_analysis",
            "content": "Analyze performance issues in the database layer",
            "operation_id": operation_id
        }
        
        # Process the request in debug mode
        start_time = metrics.start_operation("process_debug_request")
        try:
            processed_debug_request = await adapter.process_request("debug", debug_request)
            logger.info(f"Processed request in debug mode as part of boomerang operation")
        except Exception as e:
            logger.error(f"Failed to process request in debug mode: {e}")
            return None
        finally:
            duration = metrics.end_operation("process_debug_request", start_time)
            logger.debug(f"Debug request processing took {duration*1000:.2f} ms")
        
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
        start_time = metrics.start_operation("process_debug_response")
        try:
            processed_debug_response = await adapter.process_response(
                "debug", 
                processed_debug_request, 
                debug_response
            )
        except Exception as e:
            logger.error(f"Failed to process debug response: {e}")
            return None
        finally:
            duration = metrics.end_operation("process_debug_response", start_time)
            logger.debug(f"Debug response processing took {duration*1000:.2f} ms")
        
        if "operation_result" in processed_debug_response:
            next_mode = processed_debug_response["operation_result"]["next_mode"]
            logger.info(f"Operation advanced to {next_mode} mode")
            
            # Continue with reviewer mode (simplified for example)
            logger.info(f"Simulating reviewer mode step...")
            
            # Simulate completing the entire operation
            # In a real implementation, you would go through each mode
            
            # Get the final results
            start_time = metrics.start_operation("get_operation_results")
            try:
                operation_results = await adapter.boomerang.get_operation_results(operation_id)
                if operation_results:
                    logger.info(f"Boomerang operation completed with results:")
                    logger.info(json.dumps(operation_results, indent=2))
                    return {"operation_id": operation_id, "results": operation_results}
                else:
                    logger.error(f"Failed to get operation results")
                    return None
            except Exception as e:
                logger.error(f"Failed to get operation results: {e}")
                return None
            finally:
                duration = metrics.end_operation("get_operation_results", start_time)
                logger.debug(f"Getting operation results took {duration*1000:.2f} ms")
        else:
            logger.error(f"Failed to advance operation")
            return None
    except Exception as e:
        logger.error(f"Error in simulate_boomerang_operation: {e}")
        logger.debug(traceback.format_exc())
        return None


async def demonstrate_memory_operations(
    roo_memory: RooMemoryManager,
    metrics: PerformanceMetrics
) -> Dict[str, Any]:
    """
    Demonstrate memory operations with performance tracking.
    
    Args:
        roo_memory: The RooMemoryManager instance
        metrics: Performance metrics tracker
        
    Returns:
        Dictionary with operation results
    """
    results = {}
    
    # Store a user preference
    start_time = metrics.start_operation("store_user_preference")
    try:
        preference_key = await roo_memory.store_user_preference("theme", "dark")
        logger.info(f"Stored user preference with key: {preference_key}")
        results["store_preference"] = {"success": True, "key": preference_key}
    except Exception as e:
        logger.error(f"Failed to store user preference: {e}")
        results["store_preference"] = {"success": False, "error": str(e)}
    finally:
        duration = metrics.end_operation("store_user_preference", start_time)
        logger.debug(f"Storing user preference took {duration*1000:.2f} ms")
    
    # Retrieve the user preference
    start_time = metrics.start_operation("get_user_preference")
    try:
        theme = await roo_memory.get_user_preference("theme")
        logger.info(f"Retrieved user preference - theme: {theme}")
        results["get_preference"] = {"success": True, "value": theme}
    except Exception as e:
        logger.error(f"Failed to retrieve user preference: {e}")
        results["get_preference"] = {"success": False, "error": str(e)}
    finally:
        duration = metrics.end_operation("get_user_preference", start_time)
        logger.debug(f"Retrieving user preference took {duration*1000:.2f} ms")
    
    # Store a code change
    start_time = metrics.start_operation("store_code_change")
    try:
        change_key = await roo_memory.store_code_change(
            "database.py",
            "update",
            {
                "before": "def get_user(id):",
                "after": "def get_user(id: int) -> User:",
                "description": "Added type hints"
            },
            "code"
        )
        logger.info(f"Stored code change with key: {change_key}")
        results["store_code_change"] = {"success": True, "key": change_key}
    except Exception as e:
        logger.error(f"Failed to store code change: {e}")
        results["store_code_change"] = {"success": False, "error": str(e)}
    finally:
        duration = metrics.end_operation("store_code_change", start_time)
        logger.debug(f"Storing code change took {duration*1000:.2f} ms")
    
    # Get recent changes for the file
    start_time = metrics.start_operation("get_recent_changes")
    try:
        changes = await roo_memory.get_recent_changes_for_file("database.py")
        logger.info(f"Retrieved recent changes for database.py:")
        logger.info(json.dumps(changes, indent=2))
        results["get_changes"] = {"success": True, "changes": changes}
    except Exception as e:
        logger.error(f"Failed to retrieve recent changes: {e}")
        results["get_changes"] = {"success": False, "error": str(e)}
    finally:
        duration = metrics.end_operation("get_recent_changes", start_time)
        logger.debug(f"Retrieving recent changes took {duration*1000:.2f} ms")
    
    return results


async def main() -> int:
    """
    Main function with comprehensive error handling.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        logger.info("Starting Roo-MCP integration example...")
        
        # Set up memory system
        try:
            memory_manager, metrics = await setup_memory_system()
        except Exception as e:
            logger.error(f"Failed to set up memory system: {e}")
            return 1
        
        # Create transition manager
        try:
            transition_manager = ModeTransitionManager(memory_manager)
            logger.info("Transition manager created successfully.")
        except Exception as e:
            logger.error(f"Failed to create transition manager: {e}")
            return 1
        
        # Create rule engine
        try:
            rule_engine = create_rule_engine()
            logger.info("Rule engine created successfully.")
        except Exception as e:
            logger.error(f"Failed to create rule engine: {e}")
            return 1
        
        # Create Gemini adapter
        try:
            adapter = GeminiRooAdapter(memory_manager, transition_manager, rule_engine)
            logger.info("Gemini adapter created successfully.")
        except Exception as e:
            logger.error(f"Failed to create Gemini adapter: {e}")
            return 1
        
        # Simulate a mode transition
        transition_result = await simulate_mode_transition(adapter, metrics)
        if transition_result:
            logger.info("Mode transition simulation completed successfully.")
        else:
            logger.warning("Mode transition simulation did not complete successfully.")
        
        logger.info("\n" + "-" * 50 + "\n")
        
        # Simulate a boomerang operation
        operation_result = await simulate_boomerang_operation(adapter, metrics)
        if operation_result:
            logger.info("Boomerang operation simulation completed successfully.")
        else:
            logger.warning("Boomerang operation simulation did not complete successfully.")
        
        logger.info("\n" + "-" * 50 + "\n")
        
        # Demonstrate memory access
        roo_memory = RooMemoryManager(memory_manager)
        memory_results = await demonstrate_memory_operations(roo_memory, metrics)
        
        # Print performance metrics
        metrics.print_summary()
        
        logger.info("Roo-MCP integration example completed.")
        return 0
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")
        logger.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
        sys.exit(130)
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)