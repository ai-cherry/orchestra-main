"""
Pulumi GCP Infrastructure Stack for Orchestra AI

- Modular, Python-based Pulumi stack for reproducible, high-performance GCP environments.
- Provisions VPC, subnets, IAM, Cloud Run, Redis, AlloyDB, Secret Manager, Artifact Registry, and monitoring.
- Designed for extensibility, automation, and optimal performance.

Author: Orchestra AI Platform
"""

import pulumi
import pulumi_gcp as gcp

# --- CONFIGURATION ---
config = pulumi.Config()
project = config.require("project")
region = config.get("region") or "us-central1"
image_tag = config.get("image_tag") or "latest"
network_name = "orchestra-vpc"
subnet_name = "orchestra-subnet"
redis_instance_name = "orchestra-redis"
alloydb_instance_name = "orchestra-alloydb"
cloud_run_api_service_name = "ai-orchestra-minimal"
cloud_run_admin_service_name = "admin-interface"
cloud_run_webscraping_service_name = "web-scraping-agents"
artifact_registry_name = "orchestra-repo"
service_directory_namespace = "orchestra-ai"

# --- VPC & SUBNET ---
network = gcp.compute.Network(
    network_name,
    auto_create_subnetworks=False,
    project=project,
)

subnet = gcp.compute.Subnetwork(
    subnet_name,
    ip_cidr_range="10.10.0.0/16",
    region=region,
    network=network.id,
    project=project,
)

# --- ARTIFACT REGISTRY ---
artifact_registry = gcp.artifactregistry.Repository(
    artifact_registry_name,
    repository_id=artifact_registry_name,
    format="DOCKER",
    location=region,
    project=project,
)

# --- SERVICE ACCOUNTS (LEAST PRIVILEGE) ---
# Main orchestrator service account
orchestrator_sa = gcp.serviceaccount.Account(
    "orchestra-orchestrator-sa",
    account_id="orchestra-orchestrator-sa",
    display_name="Orchestra Orchestrator Service Account",
    project=project,
)

# Web scraping service account
webscraping_sa = gcp.serviceaccount.Account(
    "orchestra-webscraping-sa",
    account_id="orchestra-webscraping-sa",
    display_name="Orchestra Web Scraping Service Account",
    project=project,
)

# Admin interface service account
admin_sa = gcp.serviceaccount.Account(
    "orchestra-admin-sa",
    account_id="orchestra-admin-sa",
    display_name="Orchestra Admin Service Account",
    project=project,
)

# --- IAM ROLES (LEAST PRIVILEGE) ---
# Orchestrator SA roles
orchestrator_roles = [
    "roles/run.invoker",
    "roles/secretmanager.secretAccessor",
    "roles/datastore.user",
    "roles/pubsub.publisher",
    "roles/pubsub.subscriber",
    "roles/servicedirectory.editor",
    "roles/redis.editor",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent",
    "roles/logging.logWriter",
]

for role in orchestrator_roles:
    gcp.projects.IAMMember(
        f"orchestrator-sa-{role.replace('/', '-').replace('.', '-')}",
        project=project,
        role=role,
        member=orchestrator_sa.email.apply(lambda email: f"serviceAccount:{email}"),
    )

# Web scraping SA roles
webscraping_roles = [
    "roles/run.invoker",
    "roles/secretmanager.secretAccessor",
    "roles/redis.editor",
    "roles/pubsub.publisher",
    "roles/servicedirectory.viewer",
    "roles/monitoring.metricWriter",
    "roles/logging.logWriter",
]

for role in webscraping_roles:
    gcp.projects.IAMMember(
        f"webscraping-sa-{role.replace('/', '-').replace('.', '-')}",
        project=project,
        role=role,
        member=webscraping_sa.email.apply(lambda email: f"serviceAccount:{email}"),
    )

# Admin SA roles
admin_roles = [
    "roles/secretmanager.secretAccessor",
    "roles/datastore.viewer",
    "roles/monitoring.viewer",
    "roles/logging.viewer",
    "roles/servicedirectory.viewer",
]

