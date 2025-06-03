# TODO: Consider adding connection pooling configuration
"""
"""
    """LiteLLM gateway for unified LLM access"""
        super().__init__("orchestra:llm:LiteLLM", name, {}, opts)

        namespace = config["namespace"]
        image = config.get("image", "ghcr.io/berriai/litellm:main-latest")
        replicas = config.get("replicas", 2)
        port = config.get("port", 4000)
        api_keys = config.get("api_keys", {})

        # Create ConfigMap for LiteLLM configuration
        litellm_config = k8s.core.v1.ConfigMap(
            f"{name}-config",
            metadata=k8s.meta.v1.ObjectMetaArgs(name="litellm-config", namespace=namespace),
            data={
                "config.yaml": """
"""
            f"{name}-secret",
            metadata=k8s.meta.v1.ObjectMetaArgs(name="litellm-secret", namespace=namespace),
            string_data={
                **api_keys,
                "LITELLM_MASTER_KEY": "sk-1234567890abcdef",  # Generate a secure key
                "DATABASE_URL": "postgresql://litellm:password@postgres:5432/litellm",
            },
            opts=ResourceOptions(parent=self),
        )

        # Create Deployment
        deployment = k8s.apps.v1.Deployment(
            f"{name}-deployment",
            metadata=k8s.meta.v1.ObjectMetaArgs(name="litellm", namespace=namespace, labels={"app": "litellm"}),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                replicas=replicas,
                selector=k8s.meta.v1.LabelSelectorArgs(match_labels={"app": "litellm"}),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(
                        labels={"app": "litellm"},
                        annotations={
                            "prometheus.io/scrape": "true",
                            "prometheus.io/port": str(port),
                            "prometheus.io/path": "/metrics",
                        },
                    ),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name="litellm",
                                image=image,
                                command=["litellm"],
                                args=[
                                    "--config",
                                    "/app/config.yaml",
                                    "--port",
                                    str(port),
                                    "--num_workers",
                                    "4",
                                ],
                                ports=[k8s.core.v1.ContainerPortArgs(container_port=port, name="http")],
                                env_from=[
                                    k8s.core.v1.EnvFromSourceArgs(
                                        secret_ref=k8s.core.v1.SecretEnvSourceArgs(name="litellm-secret")
                                    )
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(name="config", mount_path="/app", read_only=True)
                                ],
                                resources=k8s.core.v1.ResourceRequirementsArgs(
                                    requests={"memory": "512Mi", "cpu": "500m"},
                                    limits={"memory": "1Gi", "cpu": "1"},
                                ),
                                liveness_probe=k8s.core.v1.ProbeArgs(
                                    http_get=k8s.core.v1.HTTPGetActionArgs(path="/health", port=port),
                                    initial_delay_seconds=30,
                                    period_seconds=10,
                                ),
                                readiness_probe=k8s.core.v1.ProbeArgs(
                                    http_get=k8s.core.v1.HTTPGetActionArgs(path="/health/readiness", port=port),
                                    initial_delay_seconds=10,
                                    period_seconds=5,
                                ),
                            )
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name="config",
                                config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(name="litellm-config"),
                            )
                        ],
                    ),
                ),
            ),
            opts=ResourceOptions(parent=self, depends_on=[litellm_config, litellm_secret]),
        )

        # Create Service
        service = k8s.core.v1.Service(
            f"{name}-service",
            metadata=k8s.meta.v1.ObjectMetaArgs(name="litellm", namespace=namespace, labels={"app": "litellm"}),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector={"app": "litellm"},
                ports=[k8s.core.v1.ServicePortArgs(port=port, target_port=port, name="http")],
                type="ClusterIP",
            ),
            opts=ResourceOptions(parent=self, depends_on=[deployment]),
        )

        # Create HPA for auto-scaling
        k8s.autoscaling.v2.HorizontalPodAutoscaler(
            f"{name}-hpa",
            metadata=k8s.meta.v1.ObjectMetaArgs(name="litellm-hpa", namespace=namespace),
            spec=k8s.autoscaling.v2.HorizontalPodAutoscalerSpecArgs(
                scale_target_ref=k8s.autoscaling.v2.CrossVersionObjectReferenceArgs(
                    api_version="apps/v1", kind="Deployment", name="litellm"
                ),
                min_replicas=replicas,
                max_replicas=10,
                metrics=[
                    k8s.autoscaling.v2.MetricSpecArgs(
                        type="Resource",
                        resource=k8s.autoscaling.v2.ResourceMetricSourceArgs(
                            name="cpu",
                            target=k8s.autoscaling.v2.MetricTargetArgs(type="Utilization", average_utilization=70),
                        ),
                    ),
                    k8s.autoscaling.v2.MetricSpecArgs(
                        type="Resource",
                        resource=k8s.autoscaling.v2.ResourceMetricSourceArgs(
                            name="memory",
                            target=k8s.autoscaling.v2.MetricTargetArgs(type="Utilization", average_utilization=80),
                        ),
                    ),
                ],
            ),
            opts=ResourceOptions(parent=self, depends_on=[deployment]),
        )

        # Export outputs
        self.service = service
        self.endpoint = Output.concat(
            "http://",
            service.metadata.name,
            ".",
            namespace,
            ".svc.cluster.local:",
            str(port),
        )

        self.outputs = {
            "endpoint": self.endpoint,
            "service_name": service.metadata.name,
            "namespace": namespace,
            "port": port,
        }

        self.register_outputs({"endpoint": self.endpoint, "outputs": self.outputs})
