"""
Agent Endpoints for AI Orchestration System.

This module provides API endpoints for working with Runtime Agents,
allowing them to be triggered and monitored through the API.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from pydantic import BaseModel

from core.orchestrator.src.config.config import get_settings
from core.orchestrator.src.services.agent_service import get_agent_instance
from packages.shared.src.memory.stubs import InMemoryMemoryManagerStub

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize a memory manager for storing agent results
# In a production environment, this would be replaced with a persistent implementation
memory_manager = InMemoryMemoryManagerStub()
memory_manager.initialize()

class AgentRunRequest(BaseModel):
    """Request model for running an agent."""

    context: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None
    persona_id: Optional[str] = None

class AgentRunResponse(BaseModel):
    """Response model for the agent run endpoint."""

    status: str
    agent_name: str
    task_id: str

@router.post("/run/{agent_name}", response_model=AgentRunResponse, tags=["agents"])
async def run_agent_task(
    agent_name: str,
    request: AgentRunRequest = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    settings=Depends(get_settings),
):
    """
    Run an agent task asynchronously.

    Args:
        agent_name: The name/type of agent to run
        request: The request body containing context and optional configuration
        background_tasks: FastAPI's BackgroundTasks for async execution
        settings: Application settings

    Returns:
        Status information about the task

    Raises:
        HTTPException: If the agent is not found or other errors occur
    """
    logger.info(f"Request to run agent: {agent_name}")

    # Generate a task ID for tracking
    import uuid

    task_id = str(uuid.uuid4())

    try:
        # Get the agent instance with memory manager
        persona = None  # In the future, we might look up persona by ID
        agent = get_agent_instance(
            agent_name,
            config=request.config,
            persona=persona,
            memory_manager=memory_manager,
        )

        # Add the agent run to background tasks
        background_tasks.add_task(_execute_agent_task, agent=agent, context=request.context, task_id=task_id)

        return {"status": "Task started", "agent_name": agent_name, "task_id": task_id}

    except ValueError as e:
        # Agent not found or invalid
        logger.error(f"Agent error: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Agent not found: {str(e)}")

    except Exception as e:
        # Other unexpected errors
        logger.error(f"Error starting agent task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start agent task: {str(e)}")

async def _execute_agent_task(agent, context: Dict[str, Any], task_id: str) -> None:
    """
    Execute an agent task and handle any exceptions.

    This function is designed to be run as a background task.

    Args:
        agent: The agent instance to run
        context: The context dictionary for the agent
        task_id: A unique ID for the task
    """
    logger.info(f"Starting agent task {task_id} with agent {agent.name}")

    try:
        # Execute the agent
        result = await agent.run(context)
        logger.info(f"Agent task {task_id} completed successfully: {result.get('status', 'unknown')}")

    except Exception as e:
        logger.error(f"Agent task {task_id} failed with error: {str(e)}", exc_info=True)
        logger.warning(f"Failure of agent task {task_id} may affect dependent processes or results.")

    finally:
        # Ensure agent is properly shut down
        try:
            agent.shutdown()
            logger.debug(f"Agent {agent.name} shut down after task {task_id}")
        except Exception as e:
            logger.warning(f"Error shutting down agent: {str(e)}", exc_info=True)
            logger.warning(f"Agent shutdown failure for {agent.name} may lead to resource leaks.")