for role in admin_roles:
    gcp.projects.IAMMember(
        f"admin-sa-{role.replace('/', '-').replace('.', '-')}",
        project=project,
        role=role,
        member=admin_sa.email.apply(lambda email: f"serviceAccount:{email}"),
    )

# --- PUB/SUB TOPICS ---
# Main MCP events topic
mcp_events_topic = gcp.pubsub.Topic(
    "mcp-events",
    project=project,
    message_retention_duration="604800s",  # 7 days
)

# Web scraping events topic
webscraping_events_topic = gcp.pubsub.Topic(
    "web-scraping-events",
    project=project,
    message_retention_duration="86400s",  # 1 day
)

# Dead letter topic for failed messages
dead_letter_topic = gcp.pubsub.Topic(
    "mcp-dead-letter",
    project=project,
    message_retention_duration="2592000s",  # 30 days
)

# --- PUB/SUB SUBSCRIPTIONS ---
# MCP events subscription
mcp_events_subscription = gcp.pubsub.Subscription(
    "mcp-events-sub",
    topic=mcp_events_topic.name,
    ack_deadline_seconds=60,
    message_retention_duration="604800s",
    retain_acked_messages=True,
    dead_letter_policy={
        "dead_letter_topic": dead_letter_topic.id,
        "max_delivery_attempts": 5,
    },
    project=project,
)

# Web scraping events subscription
webscraping_events_subscription = gcp.pubsub.Subscription(
    "web-scraping-events-sub",
    topic=webscraping_events_topic.name,
    ack_deadline_seconds=120,
    message_retention_duration="86400s",
    project=project,
)

# --- SERVICE DIRECTORY ---
# Create namespace
service_directory_namespace = gcp.servicedirectory.Namespace(
    "orchestra-ai-namespace",
    namespace_id=service_directory_namespace,
    location=region,
    project=project,
)

# --- REDIS (MEMORYSTORE) ---
redis = gcp.redis.Instance(
    redis_instance_name,
    tier="STANDARD_HA",
    memory_size_gb=4,
    region=region,
    authorized_network=network.id,
    redis_version="REDIS_7_0",
    display_name="Orchestra Redis Cache",
    replica_count=1,
    read_replicas_mode="READ_REPLICAS_ENABLED",
    transit_encryption_mode="SERVER_AUTHENTICATION",
    project=project,
)

# --- SECRET MANAGER ---
# API Keys
api_key_secret = gcp.secretmanager.Secret(
    "orchestra-api-key",
    replication={"automatic": {}},
    project=project,
)

# Web scraping API keys
zenrows_secret = gcp.secretmanager.Secret(
    "zenrows-api-key",
    secret_id="ZENROWS_API_KEY",
    replication={"automatic": {}},
    project=project,
)

apify_secret = gcp.secretmanager.Secret(
    "apify-api-key",
    secret_id="APIFY_API_KEY",
    replication={"automatic": {}},
    project=project,
)

phantombuster_secret = gcp.secretmanager.Secret(
    "phantombuster-api-key",
    secret_id="PHANTOMBUSTER_API_KEY",
    replication={"automatic": {}},
    project=project,
)

# --- CLOUD RUN SERVICES ---

