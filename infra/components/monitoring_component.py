"""
Monitoring Component for SuperAGI
================================
Deploys Prometheus, Grafana, and alerting infrastructure
"""

from typing import Optional

import pulumi_kubernetes as k8s
from pulumi import ComponentResource, Output, ResourceOptions


class MonitoringComponent(ComponentResource):
    """Monitoring stack with Prometheus, Grafana, and alerting"""

    def __init__(
        self,
        name: str,
        namespace: str,
        storage_class: str = "standard",
        grafana_admin_password: Optional[str] = None,
        opts: Optional[ResourceOptions] = None,
    ):
        super().__init__("orchestra:monitoring:Stack", name, {}, opts)

        # Create monitoring namespace
        monitoring_ns = k8s.core.v1.Namespace(
            f"{name}-namespace",
            metadata=k8s.meta.v1.ObjectMetaArgs(name=namespace, labels={"name": namespace, "monitoring": "true"}),
            opts=ResourceOptions(parent=self),
        )

        # Prometheus ConfigMap
        prometheus_config = k8s.core.v1.ConfigMap(
            f"{name}-prometheus-config",
            metadata=k8s.meta.v1.ObjectMetaArgs(name="prometheus-config", namespace=namespace),
            data={
                "prometheus.yml": """
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - '/etc/prometheus/rules/*.yml'

scrape_configs:
  - job_name: 'kubernetes-apiservers'
    kubernetes_sd_configs:
      - role: endpoints
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https

  - job_name: 'kubernetes-nodes'
    kubernetes_sd_configs:
      - role: node
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)

  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: r'\1'
        replacement: $1:$2
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: kubernetes_pod_name

  - job_name: 'superagi'
    static_configs:
      - targets: ['superagi.superagi.svc.cluster.local:8080']
    metrics_path: '/metrics'

  - job_name: 'dragonfly'
    static_configs:
      - targets: ['dragonfly.superagi.svc.cluster.local:6379']
"""
            },
            opts=ResourceOptions(parent=self, depends_on=[monitoring_ns]),
        )

        # Alerting rules ConfigMap
        alerting_rules = k8s.core.v1.ConfigMap(
            f"{name}-alerting-rules",
            metadata=k8s.meta.v1.ObjectMetaArgs(name="alerting-rules", namespace=namespace),
            data={
                "alerts.yml": """
groups:
  - name: superagi_alerts
    interval: 30s
    rules:
      - alert: HighAgentErrorRate
        expr: rate(superagi_agent_executions_total{status="failed"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate in agent executions"
          description: "Error rate is {{ $value }} errors per second"

      - alert: DragonflyHighMemoryUsage
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "DragonflyDB memory usage above 90%"
          description: "Memory usage is {{ $value }}%"

      - alert: SuperAGIPodNotReady
        expr: kube_deployment_status_replicas_ready{deployment="superagi"} < kube_deployment_spec_replicas{deployment="superagi"}
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "SuperAGI pods not ready"
          description: "Only {{ $value }} replicas are ready"

      - alert: HighAgentExecutionLatency
        expr: histogram_quantile(0.95, rate(superagi_execution_duration_seconds_bucket[5m])) > 30
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High agent execution latency"
          description: "95th percentile latency is {{ $value }} seconds"
"""
            },
            opts=ResourceOptions(parent=self, depends_on=[monitoring_ns]),
        )

        # Prometheus RBAC
        prometheus_sa = k8s.core.v1.ServiceAccount(
            f"{name}-prometheus-sa",
            metadata=k8s.meta.v1.ObjectMetaArgs(name="prometheus", namespace=namespace),
            opts=ResourceOptions(parent=self, depends_on=[monitoring_ns]),
        )

        prometheus_cluster_role = k8s.rbac.v1.ClusterRole(
            f"{name}-prometheus-role",
            metadata=k8s.meta.v1.ObjectMetaArgs(name="prometheus"),
            rules=[
                k8s.rbac.v1.PolicyRuleArgs(
                    api_groups=[""],
                    resources=["nodes", "nodes/proxy", "services", "endpoints", "pods"],
                    verbs=["get", "list", "watch"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    api_groups=["extensions"],
                    resources=["ingresses"],
                    verbs=["get", "list", "watch"],
                ),
            ],
            opts=ResourceOptions(parent=self),
        )

        prometheus_cluster_role_binding = k8s.rbac.v1.ClusterRoleBinding(
            f"{name}-prometheus-binding",
            metadata=k8s.meta.v1.ObjectMetaArgs(name="prometheus"),
            role_ref=k8s.rbac.v1.RoleRefArgs(
                api_group="rbac.authorization.k8s.io",
                kind="ClusterRole",
                name="prometheus",
            ),
            subjects=[k8s.rbac.v1.SubjectArgs(kind="ServiceAccount", name="prometheus", namespace=namespace)],
            opts=ResourceOptions(parent=self, depends_on=[prometheus_sa, prometheus_cluster_role]),
        )

        # Prometheus PVC
        prometheus_pvc = k8s.core.v1.PersistentVolumeClaim(
            f"{name}-prometheus-pvc",
            metadata=k8s.meta.v1.ObjectMetaArgs(name="prometheus-data", namespace=namespace),
            spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
                access_modes=["ReadWriteOnce"],
                storage_class_name=storage_class,
                resources=k8s.core.v1.ResourceRequirementsArgs(requests={"storage": "50Gi"}),
            ),
            opts=ResourceOptions(parent=self, depends_on=[monitoring_ns]),
        )

        # Prometheus Deployment
        prometheus_deployment = k8s.apps.v1.Deployment(
            f"{name}-prometheus",
            metadata=k8s.meta.v1.ObjectMetaArgs(name="prometheus", namespace=namespace, labels={"app": "prometheus"}),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                replicas=1,
                selector=k8s.meta.v1.LabelSelectorArgs(match_labels={"app": "prometheus"}),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(
                        labels={"app": "prometheus"},
                        annotations={
                            "prometheus.io/scrape": "true",
                            "prometheus.io/port": "9090",
                        },
                    ),
                    spec=k8s.core.v1.PodSpecArgs(
                        service_account_name="prometheus",
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name="prometheus",
                                image="prom/prometheus:v2.45.0",
                                args=[
                                    "--config.file=/etc/prometheus/prometheus.yml",
                                    "--storage.tsdb.path=/prometheus",
                                    "--web.console.libraries=/usr/share/prometheus/console_libraries",
                                    "--web.console.templates=/usr/share/prometheus/consoles",
                                    "--web.enable-lifecycle",
                                    "--storage.tsdb.retention.time=30d",
                                ],
                                ports=[k8s.core.v1.ContainerPortArgs(container_port=9090, name="web")],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(name="config", mount_path="/etc/prometheus"),
                                    k8s.core.v1.VolumeMountArgs(name="rules", mount_path="/etc/prometheus/rules"),
                                    k8s.core.v1.VolumeMountArgs(name="data", mount_path="/prometheus"),
                                ],
                                resources=k8s.core.v1.ResourceRequirementsArgs(
                                    requests={"memory": "1Gi", "cpu": "500m"},
                                    limits={"memory": "2Gi", "cpu": "1"},
                                ),
                            )
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name="config",
                                config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(name="prometheus-config"),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name="rules",
                                config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(name="alerting-rules"),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name="data",
                                persistent_volume_claim=k8s.core.v1.PersistentVolumeClaimVolumeSourceArgs(
                                    claim_name="prometheus-data"
                                ),
                            ),
                        ],
                    ),
                ),
            ),
            opts=ResourceOptions(
                parent=self,
                depends_on=[
                    prometheus_config,
                    alerting_rules,
                    prometheus_pvc,
                    prometheus_cluster_role_binding,
                ],
            ),
        )

        # Prometheus Service
        prometheus_service = k8s.core.v1.Service(
            f"{name}-prometheus-service",
            metadata=k8s.meta.v1.ObjectMetaArgs(name="prometheus", namespace=namespace, labels={"app": "prometheus"}),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector={"app": "prometheus"},
                ports=[k8s.core.v1.ServicePortArgs(port=9090, target_port=9090, name="web")],
                type="ClusterIP",
            ),
            opts=ResourceOptions(parent=self, depends_on=[prometheus_deployment]),
        )

        # Grafana ConfigMap
        grafana_config = k8s.core.v1.ConfigMap(
            f"{name}-grafana-config",
            metadata=k8s.meta.v1.ObjectMetaArgs(name="grafana-config", namespace=namespace),
            data={
                "grafana.ini": """
[server]
root_url = %(protocol)s://%(domain)s:%(http_port)s/

[security]
admin_password = ${GRAFANA_ADMIN_PASSWORD}

[auth.anonymous]
enabled = true
org_role = Viewer

[dashboards]
default_home_dashboard_path = /var/lib/grafana/dashboards/superagi-dashboard.json
""",
                "datasources.yaml": """
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
""",
            },
            opts=ResourceOptions(parent=self, depends_on=[monitoring_ns]),
        )

        # Grafana Dashboard ConfigMap
        grafana_dashboards = k8s.core.v1.ConfigMap(
            f"{name}-grafana-dashboards",
            metadata=k8s.meta.v1.ObjectMetaArgs(name="grafana-dashboards", namespace=namespace),
            data={"superagi-dashboard.json": self._get_grafana_dashboard()},
            opts=ResourceOptions(parent=self, depends_on=[monitoring_ns]),
        )

        # Grafana Deployment
        grafana_deployment = k8s.apps.v1.Deployment(
            f"{name}-grafana",
            metadata=k8s.meta.v1.ObjectMetaArgs(name="grafana", namespace=namespace, labels={"app": "grafana"}),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                replicas=1,
                selector=k8s.meta.v1.LabelSelectorArgs(match_labels={"app": "grafana"}),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(labels={"app": "grafana"}),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name="grafana",
                                image="grafana/grafana:10.0.0",
                                ports=[k8s.core.v1.ContainerPortArgs(container_port=3000, name="web")],
                                env=[
                                    k8s.core.v1.EnvVarArgs(
                                        name="GRAFANA_ADMIN_PASSWORD",
                                        value=grafana_admin_password or "admin",
                                    )
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(name="config", mount_path="/etc/grafana"),
                                    k8s.core.v1.VolumeMountArgs(
                                        name="datasources",
                                        mount_path="/etc/grafana/provisioning/datasources",
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name="dashboards",
                                        mount_path="/var/lib/grafana/dashboards",
                                    ),
                                ],
                                resources=k8s.core.v1.ResourceRequirementsArgs(
                                    requests={"memory": "256Mi", "cpu": "100m"},
                                    limits={"memory": "512Mi", "cpu": "200m"},
                                ),
                            )
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name="config",
                                config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(name="grafana-config"),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name="datasources",
                                config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(
                                    name="grafana-config",
                                    items=[
                                        k8s.core.v1.KeyToPathArgs(
                                            key="datasources.yaml",
                                            path="datasources.yaml",
                                        )
                                    ],
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name="dashboards",
                                config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(name="grafana-dashboards"),
                            ),
                        ],
                    ),
                ),
            ),
            opts=ResourceOptions(parent=self, depends_on=[grafana_config, grafana_dashboards]),
        )

        # Grafana Service
        grafana_service = k8s.core.v1.Service(
            f"{name}-grafana-service",
            metadata=k8s.meta.v1.ObjectMetaArgs(name="grafana", namespace=namespace, labels={"app": "grafana"}),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector={"app": "grafana"},
                ports=[k8s.core.v1.ServicePortArgs(port=3000, target_port=3000, name="web")],
                type="LoadBalancer",
            ),
            opts=ResourceOptions(parent=self, depends_on=[grafana_deployment]),
        )

        # Export endpoints
        self.prometheus_endpoint = Output.concat("http://", prometheus_service.metadata.name, ":", "9090")
        self.grafana_endpoint = grafana_service.status.apply(
            lambda status: (
                f"http://{status.load_balancer.ingress[0].ip}:3000" if status.load_balancer.ingress else "pending"
            )
        )

        self.register_outputs(
            {
                "prometheus_endpoint": self.prometheus_endpoint,
                "grafana_endpoint": self.grafana_endpoint,
                "namespace": namespace,
            }
        )

    def _get_grafana_dashboard(self) -> str:
        """Return the SuperAGI monitoring dashboard JSON"""
        return """{
  "dashboard": {
    "id": null,
    "uid": "superagi-monitoring",
    "title": "SuperAGI Monitoring",
    "tags": ["superagi", "ai", "agents"],
    "timezone": "browser",
    "schemaVersion": 38,
    "version": 1,
    "refresh": "10s",
    "panels": [
      {
        "id": 1,
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "type": "graph",
        "title": "Agent Execution Rate",
        "targets": [
          {
            "expr": "rate(superagi_agent_executions_total[5m])",
            "legendFormat": "{{agent_id}} - {{status}}"
          }
        ]
      },
      {
        "id": 2,
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "type": "graph",
        "title": "Execution Duration (95th percentile)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(superagi_execution_duration_seconds_bucket[5m]))",
            "legendFormat": "{{agent_id}}"
          }
        ]
      },
      {
        "id": 3,
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
        "type": "graph",
        "title": "DragonflyDB Memory Usage",
        "targets": [
          {
            "expr": "redis_memory_used_bytes",
            "legendFormat": "Used"
          },
          {
            "expr": "redis_memory_max_bytes",
            "legendFormat": "Max"
          }
        ]
      },
      {
        "id": 4,
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
        "type": "graph",
        "title": "Pod CPU Usage",
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total{namespace='superagi'}[5m])",
            "legendFormat": "{{pod}}"
          }
        ]
      },
      {
        "id": 5,
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 16},
        "type": "stat",
        "title": "Total Agents",
        "targets": [
          {
            "expr": "count(count by (agent_id)(superagi_agent_executions_total))"
          }
        ]
      },
      {
        "id": 6,
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 16},
        "type": "stat",
        "title": "Success Rate",
        "targets": [
          {
            "expr": "sum(rate(superagi_agent_executions_total{status='success'}[5m])) / sum(rate(superagi_agent_executions_total[5m])) * 100"
          }
        ],
        "options": {
          "unit": "percent"
        }
      },
      {
        "id": 7,
        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 16},
        "type": "stat",
        "title": "Active Connections",
        "targets": [
          {
            "expr": "redis_connected_clients"
          }
        ]
      },
      {
        "id": 8,
        "gridPos": {"h": 4, "w": 6, "x": 18, "y": 16},
        "type": "stat",
        "title": "Ready Pods",
        "targets": [
          {
            "expr": "kube_deployment_status_replicas_ready{deployment='superagi'}"
          }
        ]
      }
    ]
  }
}"""
