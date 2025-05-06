"""
Persona middleware for AI Orchestration System.

This middleware manages persona selection for incoming requests, ensuring
that the appropriate persona configuration is available for the interaction endpoint.
"""

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi import Depends

from core.orchestrator.src.api.dependencies.personas import get_persona_config

# Configure logging
logger = logging.getLogger(__name__)


class PersonaMiddleware(BaseHTTPMiddleware):
    """
    Middleware that sets the active persona for incoming requests.
    
    This middleware examines the request query parameters or path for
    a persona identifier and sets the appropriate persona configuration
    on the request state for use by the interaction endpoint.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and set the active persona.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or endpoint handler
            
        Returns:
            The HTTP response from the next handler
        """
        # Extract persona name from query parameters
        persona_name = request.query_params.get("persona")
        
        try:
            # Get persona configuration
            persona_config = get_persona_config(request, persona_name)
            
            # Set on the request state
            request.state.active_persona = persona_config
            
            logger.debug(f"Set active persona to {persona_config.name}")
        except Exception as e:
            # Log error but continue processing
            logger.error(f"Failed to set active persona: {e}")
        
        # Proceed with the request
        response = await call_next(request)
        return response
