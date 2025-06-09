from __future__ import annotations

import os
from typing import Any, Dict

try:
    import redis  # type: ignore
except ImportError:  # pragma: no cover
    redis = None  # type: ignore

from . import BaseIntegration

__all__ = ["RedisIntegration"]


class RedisIntegration(BaseIntegration):
    """Tiny wrapper for basic Redis GET/SET."""

    name = "redis"
    required_env_vars = ("REDIS_URL",)

    @property
    def credentials(self) -> Dict[str, str]:
        return {"REDIS_URL": os.getenv("REDIS_URL", "")}

    # ------------------------------------------------------------------
    def get_action(self, action_name: str):  # noqa: ANN001
        match action_name:
            case "get":
                return self.get
            case "set":
                return self.set
            case _:
                raise KeyError(f"Unknown Redis action: {action_name}")

    # ----------------------- helpers ------------------------------
    def _client(self):  # noqa: ANN001
        if redis is None:
            raise RuntimeError("redis-py is not installed.")
        return redis.from_url(self.credentials["REDIS_URL"])

    # ------------------------- actions ---------------------------
    def get(self, key: str) -> Any:  # noqa: ANN001
        return self._client().get(key)

    def set(self, key: str, value: Any, ex: int | None = None) -> bool:  # noqa: ANN001
        return bool(self._client().set(key, value, ex=ex)) 