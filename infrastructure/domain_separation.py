# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
environment = config.get("environment") or "development"

# Domain configurations
domains = {
    "personal": {
        "name": "Cherry",
        "namespace": "personal-domain",
        "replicas": 2,
        "resources": {
            "requests": {"memory": "512Mi", "cpu": "250m"},
            "limits": {"memory": "1Gi", "cpu": "500m"}
        }
    },
    "payready": {
        "name": "Sophia",
        "namespace": "payready-domain",
        "replicas": 2,
        "resources": {
            "requests": {"memory": "1Gi", "cpu": "500m"},
            "limits": {"memory": "2Gi", "cpu": "1000m"}
        }
    },
    "paragonrx": {
        "name": "Karen",
        "namespace": "paragonrx-domain",
        "replicas": 3,
        "resources": {
            "requests": {"memory": "1Gi", "cpu": "500m"},
            "limits": {"memory": "2Gi", "cpu": "1000m"}
        }
    }
}

# Create namespaces for each domain
namespaces = {}
for domain_key, domain_config in domains.items():
    namespaces[domain_key] = k8s.core.v1.Namespace(
        f"{domain_key}-namespace",
        metadata={
            "name": domain_config["namespace"],
            "labels": {
                "domain": domain_key,
                "persona": domain_config["name"],
                "environment": environment
            }
        }
    )

# Deploy domain services
for domain_key, domain_config in domains.items():
    # Deployment
    deployment = k8s.apps.v1.Deployment(
        f"{domain_key}-deployment",
        metadata={
            "namespace": domain_config["namespace"],
            "name": f"{domain_key}-service"
        },
        spec={
            "replicas": domain_config["replicas"],
            "selector": {"matchLabels": {"app": domain_key}},
            "template": {
                "metadata": {"labels": {"app": domain_key}},
                "spec": {
                    "containers": [{
                        "name": domain_key,
                        "image": f"orchestra/{domain_key}:latest",
                        "ports": [{"containerPort": 8000}],
                        "resources": domain_config["resources"],
                        "env": [
                            {"name": "DOMAIN", "value": domain_key},
                            {"name": "PERSONA", "value": domain_config["name"]},
                            {"name": "WEAVIATE_URL", "value": f"https://{domain_key}-cluster.weaviate.network"},
                            {"name": "POSTGRES_SCHEMA", "value": f"{domain_key}_domain"}
                        ]
                    }]
                }
            }
        }
    )
    
    # Service
    service = k8s.core.v1.Service(
        f"{domain_key}-service",
        metadata={
            "namespace": domain_config["namespace"],
            "name": f"{domain_key}-service"
        },
        spec={
            "selector": {"app": domain_key},
            "ports": [{"port": 80, "targetPort": 8000}],
            "type": "ClusterIP"
        }
    )

# API Gateway Ingress
ingress = k8s.networking.v1.Ingress(
    "api-gateway-ingress",
    metadata={
        "name": "api-gateway",
        "annotations": {
            "kubernetes.io/ingress.class": "nginx",
            "cert-manager.io/cluster-issuer": "letsencrypt-prod"
        }
    },
    spec={
        "tls": [{
            "hosts": ["api.orchestra.ai"],
            "secretName": "api-tls"
        }],
        "rules": [{
            "host": "api.orchestra.ai",
            "http": {
                "paths": [
                    {
                        "path": "/personal",
                        "pathType": "Prefix",
                        "backend": {
                            "service": {
                                "name": "personal-service",
                                "port": {"number": 80}
                            }
                        }
                    },
                    {
                        "path": "/payready",
                        "pathType": "Prefix",
                        "backend": {
                            "service": {
                                "name": "payready-service",
                                "port": {"number": 80}
                            }
                        }
                    },
                    {
                        "path": "/paragonrx",
                        "pathType": "Prefix",
                        "backend": {
                            "service": {
                                "name": "paragonrx-service",
                                "port": {"number": 80}
                            }
                        }
                    }
                ]
            }
        }]
    }
)

# Export endpoints
pulumi.export("personal_endpoint", Output.concat("https://api.orchestra.ai/personal"))
pulumi.export("payready_endpoint", Output.concat("https://api.orchestra.ai/payready"))
pulumi.export("paragonrx_endpoint", Output.concat("https://api.orchestra.ai/paragonrx"))
