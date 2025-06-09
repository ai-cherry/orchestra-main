from __future__ import annotations

import os
from typing import Dict

from .http_base import HTTPIntegrationBase

__all__ = ["WeaviateIntegration"]


class WeaviateIntegration(HTTPIntegrationBase):
    """Simple Weaviate schema inspection."""

    name = "weaviate"
    required_env_vars = ("WEAVIATE_URL",)

    @property
    def credentials(self) -> Dict[str, str]:
        return {"WEAVIATE_URL": os.getenv("WEAVIATE_URL", "")}

    @property
    def _BASE_URL(self) -> str:  # type: ignore
        return self.credentials["WEAVIATE_URL"].rstrip("/")

    def get_action(self, action_name: str):  # noqa: ANN001
        match action_name:
            case "list_classes":
                return self.list_classes
            case _:
                raise KeyError(f"Unknown Weaviate action: {action_name}")

    def list_classes(self) -> list[str]:
        result = self._request("GET", "/v1/schema")
        return [c["class"] for c in result.get("classes", [])] 