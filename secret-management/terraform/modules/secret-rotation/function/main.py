"""
GCP Secret Manager - Automated Secret Rotation Function

This Cloud Function automatically rotates secrets in Google Cloud Secret Manager
based on configured rotation strategies.

Rotation strategies:
- random: Generate a new random secret
- api: Call an external API to generate a new secret (e.g., token refresh)
- custom: Use custom logic defined for specific secret types

Environment variables:
- PROJECT_ID: GCP project ID
- ENVIRONMENT: Environment (dev, staging, prod)
- SECRETS: Comma-separated list of secrets to rotate
"""

import datetime
import logging
import os
import random
import secrets
import string
from typing import Dict, Optional, Tuple

import functions_framework
from google.cloud import secretmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Secret Manager client
client = secretmanager.SecretManagerServiceClient()

# Get environment variables
PROJECT_ID = os.environ.get("PROJECT_ID")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
SECRETS_TO_ROTATE = os.environ.get("SECRETS", "").split(",")


# Secret rotation strategies
class RotationStrategy:
    @staticmethod
    def random(secret_id: str, min_length: int = 32, **kwargs) -> str:
        """Generate a random secure string."""
        chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
        return "".join(secrets.choice(chars) for _ in range(min_length))

    @staticmethod
    def api(secret_id: str, api_url: Optional[str] = None, **kwargs) -> str:
        """Call an external API to refresh a token or generate a credential."""
        # This is a placeholder - in a real implementation, you would call
        # the appropriate API for each secret type
        if "api_key" in secret_id.lower():
            # Simulate API key generation
            prefix = "api_" if "prefix" not in kwargs else kwargs["prefix"]
            key = secrets.token_hex(20)
            return f"{prefix}{key}"
        elif "oauth" in secret_id.lower() or "token" in secret_id.lower():
            # Simulate OAuth token refresh
            return f"ya29.{secrets.token_urlsafe(40)}"
        else:
            # Default to random if no specific API logic is defined
            return RotationStrategy.random(secret_id)

    @staticmethod
    def custom(secret_id: str, **kwargs) -> str:
        """Apply custom logic based on the secret ID."""
        if "password" in secret_id.lower():
            # Generate a password with specific complexity
            length = kwargs.get("length", 16)
            uppercase = int(kwargs.get("uppercase", 2))
            numbers = int(kwargs.get("numbers", 2))
            special = int(kwargs.get("special", 2))

            # Start with the required character types
            result = (
                [secrets.choice(string.ascii_uppercase) for _ in range(uppercase)]
                + [secrets.choice(string.digits) for _ in range(numbers)]
                + [secrets.choice("!@#$%^&*()-_=+") for _ in range(special)]
            )

            # Fill the rest with lowercase
            remaining = length - (uppercase + numbers + special)
            result.extend(
                secrets.choice(string.ascii_lowercase) for _ in range(remaining)
            )

            # Shuffle the result
            random.shuffle(result)
            return "".join(result)
        elif "github" in secret_id.lower():
            # Format similar to GitHub tokens
            return f"ghp_{secrets.token_hex(20)}"
        else:
            # Default to random
            return RotationStrategy.random(secret_id)


def get_secret_info(secret_id: str) -> Tuple[str, Dict]:
    """Get metadata about a secret to help with rotation strategy."""
    try:
        # Get the secret's metadata
        name = f"projects/{PROJECT_ID}/secrets/{secret_id}"
        response = client.get_secret(request={"name": name})

        # Parse labels to get rotation strategy and parameters
        labels = response.labels

        # Default strategy is "random" if not specified
        strategy = labels.get("rotation_strategy", "random")

        # Get additional parameters from labels
        params = {
            k.replace("rotation_param_", ""): v
            for k, v in labels.items()
            if k.startswith("rotation_param_")
        }

        return strategy, params
    except Exception as e:
        logger.error(f"Error getting info for secret {secret_id}: {e}")
        return "random", {}


def rotate_secret(secret_id: str) -> bool:
    """Rotate a single secret."""
    try:
        logger.info(f"Starting rotation for secret: {secret_id}")

        # Get the rotation strategy and parameters for this secret
        strategy_name, params = get_secret_info(secret_id)

        # Get the rotation function based on strategy
        if hasattr(RotationStrategy, strategy_name):
            strategy_func = getattr(RotationStrategy, strategy_name)
        else:
            logger.warning(
                f"Unknown strategy '{strategy_name}' for {secret_id}, using 'random'"
            )
            strategy_func = RotationStrategy.random

        # Generate the new secret value
        new_value = strategy_func(secret_id=secret_id, **params)

        # Add a new version to the secret
        secret_path = f"projects/{PROJECT_ID}/secrets/{secret_id}"

        # Create a new version with the new secret value
        client.add_secret_version(
            request={
                "parent": secret_path,
                "payload": {"data": new_value.encode("UTF-8")},
            }
        )

        logger.info(f"Secret {secret_id} rotated successfully")
        return True

    except Exception as e:
        logger.error(f"Error rotating secret {secret_id}: {e}")
        return False


@functions_framework.http
def rotate_secrets(request):
    """HTTP Cloud Function to rotate secrets."""
    # Get the list of secrets to rotate from the request or environment
    request_json = request.get_json(silent=True)
    secrets_to_rotate = SECRETS_TO_ROTATE

    if request_json and "secrets" in request_json:
        secrets_to_rotate = request_json["secrets"]

    if not secrets_to_rotate or secrets_to_rotate == [""]:
        return {"status": "error", "message": "No secrets specified for rotation"}, 400

    # Track results
    results = {
        "timestamp": datetime.datetime.now().isoformat(),
        "environment": ENVIRONMENT,
        "successes": [],
        "failures": [],
    }

    # Rotate each secret
    for secret_id in secrets_to_rotate:
        if not secret_id:
            continue

        if rotate_secret(secret_id):
            results["successes"].append(secret_id)
        else:
            results["failures"].append(secret_id)

    # Prepare response with rotation results
    if not results["failures"]:
        return {
            "status": "success",
            "message": f"Rotated {len(results['successes'])} secrets successfully",
            "details": results,
        }
    else:
        return {
            "status": "partial_failure",
            "message": f"Rotated {len(results['successes'])} secrets, {len(results['failures'])} failed",
            "details": results,
        }, 500


if __name__ == "__main__":
    # Allow for local testing
    test_secrets = ["test-secret-1", "test-secret-2"]
    print(f"Testing rotation for: {test_secrets}")

    for secret in test_secrets:
        rotate_secret(secret)
