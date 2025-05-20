"""
Chat Integration Module for File Ingestion System.

This module provides integration with the Phidata chat system
to handle file ingestion commands.
"""

import logging
from typing import Dict, List, Optional, Any, Union, Tuple

from fastapi import Depends, Request

from packages.ingestion.src.api.ingestion_api import IngestionAPI
from packages.ingestion.src.config.settings import get_settings

# Configure logging
logger = logging.getLogger(__name__)


class IngestionChatMiddleware:
    """
    Middleware for integrating file ingestion with chat.

    This class provides methods for processing chat messages and
    intercepting ingestion commands.
    """

    def __init__(self):
        """Initialize the chat middleware."""
        self.settings = get_settings()
        self.api = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the chat middleware and API."""
        if self._initialized:
            return

        try:
            # Create and initialize the API
            self.api = await IngestionAPI.create_api()

            self._initialized = True
            logger.info("Ingestion chat middleware initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ingestion chat middleware: {e}")
            # Continue without ingestion capabilities if initialization fails

    async def close(self) -> None:
        """Close the chat middleware and API."""
        if self.api:
            await self.api.close()

        self._initialized = False
        logger.debug("Ingestion chat middleware closed")

    async def process_message(
        self, message: str, user_id: str, session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process a chat message for ingestion commands.

        Args:
            message: The message text
            user_id: ID of the user
            session_id: Optional session ID

        Returns:
            Response data if message is an ingestion command, None otherwise
        """
        if not self._initialized or not self.api:
            return None

        try:
            # Process the message with the API
            response_data = await self.api.process_chat_command(
                message, user_id, session_id
            )
            return response_data
        except Exception as e:
            logger.error(f"Error processing chat message for ingestion: {e}")
            return None


# Singleton instance
_ingestion_middleware = None


async def get_ingestion_middleware() -> IngestionChatMiddleware:
    """
    Get or create the ingestion chat middleware instance.

    This function is used as a FastAPI dependency to get the middleware
    instance for processing chat messages.

    Returns:
        Initialized ingestion chat middleware
    """
    global _ingestion_middleware

    if _ingestion_middleware is None:
        _ingestion_middleware = IngestionChatMiddleware()
        await _ingestion_middleware.initialize()

    return _ingestion_middleware


async def process_phidata_message(
    message: str,
    user_id: str,
    session_id: Optional[str] = None,
    middleware: Optional[IngestionChatMiddleware] = None,
) -> Dict[str, Any]:
    """
    Process a Phidata chat message for ingestion commands.

    This function can be called from the Phidata chat endpoint to
    process messages and detect ingestion commands. If an ingestion
    command is detected, it returns the response data to be included
    in the agent response.

    Args:
        message: The message text
        user_id: ID of the user
        session_id: Optional session ID
        middleware: Optional middleware instance

    Returns:
        Response data for agent or empty dict if not an ingestion command
    """
    try:
        # Create middleware if not provided
        if middleware is None:
            middleware = await get_ingestion_middleware()

        # Process the message
        response_data = await middleware.process_message(message, user_id, session_id)

        if response_data:
            # Format for agent response
            agent_response = {
                "ingestion_task": True,
                "task_id": response_data.get("task_id"),
                "status": response_data.get("status"),
                "message": response_data.get("message"),
            }

            # Add any details if present
            details = response_data.get("details")
            if details:
                agent_response["details"] = details

            return agent_response
        else:
            # Not an ingestion command
            return {}
    except Exception as e:
        logger.error(f"Error processing Phidata message: {e}")
        return {}


async def create_agent_response_for_task(
    task_id: str, middleware: Optional[IngestionChatMiddleware] = None
) -> Dict[str, Any]:
    """
    Create an agent response for an ingestion task.

    This function can be used to create a response for an existing
    ingestion task, for example when checking the status of a task.

    Args:
        task_id: ID of the ingestion task
        middleware: Optional middleware instance

    Returns:
        Agent response data
    """
    try:
        # Create middleware if not provided
        if middleware is None:
            middleware = await get_ingestion_middleware()

        # Get task status
        if middleware.api:
            result = await middleware.api.get_task_status(task_id)

            # Format for agent response
            agent_response = {
                "ingestion_task": True,
                "task_id": task_id,
                "status": str(result.status),
                "message": result.message,
                "details": result.details,
            }

            return agent_response
        else:
            return {}
    except Exception as e:
        logger.error(f"Error creating agent response for task {task_id}: {e}")
        return {}
