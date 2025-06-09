from __future__ import annotations

import os
import json
from typing import Any, Dict

from .http_base import HTTPIntegrationBase

__all__ = ["NotionIntegration"]


class NotionIntegration(HTTPIntegrationBase):
    name = "notion"
    required_env_vars = ("NOTION_API_KEY",)

    _BASE_URL = "https://api.notion.com/v1"
    _NOTION_VERSION = "2022-06-28"

    @property
    def credentials(self) -> Dict[str, str]:
        return {"NOTION_API_KEY": os.getenv("NOTION_API_KEY", "")}

    def _headers(self):  # noqa: ANN001
        return {
            "Authorization": f"Bearer {self.credentials['NOTION_API_KEY']}",
            "Notion-Version": self._NOTION_VERSION,
            "Content-Type": "application/json",
        }

    def get_action(self, action_name: str):  # noqa: ANN001
        return self.create_page if action_name == "create_page" else super().get_action(action_name)

    def create_page(
        self,
        parent_database_id: str,
        properties: Dict[str, Any],
        children: list[Dict[str, Any]] | None = None,
    ) -> str:
        body = {
            "parent": {"database_id": parent_database_id},
            "properties": properties,
        }
        if children:
            body["children"] = children
        result = self._request("POST", "/pages", headers=self._headers(), data=json.dumps(body))
        return result.get("id", "<no-id>") 