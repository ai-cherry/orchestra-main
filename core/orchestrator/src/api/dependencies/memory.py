"""
Memory manager dependency for AI Orchestration System.

This module provides the dependency injection function for the memory manager,
supporting both in-memory and persistent Firestore storage options.

The memory manager is chosen based on environment settings and cloud configuration.
- In development/local mode: Uses InMemoryMemoryManager
- In cloud environments: Uses FirestoreMemoryManager when credentials are available
"""

import logging
import os
from typing import Optional, Dict, Any
import asyncio
from functools import lru_cache
from fastapi import Depends

# Import settings
from core.orchestrator.src.config.settings import Settings, get_settings

# Import the memory manager interface and implementations
try:
    from packages.shared.src.memory.memory_manager import MemoryManager
    from packages.shared.src.memory.memory_manager import InMemoryMemoryManager
    # Try to import the Firestore adapter
    try:
        from packages.shared.src.memory.firestore_adapter import FirestoreMemoryAdapter
        FIRESTORE_AVAILABLE = True
    except ImportError:
        logger.warning("Failed to import FirestoreMemoryAdapter, Firestore storage will not be available")
        FIRESTORE_AVAILABLE = False
        
    # Fall back to using stubs if the main implementation isn't available
    USE_STUBS = False
except ImportError:
    logging.warning("Failed to import memory managers from packages.shared.src.memory, falling back to stub implementation")
    from packages.shared.src.memory.memory_manager import MemoryManager
    from packages.shared.src.memory.stubs import InMemoryMemoryManagerStub as InMemoryMemoryManager
    FIRESTORE_AVAILABLE = False
    USE_STUBS = True

# Configure logging
logger = logging.getLogger(__name__)

# Global memory manager instance
_memory_manager = None

def create_memory_manager(settings: Settings) -> MemoryManager:
    """
    Create a memory manager instance based on settings.
    
    This function selects the appropriate memory manager based on
    environment and configuration, but does not initialize it.
    Initialization happens in the application's lifespan event.
    
    Args:
        settings: Application settings
    
    Returns:
        A memory manager instance (not initialized)
    """    
    # Determine if we need cloud storage based on environment and project ID
    use_firestore = (
        settings.ENVIRONMENT in ["prod", "production", "stage", "staging"] and 
        settings.get_gcp_project_id() is not None and 
        FIRESTORE_AVAILABLE
    )
    
    # Use Firestore if available and configured
    if use_firestore:
        try:
            logger.info(f"Creating Firestore memory adapter for environment: {settings.ENVIRONMENT}")
            return FirestoreMemoryAdapter(
                project_id=settings.get_gcp_project_id(),
                credentials_path=settings.get_gcp_credentials_path(),
                namespace=settings.FIRESTORE_NAMESPACE or f"orchestra-{settings.ENVIRONMENT}"
            )
        except Exception as e:
            logger.error(f"Failed to create Firestore memory adapter: {e}")
            logger.warning("Falling back to in-memory implementation")
    
    # Use in-memory implementation
    namespace = settings.FIRESTORE_NAMESPACE or f"orchestra-{settings.ENVIRONMENT}"
    logger.info(f"Using in-memory memory manager with namespace: {namespace}")
    return InMemoryMemoryManager(namespace=namespace)

async def get_memory_manager(
    settings: Settings = Depends(get_settings)
) -> MemoryManager:
    """
    Get an initialized memory manager instance.
    
    This dependency function creates and initializes a memory manager
    if one doesn't exist, or returns the existing one.
    
    Args:
        settings: Application settings
    
    Returns:
        An initialized memory manager
    """
    global _memory_manager
    
    # Create the memory manager if it doesn't exist
    if _memory_manager is None:
        _memory_manager = create_memory_manager(settings)
        
        try:
            # Initialize the memory manager
            await _memory_manager.initialize()
            logger.info(f"Memory manager initialized: {type(_memory_manager).__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize memory manager: {e}")
            # Fall back to in-memory if initialization fails
            if not isinstance(_memory_manager, InMemoryMemoryManager):
                logger.warning("Falling back to in-memory implementation")
                _memory_manager = InMemoryMemoryManager()
                await _memory_manager.initialize()
    
    return _memory_manager

async def initialize_memory_manager(settings: Settings = None) -> None:
    """
    Initialize the memory manager during application startup.
    
    Args:
        settings: Optional application settings
    """
    global _memory_manager
    
    if settings is None:
        settings = get_settings()
    
    # Create the memory manager if it doesn't exist
    if _memory_manager is None:
        _memory_manager = create_memory_manager(settings)
    
    # Initialize the memory manager
    logger.info(f"Initializing memory manager: {type(_memory_manager).__name__}")
    await _memory_manager.initialize()
    logger.info("Memory manager initialized successfully")
    
    # Perform a health check
    if hasattr(_memory_manager, "health_check"):
        health_info = await _memory_manager.health_check()
        logger.info(f"Memory manager health check: {health_info}")

async def close_memory_manager() -> None:
    """
    Close the memory manager during application shutdown.
    """
    global _memory_manager
    
    if _memory_manager is not None:
        logger.info(f"Closing memory manager: {type(_memory_manager).__name__}")
        await _memory_manager.close()
        logger.info("Memory manager closed successfully")
        _memory_manager = None
