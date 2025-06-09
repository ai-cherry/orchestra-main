from __future__ import annotations

import json
from os import getenv
from typing import Any, Dict, List

from .http_base import HTTPIntegrationBase

__all__ = ["OpenAIIntegration"]


class OpenAIIntegration(HTTPIntegrationBase):
    """Simple wrapper for OpenAI Chat Completions API."""

    name = "openai"

    required_env_vars = ("OPENAI_API_KEY",)

    _BASE_URL = "https://api.openai.com/v1"

    @property
    def credentials(self) -> Dict[str, str]:
        return {"OPENAI_API_KEY": getenv("OPENAI_API_KEY", "")}

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.credentials['OPENAI_API_KEY']}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    def get_action(self, action_name: str):  # noqa: ANN001
        match action_name:
            case "chat":
                return self.chat_completion
            case _:
                raise KeyError(f"Unknown OpenAI action: {action_name}")

    # ----------------------------- actions --------------------------
    def chat_completion(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        max_tokens: int = 256,
    ) -> str:
        body: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        result = self._request("POST", "/chat/completions", data=json.dumps(body), headers=self._headers())
        return result["choices"][0]["message"]["content"].strip() 