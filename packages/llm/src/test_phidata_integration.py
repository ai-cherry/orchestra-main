Test script for Phidata/Agno LLM models with Portkey integration.

This script provides a simple way to verify that the Portkey integration
with Phidata/Agno models is working correctly.

Usage:
    python -m packages.llm.src.test_phidata_integration

Environment variables required:
    PORTKEY_API_KEY: Your Portkey API key
    PORTKEY_VIRTUAL_KEY_OPENAI: (Optional) Your Portkey virtual key for OpenAI
    PORTKEY_VIRTUAL_KEY_ANTHROPIC: (Optional) Your Portkey virtual key for Anthropic
    PORTKEY_VIRTUAL_KEY_OPENROUTER: (Optional) Your Portkey virtual key for OpenRouter
"""

import os
import asyncio
import logging
from typing import List, Dict, Any

from core.orchestrator.src.config.settings import Settings

# Import required modules
from packages.llm.src.models.openai import create_openai_model
from packages.llm.src.models.anthropic import create_anthropic_model
from packages.llm.src.models.openrouter import create_openrouter_model

# Check if phi is available
try:
    import phi
    PHI_AVAILABLE = True
except ImportError:
    logger.warning("phi package not installed. Some features will be disabled.")
    PHI_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_model(model: Any, model_name: str) -> None:
    """
    Test a model by sending a simple message and displaying the response.
    
    Args:
        model: The model to test
        model_name: A name for the model for display purposes
    """
    # Format differs by model type - try different formats to find one that works
    
    # For some models like OpenRouter, the message format might need to be different
    # Try to determine the model type
    model_type = model.__class__.__name__.lower()
    
    message = "Hello! What's your name and what provider are you from?"
    system = "You are a helpful assistant."
    
    logger.info(f"Testing {model_name}...")
    try:
        # For compatibility with various model interfaces, we'll try different formats
        messages = [
            {
                "role": "system",
                "content": system
            },
            {
                "role": "user",
                "content": message
            }
        ]

        try:
            # First try with standard format
            response = await model.invoke(messages)
        except Exception as format_error:
            logger.warning(f"Standard format failed, trying alternative: {format_error}")
            try:
                # Try with just the message
                response = await model.complete(message)
            except AttributeError:
                # If complete is not available, try with a different message format
                prompt = f"{system}\n\n{message}"
                response = await model.invoke(prompt)
        
        logger.info(f"Response from {model_name}:\n{response}")
        return response
    except Exception as e:
        logger.error(f"Error testing {model_name}: {e}")
        return None


async def main() -> None:
    """Run tests for all supported models."""
    settings = Settings()
    
    # Check if required environment variables are set
    if not settings.PORTKEY_API_KEY:
        logger.error("PORTKEY_API_KEY environment variable not set")
        return
    
    # List of models to test - only test models with virtual keys available
    models_to_test = []
    
    if settings.PORTKEY_VIRTUAL_KEY_OPENAI:
        models_to_test.append({
            "name": "OpenAI via Portkey",
            "factory": create_openai_model,
            "settings": settings
        })
    
    if settings.PORTKEY_VIRTUAL_KEY_ANTHROPIC:
        models_to_test.append({
            "name": "Anthropic Claude via Portkey",
            "factory": create_anthropic_model,
            "settings": settings
        })
    
    if settings.PORTKEY_VIRTUAL_KEY_OPENROUTER:
        models_to_test.append({
            "name": "OpenRouter via Portkey",
            "factory": create_openrouter_model,
            "settings": settings
        })
    
    # If no models with virtual keys, try OpenRouter without virtual key
    if not models_to_test:
        models_to_test.append({
            "name": "OpenRouter via Portkey (no virtual key)",
            "factory": create_openrouter_model,
            "settings": settings
        })
    
    # Initialize and test each model
    for model_config in models_to_test:
        name = model_config["name"]
        factory = model_config["factory"]
        cfg_settings = model_config["settings"]
        
        try:
            # Instantiate the model
            model = factory(cfg_settings)
            # Test the model
            await test_model(model, name)
        except Exception as e:
            logger.error(f"Failed to initialize or test {name}: {e}")
    
    logger.info("All tests completed")


if __name__ == "__main__":
    asyncio.run(main())
