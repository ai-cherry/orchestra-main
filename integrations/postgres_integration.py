from __future__ import annotations

import os
from typing import Any, Dict, List

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:  # pragma: no cover
    psycopg2 = None  # type: ignore

from . import BaseIntegration, ActionFn

__all__ = ["PostgresIntegration"]


class PostgresIntegration(BaseIntegration):
    """Execute read-only queries against Postgres (safe for agent use)."""

    name = "postgres"
    required_env_vars = (
        "POSTGRES_HOST",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    )

    @property
    def credentials(self) -> Dict[str, str]:
        return {key: os.getenv(key, "") for key in self.required_env_vars}

    # ------------------------------------------------------------------
    def get_action(self, action_name: str):  # noqa: ANN001
        match action_name:
            case "query":
                return self.query
            case _:
                raise KeyError(f"Unknown Postgres action: {action_name}")

    # --------------------------- actions ----------------------------
    def _get_conn(self):  # noqa: ANN001
        if psycopg2 is None:
            raise RuntimeError("psycopg2 is not installed in this environment.")
        return psycopg2.connect(
            host=self.credentials["POSTGRES_HOST"],
            dbname=self.credentials["POSTGRES_DB"],
            user=self.credentials["POSTGRES_USER"],
            password=self.credentials["POSTGRES_PASSWORD"],
        )

    def query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute a read-only SQL query and return rows."""
        if not sql.lstrip().lower().startswith("select"):
            raise ValueError("Only SELECT queries are allowed via the agent.")
        with self._get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            return cur.fetchall() 