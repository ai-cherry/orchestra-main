"""
Example Client for Enhanced Persona System.

This module demonstrates how to interact with the enhanced persona system
programmatically. It provides examples of making API calls to the persona-based
endpoints and processing the responses.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

import aiohttp
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedInteractionRequest(BaseModel):
    """Request model for enhanced interactions."""

    message: str
    user_id: str
    session_id: Optional[str] = None
    persona_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class PersonaClient:
    """
    Client for interacting with the enhanced persona system.

    This class provides methods for:
    1. Listing available personas
    2. Sending messages with specific personas
    3. Managing conversation sessions
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the persona client.

        Args:
            base_url: Base URL for the API server
        """
        self.base_url = base_url
        self.api_prefix = "/api/enhanced"
        self.current_session_id = None
        self.current_persona_id = None

    async def list_personas(self) -> Dict[str, Dict[str, Any]]:
        """
        List all available personas.

        Returns:
            Dictionary of persona IDs and their configurations
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}{self.api_prefix}/personas") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to list personas: {error_text}")

    async def start_conversation(self, user_id: str, persona_id: Optional[str] = None) -> str:
        """
        Start a new conversation session.

        Args:
            user_id: User identifier
            persona_id: Optional persona to use for this conversation

        Returns:
            The session ID for the new conversation
        """
        import uuid

        self.current_session_id = f"session_{uuid.uuid4().hex[:8]}"
        self.current_persona_id = persona_id

        logger.info(f"Started new conversation session: {self.current_session_id}")
        logger.info(f"Using persona: {persona_id or 'default'}")

        return self.current_session_id

    async def send_message(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None,
        persona_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a message to the enhanced persona system.

        Args:
            message: The user's message
            user_id: User identifier
            session_id: Optional session ID for conversation continuity
            persona_id: Optional persona to use for this message
            context: Optional additional context

        Returns:
            The system's response
        """
        # Use current session and persona if not specified
        if session_id is None:
            session_id = self.current_session_id

        if persona_id is None:
            persona_id = self.current_persona_id

        # Create request
        request = EnhancedInteractionRequest(
            message=message,
            user_id=user_id,
            session_id=session_id,
            persona_id=persona_id,
            context=context,
        )

        # Send request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}{self.api_prefix}/interact",
                json=request.dict(exclude_none=True),
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    # Update session ID if this is a new conversation
                    if self.current_session_id is None:
                        self.current_session_id = result.get("session_id")
                    return result
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to send message: {error_text}")


async def run_example():
    """Run an example conversation with different personas."""

    client = PersonaClient()
    user_id = "example_user_123"

    # List available personas
    try:
        print("Listing available personas...")
        personas = await client.list_personas()
        print(f"Found {len(personas)} personas:")
        for persona_id, persona in personas.items():
            print(f"  - {persona_id}: {persona['name']} ({persona['description']})")
        print()
    except Exception as e:
        print(f"Error listing personas: {e}")
        return

    # Use different personas for different messages
    personas_to_try = ["default", "cherry", "grumpy", "tech", "concise"]
    test_message = "Tell me about artificial intelligence"

    for persona_id in personas_to_try:
        try:
            # Start new conversation with this persona
            await client.start_conversation(user_id, persona_id)

            print(f"\n--- Conversation with {persona_id} persona ---")
            print(f"User: {test_message}")

            # Send message
            response = await client.send_message(message=test_message, user_id=user_id)

            # Print response
            print(f"{response['persona_name']}: {response['message']}")
            print(f"Template used: {response.get('template_used', 'N/A')}")
            print("--------------------------------\n")
        except Exception as e:
            print(f"Error with {persona_id} persona: {e}")


if __name__ == "__main__":
    # Run the example
    asyncio.run(run_example())