# Orchestra API Service
orchestra_api_service = gcp.cloudrun.Service(
    cloud_run_api_service_name,
    location=region,
    template={
        "metadata": {
            "annotations": {
                "autoscaling.knative.dev/maxScale": "10",
                "autoscaling.knative.dev/minScale": "0",
                "run.googleapis.com/execution-environment": "gen2",
                "run.googleapis.com/cpu-throttling": "false",
            }
        },
        "spec": {
            "containers": [
                {
                    "image": f"us-central1-docker.pkg.dev/{project}/orchestra-images/orchestra-main:{image_tag}",
                    "envs": [
                        {"name": "GOOGLE_CLOUD_PROJECT", "value": project},
                        {"name": "REDIS_HOST", "valueFrom": {"secretKeyRef": {"name": "REDIS_HOST", "key": "latest"}}},
                        {
                            "name": "DRAGONFLY_HOST",
                            "valueFrom": {"secretKeyRef": {"name": "DRAGONFLY_HOST", "key": "latest"}},
                        },
                        {"name": "SERVICE_DIRECTORY_NAMESPACE", "value": service_directory_namespace},
                        {"name": "PUBSUB_TOPIC_MCP_EVENTS", "value": mcp_events_topic.name},
                    ],
                    "ports": [{"containerPort": 8080}],
                    "resources": {"limits": {"cpu": "2", "memory": "4Gi"}, "requests": {"cpu": "1", "memory": "2Gi"}},
                    "startupProbe": {
                        "httpGet": {"path": "/health", "port": 8080},
                        "initialDelaySeconds": 30,
                        "timeoutSeconds": 5,
                        "periodSeconds": 10,
                        "failureThreshold": 3,
                    },
                    "livenessProbe": {
                        "httpGet": {"path": "/health", "port": 8080},
                        "periodSeconds": 30,
                        "timeoutSeconds": 10,
                    },
                }
            ],
            "serviceAccountName": orchestrator_sa.email,
            "containerConcurrency": 80,
            "timeoutSeconds": 300,
        },
    },
    traffics=[{"percent": 100, "latestRevision": True}],
    project=project,
)

# Web Scraping Agents Service
web_scraping_service = gcp.cloudrun.Service(
    cloud_run_webscraping_service_name,
    location=region,
    template={
        "metadata": {
            "annotations": {
                "autoscaling.knative.dev/maxScale": "20",
                "autoscaling.knative.dev/minScale": "1",
                "run.googleapis.com/execution-environment": "gen2",
                "run.googleapis.com/cpu-throttling": "false",
            }
        },
        "spec": {
            "containers": [
                {
                    "image": f"us-central1-docker.pkg.dev/{project}/orchestra-images/web-scraping-agents:{image_tag}",
                    "envs": [
                        {"name": "GOOGLE_CLOUD_PROJECT", "value": project},
                        {"name": "REDIS_HOST", "valueFrom": {"secretKeyRef": {"name": "REDIS_HOST", "key": "latest"}}},
                        {"name": "REDIS_PORT", "value": "6379"},
                        {"name": "SEARCH_AGENTS", "value": "3"},
                        {"name": "SCRAPER_AGENTS", "value": "5"},
                        {"name": "ANALYZER_AGENTS", "value": "3"},
                        {
                            "name": "ZENROWS_API_KEY",
                            "valueFrom": {"secretKeyRef": {"name": "ZENROWS_API_KEY", "key": "latest"}},
                        },
                        {
                            "name": "APIFY_API_KEY",
                            "valueFrom": {"secretKeyRef": {"name": "APIFY_API_KEY", "key": "latest"}},
                        },
                        {
                            "name": "PHANTOMBUSTER_API_KEY",
                            "valueFrom": {"secretKeyRef": {"name": "PHANTOMBUSTER_API_KEY", "key": "latest"}},
                        },
                        {
                            "name": "OPENAI_API_KEY",
                            "valueFrom": {"secretKeyRef": {"name": "OPENAI_API_KEY", "key": "latest"}},
                        },
                        {"name": "PUBSUB_TOPIC_WEBSCRAPING", "value": webscraping_events_topic.name},
                    ],
                    "ports": [{"containerPort": 8080}],
                    "resources": {"limits": {"cpu": "4", "memory": "8Gi"}, "requests": {"cpu": "2", "memory": "4Gi"}},
                    "startupProbe": {
                        "httpGet": {"path": "/health", "port": 8080},
                        "initialDelaySeconds": 60,
                        "timeoutSeconds": 10,
                        "periodSeconds": 15,
                        "failureThreshold": 5,
                    },
                    "livenessProbe": {
                        "httpGet": {"path": "/health", "port": 8080},
                        "periodSeconds": 60,
                        "timeoutSeconds": 15,
                    },
                }
            ],
            "serviceAccountName": webscraping_sa.email,
            "containerConcurrency": 40,
            "timeoutSeconds": 900,
        },
    },
    traffics=[{"percent": 100, "latestRevision": True}],
    project=project,
)

