from __future__ import annotations

import os
from typing import Dict

import requests

from . import BaseIntegration

__all__ = ["SlackIntegration"]


class SlackIntegration(BaseIntegration):
    name = "slack"
    required_env_vars = ("SLACK_BOT_TOKEN",)

    @property
    def credentials(self) -> Dict[str, str]:
        return {"SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN", "")}

    def get_action(self, action_name: str):  # noqa: ANN001
        return self.send_message if action_name == "send_message" else super().get_action(action_name)

    def send_message(self, channel: str, text: str) -> str:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {self.credentials['SLACK_BOT_TOKEN']}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json={"channel": channel, "text": text},
            timeout=30,
        )
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack API error: {data.get('error')}")
        return data["ts"] 