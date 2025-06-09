from __future__ import annotations

import os
import json
from typing import Dict, Any

from .http_base import HTTPIntegrationBase

__all__ = ["GrafanaIntegration"]


class GrafanaIntegration(HTTPIntegrationBase):
    name = "grafana"
    required_env_vars = ("GRAFANA_API_KEY", "GRAFANA_URL")

    @property
    def credentials(self) -> Dict[str, str]:
        return {
            "GRAFANA_API_KEY": os.getenv("GRAFANA_API_KEY", ""),
            "GRAFANA_URL": os.getenv("GRAFANA_URL", ""),
        }

    @property
    def _BASE_URL(self) -> str:  # type: ignore
        return self.credentials["GRAFANA_URL"].rstrip("/") + "/api"

    def _headers(self):  # noqa: ANN001
        return {
            "Authorization": f"Bearer {self.credentials['GRAFANA_API_KEY']}",
            "Content-Type": "application/json",
        }

    def get_action(self, action_name: str):  # noqa: ANN001
        return self.annotate if action_name == "annotate" else super().get_action(action_name)

    def annotate(
        self,
        text: str,
        tags: list[str] | None = None,
        dashboard_uid: str | None = None,
    ) -> Dict[str, Any]:
        payload = {
            "text": text,
            "tags": tags or ["orchestra-ai"],
        }
        if dashboard_uid:
            payload["dashboardUID"] = dashboard_uid
        return self._request("POST", "/annotations", headers=self._headers(), data=json.dumps(payload)) 