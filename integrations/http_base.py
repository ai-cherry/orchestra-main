from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from . import BaseIntegration, ActionFn

__all__ = ["HTTPIntegrationBase"]


class HTTPIntegrationBase(BaseIntegration):
    """Common functionality for REST-based integrations."""

    _BASE_URL: str  # to be defined in subclass
    _DEFAULT_HEADERS: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Request helper
    # ------------------------------------------------------------------
    def _request(
        self,
        method: str,
        path: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Any:  # noqa: ANN401
        if not hasattr(self, "_BASE_URL"):
            raise AttributeError("Integration subclass must define _BASE_URL")
        url = self._BASE_URL.rstrip("/") + path
        merged_headers = {**self._DEFAULT_HEADERS, **(headers or {})}
        resp = requests.request(method, url, headers=merged_headers, timeout=30, **kwargs)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"{self.name} API error {resp.status_code}: {resp.text[:300]}"
            )
        if resp.headers.get("content-type", "").startswith("application/json"):
            return resp.json()
        return resp.text 