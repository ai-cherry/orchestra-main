"""
"""
    """
    """
    logger.info("Starting Orchestra AI API...")

    try:


        pass
        # Initialize Orchestra system
        orchestra_system = OrchestraSystem()
        await orchestra_system.initialize()

        # Register example workflows
        register_example_workflows()
        logger.info("Registered example workflows")

        # Register example agents
        register_example_agents()
        logger.info("Registered example agents")

        # Register default personas
        persona_manager = get_persona_manager()

        # Helpful Assistant persona
        persona_manager.register_persona(
            PersonaConfig(
                id="helpful_assistant",
                name="Helpful Assistant",
                description="A knowledgeable and helpful AI assistant",
                traits=[
                    PersonaTrait.HELPFUL,
                    PersonaTrait.PROFESSIONAL,
                    PersonaTrait.DETAILED,
                ],
                style=ResponseStyle.EDUCATIONAL,
            )
        )

        # Task Executor persona
        persona_manager.register_persona(
            PersonaConfig(
                id="task_executor",
                name="Task Executor",
                description="An efficient task-focused AI",
                traits=[
                    PersonaTrait.ANALYTICAL,
                    PersonaTrait.CONCISE,
                    PersonaTrait.TECHNICAL,
                ],
                style=ResponseStyle.TECHNICAL,
            )
        )

        # Conversationalist persona
        persona_manager.register_persona(
            PersonaConfig(
                id="conversationalist",
                name="Friendly Conversationalist",
                description="A friendly and engaging conversational partner",
                traits=[
                    PersonaTrait.FRIENDLY,
                    PersonaTrait.EMPATHETIC,
                    PersonaTrait.HUMOROUS,
                ],
                style=ResponseStyle.CONVERSATIONAL,
            )
        )

        logger.info("Registered default personas")

        # Start all agents
        from core.services.agents.base import get_agent_manager

        agent_manager = get_agent_manager()
        await agent_manager.start_all_agents()
        logger.info("Started all agents")

        logger.info("Orchestra AI API started successfully")

    except Exception:


        pass
        logger.error(f"Failed to start Orchestra AI API: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down Orchestra AI API...")

    try:


        pass
        if orchestra_system:
            await orchestra_system.shutdown()

        # Stop all agents
        agent_manager = get_agent_manager()
        await agent_manager.stop_all_agents()

        logger.info("Orchestra AI API shut down successfully")

    except Exception:


        pass
        logger.error(f"Error during shutdown: {e}", exc_info=True)

# Create FastAPI application
app = FastAPI(
    title="Orchestra AI API",
    description="AI orchestration platform with multi-agent collaboration",
    version="1.0.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(ErrorHandlerMiddleware)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversation.router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {"name": "Orchestra AI API", "version": "1.0.0", "status": "running"}

# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    """
        services_health["orchestra"] = {"status": "healthy", "initialized": True}
    else:
        services_health["orchestra"] = {"status": "unhealthy", "initialized": False}

    # Check memory service
    try:

        pass
        from core.services.memory.unified_memory import get_memory_service

        memory_service = get_memory_service()
        # Simple health check - try to get a non-existent key
        await memory_service.get("health_check_test")
        services_health["memory"] = {"status": "healthy"}
    except Exception:

        pass
        services_health["memory"] = {"status": "unhealthy", "error": str(e)}

    # Check event bus
    try:

        pass
        from core.services.events.event_bus import get_event_bus

        event_bus = get_event_bus()
        services_health["event_bus"] = {
            "status": "healthy",
            "subscribers": len(event_bus._subscribers),
        }
    except Exception:

        pass
        services_health["event_bus"] = {"status": "unhealthy", "error": str(e)}

    # Check agents
    try:

        pass
        from core.services.agents.base import get_agent_manager

        agent_manager = get_agent_manager()
        agents = agent_manager.list_agents()
        services_health["agents"] = {"status": "healthy", "count": len(agents)}
    except Exception:

        pass
        services_health["agents"] = {"status": "unhealthy", "error": str(e)}

    # Determine overall status
    overall_status = "healthy"
    for service, health in services_health.items():
        if health.get("status") != "healthy":
            overall_status = "degraded"
            break

    return HealthCheckResponse(success=True, status=overall_status, services=services_health, version="1.0.0")

if __name__ == "__main__":
    import uvicorn

    # Run the application
    uvicorn.run("core.api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
