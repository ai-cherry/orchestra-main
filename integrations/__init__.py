from __future__ import annotations

"""Central registry for Orchestra AI external service integrations.

This package exposes a thin, uniform interface that the agent layer (e.g.
OpenAI Agents SDK, CrewAI, LangGraph) can use to invoke third-party APIs.

Design goals:
1.  **Lazy Importing** – avoid importing heavy SDKs unless the integration is used.
2.  **Typed Actions**  – every public method is type-annotated for clarity.
3.  **Secret Management** – credentials are read from environment variables that
    are **injected by GitHub Actions** from repository secrets at runtime.
4.  **Pluggability** – new integrations only need to subclass `BaseIntegration`
    and register themselves via the `registry` dict.
"""

from collections.abc import Callable
from importlib import import_module
from os import getenv
from typing import Any, Dict, Optional, Protocol

__all__ = [
    "BaseIntegration",
    "registry",
    "get_integration",
]


class ActionFn(Protocol):
    """Callable protocol for an integration action."""

    def __call__(self, **kwargs: Any) -> Any: ...  # noqa: D401,E501


class BaseIntegration:
    """Base class every integration must subclass."""

    # Human-readable name → will also be used in tool registration.
    name: str

    def __init__(self) -> None:
        self._verify_credentials()

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    @property
    def credentials(self) -> Dict[str, str]:
        """Return the env-loaded credentials for this integration."""
        raise NotImplementedError

    # Each integration exposes a set of *actions* – these are mapped to
    # function-calling friendly signatures when registered with an agent.
    def get_action(self, action_name: str) -> ActionFn:
        """Return the callable associated with *action_name*."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _verify_credentials(self) -> None:
        """Validate that required env vars have been set."""
        missing = [key for key in self.required_env_vars if getenv(key) is None]
        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(
                f"[{self.name}] Missing required environment variables: {joined}."
            )

    # Sub-classes *must* define this.
    required_env_vars: tuple[str, ...] = ()


# -------------------------------------------------------------------------
# Lazy-loading registry ----------------------------------------------------
# -------------------------------------------------------------------------
registry: Dict[str, str] = {
    # Infrastructure
    "pulumi": "integrations.pulumi_integration:PulumiIntegration",
    "vercel": "integrations.vercel_integration:VercelIntegration",
    "lambda_labs": "integrations.lambda_labs_integration:LambdaLabsIntegration",
    # Databases & Cache
    "postgres": "integrations.postgres_integration:PostgresIntegration",
    "redis": "integrations.redis_integration:RedisIntegration",
    # Vector DBs
    "pinecone": "integrations.pinecone_integration:PineconeIntegration",
    "weaviate": "integrations.weaviate_integration:WeaviateIntegration",
    # LLM Providers
    "openai": "integrations.openai_integration:OpenAIIntegration",
    "anthropic": "integrations.anthropic_integration:ClaudeIntegration",
    # SaaS & Ops
    "notion": "integrations.notion_integration:NotionIntegration",
    "slack": "integrations.slack_integration:SlackIntegration",
    "portkey": "integrations.portkey_integration:PortkeyIntegration",
    "grafana": "integrations.grafana_integration:GrafanaIntegration",
}


def _import_string(path: str):
    module_path, _, attr = path.partition(":")
    module = import_module(module_path)
    return getattr(module, attr)


def get_integration(name: str) -> BaseIntegration:
    """Return an *initialized* integration by name.

    Example:
        >>> pulumi = get_integration("pulumi")
        >>> pulumi.get_action("preview")(stack="dev")
    """
    if name not in registry:
        raise KeyError(f"Integration '{name}' is not registered.")
    cls: type[BaseIntegration] = _import_string(registry[name])
    return cls() 