#!/usr/bin/env python
"""
LLM Integration Demo for AI Orchestration System.

This script demonstrates a complete workflow using the LLM integration:
1. Setting up the environment
2. Initializing components
3. Processing interactions with different personas
4. Showing direct LLM completions

Run this script with:
    python core/orchestrator/examples/llm_demo.py
"""

import asyncio
import logging
import os

from core.orchestrator.src.agents.llm_agent import ConversationFormatter
from core.orchestrator.src.config.config import get_settings
from core.orchestrator.src.personas.loader import PersonaManager
from core.orchestrator.src.services.llm.providers import get_llm_provider

# Removed load_dotenv for production: all secrets are managed via GCP Secret Manager and Pulumi config.

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

async def demo_conversation_with_persona(persona_id: str):
    """
    Run a demo conversation with a specific persona.

    Args:
        persona_id: The persona to use
    """
    print(f"\n\n=== Conversation with Persona: {persona_id} ===\n")

    # Initialize components
    persona_manager = PersonaManager("core/orchestrator/src/config/personas.yaml")
    persona = persona_manager.get_persona(persona_id)

    # Get LLM provider for generation
    llm_provider = get_llm_provider()

    # Create a conversation history
    conversation_history = []

    # Sample conversation
    questions = [
        "Hello, how are you today?",
        "Tell me something interesting about artificial intelligence.",
        "What do you think about the future of technology?",
    ]

    # Process each question
    for i, question in enumerate(questions):
        print(f"User: {question}")

        # Format conversation for the LLM
        messages = []

        # Add system message with persona information
        system_message = ConversationFormatter.create_system_message(persona)
        messages.append(system_message)

        # Add conversation history
        for entry in conversation_history:
            messages.append(entry)

        # Add the current question
        messages.append({"role": "user", "content": question})

        # Generate response
        try:
            response = await llm_provider.generate_chat_completion(messages=messages, temperature=0.7)

            # Extract response text
            response_text = response["content"]

            # Print the response
            print(f"{persona.name}: {response_text}")

            # Update conversation history
            conversation_history.append({"role": "user", "content": question})
            conversation_history.append({"role": "assistant", "content": response_text})

            # Print token usage
            if "usage" in response:
                usage = response["usage"]
                print(
                    f"\nToken usage: {usage.get('total_tokens', 'N/A')} tokens "
                    f"({usage.get('prompt_tokens', 'N/A')} prompt, "
                    f"{usage.get('completion_tokens', 'N/A')} completion)"
                )

            print("\n---\n")

            # Small delay for better readability
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            break

async def demo_direct_completion():
    """Demonstrate direct completions without personas or history."""
    print("\n\n=== Direct Completions ===\n")

    llm_provider = get_llm_provider()

    # Sample system prompts and questions
    examples = [
        {
            "system": "You are a helpful assistant with a focus on science and technology.",
            "user": "Explain quantum computing in simple terms.",
        },
        {
            "system": "You are a creative writing assistant that specializes in poetry.",
            "user": "Write a short poem about the night sky.",
        },
    ]

    # Process each example
    for example in examples:
        print(f"System: {example['system']}")
        print(f"User: {example['user']}")

        messages = [
            {"role": "system", "content": example["system"]},
            {"role": "user", "content": example["user"]},
        ]

        try:
            response = await llm_provider.generate_chat_completion(messages=messages, temperature=0.8)

            # Print the response
            print(f"Assistant: {response['content']}")

            # Print token usage
            if "usage" in response:
                usage = response["usage"]
                print(
                    f"\nToken usage: {usage.get('total_tokens', 'N/A')} tokens "
                    f"({usage.get('prompt_tokens', 'N/A')} prompt, "
                    f"{usage.get('completion_tokens', 'N/A')} completion)"
                )

            print("\n---\n")

            # Small delay for better readability
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error: {e}")

async def main():
    """Run the complete demo."""
    # Environment variables for secrets are injected by GCP infra or set in CI/CD.
    # Do NOT use load_dotenv in production.

    # Check for API key
    settings = get_settings()
    if not hasattr(settings, "OPENROUTER_API_KEY") or not settings.OPENROUTER_API_KEY:
        print("Warning: OpenRouter API key not found. Please set OPENROUTER_API_KEY in your environment.")

        # Set a dummy key for testing
        os.environ["OPENROUTER_API_KEY"] = "dummy_key"
        print("Using a dummy key for demonstration purposes. API calls will fail.")

    # Print header
    print("\n" + "=" * 50)
    print(" LLM Integration Demo for AI Orchestration System ")
    print("=" * 50 + "\n")

    # Run conversation demos with different personas
    await demo_conversation_with_persona("cherry")
    await demo_conversation_with_persona("sage")

    # Run direct completion demo
    await demo_direct_completion()

    # Print footer
    print("\n" + "=" * 50)
    print(" Demo Complete ")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
