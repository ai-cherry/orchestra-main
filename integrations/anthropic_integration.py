from __future__ import annotations

import json
from os import getenv
from typing import Any, Dict

from .http_base import HTTPIntegrationBase

__all__ = ["ClaudeIntegration"]


class ClaudeIntegration(HTTPIntegrationBase):
    """Wrapper for Anthropic Messages API (Claude)."""

    name = "anthropic"
    required_env_vars = ("ANTHROPIC_API_KEY",)

    _BASE_URL = "https://api.anthropic.com/v1"

    def _headers(self) -> Dict[str, str]:
        return {
            "x-api-key": getenv("ANTHROPIC_API_KEY", ""),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    @property
    def credentials(self) -> Dict[str, str]:
        return {"ANTHROPIC_API_KEY": getenv("ANTHROPIC_API_KEY", "")}

    def get_action(self, action_name: str):  # noqa: ANN001
        return self.chat if action_name == "chat" else super().get_action(action_name)

    def chat(
        self,
        prompt: str,
        model: str = "claude-3-sonnet-20240229",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        body: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": temperature,
        }
        result = self._request("POST", "/messages", data=json.dumps(body), headers=self._headers())
        return result["content"][0]["text"].strip() 