"""
GitHub Personal Access Token (PAT) Manager for AI Orchestra.

This module provides a secure, tiered approach to PAT management that balances
security with practical workflow needs for the CI/CD pipeline.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Literal, Optional

PAT_SCOPE = Literal["read", "write_packages", "workflow", "deployment"]


class PATManager:
    """Manages GitHub Personal Access Tokens with security best practices.

    This class implements a least-privilege approach to token management,
    supporting different scopes for different operations, and includes
    built-in token rotation mechanisms.
    """

    def __init__(self, config_path: str = ".github/pat_config.json"):
        """Initialize the PAT Manager.

        Args:
            config_path: Path to the PAT configuration file
        """
        self.config_path = Path(config_path)
        self.logger = logging.getLogger("pat_manager")
        self._load_config()

    def _load_config(self) -> None:
        """Load PAT configuration from file or initialize defaults."""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "tokens": {},
                "rotation_schedule": {
                    "read": 180,  # days
                    "write_packages": 90,
                    "workflow": 60,
                    "deployment": 30,
                },
            }
            self._save_config()

    def _save_config(self) -> None:
        """Save PAT configuration to file (redacting sensitive values)."""
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "w") as f:
            # Never write actual tokens to file
            safe_config = self.config.copy()
            for token_id, token_info in safe_config["tokens"].items():
                if "value" in token_info:
                    token_info["value"] = "***REDACTED***"
            json.dump(safe_config, f, indent=2)

    def register_token(self, token_id: str, scope: PAT_SCOPE, value: str) -> None:
        """Register a new PAT with specified scope and value.

        Args:
            token_id: Unique identifier for the token
            scope: Permission scope for the token
            value: The actual token value
        """
        self.config["tokens"][token_id] = {
            "scope": scope,
            "created_at": datetime.now().isoformat(),
            "expires_at": (
                datetime.now() + timedelta(days=self.config["rotation_schedule"][scope])
            ).isoformat(),
            "value": value,
            "last_used": None,
        }
        # Save token value securely in environment variable instead of file
        os.environ[f"GH_PAT_{token_id.upper()}"] = value
        self._save_config()
        self.logger.info(f"Registered PAT {token_id} with scope {scope}")

    def get_token(self, required_scope: PAT_SCOPE) -> Optional[str]:
        """Get a valid PAT with the required scope or higher permission level.

        Args:
            required_scope: Minimum permission scope needed

        Returns:
            The token string if available, None otherwise
        """
        scope_levels = {"read": 0, "write_packages": 1, "workflow": 2, "deployment": 3}
        required_level = scope_levels[required_scope]

        valid_tokens = []
        for token_id, token_info in self.config["tokens"].items():
            # Skip if token is expired
            if datetime.fromisoformat(token_info["expires_at"]) < datetime.now():
                continue

            # Check if token has sufficient permissions
            token_level = scope_levels[token_info["scope"]]
            if token_level >= required_level:
                # Get token from environment variable, not config file
                token_value = os.environ.get(f"GH_PAT_{token_id.upper()}")
                if token_value:
                    valid_tokens.append((token_id, token_value))

        if not valid_tokens:
            return None

        # Use the token with the lowest appropriate permission level
        selected_token = sorted(
            valid_tokens,
            key=lambda t: scope_levels[self.config["tokens"][t[0]]["scope"]],
        )[0]

        # Update last_used timestamp
        self.config["tokens"][selected_token[0]][
            "last_used"
        ] = datetime.now().isoformat()
        self._save_config()

        return selected_token[1]

    def check_rotation_needed(self) -> List[Dict]:
        """Check which PATs need rotation based on schedule.

        Returns:
            List of tokens that need rotation
        """
        tokens_to_rotate = []
        for token_id, token_info in self.config["tokens"].items():
            if datetime.fromisoformat(
                token_info["expires_at"]
            ) < datetime.now() + timedelta(days=7):
                tokens_to_rotate.append(
                    {
                        "token_id": token_id,
                        "scope": token_info["scope"],
                        "expires_at": token_info["expires_at"],
                    }
                )
        return tokens_to_rotate


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    manager = PATManager()

    # Check if any tokens need rotation
    tokens_to_rotate = manager.check_rotation_needed()
    for token in tokens_to_rotate:
        print(
            f"Token {token['token_id']} (scope: {token['scope']}) expires on {token['expires_at']}"
        )
