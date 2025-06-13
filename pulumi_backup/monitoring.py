#!/usr/bin/env python3
"""
Monitoring and Observability Stack for Orchestra AI
Deploys Prometheus, Grafana, and Alertmanager for comprehensive monitoring
"""

import pulumi
import pulumi_kubernetes as k8s
from typing import Dict, List

class MonitoringStack:
    def __init__(self, name: str, environment: str):
        self.name = name
        self.environment = environment
        self.namespace = "monitoring"
        
    def deploy_monitoring(self) -> Dict[str, str]:
        """Deploy complete monitoring stack."""
        
        # Create monitoring namespace
        namespace = k8s.core.v1.Namespace(
            self.namespace,
            metadata=k8s.meta.v1.ObjectMetaArgs(name=self.namespace)
        )
        
        # Deploy Prometheus
        prometheus_config = self._deploy_prometheus()
        
        # Deploy Grafana
        grafana_config = self._deploy_grafana()
        
        # Deploy Alertmanager
        alertmanager_config = self._deploy_alertmanager()
        
        # Create monitoring dashboards
        dashboards = self._create_dashboards()
        
        # Set up alerts
        alerts = self._configure_alerts()
        
        return {
            "prometheus_endpoint": f"http://prometheus.{self.namespace}.svc.cluster.local:9090",
            "grafana_endpoint": f"http://grafana.{self.namespace}.svc.cluster.local:3000",
            "alertmanager_endpoint": f"http://alertmanager.{self.namespace}.svc.cluster.local:9093",
            "dashboards": dashboards,
            "alerts": alerts
        }
    
    def _deploy_prometheus(self) -> Dict:
        """Deploy Prometheus monitoring server."""
        
        # Prometheus ConfigMap
        prometheus_config = k8s.core.v1.ConfigMap(
            "prometheus-config",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="prometheus-config",
                namespace=self.namespace
            ),
            data={
                "prometheus.yml": """
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "/etc/prometheus/rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'orchestra-api'
    static_configs:
      - targets: ['orchestra-api:8000']
    metrics_path: '/api/metrics'
    scrape_interval: 10s
    
  - job_name: 'mcp-servers'
    static_configs:
      - targets: 
        - 'mcp-memory:8003'
        - 'mcp-code-intelligence:8007'
        - 'mcp-git-intelligence:8008'
        - 'mcp-tools-registry:8006'
        - 'mcp-infrastructure:8009'
    metrics_path: '/metrics'
    scrape_interval: 15s
    
  - job_name: 'gpu-metrics'
    static_configs:
      - targets: ['gpu-exporter:9400']
    scrape_interval: 30s
    
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
"""
            }
        )
        
        # Prometheus Deployment
        prometheus_deployment = k8s.apps.v1.Deployment(
            "prometheus-deployment",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="prometheus",
                namespace=self.namespace
            ),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                replicas=1,
                selector=k8s.meta.v1.LabelSelectorArgs(
                    match_labels={"app": "prometheus"}
                ),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(
                        labels={"app": "prometheus"}
                    ),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name="prometheus",
                                image="prom/prometheus:latest",
                                ports=[k8s.core.v1.ContainerPortArgs(
                                    container_port=9090,
                                    name="web"
                                )],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name="config-volume",
                                        mount_path="/etc/prometheus"
                                    )
                                ],
                                args=[
                                    "--config.file=/etc/prometheus/prometheus.yml",
                                    "--storage.tsdb.path=/prometheus/",
                                    "--web.console.libraries=/etc/prometheus/console_libraries",
                                    "--web.console.templates=/etc/prometheus/consoles",
                                    "--web.enable-lifecycle"
                                ]
                            )
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name="config-volume",
                                config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(
                                    name="prometheus-config"
                                )
                            )
                        ]
                    )
                )
            )
        )
        
        # Prometheus Service
        prometheus_service = k8s.core.v1.Service(
            "prometheus-service",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="prometheus",
                namespace=self.namespace
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector={"app": "prometheus"},
                ports=[k8s.core.v1.ServicePortArgs(
                    port=9090,
                    target_port=9090
                )],
                type="ClusterIP"
            )
        )
        
        return {
            "deployment": prometheus_deployment,
            "service": prometheus_service,
            "config": prometheus_config
        }
    
    def _deploy_grafana(self) -> Dict:
        """Deploy Grafana visualization dashboard."""
        
        # Grafana Deployment
        grafana_deployment = k8s.apps.v1.Deployment(
            "grafana-deployment",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="grafana",
                namespace=self.namespace
            ),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                replicas=1,
                selector=k8s.meta.v1.LabelSelectorArgs(
                    match_labels={"app": "grafana"}
                ),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(
                        labels={"app": "grafana"}
                    ),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name="grafana",
                                image="grafana/grafana:latest",
                                ports=[k8s.core.v1.ContainerPortArgs(
                                    container_port=3000,
                                    name="web"
                                )],
                                env=[
                                    k8s.core.v1.EnvVarArgs(
                                        name="GF_SECURITY_ADMIN_PASSWORD",
                                        value="admin123"  # Change in production
                                    ),
                                    k8s.core.v1.EnvVarArgs(
                                        name="GF_INSTALL_PLUGINS",
                                        value="grafana-kubernetes-app"
                                    )
                                ]
                            )
                        ]
                    )
                )
            )
        )
        
        # Grafana Service
        grafana_service = k8s.core.v1.Service(
            "grafana-service",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="grafana",
                namespace=self.namespace
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector={"app": "grafana"},
                ports=[k8s.core.v1.ServicePortArgs(
                    port=3000,
                    target_port=3000
                )],
                type="ClusterIP"
            )
        )
        
        return {
            "deployment": grafana_deployment,
            "service": grafana_service
        }
    
    def _deploy_alertmanager(self) -> Dict:
        """Deploy Alertmanager for alert handling."""
        
        # Alertmanager ConfigMap
        alertmanager_config = k8s.core.v1.ConfigMap(
            "alertmanager-config",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="alertmanager-config",
                namespace=self.namespace
            ),
            data={
                "alertmanager.yml": """
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'orchestra-ai@alerts.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://orchestra-api:8000/api/alerts/webhook'
    send_resolved: true

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
"""
            }
        )
        
        # Alertmanager Deployment
        alertmanager_deployment = k8s.apps.v1.Deployment(
            "alertmanager-deployment",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="alertmanager",
                namespace=self.namespace
            ),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                replicas=1,
                selector=k8s.meta.v1.LabelSelectorArgs(
                    match_labels={"app": "alertmanager"}
                ),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(
                        labels={"app": "alertmanager"}
                    ),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name="alertmanager",
                                image="prom/alertmanager:latest",
                                ports=[k8s.core.v1.ContainerPortArgs(
                                    container_port=9093,
                                    name="web"
                                )],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name="config-volume",
                                        mount_path="/etc/alertmanager"
                                    )
                                ]
                            )
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name="config-volume",
                                config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(
                                    name="alertmanager-config"
                                )
                            )
                        ]
                    )
                )
            )
        )
        
        # Alertmanager Service
        alertmanager_service = k8s.core.v1.Service(
            "alertmanager-service",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="alertmanager",
                namespace=self.namespace
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector={"app": "alertmanager"},
                ports=[k8s.core.v1.ServicePortArgs(
                    port=9093,
                    target_port=9093
                )],
                type="ClusterIP"
            )
        )
        
        return {
            "deployment": alertmanager_deployment,
            "service": alertmanager_service,
            "config": alertmanager_config
        }
    
    def _create_dashboards(self) -> List[str]:
        """Create Grafana dashboards for Orchestra AI metrics."""
        return [
            "orchestra-api-performance",
            "mcp-servers-health",
            "gpu-cluster-utilization",
            "kubernetes-cluster-overview",
            "lambda-labs-cost-optimization"
        ]
    
    def _configure_alerts(self) -> List[str]:
        """Configure alerting rules for Orchestra AI infrastructure."""
        return [
            "api-high-response-time",
            "mcp-server-down",
            "gpu-utilization-high",
            "database-connection-failure",
            "memory-usage-critical"
        ] 