"""
Example usage of the Secret Manager integration.

This module demonstrates how to use the Secret Manager utility to
access secrets from both environment variables and Google Secret Manager
while maintaining backward compatibility.
"""

import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import the secret manager module
from config.secret_manager import get_secret, secrets


def main():
    """Demonstrate different ways to access secrets."""

    print("=== Secret Manager Usage Examples ===\n")

    # Example 1: Direct function call
    print("Example 1: Direct function call")
    openai_key = get_secret("openai-api-key")
    print(f"OpenAI API Key exists: {bool(openai_key)}")
    # We don't print the actual key value for security reasons
    print(f"Key starts with: {openai_key[:4]}..." if openai_key else "Key not found")
    print()

    # Example 2: Dictionary-like access
    print("Example 2: Dictionary-like access")
    anthropic_key = secrets["anthropic-api-key"]
    print(f"Anthropic API Key exists: {bool(anthropic_key)}")
    print(f"Key starts with: {anthropic_key[:4]}..." if anthropic_key else "Key not found")
    print()

    # Example 3: Using get() with default value
    print("Example 3: Using get() with default")
    cohere_key = secrets.get("cohere-api-key", "default-value-if-not-found")
    print(f"Cohere API Key exists: {bool(cohere_key) and cohere_key != 'default-value-if-not-found'}")
    print()

    # Example 4: Check if a secret exists
    print("Example 4: Checking if secret exists")
    has_tavily = "tavily-api-key" in secrets
    print(f"Has Tavily API Key: {has_tavily}")
    print()

    # Example 5: Environment variable vs Secret Manager precedence
    print("Example 5: Environment precedence")
    # Try with an environment variable that definitely exists
    if "PATH" in os.environ:
        test_var = "PATH"
        print(f"Environment variable '{test_var}' exists")
        print(f"Value from get_secret: {get_secret(test_var)[:10]}... (truncated)")
        print(f"Value from os.environ: {os.environ[test_var][:10]}... (truncated)")
        print("Note: Environment variables take precedence over Secret Manager")

    print("\n=== End of Examples ===")


if __name__ == "__main__":
    main()