# Admin Interface Service
admin_interface_service = gcp.cloudrun.Service(
    cloud_run_admin_service_name,
    location=region,
    template={
        "metadata": {
            "annotations": {
                "autoscaling.knative.dev/maxScale": "5",
                "autoscaling.knative.dev/minScale": "0",
                "run.googleapis.com/execution-environment": "gen2",
            }
        },
        "spec": {
            "containers": [
                {
                    "image": f"us-central1-docker.pkg.dev/{project}/orchestra-images/admin-interface:{image_tag}",
                    "envs": [
                        {"name": "GOOGLE_CLOUD_PROJECT", "value": project},
                        {"name": "SERVICE_DIRECTORY_NAMESPACE", "value": service_directory_namespace},
                    ],
                    "ports": [{"containerPort": 8080}],
                    "resources": {"limits": {"cpu": "2", "memory": "2Gi"}, "requests": {"cpu": "1", "memory": "1Gi"}},
                    "startupProbe": {
                        "httpGet": {"path": "/", "port": 8080},
                        "initialDelaySeconds": 20,
                        "timeoutSeconds": 5,
                    },
                    "livenessProbe": {"httpGet": {"path": "/", "port": 8080}, "periodSeconds": 30},
                }
            ],
            "serviceAccountName": admin_sa.email,
            "containerConcurrency": 100,
        },
    },
    traffics=[{"percent": 100, "latestRevision": True}],
    project=project,
)

# --- MONITORING & ALERTING ---

# Uptime checks for each service
orchestra_uptime_check = gcp.monitoring.UptimeCheckConfig(
    "orchestra-api-uptime",
    display_name="Orchestra API Uptime Check",
    monitored_resource={
        "type": "uptime_url",
        "labels": {
            "host": orchestra_api_service.statuses[0].url.apply(
                lambda url: url.replace("https://", "").replace("http://", "")
            ),
            "project_id": project,
        },
    },
    http_check={
        "path": "/health",
        "port": 443,
        "request_method": "GET",
        "use_ssl": True,
        "validate_ssl": True,
    },
    timeout="10s",
    period="60s",
)

webscraping_uptime_check = gcp.monitoring.UptimeCheckConfig(
    "webscraping-uptime",
    display_name="Web Scraping Service Uptime Check",
    monitored_resource={
        "type": "uptime_url",
        "labels": {
            "host": web_scraping_service.statuses[0].url.apply(
                lambda url: url.replace("https://", "").replace("http://", "")
            ),
            "project_id": project,
        },
    },
    http_check={
        "path": "/health",
        "port": 443,
        "request_method": "GET",
        "use_ssl": True,
        "validate_ssl": True,
    },
    timeout="10s",
    period="60s",
)

# Alert policies
error_rate_alert_policy = gcp.monitoring.AlertPolicy(
    "high-error-rate",
    display_name="High Error Rate Alert",
    conditions=[
        {
            "display_name": "Error rate exceeds 5%",
            "condition_threshold": {
                "filter": 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count" AND metric.labels.response_code_class!="2xx"',
                "comparison": "COMPARISON_GT",
                "threshold_value": 0.05,
                "duration": "300s",
                "aggregations": [
                    {
                        "alignment_period": "60s",
                        "per_series_aligner": "ALIGN_RATE",
                        "cross_series_reducer": "REDUCE_SUM",
                        "group_by_fields": ["resource.label.service_name"],
                    }
                ],
            },
        }
    ],
    notification_channels=[],  # Add notification channel IDs here
    alert_strategy={
        "auto_close": "1800s",
    },
)

memory_usage_alert_policy = gcp.monitoring.AlertPolicy(
    "high-memory-usage",
    display_name="High Memory Usage Alert",
    conditions=[
        {
            "display_name": "Memory usage exceeds 90%",
            "condition_threshold": {
                "filter": 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/container/memory/utilizations"',
                "comparison": "COMPARISON_GT",
                "threshold_value": 0.9,
                "duration": "300s",
                "aggregations": [
                    {
                        "alignment_period": "60s",
                        "per_series_aligner": "ALIGN_MEAN",
                    }
                ],
            },
        }
    ],
    notification_channels=[],  # Add notification channel IDs here
)

