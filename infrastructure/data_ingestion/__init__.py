# TODO: Consider adding connection pooling configuration
"""
"""
project_name = "data-ingestion"
environment = config.get("environment") or "production"
region = config.get("region") or "ewr"  # New Jersey

# Resource naming convention
def resource_name(name: str) -> str:
    """Generate consistent resource names."""
    return f"{project_name}-{environment}-{name}"

# Tags for all resources
common_tags = [
    f"project:{project_name}",
    f"environment:{environment}",
    "managed-by:pulumi",
    "component:data-ingestion"
]

class DataIngestionInfrastructure:
    """
    """
        """Initialize infrastructure components."""
        """Create all infrastructure components."""
        """Create VPC for network isolation."""
            resource_name("vpc"),
            region=region,
            description=f"VPC for {project_name} {environment}",
            v4_subnet="10.0.0.0",
            v4_subnet_mask=24,
            tags=common_tags
        )
        
        pulumi.export("vpc_id", self.vpc.id)
        pulumi.export("vpc_subnet", self.vpc.v4_subnet)
    
    def create_postgres_cluster(self):
        """Create managed PostgreSQL cluster with optimizations."""
            "shared_buffers": "256MB",
            "effective_cache_size": "1GB",
            "maintenance_work_mem": "128MB",
            "checkpoint_completion_target": "0.9",
            "wal_buffers": "16MB",
            "default_statistics_target": "100",
            "random_page_cost": "1.1",  # SSD optimized
            "effective_io_concurrency": "200",
            "work_mem": "16MB",
            "min_wal_size": "1GB",
            "max_wal_size": "4GB",
            "max_worker_processes": "8",
            "max_parallel_workers_per_gather": "4",
            "max_parallel_workers": "8"
        }
        
        self.postgres_cluster = vultr.DatabaseCluster(
            resource_name("postgres"),
            database_engine="pg",
            database_engine_version="15",
            region=region,
            plan="vultr-dbaas-startup-cc-2-80-4",  # 2 vCPU, 4GB RAM, 80GB NVMe
            cluster_size=3,  # 3-node cluster for HA
            vpc_id=self.vpc.id,
            tags=common_tags,
            # Enable automated backups
            maintenance_dow="sunday",
            maintenance_time="03:00",
            # PostgreSQL specific settings
            pg_settings=postgres_config
        )
        
        # Create read replica for query performance
        self.postgres_read_replica = vultr.DatabaseReadReplica(
            resource_name("postgres-read"),
            database_cluster_id=self.postgres_cluster.id,
            region=region,
            plan="vultr-dbaas-startup-cc-2-80-4",
            tags=common_tags + ["role:read-replica"]
        )
        
        pulumi.export("postgres_host", self.postgres_cluster.host)
        pulumi.export("postgres_port", self.postgres_cluster.port)
        pulumi.export("postgres_database", self.postgres_cluster.database)
        pulumi.export("postgres_read_host", self.postgres_read_replica.host)
    
    def create_redis_cache(self):
        """Create Redis instance for caching."""
            resource_name("redis"),
            database_engine="redis",
            database_engine_version="7",
            region=region,
            plan="vultr-dbaas-hobbyist-cc-1-25-1",  # 1 vCPU, 1GB RAM
            vpc_id=self.vpc.id,
            tags=common_tags + ["component:cache"],
            redis_eviction_policy="allkeys-lru"
        )
        
        pulumi.export("redis_host", self.redis_instance.host)
        pulumi.export("redis_port", self.redis_instance.port)
    
    def create_kubernetes_cluster(self):
        """Create Kubernetes cluster for services."""
                "node_quantity": 3,
                "plan": "vc2-4c-8gb",  # 4 vCPU, 8GB RAM
                "label": "data-processing",
                "auto_scaler": True,
                "min_nodes": 3,
                "max_nodes": 10
            },
            {
                "node_quantity": 2,
                "plan": "vc2-2c-4gb",  # 2 vCPU, 4GB RAM
                "label": "api-services",
                "auto_scaler": True,
                "min_nodes": 2,
                "max_nodes": 5
            }
        ]
        
        self.k8s_cluster = vultr.Kubernetes(
            resource_name("k8s"),
            region=region,
            version="v1.28.2",
            vpc_id=self.vpc.id,
            node_pools=node_pools,
            tags=common_tags
        )
        
        # Create Kubernetes provider
        k8s_provider = k8s.Provider(
            resource_name("k8s-provider"),
            kubeconfig=self.k8s_cluster.kube_config
        )
        
        # Create namespaces
        self.create_k8s_namespaces(k8s_provider)
        
        # Deploy Weaviate
        self.deploy_weaviate(k8s_provider)
        
        pulumi.export("k8s_cluster_id", self.k8s_cluster.id)
        pulumi.export("k8s_endpoint", self.k8s_cluster.endpoint)
    
    def create_k8s_namespaces(self, provider: k8s.Provider):
        """Create Kubernetes namespaces."""
        namespaces = ["data-ingestion", "weaviate", "monitoring"]
        
        for ns in namespaces:
            k8s.core.v1.Namespace(
                f"{resource_name('ns')}-{ns}",
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    name=ns,
                    labels={
                        "project": project_name,
                        "environment": environment
                    }
                ),
                opts=ResourceOptions(provider=provider)
            )
    
    def deploy_weaviate(self, provider: k8s.Provider):
        """Deploy Weaviate vector database on Kubernetes."""
            "authentication": {
                "anonymous_access": {
                    "enabled": False
                }
            },
            "authorization": {
                "admin_list": {
                    "enabled": True
                }
            },
            "modules": {
                "text2vec-openai": {
                    "enabled": True
                }
            }
        }
        
        # Create Weaviate StatefulSet
        weaviate_statefulset = k8s.apps.v1.StatefulSet(
            resource_name("weaviate"),
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="weaviate",
                namespace="weaviate"
            ),
            spec=k8s.apps.v1.StatefulSetSpecArgs(
                replicas=3,
                service_name="weaviate",
                selector=k8s.meta.v1.LabelSelectorArgs(
                    match_labels={"app": "weaviate"}
                ),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(
                        labels={"app": "weaviate"}
                    ),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name="weaviate",
                                image="semitechnologies/weaviate:1.22.4",
                                env=[
                                    k8s.core.v1.EnvVarArgs(
                                        name="CLUSTER_HOSTNAME",
                                        value="weaviate"
                                    ),
                                    k8s.core.v1.EnvVarArgs(
                                        name="CLUSTER_GOSSIP_BIND_PORT",
                                        value="7100"
                                    ),
                                    k8s.core.v1.EnvVarArgs(
                                        name="CLUSTER_DATA_BIND_PORT",
                                        value="7101"
                                    ),
                                    k8s.core.v1.EnvVarArgs(
                                        name="AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED",
                                        value="false"
                                    ),
                                    k8s.core.v1.EnvVarArgs(
                                        name="PERSISTENCE_DATA_PATH",
                                        value="/var/lib/weaviate"
                                    )
                                ],
                                ports=[
                                    k8s.core.v1.ContainerPortArgs(
                                        container_port=8080,
                                        name="http"
                                    )
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name="data",
                                        mount_path="/var/lib/weaviate"
                                    )
                                ],
                                resources=k8s.core.v1.ResourceRequirementsArgs(
                                    requests={
                                        "cpu": "1",
                                        "memory": "2Gi"
                                    },
                                    limits={
                                        "cpu": "2",
                                        "memory": "4Gi"
                                    }
                                )
                            )
                        ]
                    )
                ),
                volume_claim_templates=[
                    k8s.core.v1.PersistentVolumeClaimArgs(
                        metadata=k8s.meta.v1.ObjectMetaArgs(
                            name="data"
                        ),
                        spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
                            access_modes=["ReadWriteOnce"],
                            storage_class_name="vultr-block-storage",
                            resources=k8s.core.v1.ResourceRequirementsArgs(
                                requests={"storage": "50Gi"}
                            )
                        )
                    )
                ]
            ),
            opts=ResourceOptions(provider=provider)
        )
        
        # Create Weaviate Service
        weaviate_service = k8s.core.v1.Service(
            resource_name("weaviate-svc"),
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="weaviate",
                namespace="weaviate"
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector={"app": "weaviate"},
                ports=[
                    k8s.core.v1.ServicePortArgs(
                        port=8080,
                        target_port=8080,
                        name="http"
                    )
                ],
                type="ClusterIP"
            ),
            opts=ResourceOptions(provider=provider)
        )
    
    def create_object_storage(self):
        """Create S3-compatible object storage."""
            resource_name("storage"),
            cluster_id=1,  # New Jersey cluster
            label=resource_name("files"),
            tags=common_tags
        )
        
        # Create buckets for different purposes
        buckets = ["raw-files", "processed-files", "temp-files"]
        
        for bucket_name in buckets:
            vultr.ObjectStorageBucket(
                resource_name(f"bucket-{bucket_name}"),
                object_storage_id=self.object_storage.id,
                label=f"{project_name}-{environment}-{bucket_name}",
                tags=common_tags + [f"bucket:{bucket_name}"]
            )
        
        pulumi.export("object_storage_id", self.object_storage.id)
        pulumi.export("object_storage_endpoint", self.object_storage.s3_hostname)
    
    def create_load_balancer(self):
        """Create load balancer for API endpoints."""
            resource_name("lb"),
            region=region,
            vpc_id=self.vpc.id,
            forwarding_rules=[
                {
                    "frontend_protocol": "https",
                    "frontend_port": 443,
                    "backend_protocol": "http",
                    "backend_port": 8000
                },
                {
                    "frontend_protocol": "http",
                    "frontend_port": 80,
                    "backend_protocol": "http",
                    "backend_port": 8000
                }
            ],
            health_check={
                "protocol": "http",
                "port": 8000,
                "path": "/health",
                "check_interval": 10,
                "response_timeout": 5,
                "unhealthy_threshold": 3,
                "healthy_threshold": 2
            },
            ssl_redirect=True,
            proxy_protocol=True,
            tags=common_tags
        )
        
        pulumi.export("load_balancer_ip", self.load_balancer.ipv4)
    
    def export_outputs(self):
        """Export stack outputs for use by other components."""
        pulumi.export("project_name", project_name)
        pulumi.export("environment", environment)
        pulumi.export("region", region)
        
        # Connection strings (secrets)
        postgres_connection = Output.all(
            self.postgres_cluster.host,
            self.postgres_cluster.port,
            self.postgres_cluster.database,
            self.postgres_cluster.username,
            self.postgres_cluster.password
        ).apply(
            lambda args: f"postgresql://{args[3]}:{args[4]}@{args[0]}:{args[1]}/{args[2]}"
        )
        
        pulumi.export("postgres_connection_string", Output.secret(postgres_connection))
        
        redis_connection = Output.all(
            self.redis_instance.host,
            self.redis_instance.port,
            self.redis_instance.password
        ).apply(
            lambda args: f"redis://:{args[2]}@{args[0]}:{args[1]}/0"
        )
        
        pulumi.export("redis_connection_string", Output.secret(redis_connection))

# Create infrastructure
infra = DataIngestionInfrastructure()
infra.create_infrastructure()