"""Example Tool Agent that enriches documents using an external API."""
    name = "tool_agent"

    def run(self, payload: dict) -> dict:
        # Placeholder logic
        resp = requests.post("https://example.com/api", json=payload, timeout=30)
        return resp.json()
