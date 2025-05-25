"""
Pulumi stack for Orchestra MCP: IAM, Pub/Sub, Service Directory, and Monitoring
-------------------------------------------------------------------------------
This refined, modular Pulumi program provisions all foundational GCP resources
for a high-performance, secure, and observable MCP deployment.

- IAM: Service accounts and least-privilege roles
- Pub/Sub: Topics and subscriptions for event-driven orchestration
- Service Directory: Namespaces and services for dynamic discovery
- Monitoring: Log-based metrics for operational excellence

Author: AI Orchestra
"""

import pulumi
import pulumi_gcp as gcp

# ---------------------------
# 1. IAM: Service Account & Roles
# ---------------------------
mcp_sa = gcp.serviceaccount.Account(
    "mcp-server-sa", account_id="mcp-server", display_name="MCP Server Service Account"
)

# Attach only the roles needed for Pub/Sub and Service Directory
gcp.projects.IAMMember(
    "mcp-pubsub-publisher",
    project=mcp_sa.project,
    role="roles/pubsub.publisher",
    member=mcp_sa.email.apply(lambda email: f"serviceAccount:{email}"),
)
gcp.projects.IAMMember(
    "mcp-pubsub-subscriber",
    project=mcp_sa.project,
    role="roles/pubsub.subscriber",
    member=mcp_sa.email.apply(lambda email: f"serviceAccount:{email}"),
)
gcp.projects.IAMMember(
    "mcp-servicedirectory-editor",
    project=mcp_sa.project,
    role="roles/servicedirectory.editor",
    member=mcp_sa.email.apply(lambda email: f"serviceAccount:{email}"),
)

# ---------------------------
# 2. Pub/Sub: Topics & Subscriptions
# ---------------------------
orchestra_topic = gcp.pubsub.Topic("orchestra-events")
orchestra_sub = gcp.pubsub.Subscription(
    "orchestra-events-sub", topic=orchestra_topic.name, ack_deadline_seconds=30
)

# ---------------------------
# 3. Service Directory: Namespace & Service
# ---------------------------
namespace = gcp.servicedirectory.Namespace(
    "orchestra-namespace", namespace_id="orchestra", location="us-central1"
)
mcp_service = gcp.servicedirectory.Service(
    "mcp-service", namespace=namespace.id, service_id="mcp-server"
)

# ---------------------------
# 4. Monitoring: Log-Based Metric
# ---------------------------
log_metric = gcp.logging.Metric(
    "mcp-error-metric",
    name="mcp_error_count",
    filter='resource.type="cloud_run_revision" severity>=ERROR',
    metric_descriptor={
        "metric_kind": "DELTA",
        "value_type": "INT64",
        "unit": "1",
        "description": "Count of MCP server errors",
    },
)

# ---------------------------
# 5. Outputs for Reference
# ---------------------------
pulumi.export("service_account_email", mcp_sa.email)
pulumi.export("pubsub_topic", orchestra_topic.name)
pulumi.export("pubsub_subscription", orchestra_sub.name)
pulumi.export("service_directory_namespace", namespace.name)
pulumi.export("service_directory_service", mcp_service.name)
pulumi.export("log_metric_name", log_metric.name)
