"""Example Tool Agent that enriches documents using an external API."""

from packages.agents.src._base import OrchestraAgentBase
import requests

class ToolAgent(OrchestraAgentBase):
    name = "tool_agent"

    def run(self, payload: dict) -> dict:
        # Placeholder logic
        resp = requests.post("https://example.com/api", json=payload)
        return resp.json()
