"""
Database Component for Pulumi Infrastructure
===========================================
Modular component for managing database resources (DragonflyDB, MongoDB, Firestore)
"""

import pulumi
import pulumi_kubernetes as k8s
import pulumi_gcp as gcp
from pulumi import ComponentResource, ResourceOptions
from typing import Dict, Any, Optional


from .secret_helper import create_k8s_secret_from_config


class DatabaseComponent(ComponentResource):
    """
    Reusable database component for the AI Orchestra system.
    Manages DragonflyDB, MongoDB, and Firestore resources.
    """

    def __init__(
        self, name: str, config: Dict[str, Any], opts: Optional[ResourceOptions] = None
    ):
        super().__init__("orchestra:database:Component", name, None, opts)

        self.config = config
        self.namespace = config.get("namespace", "superagi")
        self.project_id = config.get("project_id")

        # Create child options
        child_opts = ResourceOptions(parent=self)

        # Deploy DragonflyDB for short-term memory
        self.dragonfly = self._create_dragonfly(child_opts)

        # Deploy MongoDB for mid/long-term memory (if enabled)
        if config.get("enable_mongodb", False):
            # Create a Kubernetes Secret for MongoDB credentials from Pulumi config
            self.mongodb_secret = create_k8s_secret_from_config(
                name="mongodb-secrets",
                namespace=self.namespace,
                keys=[
                    "root-password",
                    "mongodb-uri",
                ],  # Pulumi config keys: mongodb_password, mongodb_uri
                config_prefix="mongodb_",
                opts=child_opts,
            )
            self.mongodb = self._create_mongodb(child_opts)

        # Configure Firestore
        self.firestore_config = self._configure_firestore(child_opts)

        # Register outputs
        self.register_outputs(
            {
                "dragonfly_host": self.dragonfly["host"],
                "dragonfly_port": self.dragonfly["port"],
                "mongodb_uri": (
                    self.mongodb.get("uri") if hasattr(self, "mongodb") else None
                ),
                "firestore_project": self.project_id,
            }
        )

    def _create_dragonfly(self, opts: ResourceOptions) -> Dict[str, Any]:
        """Deploy DragonflyDB for short-term memory"""

        # Create PVC for DragonflyDB
        dragonfly_pvc = k8s.core.v1.PersistentVolumeClaim(
            f"{self._name}-dragonfly-pvc",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="dragonfly-data",
                namespace=self.namespace,
            ),
            spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
                access_modes=["ReadWriteOnce"],
                storage_class_name="pd-ssd",
                resources=k8s.core.v1.ResourceRequirementsArgs(
                    requests={"storage": self.config.get("dragonfly_storage", "10Gi")},
                ),
            ),
            opts=opts,
        )

        # Deploy DragonflyDB
        dragonfly_deployment = k8s.apps.v1.Deployment(
            f"{self._name}-dragonfly",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="dragonfly",
                namespace=self.namespace,
            ),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                replicas=1,
                selector=k8s.meta.v1.LabelSelectorArgs(
                    match_labels={"app": "dragonfly"},
                ),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(
                        labels={"app": "dragonfly"},
                    ),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name="dragonfly",
                                image="docker.dragonflydb.io/dragonflydb/dragonfly:latest",
                                ports=[
                                    k8s.core.v1.ContainerPortArgs(container_port=6379)
                                ],
                                env=[
                                    k8s.core.v1.EnvVarArgs(
                                        name="DRAGONFLY_max_memory",
                                        value=self.config.get(
                                            "dragonfly_max_memory", "4gb"
                                        ),
                                    ),
                                    k8s.core.v1.EnvVarArgs(
                                        name="DRAGONFLY_cache_mode",
                                        value="true",
                                    ),
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name="data",
                                        mount_path="/data",
                                    ),
                                ],
                                resources=k8s.core.v1.ResourceRequirementsArgs(
                                    requests={
                                        "memory": "2Gi",
                                        "cpu": "1",
                                    },
                                    limits={
                                        "memory": self.config.get(
                                            "dragonfly_max_memory", "4Gi"
                                        ),
                                        "cpu": "2",
                                    },
                                ),
                            )
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name="data",
                                persistent_volume_claim=k8s.core.v1.PersistentVolumeClaimVolumeSourceArgs(
                                    claim_name=dragonfly_pvc.metadata.name,
                                ),
                            ),
                        ],
                    ),
                ),
            ),
            opts=opts,
        )

        # Create service
        dragonfly_service = k8s.core.v1.Service(
            f"{self._name}-dragonfly-service",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="dragonfly",
                namespace=self.namespace,
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector={"app": "dragonfly"},
                ports=[k8s.core.v1.ServicePortArgs(port=6379, target_port=6379)],
                type="ClusterIP",
            ),
            opts=opts,
        )

        return {
            "host": dragonfly_service.metadata.name,
            "port": 6379,
            "deployment": dragonfly_deployment,
            "service": dragonfly_service,
        }

    def _create_mongodb(self, opts: ResourceOptions) -> Dict[str, Any]:
        """Deploy MongoDB for mid/long-term memory"""

        # MongoDB StatefulSet for persistence
        mongodb_statefulset = k8s.apps.v1.StatefulSet(
            f"{self._name}-mongodb",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="mongodb",
                namespace=self.namespace,
            ),
            spec=k8s.apps.v1.StatefulSetSpecArgs(
                service_name="mongodb",
                replicas=1,
                selector=k8s.meta.v1.LabelSelectorArgs(
                    match_labels={"app": "mongodb"},
                ),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(
                        labels={"app": "mongodb"},
                    ),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name="mongodb",
                                image="mongo:7.0",
                                ports=[
                                    k8s.core.v1.ContainerPortArgs(container_port=27017)
                                ],
                                env=[
                                    k8s.core.v1.EnvVarArgs(
                                        name="MONGO_INITDB_ROOT_USERNAME",
                                        value="admin",
                                    ),
                                    k8s.core.v1.EnvVarArgs(
                                        name="MONGO_INITDB_ROOT_PASSWORD",
                                        value_from=k8s.core.v1.EnvVarSourceArgs(
                                            secret_key_ref=k8s.core.v1.SecretKeySelectorArgs(
                                                name="mongodb-secrets",
                                                key="root-password",
                                            ),
                                        ),
                                    ),
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name="data",
                                        mount_path="/data/db",
                                    ),
                                ],
                                resources=k8s.core.v1.ResourceRequirementsArgs(
                                    requests={
                                        "memory": "2Gi",
                                        "cpu": "1",
                                    },
                                    limits={
                                        "memory": "4Gi",
                                        "cpu": "2",
                                    },
                                ),
                            )
                        ],
                    ),
                ),
                volume_claim_templates=[
                    k8s.core.v1.PersistentVolumeClaimArgs(
                        metadata=k8s.meta.v1.ObjectMetaArgs(name="data"),
                        spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
                            access_modes=["ReadWriteOnce"],
                            storage_class_name="pd-ssd",
                            resources=k8s.core.v1.ResourceRequirementsArgs(
                                requests={
                                    "storage": self.config.get(
                                        "mongodb_storage", "50Gi"
                                    )
                                },
                            ),
                        ),
                    ),
                ],
            ),
            opts=opts,
        )

        # MongoDB Service
        mongodb_service = k8s.core.v1.Service(
            f"{self._name}-mongodb-service",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="mongodb",
                namespace=self.namespace,
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector={"app": "mongodb"},
                ports=[k8s.core.v1.ServicePortArgs(port=27017, target_port=27017)],
                type="ClusterIP",
            ),
            opts=opts,
        )

        # Construct MongoDB URI from the Kubernetes Secret (as a Pulumi secret output)
        # The URI will be: mongodb://admin:<password>@mongodb:27017/orchestra?authSource=admin
        mongodb_password = self.mongodb_secret.string_data.apply(
            lambda d: d["root-password"]
        )
        mongodb_uri = pulumi.Output.concat(
            "mongodb://admin:",
            mongodb_password,
            "@mongodb:27017/orchestra?authSource=admin",
        )

        return {
            "uri": mongodb_uri,
            "statefulset": mongodb_statefulset,
            "service": mongodb_service,
        }

    def _configure_firestore(self, opts: ResourceOptions) -> Dict[str, Any]:
        """Configure Firestore for document storage"""

        # Ensure Firestore API is enabled
        firestore_api = gcp.projects.Service(
            f"{self._name}-firestore-api",
            service="firestore.googleapis.com",
            project=self.project_id,
            disable_on_destroy=False,
            opts=opts,
        )

        # Create Firestore database (if not exists)
        # Note: Firestore database creation via Pulumi requires specific API
        # For now, we'll ensure the API is enabled and document the setup

        return {
            "project_id": self.project_id,
            "api_enabled": firestore_api,
            "collections": ["agents", "memories", "tools", "conversations"],
        }
