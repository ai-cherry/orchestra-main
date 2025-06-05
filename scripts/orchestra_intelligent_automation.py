#!/usr/bin/env python3
"""
Orchestra Intelligent Automation System
A fully automated, self-configuring orchestration system with zero-maintenance operation
"""

import asyncio
import json
import os
import sys
import time
import subprocess
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import logging
import psutil
import schedule
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/orchestra_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPED = "stopped"
    UNKNOWN = "unknown"


class AutomationMode(Enum):
    """Automation operation modes"""
    FULL_AUTO = "full_auto"
    SEMI_AUTO = "semi_auto"
    MONITORING = "monitoring"
    MAINTENANCE = "maintenance"


@dataclass
class ServiceHealth:
    """Service health information"""
    name: str
    status: ServiceStatus
    last_check: datetime
    error_count: int = 0
    last_error: Optional[str] = None
    auto_restart_count: int = 0


@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    active_connections: int
    response_time_ms: float
    timestamp: datetime


class IntelligentOrchestrator:
    """Intelligent orchestration system with self-healing and auto-configuration"""
    
    def __init__(self):
        self.mode = AutomationMode.FULL_AUTO
        self.services: Dict[str, ServiceHealth] = {}
        self.metrics_history: List[SystemMetrics] = []
        self.running = False
        self.tasks: List[asyncio.Task] = []
        self.config = self._load_config()
        self.patterns = self._initialize_patterns()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load or create intelligent configuration"""
        config_path = Path("config/intelligent_automation.json")
        
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        
        # Default intelligent configuration
        default_config = {
            "mode": "full_auto",
            "health_check_interval": 30,
            "metrics_interval": 60,
            "auto_restart_threshold": 3,
            "self_healing": {
                "enabled": True,
                "max_retries": 5,
                "backoff_multiplier": 2
            },
            "smart_scheduling": {
                "enabled": True,
                "learn_patterns": True,
                "optimize_resources": True
            },
            "services": {
                "postgres": {
                    "priority": 1,
                    "health_endpoint": "pg_isready",
                    "restart_command": "docker-compose -f docker-compose.production.yml restart postgres"
                },
                "redis": {
                    "priority": 2,
                    "health_endpoint": "redis-cli ping",
                    "restart_command": "docker-compose -f docker-compose.production.yml restart redis"
                },
                "weaviate": {
                    "priority": 3,
                    "health_endpoint": "http://localhost:8080/v1/.well-known/ready",
                    "restart_command": "docker-compose -f docker-compose.production.yml restart weaviate",
                    "init_delay": 60
                },
                "mcp_memory": {
                    "priority": 4,
                    "health_endpoint": "http://localhost:8003/health",
                    "start_command": "python3 mcp_server/servers/memory_server.py"
                },
                "mcp_tools": {
                    "priority": 5,
                    "health_endpoint": "http://localhost:8006/health",
                    "start_command": "python3 mcp_server/servers/tools_server.py"
                }
            },
            "triggers": {
                "cpu_high": {"threshold": 80, "action": "scale_up"},
                "memory_high": {"threshold": 85, "action": "optimize_memory"},
                "error_rate_high": {"threshold": 0.05, "action": "investigate_errors"},
                "response_slow": {"threshold": 1000, "action": "optimize_performance"}
            },
            "schedules": {
                "health_check": "*/1 * * * *",
                "cache_warming": "0 */6 * * *",
                "backup": "0 3 * * *",
                "optimization": "0 4 * * 0"
            }
        }
        
        # Save default config
        os.makedirs("config", exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def _initialize_patterns(self) -> Dict[str, Any]:
        """Initialize pattern recognition for intelligent automation"""
        return {
            "usage_patterns": [],
            "error_patterns": {},
            "performance_patterns": {},
            "user_behavior": {}
        }
    
    async def start(self):
        """Start the intelligent orchestration system"""
        logger.info("🚀 Starting Intelligent Orchestra Automation System")
        self.running = True
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Start core services
        await self._ensure_core_services()
        
        # Start automation tasks
        self.tasks = [
            asyncio.create_task(self._health_monitor()),
            asyncio.create_task(self._metrics_collector()),
            asyncio.create_task(self._pattern_analyzer()),
            asyncio.create_task(self._self_optimizer()),
            asyncio.create_task(self._smart_scheduler())
        ]
        
        # Wait for tasks
        await asyncio.gather(*self.tasks, return_exceptions=True)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("Received shutdown signal, stopping gracefully...")
        self.running = False
    
    async def _ensure_core_services(self):
        """Ensure all core services are running"""
        logger.info("Ensuring core services are running...")
        
        # Check Docker services
        compose_file = "docker-compose.production.yml"
        if not Path(compose_file).exists():
            compose_file = "docker-compose.local.yml"
        
        # Start Docker services if not running
        result = subprocess.run(
            ["docker-compose", "-f", compose_file, "ps", "-q"],
            capture_output=True,
            text=True
        )
        
        if not result.stdout.strip():
            logger.info("Starting Docker services...")
            subprocess.run(
                ["docker-compose", "-f", compose_file, "up", "-d"],
                check=True
            )
            await asyncio.sleep(30)  # Wait for services to initialize
        
        # Initialize service health tracking
        for service_name in self.config["services"]:
            self.services[service_name] = ServiceHealth(
                name=service_name,
                status=ServiceStatus.UNKNOWN,
                last_check=datetime.now()
            )
    
    async def _health_monitor(self):
        """Monitor service health and perform self-healing"""
        while self.running:
            try:
                for service_name, service_config in self.config["services"].items():
                    health = await self._check_service_health(service_name, service_config)
                    
                    if health.status == ServiceStatus.UNHEALTHY:
                        if self.config["self_healing"]["enabled"]:
                            await self._heal_service(service_name, service_config)
                
                await asyncio.sleep(self.config["health_check_interval"])
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(10)
    
    async def _check_service_health(self, service_name: str, config: Dict) -> ServiceHealth:
        """Check health of a specific service"""
        health = self.services.get(service_name, ServiceHealth(
            name=service_name,
            status=ServiceStatus.UNKNOWN,
            last_check=datetime.now()
        ))
        
        try:
            if service_name in ["postgres", "redis", "weaviate"]:
                # Check Docker container health
                result = subprocess.run(
                    ["docker", "inspect", f"cherry_ai_{service_name}", "--format", "{{.State.Health.Status}}"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    docker_health = result.stdout.strip()
                    if docker_health == "healthy":
                        health.status = ServiceStatus.HEALTHY
                        health.error_count = 0
                    else:
                        health.status = ServiceStatus.UNHEALTHY
                        health.error_count += 1
                else:
                    health.status = ServiceStatus.STOPPED
                    
            elif service_name.startswith("mcp_"):
                # Check MCP server health
                endpoint = config.get("health_endpoint")
                if endpoint:
                    import aiohttp
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(endpoint, timeout=5) as resp:
                                if resp.status == 200:
                                    health.status = ServiceStatus.HEALTHY
                                    health.error_count = 0
                                else:
                                    health.status = ServiceStatus.UNHEALTHY
                                    health.error_count += 1
                    except Exception as e:
                        logger.error(f"Unexpected error: {e}")
                        health.status = ServiceStatus.UNHEALTHY
                        health.error_count += 1
            
            health.last_check = datetime.now()
            self.services[service_name] = health
            
            if health.status != ServiceStatus.HEALTHY:
                logger.warning(f"Service {service_name} is {health.status.value}")
            
        except Exception as e:
            health.status = ServiceStatus.UNKNOWN
            health.last_error = str(e)
            logger.error(f"Error checking {service_name}: {e}")
        
        return health
    
    async def _heal_service(self, service_name: str, config: Dict):
        """Attempt to heal an unhealthy service"""
        health = self.services[service_name]
        
        if health.auto_restart_count >= self.config["self_healing"]["max_retries"]:
            logger.error(f"Service {service_name} exceeded max restart attempts")
            return
        
        logger.info(f"Attempting to heal {service_name}...")
        
        try:
            if "restart_command" in config:
                # Restart Docker service
                subprocess.run(config["restart_command"].split(), check=True)
                health.auto_restart_count += 1
                
            elif "start_command" in config:
                # Start MCP server
                subprocess.Popen(
                    config["start_command"].split(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                health.auto_restart_count += 1
            
            # Wait for service to stabilize
            await asyncio.sleep(config.get("init_delay", 30))
            
            # Recheck health
            await self._check_service_health(service_name, config)
            
            if self.services[service_name].status == ServiceStatus.HEALTHY:
                logger.info(f"✅ Successfully healed {service_name}")
                health.auto_restart_count = 0
            else:
                logger.warning(f"Failed to heal {service_name}")
                
        except Exception as e:
            logger.error(f"Error healing {service_name}: {e}")
    
    async def _metrics_collector(self):
        """Collect system metrics for intelligent decision making"""
        while self.running:
            try:
                metrics = SystemMetrics(
                    cpu_percent=psutil.cpu_percent(interval=1),
                    memory_percent=psutil.virtual_memory().percent,
                    disk_usage=psutil.disk_usage('/').percent,
                    active_connections=len(psutil.net_connections()),
                    response_time_ms=await self._measure_response_time(),
                    timestamp=datetime.now()
                )
                
                self.metrics_history.append(metrics)
                
                # Keep only last 24 hours of metrics
                cutoff = datetime.now() - timedelta(hours=24)
                self.metrics_history = [m for m in self.metrics_history if m.timestamp > cutoff]
                
                # Check triggers
                await self._check_triggers(metrics)
                
                await asyncio.sleep(self.config["metrics_interval"])
                
            except Exception as e:
                logger.error(f"Metrics collector error: {e}")
                await asyncio.sleep(60)
    
    async def _measure_response_time(self) -> float:
        """Measure average response time of services"""
        # Simplified measurement - in production would test actual endpoints
        return 100.0  # ms
    
    async def _check_triggers(self, metrics: SystemMetrics):
        """Check automated triggers and take action"""
        for trigger_name, trigger_config in self.config["triggers"].items():
            threshold = trigger_config["threshold"]
            action = trigger_config["action"]
            
            triggered = False
            
            if trigger_name == "cpu_high" and metrics.cpu_percent > threshold:
                triggered = True
            elif trigger_name == "memory_high" and metrics.memory_percent > threshold:
                triggered = True
            elif trigger_name == "response_slow" and metrics.response_time_ms > threshold:
                triggered = True
            
            if triggered:
                logger.info(f"Trigger {trigger_name} activated, executing {action}")
                await self._execute_action(action, metrics)
    
    async def _execute_action(self, action: str, metrics: SystemMetrics):
        """Execute automated action based on trigger"""
        if action == "scale_up":
            logger.info("Scaling up resources...")
            # In production: scale containers, adjust limits
            
        elif action == "optimize_memory":
            logger.info("Optimizing memory usage...")
            # Clear caches, restart memory-heavy services
            subprocess.run(["docker", "exec", "cherry_ai_redis", "redis-cli", "FLUSHDB"])
            
        elif action == "optimize_performance":
            logger.info("Optimizing performance...")
            # Run optimization scripts
            if Path("scripts/optimize_mcp_database_architecture.py").exists():
                subprocess.run(["python3", "scripts/optimize_mcp_database_architecture.py"])
    
    async def _pattern_analyzer(self):
        """Analyze patterns for predictive automation"""
        while self.running:
            try:
                # Analyze usage patterns
                if len(self.metrics_history) > 100:
                    await self._analyze_usage_patterns()
                
                # Analyze error patterns
                await self._analyze_error_patterns()
                
                await asyncio.sleep(300)  # Every 5 minutes
                
            except Exception as e:
                logger.error(f"Pattern analyzer error: {e}")
                await asyncio.sleep(300)
    
    async def _analyze_usage_patterns(self):
        """Analyze usage patterns for predictive scaling"""
        # Simple pattern detection - in production would use ML
        recent_metrics = self.metrics_history[-100:]
        
        # Detect peak hours
        hourly_avg = {}
        for metric in recent_metrics:
            hour = metric.timestamp.hour
            if hour not in hourly_avg:
                hourly_avg[hour] = []
            hourly_avg[hour].append(metric.cpu_percent)
        
        # Find peak hours
        peak_hours = sorted(hourly_avg.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True)[:3]
        
        logger.info(f"Detected peak usage hours: {[h[0] for h in peak_hours]}")
        
        # Schedule pre-scaling for peak hours
        for hour, _ in peak_hours:
            schedule.every().day.at(f"{hour-1:02d}:50").do(
                lambda: asyncio.create_task(self._prescale_for_peak())
            )
    
    async def _prescale_for_peak(self):
        """Pre-scale resources before peak usage"""
        logger.info("Pre-scaling for anticipated peak usage...")
        # Warm caches, increase connection pools, etc.
    
    async def _analyze_error_patterns(self):
        """Analyze error patterns for proactive fixes"""
        error_counts = {}
        
        for service_name, health in self.services.items():
            if health.error_count > 0:
                error_counts[service_name] = health.error_count
        
        if error_counts:
            most_errors = max(error_counts.items(), key=lambda x: x[1])
            if most_errors[1] > 5:
                logger.warning(f"Service {most_errors[0]} has frequent errors, investigating...")
                # In production: analyze logs, suggest fixes
    
    async def _self_optimizer(self):
        """Self-optimize based on learned patterns"""
        while self.running:
            try:
                # Optimize configuration based on patterns
                if self.config["smart_scheduling"]["optimize_resources"]:
                    await self._optimize_resources()
                
                # Adjust health check intervals based on stability
                await self._adjust_check_intervals()
                
                await asyncio.sleep(3600)  # Every hour
                
            except Exception as e:
                logger.error(f"Self optimizer error: {e}")
                await asyncio.sleep(3600)
    
    async def _optimize_resources(self):
        """Optimize resource allocation based on usage"""
        if not self.metrics_history:
            return
        
        # Calculate average resource usage
        avg_cpu = sum(m.cpu_percent for m in self.metrics_history) / len(self.metrics_history)
        avg_memory = sum(m.memory_percent for m in self.metrics_history) / len(self.metrics_history)
        
        logger.info(f"Average resource usage - CPU: {avg_cpu:.1f}%, Memory: {avg_memory:.1f}%")
        
        # Adjust Docker resource limits if needed
        if avg_cpu < 30 and avg_memory < 40:
            logger.info("System underutilized, can reduce resource allocation")
        elif avg_cpu > 70 or avg_memory > 80:
            logger.info("System heavily utilized, consider scaling up")
    
    async def _adjust_check_intervals(self):
        """Adjust health check intervals based on system stability"""
        # Count recent errors
        error_count = sum(h.error_count for h in self.services.values())
        
        if error_count == 0:
            # System stable, reduce check frequency
            self.config["health_check_interval"] = min(60, self.config["health_check_interval"] + 5)
            logger.info(f"System stable, health check interval: {self.config['health_check_interval']}s")
        else:
            # System unstable, increase check frequency
            self.config["health_check_interval"] = max(10, self.config["health_check_interval"] - 5)
            logger.info(f"System unstable, health check interval: {self.config['health_check_interval']}s")
    
    async def _smart_scheduler(self):
        """Smart scheduling based on patterns and requirements"""
        while self.running:
            try:
                # Run scheduled tasks
                schedule.run_pending()
                
                # Smart cache warming
                if datetime.now().minute == 0:  # Every hour
                    await self._smart_cache_warming()
                
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Smart scheduler error: {e}")
                await asyncio.sleep(60)
    
    async def _smart_cache_warming(self):
        """Intelligently warm caches based on usage patterns"""
        logger.info("Running smart cache warming...")
        
        # Check if cache warming script exists
        if Path("src/core/cache_warmer.py").exists():
            subprocess.run(["python3", "src/core/cache_warmer.py"])
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        healthy_services = sum(1 for h in self.services.values() if h.status == ServiceStatus.HEALTHY)
        total_services = len(self.services)
        
        latest_metrics = self.metrics_history[-1] if self.metrics_history else None
        
        return {
            "mode": self.mode.value,
            "running": self.running,
            "services": {
                "healthy": healthy_services,
                "total": total_services,
                "details": {k: asdict(v) for k, v in self.services.items()}
            },
            "metrics": asdict(latest_metrics) if latest_metrics else None,
            "uptime": str(datetime.now() - self.start_time) if hasattr(self, 'start_time') else "0:00:00",
            "automation_stats": {
                "auto_heals": sum(h.auto_restart_count for h in self.services.values()),
                "patterns_learned": len(self.patterns["usage_patterns"]),
                "triggers_activated": 0  # Would track this in production
            }
        }


class OrchestraAutomationDaemon:
    """Daemon process for Orchestra automation"""
    
    def __init__(self):
        self.orchestrator = IntelligentOrchestrator()
        self.pidfile = Path("logs/orchestra_automation.pid")
    
    def start(self):
        """Start the daemon"""
        # Check if already running
        if self.pidfile.exists():
            with open(self.pidfile) as f:
                pid = int(f.read())
                if psutil.pid_exists(pid):
                    print(f"Orchestra automation already running (PID: {pid})")
                    return
        
        # Fork and run
        pid = os.fork()
        if pid > 0:
            # Parent process
            with open(self.pidfile, 'w') as f:
                f.write(str(pid))
            print(f"Orchestra automation started (PID: {pid})")
            return
        
        # Child process
        os.setsid()
        os.umask(0)
        
        # Run orchestrator
        self.orchestrator.start_time = datetime.now()
        asyncio.run(self.orchestrator.start())
    
    def stop(self):
        """Stop the daemon"""
        if not self.pidfile.exists():
            print("Orchestra automation not running")
            return
        
        with open(self.pidfile) as f:
            pid = int(f.read())
        
        try:
            os.kill(pid, signal.SIGTERM)
            self.pidfile.unlink()
            print("Orchestra automation stopped")
        except ProcessLookupError:
            print("Orchestra automation not running")
            self.pidfile.unlink()
    
    def status(self):
        """Get daemon status"""
        if not self.pidfile.exists():
            print("Orchestra automation not running")
            return
        
        with open(self.pidfile) as f:
            pid = int(f.read())
        
        if not psutil.pid_exists(pid):
            print("Orchestra automation not running (stale PID file)")
            self.pidfile.unlink()
            return
        
        # Get status from running instance
        # In production, would use IPC or API
        print(f"Orchestra automation running (PID: {pid})")
        
        # Show basic metrics
        process = psutil.Process(pid)
        print(f"  CPU: {process.cpu_percent()}%")
        print(f"  Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
        print(f"  Uptime: {datetime.now() - datetime.fromtimestamp(process.create_time())}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestra Intelligent Automation")
    parser.add_argument('command', choices=['start', 'stop', 'restart', 'status', 'run'],
                       help='Daemon command')
    parser.add_argument('--mode', choices=['full_auto', 'semi_auto', 'monitoring'],
                       default='full_auto', help='Automation mode')
    
    args = parser.parse_args()
    
    daemon = OrchestraAutomationDaemon()
    
    if args.command == 'start':
        daemon.start()
    elif args.command == 'stop':
        daemon.stop()
    elif args.command == 'restart':
        daemon.stop()
        # TODO: Replace with asyncio.sleep() for async code
        time.sleep(2)
        daemon.start()
    elif args.command == 'status':
        daemon.status()
    elif args.command == 'run':
        # Run in foreground
        orchestrator = IntelligentOrchestrator()
        orchestrator.start_time = datetime.now()
        asyncio.run(orchestrator.start())


if __name__ == "__main__":
    main()