"""
Factory AI Integration Package.

This package provides the complete integration between Factory AI Droids
and the Orchestra/Roo infrastructure, including:
- Bridge API Gateway
- MCP Server Adapters
- Context Management
- Caching Layer
- Monitoring Integration
"""

__version__ = "1.0.0"
__all__ = [
    "FactoryBridgeGateway",
    "FactoryContextManager",
    "setup_factory_integration",
]

# Import main components
from .factory.bridge import FactoryBridgeGateway
from .factory.context import FactoryContextManager


def setup_factory_integration() -> None:
    """Initialize Factory AI integration.
    
    This function sets up all necessary components for Factory AI integration,
    including database connections, cache initialization, and monitoring setup.
    """
    import logging
    import os
    
    # Configure logging
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Initializing Factory AI integration...")
    
    # Validate environment
    required_vars = [
        "FACTORY_AI_API_KEY",
        "POSTGRES_CONNECTION_STRING",
        "WEAVIATE_URL",
        "REDIS_URL",
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
    
    logger.info("Factory AI integration initialized successfully")