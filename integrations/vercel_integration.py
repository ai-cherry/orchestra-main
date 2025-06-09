from __future__ import annotations

import json
from os import getenv
from typing import Dict, Any

import requests

from . import BaseIntegration, ActionFn

__all__ = ["VercelIntegration"]

_API_BASE = "https://api.vercel.com"


class VercelIntegration(BaseIntegration):
    """Thin wrapper around the Vercel REST API."""

    name = "vercel"

    required_env_vars = ("VERCEL_TOKEN", "VERCEL_ORG_ID")

    @property
    def credentials(self) -> Dict[str, str]:
        return {
            "VERCEL_TOKEN": getenv("VERCEL_TOKEN", ""),
            "VERCEL_ORG_ID": getenv("VERCEL_ORG_ID", ""),
        }

    # ------------------------------------------------------------------
    # Public actions
    # ------------------------------------------------------------------
    def get_action(self, action_name: str) -> ActionFn:
        match action_name:
            case "deploy":
                return self.deploy
            case "logs":
                return self.get_logs
            case "project_settings":
                return self.get_project_settings
            case "set_env":
                return self.set_env_var
            case _:
                raise KeyError(f"Unknown Vercel action: {action_name}")

    # ----------------------------- helpers -----------------------------
    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = kwargs.pop("headers", {}) | {
            "Authorization": f"Bearer {self.credentials['VERCEL_TOKEN']}",
            "Content-Type": "application/json",
        }
        resp = requests.request(method, _API_BASE + path, headers=headers, **kwargs, timeout=30)
        if resp.status_code >= 400:
            raise RuntimeError(f"Vercel API error {resp.status_code}: {resp.text}")
        return resp.json()

    # ------------------------------ actions ----------------------------
    def deploy(self, project_id: str, files: list[dict[str, Any]], **kwargs: Any) -> str:
        """Trigger a deployment. *files* must be a Vercel File List structure.

        For CI usage, prefer using the official `amondnet/vercel-action` – this
        wrapper is mainly for programmatic control from an agent.
        """
        data = {
            "name": project_id,
            "files": files,
            "project": project_id,
            "target": kwargs.get("target", "production"),
            "orgId": self.credentials["VERCEL_ORG_ID"],
        }
        result = self._request("POST", "/v13/deployments", data=json.dumps(data))
        return result.get("url", "<no-url-returned>")

    def get_logs(self, deployment_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Fetch the latest logs for a deployment."""
        params = {"limit": limit}
        result = self._request("GET", f"/v2/deployments/{deployment_id}/events", params=params)
        return result.get("events", [])

    # ---------------- Additional helper actions -----------------------
    def get_project_settings(self, project_id: str) -> dict[str, Any]:
        """Return the project configuration (env vars, builds, routes)."""
        return self._request("GET", f"/v9/projects/{project_id}")

    def set_env_var(
        self,
        project_id: str,
        key: str,
        value: str,
        env: str = "production",
        target: str = "production",
    ) -> dict[str, Any]:
        """Create or update an env var in the given project."""
        payload = {
            "key": key,
            "value": value,
            "target": [target],
            "type": "encrypted",
        }
        return self._request(
            "POST",
            f"/v10/projects/{project_id}/env",
            headers={
                "Authorization": f"Bearer {self.credentials['VERCEL_TOKEN']}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
        ) 