"""
Ingress Component for Domain Configuration
==========================================
Configures NGINX ingress with SSL/TLS for cherry-ai.me
"""

import pulumi_kubernetes as k8s
from pulumi import ComponentResource, ResourceOptions
from typing import Dict, Any, Optional


class IngressComponent(ComponentResource):
    """Configure ingress with SSL for cherry-ai.me"""

    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        service_name: str,
        opts: Optional[ResourceOptions] = None,
    ):
        super().__init__("orchestra:ingress:Component", name, None, opts)

        self.namespace = config.get("namespace", "superagi")
        self.domain = config.get("domain", "cherry-ai.me")

        # Create child options
        child_opts = ResourceOptions(parent=self)

        # Install NGINX ingress controller
        self._install_nginx_ingress(child_opts)

        # Install cert-manager for automatic SSL
        self._install_cert_manager(child_opts)

        # Create certificate issuer
        self.issuer = self._create_certificate_issuer(child_opts)

        # Create ingress
        self.ingress = self._create_ingress(service_name, child_opts)

        # Register outputs
        self.register_outputs(
            {
                "domain": self.domain,
                "ingress_name": self.ingress.metadata.name,
            }
        )

    def _install_nginx_ingress(self, opts: ResourceOptions):
        """Install NGINX ingress controller"""

        k8s.yaml.ConfigFile(
            f"{self._name}-nginx-ingress",
            file="https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml",
            opts=opts,
        )

    def _install_cert_manager(self, opts: ResourceOptions):
        """Install cert-manager for automatic SSL certificates"""

        k8s.yaml.ConfigFile(
            f"{self._name}-cert-manager",
            file="https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml",
            opts=opts,
        )

    def _create_certificate_issuer(self, opts: ResourceOptions):
        """Create Let's Encrypt certificate issuer"""

        # Wait for cert-manager to be ready
        import time

        time.sleep(30)  # Give cert-manager time to initialize

        return k8s.apiextensions.CustomResource(
            f"{self._name}-letsencrypt-issuer",
            api_version="cert-manager.io/v1",
            kind="ClusterIssuer",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="letsencrypt-prod",
            ),
            spec={
                "acme": {
                    "server": "https://acme-v02.api.letsencrypt.org/directory",
                    "email": "scoobyjava@cherry-ai.me",
                    "privateKeySecretRef": {
                        "name": "letsencrypt-prod",
                    },
                    "solvers": [
                        {
                            "http01": {
                                "ingress": {
                                    "class": "nginx",
                                },
                            },
                        }
                    ],
                },
            },
            opts=opts,
        )

    def _create_ingress(
        self, service_name: str, opts: ResourceOptions
    ) -> k8s.networking.v1.Ingress:
        """Create ingress for cherry-ai.me"""

        return k8s.networking.v1.Ingress(
            f"{self._name}-ingress",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="superagi-ingress",
                namespace=self.namespace,
                annotations={
                    "kubernetes.io/ingress.class": "nginx",
                    "cert-manager.io/cluster-issuer": "letsencrypt-prod",
                    "nginx.ingress.kubernetes.io/proxy-body-size": "50m",
                    "nginx.ingress.kubernetes.io/proxy-read-timeout": "600",
                    "nginx.ingress.kubernetes.io/proxy-send-timeout": "600",
                    # Rate limiting
                    "nginx.ingress.kubernetes.io/limit-rps": "100",
                    # Security headers
                    "nginx.ingress.kubernetes.io/configuration-snippet": """
more_set_headers "X-Frame-Options: SAMEORIGIN";
more_set_headers "X-Content-Type-Options: nosniff";
more_set_headers "X-XSS-Protection: 1; mode=block";
more_set_headers "Referrer-Policy: strict-origin-when-cross-origin";
""",
                },
            ),
            spec=k8s.networking.v1.IngressSpecArgs(
                ingress_class_name="nginx",
                tls=[
                    k8s.networking.v1.IngressTLSArgs(
                        hosts=[self.domain, f"www.{self.domain}"],
                        secret_name="superagi-tls",
                    )
                ],
                rules=[
                    # Main domain
                    k8s.networking.v1.IngressRuleArgs(
                        host=self.domain,
                        http=k8s.networking.v1.HTTPIngressRuleValueArgs(
                            paths=[
                                k8s.networking.v1.HTTPIngressPathArgs(
                                    path="/",
                                    path_type="Prefix",
                                    backend=k8s.networking.v1.IngressBackendArgs(
                                        service=k8s.networking.v1.IngressServiceBackendArgs(
                                            name=service_name,
                                            port=k8s.networking.v1.ServiceBackendPortArgs(
                                                number=8080,
                                            ),
                                        ),
                                    ),
                                ),
                            ],
                        ),
                    ),
                    # WWW subdomain (redirect to main)
                    k8s.networking.v1.IngressRuleArgs(
                        host=f"www.{self.domain}",
                        http=k8s.networking.v1.HTTPIngressRuleValueArgs(
                            paths=[
                                k8s.networking.v1.HTTPIngressPathArgs(
                                    path="/",
                                    path_type="Prefix",
                                    backend=k8s.networking.v1.IngressBackendArgs(
                                        service=k8s.networking.v1.IngressServiceBackendArgs(
                                            name=service_name,
                                            port=k8s.networking.v1.ServiceBackendPortArgs(
                                                number=8080,
                                            ),
                                        ),
                                    ),
                                ),
                            ],
                        ),
                    ),
                ],
            ),
            opts=ResourceOptions(parent=self, depends_on=[self.issuer]),
        )
