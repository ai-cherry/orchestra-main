"""
"""
    """Request model for running an agent."""
    """Response model for the agent run endpoint."""
@router.post("/run/{agent_name}", response_model=AgentRunResponse, tags=["agents"])
async def run_agent_task(
    agent_name: str,
    request: AgentRunRequest = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    settings=Depends(get_settings),
):
    """
    """
    logger.info(f"Request to run agent: {agent_name}")

    # Generate a task ID for tracking
    import uuid

    task_id = str(uuid.uuid4())

    try:


        pass
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

    except Exception:


        pass
        # Agent not found or invalid
        logger.error(f"Agent error: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Agent not found: {str(e)}")

    except Exception:


        pass
        # Other unexpected errors
        logger.error(f"Error starting agent task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start agent task: {str(e)}")

async def _execute_agent_task(agent, context: Dict[str, Any], task_id: str) -> None:
    """
    """
    logger.info(f"Starting agent task {task_id} with agent {agent.name}")

    try:


        pass
        # Execute the agent
        result = await agent.run(context)
        logger.info(f"Agent task {task_id} completed successfully: {result.get('status', 'unknown')}")

    except Exception:


        pass
        logger.error(f"Agent task {task_id} failed with error: {str(e)}", exc_info=True)
        logger.warning(f"Failure of agent task {task_id} may affect dependent processes or results.")

    finally:
        # Ensure agent is properly shut down
        try:

            pass
            agent.shutdown()
        except Exception:

            pass
            logger.warning(f"Error shutting down agent: {str(e)}", exc_info=True)
            logger.warning(f"Agent shutdown failure for {agent.name} may lead to resource leaks.")
