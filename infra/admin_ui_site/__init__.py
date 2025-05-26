"""Admin UI Static Site Infrastructure
=====================================
Pulumi component that provisions:
1. GCS bucket configured for static website hosting.
2. Public read access for site assets.
3. Cloud CDN-enabled backend bucket + HTTPS load balancer.
4. (Optional) DNS A-record for the custom domain.

This component is intentionally minimal yet production-ready and may be
extended with caching, logging, or Cloud Armor rules as needed.

Example usage in a Pulumi program:
    from admin_ui_site import AdminUiSite

    site = AdminUiSite("admin-ui", domain_name="cherry-ai.me")
    pulumi.export("bucket_name", site.bucket_name)
    pulumi.export("lb_ip", site.lb_ip_address)
"""

from __future__ import annotations

from typing import Final, Optional

import pulumi
import pulumi_gcp as gcp

__all__: Final[list[str]] = ["AdminUiSite"]


class AdminUiSite(pulumi.ComponentResource):
    """Pulumi *Component* that deploys the static Admin UI to GCP.

    Args:
        name: Logical Pulumi name for the component.
        domain_name: Primary domain (e.g. ``"cherry-ai.me"``) that will point
            to the load balancer fronting the bucket.
        location: GCP location for bucket and SSL certificate. Defaults to
            ``"US"`` and ``"global"`` respectively.
        opts: Optional resource-options.

    Exports:
        bucket_name: The underlying GCS bucket name.
        lb_ip_address: The external IP of the HTTPS forwarding rule.
    """

    def __init__(
        self,
        name: str,
        *,
        domain_name: str,
        location: str = "US",
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__("orch:infra:AdminUiSite", name, None, opts)

        # 1. Storage bucket (static website)
        bucket = gcp.storage.Bucket(
            f"{name}-bucket",
            location=location,
            uniform_bucket_level_access=True,
            website=gcp.storage.BucketWebsiteArgs(
                main_page_suffix="index.html",
                not_found_page="index.html",
            ),
            cors=[
                gcp.storage.BucketCorArgs(
                    max_age_seconds=3600,
                    methods=["GET", "HEAD"],
                    origins=["*"],
                    response_headers=["Content-Type"],
                )
            ],
            force_destroy=True,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Public read access for object viewer role.
        gcp.storage.BucketIAMMember(
            f"{name}-public-read",
            bucket=bucket.name,
            role="roles/storage.objectViewer",
            member="allUsers",
            opts=pulumi.ResourceOptions(parent=self),
        )

        # 2. Backend bucket with Cloud CDN.
        backend_bucket = gcp.compute.BackendBucket(
            f"{name}-backend-bucket",
            bucket_name=bucket.name,
            enable_cdn=True,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # 3. HTTPS load balancer (URL Map → Target Proxy → Forwarding Rule)
        url_map = gcp.compute.URLMap(
            f"{name}-url-map",
            default_service=backend_bucket.self_link,
            opts=pulumi.ResourceOptions(parent=self),
        )

        managed_cert = gcp.compute.ManagedSslCertificate(
            f"{name}-managed-cert",
            managed=gcp.compute.ManagedSslCertificateManagedArgs(domains=[domain_name]),
            opts=pulumi.ResourceOptions(parent=self),
        )

        https_proxy = gcp.compute.TargetHttpsProxy(
            f"{name}-https-proxy",
            ssl_certificates=[managed_cert.name],
            url_map=url_map.id,
            opts=pulumi.ResourceOptions(parent=self),
        )

        forwarding_rule = gcp.compute.GlobalForwardingRule(
            f"{name}-https-fw-rule",
            target=https_proxy.id,
            port_range="443",
            ip_protocol="TCP",
            load_balancing_scheme="EXTERNAL",
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Optionally create a DNS A-record if the Cloud DNS managed-zone name
        # is provided through stack configuration (to keep the component
        # self-contained yet flexible).
        cfg = pulumi.Config()
        dns_zone = cfg.get("dnsZone")  # e.g. "cherry-ai-zone"
        if dns_zone:
            gcp.dns.RecordSet(
                f"{name}-dns-record",
                managed_zone=dns_zone,
                name=f"{domain_name}.",
                type="A",
                ttl=300,
                rrdatas=[forwarding_rule.ip_address],
                opts=pulumi.ResourceOptions(parent=self),
            )

        # Register component outputs.
        self.bucket_name = bucket.name
        self.lb_ip_address = forwarding_rule.ip_address

        self.register_outputs(
            {
                "bucket_name": self.bucket_name,
                "lb_ip_address": self.lb_ip_address,
            }
        )
