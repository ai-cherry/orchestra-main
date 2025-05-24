#!/usr/bin/env python
"""
Portkey Virtual Keys Demo

This example demonstrates how to use Portkey virtual keys with various LLM providers.
It shows how the PortkeyClient automatically selects the appropriate virtual key
based on the model being used.

Example usage:
python examples/portkey_virtual_keys_demo.py
"""

import asyncio
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("portkey-demo")

# Add parent directory to path
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.orchestrator.src.config.settings import get_settings
from packages.shared.src.llm_client.portkey_client import PortkeyClient


async def run_model(client: PortkeyClient, model: str, prompt: str) -> None:
    """Run a query against a specified model using Portkey."""
    logger.info(f"Running query with model: {model}")

    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": prompt},
    ]

    try:
        response = await client.generate_response(model=model, messages=messages, temperature=0.7, max_tokens=150)

        logger.info(f"Response from {model}:")
        logger.info(f"{response}\n")
    except Exception as e:
        logger.error(f"Error with {model}: {e}")


async def main() -> None:
    """Main function demonstrating Portkey virtual keys with multiple providers."""
    settings = get_settings()

    # Print available virtual keys
    logger.info("Checking for configured virtual keys...")
    available_keys = []
    if settings.PORTKEY_VIRTUAL_KEY_OPENAI:
        available_keys.append(("OpenAI", "gpt-4"))
    if settings.PORTKEY_VIRTUAL_KEY_ANTHROPIC:
        available_keys.append(("Anthropic", "claude-3-opus"))
    if settings.PORTKEY_VIRTUAL_KEY_MISTRAL:
        available_keys.append(("Mistral", "mistral-large"))
    if settings.PORTKEY_VIRTUAL_KEY_COHERE:
        available_keys.append(("Cohere", "command-r"))
    if settings.PORTKEY_VIRTUAL_KEY_OPENROUTER:
        available_keys.append(("OpenRouter", "openai/gpt-3.5-turbo"))

    if not available_keys:
        logger.error("No virtual keys configured. Please set up at least one virtual key in your .env file.")
        logger.info("Example: PORTKEY_VIRTUAL_KEY_OPENAI=vk_openai_...")
        return

    logger.info(f"Found {len(available_keys)} configured virtual keys")

    # Initialize Portkey client
    try:
        client = PortkeyClient(settings)
        logger.info("Portkey client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Portkey client: {e}")
        return

    # Test prompt
    prompt = "Explain the concept of virtual keys in API management in a single paragraph."

    # Run queries against all available models
    for provider, model in available_keys:
        logger.info(f"Testing {provider} with model: {model}")
        await run_model(client, model, prompt)

    logger.info("Demo completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
