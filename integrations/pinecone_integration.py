from __future__ import annotations

import os
from typing import Any, Dict

from .http_base import HTTPIntegrationBase

__all__ = ["PineconeIntegration"]


class PineconeIntegration(HTTPIntegrationBase):
    """Wrapper for basic Pinecone management operations."""

    name = "pinecone"
    required_env_vars = ("PINECONE_API_KEY", "PINECONE_ENVIRONMENT")

    @property
    def credentials(self) -> Dict[str, str]:
        return {
            "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY", ""),
            "PINECONE_ENVIRONMENT": os.getenv("PINECONE_ENVIRONMENT", ""),
        }

    @property
    def _BASE_URL(self) -> str:  # type: ignore
        env = self.credentials["PINECONE_ENVIRONMENT"]
        return f"https://controller.{env}.pinecone.io"

    def _headers(self):  # noqa: ANN001
        return {
            "Api-Key": self.credentials["PINECONE_API_KEY"],
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    def get_action(self, action_name: str):  # noqa: ANN001
        match action_name:
            case "list_indexes":
                return self.list_indexes
            case _:
                raise KeyError(f"Unknown Pinecone action: {action_name}")

    def list_indexes(self) -> list[str]:
        result = self._request("GET", "/databases", headers=self._headers())
        return result.get("databases", []) 