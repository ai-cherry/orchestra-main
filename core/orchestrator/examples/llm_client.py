"""
LLM Client Example for AI Orchestration System.

This script demonstrates how to interact with the LLM endpoints
of the AI Orchestration System.
"""

import argparse
import asyncio
from typing import Optional

import httpx


async def llm_interact(
    api_url: str,
    message: str,
    user_id: str,
    session_id: Optional[str] = None,
    persona_id: Optional[str] = None,
    model: Optional[str] = None,
):
    """
    Interact with the LLM endpoint.

    Args:
        api_url: Base URL of the API
        message: User message
        user_id: User ID
        session_id: Optional session ID
        persona_id: Optional persona ID
        model: Optional model to use
    """
    # Prepare request data
    data = {
        "message": message,
        "user_id": user_id,
        "session_id": session_id,
        "persona_id": persona_id,
        "model": model,
    }

    # Filter out None values
    data = {k: v for k, v in data.items() if v is not None}

    # Make request
    async with httpx.AsyncClient() as client:
        url = f"{api_url}/api/llm/interact"
        response = await client.post(url, json=data)

        # Check response
        if response.status_code == 200:
            result = response.json()

            # Print response
            print("\n=== LLM Response ===")
            print(f"Message: {result['message']}")
            print(f"Persona: {result['persona_name']} ({result['persona_id']})")
            print(f"Model: {result['model']}")
            print(f"Provider: {result['provider']}")

            # Print token usage if available
            if result.get("usage"):
                usage = result["usage"]
                print("\nToken Usage:")
                print(f"  Prompt: {usage.get('prompt_tokens', 'N/A')}")
                print(f"  Completion: {usage.get('completion_tokens', 'N/A')}")
                print(f"  Total: {usage.get('total_tokens', 'N/A')}")

            # Store session ID for reuse
            if not session_id:
                print(
                    f"\nSession ID for continuing conversation: {result['session_id']}"
                )
        else:
            print(f"Error: {response.status_code}")
            print(response.text)


async def direct_completion(
    api_url: str, system_prompt: str, user_message: str, model: Optional[str] = None
):
    """
    Make a direct LLM completion request.

    Args:
        api_url: Base URL of the API
        system_prompt: System prompt
        user_message: User message
        model: Optional model to use
    """
    # Create messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    # Make request
    async with httpx.AsyncClient() as client:
        url = f"{api_url}/api/llm/direct"
        params = {}
        if model:
            params["model"] = model

        response = await client.post(url, json=messages, params=params)

        # Check response
        if response.status_code == 200:
            result = response.json()

            # Print response
            print("\n=== Direct Completion ===")
            print(f"Content: {result['content']}")
            print(f"Model: {result['model']}")

            # Print token usage if available
            if result.get("usage"):
                usage = result["usage"]
                print("\nToken Usage:")
                print(f"  Prompt: {usage.get('prompt_tokens', 'N/A')}")
                print(f"  Completion: {usage.get('completion_tokens', 'N/A')}")
                print(f"  Total: {usage.get('total_tokens', 'N/A')}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)


async def main():
    """Run the LLM client example."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="LLM Client Example")
    parser.add_argument("--url", default="http://localhost:8000", help="API URL")
    parser.add_argument(
        "--mode", choices=["interact", "direct"], default="interact", help="Mode"
    )
    parser.add_argument("--message", help="User message")
    parser.add_argument("--user-id", default="example-user", help="User ID")
    parser.add_argument("--session-id", help="Session ID for continuing conversation")
    parser.add_argument("--persona-id", help="Persona ID")
    parser.add_argument("--model", help="Model to use")
    parser.add_argument(
        "--system",
        default="You are a helpful assistant.",
        help="System prompt (direct mode only)",
    )
    args = parser.parse_args()

    # Check if message is provided
    if not args.message:
        parser.error("--message is required")

    # Run appropriate mode
    if args.mode == "interact":
        await llm_interact(
            api_url=args.url,
            message=args.message,
            user_id=args.user_id,
            session_id=args.session_id,
            persona_id=args.persona_id,
            model=args.model,
        )
    elif args.mode == "direct":
        await direct_completion(
            api_url=args.url,
            system_prompt=args.system,
            user_message=args.message,
            model=args.model,
        )


if __name__ == "__main__":
    # Run main
    asyncio.run(main())
