"""
Enhanced monitoring and alerting system
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import aiohttp
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import json

logger = logging.getLogger(__name__)

# Prometheus metrics
request_count = Counter('ai_orchestration_requests_total',
                       'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('ai_orchestration_request_duration_seconds',
                           'Request duration', ['method', 'endpoint'])
active_agents_gauge = Gauge('ai_orchestration_active_agents',
                          'Number of active agents', ['domain'])
error_count = Counter('ai_orchestration_errors_total',
                     'Total errors', ['error_type', 'component'])
queue_size = Gauge('ai_orchestration_queue_size',
                  'Agent queue size')

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self):
        self.alert_thresholds = {
            "error_rate": 0.05,  # 5% error rate
            "response_time_p95": 2.0,  # 2 seconds
            "cpu_usage": 80,  # 80%
            "memory_usage": 85,  # 85%
            "queue_size": 100
        }
        self.alert_history = []
        self.webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        
    async def check_alerts(self, metrics: Dict[str, Any]):
        """Check metrics against thresholds and send alerts"""
        alerts = []
        
        # Check error rate
        if metrics.get("error_rate", 0) > self.alert_thresholds["error_rate"]:
            alerts.append({
                "severity": "HIGH",
                "type": "ERROR_RATE",
                "message": f"Error rate {metrics['error_rate']:.2%} exceeds threshold",
                "value": metrics["error_rate"]
            })
            
        # Check response time
        if metrics.get("response_time_p95", 0) > self.alert_thresholds["response_time_p95"]:
            alerts.append({
                "severity": "MEDIUM",
                "type": "RESPONSE_TIME",
                "message": f"P95 response time {metrics['response_time_p95']:.2f}s exceeds threshold",
                "value": metrics["response_time_p95"]
            })
            
        # Check resource usage
        if metrics.get("cpu_usage", 0) > self.alert_thresholds["cpu_usage"]:
            alerts.append({
                "severity": "HIGH",
                "type": "CPU_USAGE",
                "message": f"CPU usage {metrics['cpu_usage']:.1f}% exceeds threshold",
                "value": metrics["cpu_usage"]
            })
            
        # Send alerts
        for alert in alerts:
            await self.send_alert(alert)
            
    async def send_alert(self, alert: Dict[str, Any]):
        """Send alert via webhook"""
        alert["timestamp"] = datetime.now().isoformat()
        self.alert_history.append(alert)
        
        if self.webhook_url:
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post(self.webhook_url, json=alert)
                logger.info(f"Alert sent: {alert['type']} - {alert['message']}")
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")
        else:
            logger.warning(f"Alert (no webhook configured): {alert}")

class MetricsCollector:
    """Collects and aggregates system metrics"""
    
    def __init__(self):
        self.metrics_buffer = []
        self.collection_interval = 60  # seconds
        
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        from core.resource_management import resource_manager
        
        # Get system health
        health = resource_manager.get_system_health()
        
        # Calculate error rate from recent requests
        error_rate = self._calculate_error_rate()
        
        # Get response time percentiles
        response_times = self._get_response_time_percentiles()
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "active_agents": health["active_agents"],
            "queued_agents": health["queued_agents"],
            "cpu_usage": health["cpu_percent"],
            "memory_usage": health["memory_percent"],
            "error_rate": error_rate,
            "response_time_p50": response_times.get("p50", 0),
            "response_time_p95": response_times.get("p95", 0),
            "response_time_p99": response_times.get("p99", 0),
            "health_status": health["health_status"]
        }
        
        # Update Prometheus metrics
        queue_size.set(health["queued_agents"])
        
        return metrics
        
    def _calculate_error_rate(self) -> float:
        """Calculate error rate from recent requests"""
        # This would query actual metrics from database
        # Placeholder implementation
        return 0.02  # 2% error rate
        
    def _get_response_time_percentiles(self) -> Dict[str, float]:
        """Get response time percentiles"""
        # Placeholder implementation
        return {
            "p50": 0.5,
            "p95": 1.5,
            "p99": 2.5
        }

# Global instances
alert_manager = AlertManager()
metrics_collector = MetricsCollector()

async def start_monitoring():
    """Start the monitoring loop"""
    while True:
        try:
            metrics = await metrics_collector.collect_metrics()
            await alert_manager.check_alerts(metrics)
            await asyncio.sleep(metrics_collector.collection_interval)
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            await asyncio.sleep(60)
