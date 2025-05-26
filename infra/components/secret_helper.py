"""
Helper for creating Kubernetes Secrets from Pulumi config secrets.

This utility centralizes secret management, ensuring all sensitive values are loaded from Pulumi config (with secret=True)
and injected into Kubernetes as Kubernetes Secrets for use by deployments and services.

# For a full list of required config keys and secrets, see infra/CONFIG_REFERENCE.md

Usage:
    from .secret_helper import create_k8s_secret_from_config

    secret = create_k8s_secret_from_config(
        name="mongodb-secrets",
        namespace="superagi",
        keys=["mongodb_password", "mongodb_uri"]
    )
"""

from typing import Any, Dict, List

import pulumi
import pulumi_kubernetes as k8s


def create_k8s_secret_from_config(
    name: str,
    namespace: str,
    keys: List[str],
    config_prefix: str = "",
    labels: Dict[str, str] = None,
    opts=None,
) -> k8s.core.v1.Secret:
    """
    Create a Kubernetes Secret from Pulumi config secrets.

    Args:
        name: Name of the Kubernetes Secret.
        namespace: Namespace for the Secret.
        keys: List of Pulumi config keys to include in the Secret.
        config_prefix: Optional prefix for config keys (e.g., "db_").
        labels: Optional labels for the Secret.
        opts: Pulumi ResourceOptions.

    Returns:
        k8s.core.v1.Secret resource.
    """
    config = pulumi.Config()
    data: Dict[str, Any] = {}

    for key in keys:
        config_key = f"{config_prefix}{key}" if config_prefix else key
        # All secrets are loaded as Pulumi secrets
        data[key] = config.require_secret(config_key)

    secret = k8s.core.v1.Secret(
        name,
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=name,
            namespace=namespace,
            labels=labels or {},
        ),
        string_data=data,
        type="Opaque",
        opts=opts,
    )
    return secret
