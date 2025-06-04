#!/usr/bin/env python3
"""
"""
    """Enhances the monitoring stack with additional metrics and dashboards"""
        """Create enhanced Prometheus configuration"""
        """Create alert rules for critical thresholds"""
                'expr': 'weaviate_api_request_duration_seconds{quantile="0.99"} > 1',
                'for': '5m',
                'labels': {
                    'severity': 'warning',
                    'service': 'weaviate'
                },
                'annotations': {
                    'summary': 'Weaviate API high latency',
                    'description': '99th percentile latency is above 1 second'
                }
            },
            {
                'alert': 'EigenCodeNotResponding',
                'expr': 'up{job="eigencode"} == 0',
                'for': '2m',
                'labels': {
                    'severity': 'critical',
                    'service': 'eigencode'
                },
                'annotations': {
                    'summary': 'EigenCode service is down',
                    'description': 'EigenCode metrics endpoint is not responding'
                }
            },
            {
                'alert': 'HighMemoryUsage',
                'expr': '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.9',
                'for': '5m',
                'labels': {
                    'severity': 'warning',
                    'service': 'system'
                },
                'annotations': {
                    'summary': 'High memory usage detected',
                    'description': 'System memory usage is above 90%'
                }
            },
            {
                'alert': 'DiskSpaceLow',
                'expr': 'node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} < 0.1',
                'for': '5m',
                'labels': {
                    'severity': 'critical',
                    'service': 'system'
                },
                'annotations': {
                    'summary': 'Low disk space',
                    'description': 'Less than 10% disk space remaining on root filesystem'
                }
            }
        ]
        
        return rules
    
    def create_grafana_dashboards(self) -> List[Dict]:
        """Create comprehensive Grafana dashboards"""
            "dashboard": {
                "title": "AI conductor Overview",
                "tags": ["conductor", "overview"],
                "timezone": "browser",
                "panels": [
                    {
                        "title": "Workflow Execution Rate",
                        "type": "graph",
                        "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
                        "targets": [{
                            "expr": "rate(conductor_workflows_total[5m])",
                            "legendFormat": "Workflows/sec"
                        }]
                    },
                    {
                        "title": "Active Workflows",
                        "type": "stat",
                        "gridPos": {"x": 12, "y": 0, "w": 6, "h": 4},
                        "targets": [{
                            "expr": "conductor_active_workflows",
                            "legendFormat": "Active"
                        }]
                    },
                    {
                        "title": "Success Rate",
                        "type": "gauge",
                        "gridPos": {"x": 18, "y": 0, "w": 6, "h": 4},
                        "targets": [{
                            "expr": "rate(conductor_workflows_completed_total[5m]) / rate(conductor_workflows_total[5m]) * 100",
                            "legendFormat": "Success %"
                        }]
                    },
                    {
                        "title": "Task Duration Distribution",
                        "type": "heatmap",
                        "gridPos": {"x": 0, "y": 8, "w": 12, "h": 8},
                        "targets": [{
                            "expr": "conductor_task_duration_seconds_bucket",
                            "format": "heatmap"
                        }]
                    },
                    {
                        "title": "Agent Performance",
                        "type": "graph",
                        "gridPos": {"x": 12, "y": 8, "w": 12, "h": 8},
                        "targets": [
                            {
                                "expr": "rate(conductor_agent_tasks_total{agent='analyzer'}[5m])",
                                "legendFormat": "EigenCode"
                            },
                            {
                                "expr": "rate(conductor_agent_tasks_total{agent='implementer'}[5m])",
                                "legendFormat": "Cursor AI"
                            },
                            {
                                "expr": "rate(conductor_agent_tasks_total{agent='refiner'}[5m])",
                                "legendFormat": "Roo Code"
                            }
                        ]
                    }
                ],
                "refresh": "10s",
                "time": {"from": "now-1h", "to": "now"}
            }
        }
        dashboards.append(conductor_dashboard)
        
        # Database Performance Dashboard
        db_dashboard = {
            "dashboard": {
                "title": "PostgreSQL Performance",
                "tags": ["database", "postgresql"],
                "timezone": "browser",
                "panels": [
                    {
                        "title": "Query Performance",
                        "type": "graph",
                        "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
                        "targets": [{
                            "expr": "rate(pg_stat_database_xact_commit[5m])",
                            "legendFormat": "Commits/sec"
                        }, {
                            "expr": "rate(pg_stat_database_xact_rollback[5m])",
                            "legendFormat": "Rollbacks/sec"
                        }]
                    },
                    {
                        "title": "Connection Pool Usage",
                        "type": "graph",
                        "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
                        "targets": [{
                            "expr": "pg_stat_database_numbackends",
                            "legendFormat": "Active Connections"
                        }, {
                            "expr": "pg_settings_max_connections",
                            "legendFormat": "Max Connections"
                        }]
                    },
                    {
                        "title": "Cache Hit Ratio",
                        "type": "stat",
                        "gridPos": {"x": 0, "y": 8, "w": 6, "h": 4},
                        "targets": [{
                            "expr": "pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read) * 100",
                            "legendFormat": "Cache Hit %"
                        }]
                    },
                    {
                        "title": "Slow Queries",
                        "type": "table",
                        "gridPos": {"x": 6, "y": 8, "w": 18, "h": 8},
                        "targets": [{
                            "expr": "topk(10, pg_stat_statements_mean_exec_time)",
                            "format": "table"
                        }]
                    }
                ]
            }
        }
        dashboards.append(db_dashboard)
        
        # Weaviate Performance Dashboard
        weaviate_dashboard = {
            "dashboard": {
                "title": "Weaviate Vector Store Performance",
                "tags": ["weaviate", "vector"],
                "timezone": "browser",
                "panels": [
                    {
                        "title": "API Request Rate",
                        "type": "graph",
                        "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
                        "targets": [{
                            "expr": "rate(weaviate_api_requests_total[5m])",
                            "legendFormat": "{{method}} {{path}}"
                        }]
                    },
                    {
                        "title": "Request Latency",
                        "type": "graph",
                        "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
                        "targets": [
                            {
                                "expr": "weaviate_api_request_duration_seconds{quantile='0.5'}",
                                "legendFormat": "p50"
                            },
                            {
                                "expr": "weaviate_api_request_duration_seconds{quantile='0.95'}",
                                "legendFormat": "p95"
                            },
                            {
                                "expr": "weaviate_api_request_duration_seconds{quantile='0.99'}",
                                "legendFormat": "p99"
                            }
                        ]
                    },
                    {
                        "title": "Object Count by Class",
                        "type": "stat",
                        "gridPos": {"x": 0, "y": 8, "w": 8, "h": 4},
                        "targets": [{
                            "expr": "weaviate_objects_total",
                            "legendFormat": "{{class_name}}"
                        }]
                    },
                    {
                        "title": "Vector Index Performance",
                        "type": "graph",
                        "gridPos": {"x": 8, "y": 8, "w": 16, "h": 8},
                        "targets": [{
                            "expr": "rate(weaviate_vector_index_operations_total[5m])",
                            "legendFormat": "{{operation}}"
                        }]
                    }
                ]
            }
        }
        dashboards.append(weaviate_dashboard)
        
        # System Overview Dashboard
        system_dashboard = {
            "dashboard": {
                "title": "System Overview",
                "tags": ["system", "infrastructure"],
                "timezone": "browser",
                "panels": [
                    {
                        "title": "CPU Usage",
                        "type": "graph",
                        "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
                        "targets": [{
                            "expr": "100 - (avg(irate(node_cpu_seconds_total{mode='idle'}[5m])) * 100)",
                            "legendFormat": "CPU Usage %"
                        }]
                    },
                    {
                        "title": "Memory Usage",
                        "type": "graph",
                        "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
                        "targets": [{
                            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
                            "legendFormat": "Memory Usage %"
                        }]
                    },
                    {
                        "title": "Disk I/O",
                        "type": "graph",
                        "gridPos": {"x": 0, "y": 8, "w": 12, "h": 8},
                        "targets": [
                            {
                                "expr": "rate(node_disk_read_bytes_total[5m])",
                                "legendFormat": "Read {{device}}"
                            },
                            {
                                "expr": "rate(node_disk_written_bytes_total[5m])",
                                "legendFormat": "Write {{device}}"
                            }
                        ]
                    },
                    {
                        "title": "Network Traffic",
                        "type": "graph",
                        "gridPos": {"x": 12, "y": 8, "w": 12, "h": 8},
                        "targets": [
                            {
                                "expr": "rate(node_network_receive_bytes_total[5m])",
                                "legendFormat": "RX {{device}}"
                            },
                            {
                                "expr": "rate(node_network_transmit_bytes_total[5m])",
                                "legendFormat": "TX {{device}}"
                            }
                        ]
                    }
                ]
            }
        }
        dashboards.append(system_dashboard)
        
        return dashboards
    
    def setup_postgres_exporter(self) -> Dict:
        """Configure PostgreSQL exporter"""
            "data_source_name": f"postgresql://{os.environ.get('POSTGRES_USER')}:{os.environ.get('POSTGRES_PASSWORD')}@{os.environ.get('POSTGRES_HOST')}:{os.environ.get('POSTGRES_PORT', 5432)}/{os.environ.get('POSTGRES_DB')}?sslmode=require",
            "auto_discover_databases": True,
            "exclude_databases": ["template0", "template1"],
            "metric_prefix": "pg",
            "disable_default_metrics": False,
            "disable_settings_metrics": False,
            "custom_queries": {
                "coordination_metrics": {
                    "query": """
                    """
                    "metrics": [
                        {
                            "task_count": {
                                "usage": "GAUGE",
                                "description": "Number of tasks in workflow"
                            }
                        },
                        {
                            "completed_tasks": {
                                "usage": "GAUGE",
                                "description": "Number of completed tasks"
                            }
                        },
                        {
                            "failed_tasks": {
                                "usage": "GAUGE",
                                "description": "Number of failed tasks"
                            }
                        }
                    ]
                }
            }
        }
        
        return config
    
    def deploy_monitoring_stack(self) -> Dict:
        """Deploy the enhanced monitoring configuration"""
            "prometheus": False,
            "grafana": False,
            "exporters": {},
            "alerts": False
        }
        
        # Save Prometheus configuration
        prometheus_config = self.create_prometheus_config()
        config_path = Path("/etc/prometheus/prometheus.yml")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(prometheus_config, f)
        
        results["prometheus"] = True
        
        # Save alert rules
        alert_rules = {
            'groups': [{
                'name': 'conductor_alerts',
                'interval': '30s',
                'rules': self.create_alert_rules()
            }]
        }
        
        alerts_path = Path("/etc/prometheus/alerts/conductor.yml")
        alerts_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(alerts_path, 'w') as f:
            yaml.dump(alert_rules, f)
        
        results["alerts"] = True
        
        # Deploy Grafana dashboards
        try:

            pass
            headers = {
                'Authorization': f'Bearer {self.grafana_api_key}',
                'Content-Type': 'application/json'
            }
            
            for dashboard in self.create_grafana_dashboards():
                response = requests.post(
                    f"{self.grafana_url}/api/dashboards/db",
                    headers=headers,
                    json=dashboard
                , timeout=30)
                
                if response.status_code == 200:
                    results["grafana"] = True
        except Exception:

            pass
            print(f"Failed to deploy Grafana dashboards: {e}")
        
        # Configure exporters
        # PostgreSQL exporter
        pg_exporter_config = self.setup_postgres_exporter()
        pg_config_path = Path("/etc/postgres_exporter/config.yml")
        pg_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(pg_config_path, 'w') as f:
            yaml.dump(pg_exporter_config, f)
        
        results["exporters"]["postgres"] = True
        
        # Log deployment to database
        self.db_logger.log_action(
            workflow_id="monitoring_deployment",
            task_id="deploy_stack",
            agent_role="monitoring",
            action="deploy_monitoring",
            status="completed",
            metadata=results
        )
        
        return results
    
    def create_custom_metrics_endpoint(self) -> str:
        """Create custom metrics endpoint for conductor"""
        metrics_path = Path("ai_components/monitoring/metrics_endpoint.py")
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(metrics_path, 'w') as f:
            f.write(metrics_code)
        
        return str(metrics_path)
    
    def verify_monitoring_stack(self) -> Dict:
        """Verify monitoring stack functionality"""
            "prometheus": {"status": False, "metrics": 0},
            "grafana": {"status": False, "dashboards": 0},
            "exporters": {},
            "alerts": {"configured": 0, "firing": 0}
        }
        
        # Check Prometheus
        try:

            pass
            response = requests.get(f"{self.prometheus_url}/api/v1/targets", timeout=30)
            if response.status_code == 200:
                data = response.json()
                active_targets = [t for t in data.get('data', {}).get('activeTargets', []) if t['health'] == 'up']
                verification["prometheus"]["status"] = True
                verification["prometheus"]["metrics"] = len(active_targets)
        except Exception:

            pass
            pass
        
        # Check Grafana
        try:

            pass
            headers = {'Authorization': f'Bearer {self.grafana_api_key}'}
            response = requests.get(f"{self.grafana_url}/api/dashboards", headers=headers, timeout=30)
            if response.status_code == 200:
                verification["grafana"]["status"] = True
                verification["grafana"]["dashboards"] = len(response.json())
        except Exception:

            pass
            pass
        
        # Check alerts
        try:

            pass
            response = requests.get(f"{self.prometheus_url}/api/v1/rules", timeout=30)
            if response.status_code == 200:
                data = response.json()
                for group in data.get('data', {}).get('groups', []):
                    verification["alerts"]["configured"] += len(group.get('rules', []))
                    for rule in group.get('rules', []):
                        if rule.get('state') == 'firing':
                            verification["alerts"]["firing"] += 1
        except Exception:

            pass
            pass
        
        return verification


