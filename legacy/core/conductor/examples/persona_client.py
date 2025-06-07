"""
"""
    """Request model for enhanced interactions."""
    """
    """
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        """
        self.api_prefix = "/api/enhanced"
        self.current_session_id = None
        self.current_persona_id = None

    async def list_personas(self) -> Dict[str, Dict[str, Any]]:
        """
        """
            async with session.get(f"{self.base_url}{self.api_prefix}/personas") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to list personas: {error_text}")

    async def start_conversation(self, user_id: str, persona_id: Optional[str] = None) -> str:
        """
        """
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
        """
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
    user_id = "example_user_123"

    # List available personas
    try:

        pass
        print("Listing available personas...")
        personas = await client.list_personas()
        print(f"Found {len(personas)} personas:")
        for persona_id, persona in personas.items():
            print(f"  - {persona_id}: {persona['name']} ({persona['description']})")
        print()
    except Exception:

        pass
        print(f"Error listing personas: {e}")
        return

    # Use different personas for different messages
    personas_to_try = ["default", "cherry", "grumpy", "tech", "concise"]
    test_message = "Tell me about artificial intelligence"

    for persona_id in personas_to_try:
        try:

            pass
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
        except Exception:

            pass
            print(f"Error with {persona_id} persona: {e}")

if __name__ == "__main__":
    # Run the example
    asyncio.run(run_example())