# Log-based metrics
error_log_metric = gcp.logging.Metric(
    "mcp-server-errors",
    description="Count of MCP server errors",
    filter='resource.type="cloud_run_revision" AND severity="ERROR" AND jsonPayload.source=~"mcp-.*"',
    metric_descriptor={
        "metric_kind": "DELTA",
        "value_type": "INT64",
        "labels": [
            {
                "key": "service",
                "value_type": "STRING",
                "description": "The service that generated the error",
            },
            {
                "key": "error_type",
                "value_type": "STRING",
                "description": "The type of error",
            },
        ],
    },
    label_extractors={
        "service": "EXTRACT(jsonPayload.source)",
        "error_type": "EXTRACT(jsonPayload.error_type)",
    },
)

# Dashboard
dashboard_json = {
    "displayName": "Orchestra AI Dashboard",
    "mosaicLayout": {
        "columns": 12,
        "tiles": [
            {
                "width": 4,
                "height": 4,
                "widget": {
                    "title": "Request Rate",
                    "xyChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count"',
                                        "aggregation": {
                                            "alignmentPeriod": "60s",
                                            "perSeriesAligner": "ALIGN_RATE",
                                            "crossSeriesReducer": "REDUCE_SUM",
                                            "groupByFields": ["resource.label.service_name"],
                                        },
                                    },
                                },
                            }
                        ],
                    },
                },
            },
            {
                "xPos": 4,
                "width": 4,
                "height": 4,
                "widget": {
                    "title": "Error Rate",
                    "xyChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": 'resource.type="cloud_run_revision" AND metric.type="logging.googleapis.com/user/mcp-server-errors"',
                                        "aggregation": {
                                            "alignmentPeriod": "60s",
                                            "perSeriesAligner": "ALIGN_RATE",
                                        },
                                    },
                                },
                            }
                        ],
                    },
                },
            },
            {
                "xPos": 8,
                "width": 4,
                "height": 4,
                "widget": {
                    "title": "Memory Usage",
                    "xyChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/container/memory/utilizations"',
                                        "aggregation": {
                                            "alignmentPeriod": "60s",
                                            "perSeriesAligner": "ALIGN_MEAN",
                                            "groupByFields": ["resource.label.service_name"],
                                        },
                                    },
                                },
                            }
                        ],
                    },
                },
            },
        ],
    },
}

monitoring_dashboard = gcp.monitoring.Dashboard(
    "orchestra-dashboard",
    dashboard_json=pulumi.Output.json_dumps(dashboard_json),
    project=project,
)

# --- OUTPUTS ---
pulumi.export("network", network.id)
pulumi.export("subnet", subnet.id)
pulumi.export("orchestrator_service_account", orchestrator_sa.email)
pulumi.export("webscraping_service_account", webscraping_sa.email)
pulumi.export("admin_service_account", admin_sa.email)
pulumi.export("redis_instance", redis.id)
pulumi.export("redis_host", redis.host)
pulumi.export("api_key_secret", api_key_secret.id)
pulumi.export("artifact_registry", artifact_registry.id)
pulumi.export("orchestra_api_url", orchestra_api_service.statuses[0].url)
pulumi.export("admin_interface_url", admin_interface_service.statuses[0].url)
pulumi.export("web_scraping_url", web_scraping_service.statuses[0].url)
pulumi.export("mcp_events_topic", mcp_events_topic.name)
pulumi.export("webscraping_events_topic", webscraping_events_topic.name)
pulumi.export("service_directory_namespace", service_directory_namespace.name)
pulumi.export(
    "dashboard_url",
    pulumi.Output.concat(
        "https://console.cloud.google.com/monitoring/dashboards/custom/", monitoring_dashboard.id, "?project=", project
    ),
)
