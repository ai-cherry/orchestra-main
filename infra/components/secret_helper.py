# TODO: Consider adding connection pooling configuration
"""
        namespace="superagi",
    )
"""
    config_prefix: str = "",
    labels: Dict[str, str] = None,
    opts=None,
) -> k8s.core.v1.Secret:
    """
        config_prefix: Optional prefix for config keys (e.g., "db_").
        labels: Optional labels for the Secret.
        opts: Pulumi ResourceOptions.

    Returns:
        k8s.core.v1.Secret resource.
    """
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
