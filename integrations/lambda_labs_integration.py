from __future__ import annotations

from os import getenv
from typing import Any, Dict

import requests

from . import BaseIntegration, ActionFn

__all__ = ["LambdaLabsIntegration"]

_API_BASE = "https://cloud.lambdalabs.com/api/v1"


class LambdaLabsIntegration(BaseIntegration):
    """Interact with Lambda Labs Cloud API (GPU instances)."""

    name = "lambda_labs"

    required_env_vars = ("LAMBDA_LABS_API_KEY",)

    @property
    def credentials(self) -> Dict[str, str]:
        return {"LAMBDA_LABS_API_KEY": getenv("LAMBDA_LABS_API_KEY", "")}

    # ------------------------------------------------------------------
    # Public actions
    # ------------------------------------------------------------------
    def get_action(self, action_name: str) -> ActionFn:
        match action_name:
            case "create_instance":
                return self.create_instance
            case "terminate_instance":
                return self.terminate_instance
            case _:
                raise KeyError(f"Unknown Lambda Labs action: {action_name}")

    # ---------------------- helpers ------------------------------
    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = kwargs.pop("headers", {}) | {
            "Authorization": f"Bearer {self.credentials['LAMBDA_LABS_API_KEY']}",
            "Content-Type": "application/json",
        }
        resp = requests.request(method, _API_BASE + path, headers=headers, **kwargs, timeout=60)
        if resp.status_code >= 400:
            raise RuntimeError(f"Lambda Labs API error {resp.status_code}: {resp.text}")
        return resp.json()

    # ----------------------- actions ------------------------------
    def create_instance(
        self,
        name: str,
        instance_type: str,
        region: str = "us-west-1",
        ssh_key_name: str | None = None,
    ) -> Dict[str, Any]:
        """Provision a new GPU instance and return the instance metadata."""
        data: Dict[str, Any] = {
            "instance_type": instance_type,
            "region_name": region,
            "name": name,
        }
        if ssh_key_name:
            data["ssh_key_name"] = ssh_key_name
        result = self._request("POST", "/instances", json=data)
        return result

    def terminate_instance(self, instance_id: str) -> Dict[str, Any]:
        """Terminate an instance by ID."""
        return self._request("DELETE", f"/instances/{instance_id}") 