def main():
    """Main function"""
    print("Enhancing Monitoring Stack for AI conductor")
    print("=" * 50)
    
    # Deploy enhanced monitoring
    print("\nDeploying monitoring configuration...")
    deployment_results = enhancer.deploy_monitoring_stack()
    
    print("\nDeployment Results:")
    for component, status in deployment_results.items():
        if isinstance(status, dict):
            print(f"  {component}:")
            for sub_component, sub_status in status.items():
                print(f"    {sub_component}: {'✓' if sub_status else '✗'}")
        else:
            print(f"  {component}: {'✓' if status else '✗'}")
    
    # Create custom metrics endpoint
    print("\nCreating custom metrics endpoint...")
    metrics_path = enhancer.create_custom_metrics_endpoint()
    print(f"  Metrics endpoint created at: {metrics_path}")
    
    # Verify deployment
    print("\nVerifying monitoring stack...")
    verification = enhancer.verify_monitoring_stack()
    
    print("\nVerification Results:")
    print(f"  Prometheus: {'✓' if verification['prometheus']['status'] else '✗'} ({verification['prometheus']['metrics']} active targets)")
    print(f"  Grafana: {'✓' if verification['grafana']['status'] else '✗'} ({verification['grafana']['dashboards']} dashboards)")
    print(f"  Alerts: {verification['alerts']['configured']} configured, {verification['alerts']['firing']} firing")
    
    # Save configuration summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "deployment": deployment_results,
        "verification": verification,
        "dashboards": [d["dashboard"]["title"] for d in enhancer.create_grafana_dashboards()],
        "alert_rules": len(enhancer.create_alert_rules())
    }
    
    with open("monitoring_enhancement_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary saved to: monitoring_enhancement_summary.json")
    
    # Store in Weaviate
    enhancer.weaviate_manager.store_context(
        workflow_id="monitoring_enhancement",
        task_id="deployment",
        context_type="monitoring_config",
        content=json.dumps(summary),
        metadata={"timestamp": summary["timestamp"]}
    )


if __name__ == "__main__":
    main()