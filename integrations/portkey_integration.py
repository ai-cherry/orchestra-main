from __future__ import annotations

import os
import json
from typing import Dict, Any

from .http_base import HTTPIntegrationBase

__all__ = ["PortkeyIntegration"]


class PortkeyIntegration(HTTPIntegrationBase):
    name = "portkey"
    required_env_vars = ("PORTKEY_API_KEY",)

    _BASE_URL = "https://api.portkey.ai/v1"

    @property
    def credentials(self) -> Dict[str, str]:
        return {"PORTKEY_API_KEY": os.getenv("PORTKEY_API_KEY", "")}

    def _headers(self):  # noqa: ANN001
        return {
            "x-api-key": self.credentials["PORTKEY_API_KEY"],
            "Content-Type": "application/json",
        }

    def get_action(self, action_name: str):  # noqa: ANN001
        return self.route if action_name == "route" else super().get_action(action_name)

    def route(self, prompt: str, provider: str = "openai", model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        body = {
            "provider": provider,
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }
        return self._request("POST", "/chat/completions", headers=self._headers(), data=json.dumps(body)) 