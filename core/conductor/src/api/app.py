"""
"""
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    """
        logger.info(f"Loaded {len(personas)} persona configurations")
    except Exception:

        pass
        logger.error(f"Failed to load persona configurations: {e}")

    # Initialize memory system
    from core.conductor.src.api.dependencies.memory import initialize_memory_manager

    try:


        pass
        await initialize_memory_manager()
        logger.info("Memory manager initialized")
    except Exception:

        pass
        logger.error(f"Failed to initialize memory manager: {e}")

    # Initialize Redis cache if available
    from core.conductor.src.api.dependencies.cache import initialize_redis_cache

    try:


        pass
        await initialize_redis_cache()
        logger.info("Redis cache initialized")
    except Exception:

        pass
        logger.error(f"Failed to initialize Redis cache: {e}")

    # Log environment information
    logger.info(f"Running in environment: {settings.ENVIRONMENT}")

    logger.info("Application startup complete")

    # Yield control back to FastAPI
    yield

    # Shutdown operations
    logger.info("Application shutting down")

    # Close Redis cache
    from core.conductor.src.api.dependencies.cache import close_redis_cache

    try:


        pass
        await close_redis_cache()
        logger.info("Redis cache closed")
    except Exception:

        pass
        logger.error(f"Failed to close Redis cache: {e}")

    # Close memory system
    from core.conductor.src.api.dependencies.memory import close_memory_manager

    try:


        pass
        await close_memory_manager()
        logger.info("Memory manager closed")
    except Exception:

        pass
        logger.error(f"Failed to close memory manager: {e}")

    logger.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="AI coordination API",
    description="API for interacting with AI personas with memory",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Use specific origins instead of ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and use the persona middleware
from .middleware.persona_middleware import PersonaMiddleware

# Add persona middleware
app.add_middleware(PersonaMiddleware)

# Register API routes
app.include_router(auth.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(stubs.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))

    # Start server
    uvicorn.run(
        "core.conductor.src.api.app:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
    )
