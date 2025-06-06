#!/usr/bin/env python3
"""
Cherry AI Health Monitor - Keeps everything running with best practices
Auto-recovery, alerting, and performance monitoring
"""

import asyncio
import logging
import os
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import docker
import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/health_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("health-monitor")

class HealthMonitor:
    """
    Production-grade health monitor with auto-recovery
    Keeps services running with minimal downtime
    """
    
    def __init__(self):
        self.monitor_interval = int(os.getenv("MONITOR_INTERVAL", "30"))
        self.slack_webhook = os.getenv("SLACK_WEBHOOK")
        self.email_alerts = os.getenv("EMAIL_ALERTS", "").split(",")
        
        # Docker client for container management
        try:
            self.docker_client = docker.from_env()
            logger.info("✅ Docker client connected")
        except Exception as e:
            logger.error(f"❌ Docker client connection failed: {e}")
            self.docker_client = None
        
        # Service definitions with health check endpoints
        self.services = {
            "cherry_ai_postgres_prod": {
                "type": "database",
                "health_check": self._check_postgres,
                "restart_policy": "immediate",
                "max_restarts": 3,
                "restart_count": 0
            },
            "cherry_ai_redis_prod": {
                "type": "cache",
                "health_check": self._check_redis,
                "restart_policy": "immediate",
                "max_restarts": 3,
                "restart_count": 0
            },
            "cherry_ai_weaviate_prod": {
                "type": "vector_db",
                "health_check": self._check_weaviate,
                "restart_policy": "delayed",
                "max_restarts": 2,
                "restart_count": 0
            },
            "cherry_ai_api_prod": {
                "type": "application",
                "health_check": self._check_api,
                "restart_policy": "immediate",
                "max_restarts": 5,
                "restart_count": 0
            },
            "cherry_ai_bridge_prod": {
                "type": "bridge",
                "health_check": self._check_bridge,
                "restart_policy": "immediate",
                "max_restarts": 3,
                "restart_count": 0
            },
            "cherry_ai_nginx_prod": {
                "type": "proxy",
                "health_check": self._check_nginx,
                "restart_policy": "immediate",
                "max_restarts": 3,
                "restart_count": 0
            }
        }
        
        # Health status tracking
        self.service_status = {}
        self.last_alert = {}
        self.system_metrics = {}
        
    async def start_monitoring(self):
        """Start the health monitoring loop"""
        logger.info("🏥 Starting Cherry AI Health Monitor")
        logger.info(f"📊 Monitoring {len(self.services)} services every {self.monitor_interval}s")
        
        # Schedule tasks
        schedule.every(self.monitor_interval).seconds.do(self._run_health_checks)
        schedule.every(5).minutes.do(self._collect_metrics)
        schedule.every(1).hours.do(self._cleanup_logs)
        schedule.every(6).hours.do(self._reset_restart_counters)
        
        # Main monitoring loop
        while True:
            try:
                schedule.run_pending()
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"❌ Monitor loop error: {e}")
                await asyncio.sleep(5)
    
    def _run_health_checks(self):
        """Run health checks for all services"""
        logger.info("🔍 Running health checks...")
        
        for service_name, config in self.services.items():
            try:
                is_healthy = config["health_check"]()
                current_status = "healthy" if is_healthy else "unhealthy"
                previous_status = self.service_status.get(service_name, "unknown")
                
                self.service_status[service_name] = current_status
                
                if current_status == "unhealthy":
                    logger.warning(f"⚠️ {service_name} is unhealthy")
                    asyncio.create_task(self._handle_unhealthy_service(service_name, config))
                elif previous_status == "unhealthy" and current_status == "healthy":
                    logger.info(f"✅ {service_name} recovered")
                    config["restart_count"] = 0  # Reset on recovery
                    asyncio.create_task(self._send_alert(f"🟢 Service Recovered: {service_name}"))
                    
            except Exception as e:
                logger.error(f"❌ Health check failed for {service_name}: {e}")
                self.service_status[service_name] = "error"
    
    async def _handle_unhealthy_service(self, service_name: str, config: Dict):
        """Handle unhealthy service with auto-recovery"""
        restart_policy = config["restart_policy"]
        max_restarts = config["max_restarts"]
        restart_count = config["restart_count"]
        
        if restart_count >= max_restarts:
            logger.error(f"💥 {service_name} exceeded max restarts ({max_restarts})")
            await self._send_alert(f"🔴 CRITICAL: {service_name} exceeded max restarts!")
            return
        
        logger.info(f"🔄 Attempting to restart {service_name} (attempt {restart_count + 1})")
        
        try:
            if restart_policy == "immediate":
                success = await self._restart_service(service_name)
            else:  # delayed
                logger.info(f"⏳ Delaying restart for {service_name}")
                await asyncio.sleep(30)
                success = await self._restart_service(service_name)
            
            if success:
                config["restart_count"] += 1
                await self._send_alert(f"🔄 Service Restarted: {service_name} (attempt {config['restart_count']})")
            else:
                await self._send_alert(f"❌ Failed to restart: {service_name}")
                
        except Exception as e:
            logger.error(f"❌ Restart failed for {service_name}: {e}")
            await self._send_alert(f"💥 Restart error for {service_name}: {e}")
    
    async def _restart_service(self, service_name: str) -> bool:
        """Restart a Docker service"""
        if not self.docker_client:
            return False
        
        try:
            container = self.docker_client.containers.get(service_name)
            container.restart(timeout=60)
            
            # Wait for service to come back up
            await asyncio.sleep(10)
            
            # Verify it's running
            container.reload()
            is_running = container.status == "running"
            
            if is_running:
                logger.info(f"✅ Successfully restarted {service_name}")
            else:
                logger.error(f"❌ {service_name} failed to start after restart")
            
            return is_running
            
        except docker.errors.NotFound:
            logger.error(f"❌ Container {service_name} not found")
            return False
        except Exception as e:
            logger.error(f"❌ Restart error for {service_name}: {e}")
            return False
    
    def _check_postgres(self) -> bool:
        """Check PostgreSQL health"""
        try:
            if not self.docker_client:
                return False
            container = self.docker_client.containers.get("cherry_ai_postgres_prod")
            return container.status == "running"
        except:
            return False
    
    def _check_redis(self) -> bool:
        """Check Redis health"""
        try:
            if not self.docker_client:
                return False
            container = self.docker_client.containers.get("cherry_ai_redis_prod")
            return container.status == "running"
        except:
            return False
    
    def _check_weaviate(self) -> bool:
        """Check Weaviate health"""
        try:
            response = requests.get("http://weaviate:8080/v1/.well-known/ready", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _check_api(self) -> bool:
        """Check API health"""
        try:
            response = requests.get("http://api:8000/api/system/health", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def _check_bridge(self) -> bool:
        """Check AI Bridge health"""
        try:
            response = requests.get("http://ai_bridge:8765/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _check_nginx(self) -> bool:
        """Check Nginx health"""
        try:
            response = requests.get("http://nginx/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _collect_metrics(self):
        """Collect system metrics"""
        try:
            if not self.docker_client:
                return
            
            # Collect container stats
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "services": {}
            }
            
            for service_name in self.services.keys():
                try:
                    container = self.docker_client.containers.get(service_name)
                    stats = container.stats(stream=False)
                    
                    # Calculate CPU percentage
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                               stats['precpu_stats']['cpu_usage']['total_usage']
                    system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                                  stats['precpu_stats']['system_cpu_usage']
                    
                    cpu_percent = 0.0
                    if system_delta > 0:
                        cpu_percent = (cpu_delta / system_delta) * 100.0
                    
                    # Calculate memory usage
                    memory_usage = stats['memory_stats']['usage']
                    memory_limit = stats['memory_stats']['limit']
                    memory_percent = (memory_usage / memory_limit) * 100.0
                    
                    metrics["services"][service_name] = {
                        "status": container.status,
                        "cpu_percent": round(cpu_percent, 2),
                        "memory_percent": round(memory_percent, 2),
                        "memory_usage_mb": round(memory_usage / 1024 / 1024, 2)
                    }
                    
                except Exception as e:
                    logger.warning(f"Failed to collect metrics for {service_name}: {e}")
            
            self.system_metrics = metrics
            
            # Log high resource usage
            for service_name, service_metrics in metrics["services"].items():
                if service_metrics.get("cpu_percent", 0) > 80:
                    logger.warning(f"⚠️ High CPU usage: {service_name} ({service_metrics['cpu_percent']}%)")
                if service_metrics.get("memory_percent", 0) > 80:
                    logger.warning(f"⚠️ High memory usage: {service_name} ({service_metrics['memory_percent']}%)")
            
        except Exception as e:
            logger.error(f"❌ Metrics collection error: {e}")
    
    def _cleanup_logs(self):
        """Cleanup old log files"""
        try:
            log_dir = "/app/logs"
            if os.path.exists(log_dir):
                cutoff_time = time.time() - (7 * 24 * 60 * 60)  # 7 days
                for filename in os.listdir(log_dir):
                    filepath = os.path.join(log_dir, filename)
                    if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff_time:
                        os.remove(filepath)
                        logger.info(f"🗑️ Cleaned up old log: {filename}")
        except Exception as e:
            logger.error(f"❌ Log cleanup error: {e}")
    
    def _reset_restart_counters(self):
        """Reset restart counters periodically"""
        for service_config in self.services.values():
            service_config["restart_count"] = 0
        logger.info("🔄 Reset restart counters")
    
    async def _send_alert(self, message: str):
        """Send alert via Slack/email"""
        try:
            # Rate limiting - don't spam alerts
            alert_key = message[:50]  # First 50 chars as key
            now = time.time()
            
            if alert_key in self.last_alert:
                if now - self.last_alert[alert_key] < 300:  # 5 minutes
                    return
            
            self.last_alert[alert_key] = now
            
            # Send Slack alert
            if self.slack_webhook:
                payload = {
                    "text": f"🚨 Cherry AI Alert: {message}",
                    "username": "Cherry AI Monitor",
                    "icon_emoji": ":rotating_light:"
                }
                
                requests.post(self.slack_webhook, json=payload, timeout=10)
            
            logger.info(f"📢 Alert sent: {message}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send alert: {e}")

# Main entry point
if __name__ == "__main__":
    monitor = HealthMonitor()
    asyncio.run(monitor.start_monitoring()) 