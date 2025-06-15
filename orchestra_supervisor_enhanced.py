#!/usr/bin/env python3
"""
🎼 Orchestra AI Enhanced Production Supervisor

Comprehensive process management for ALL services:
- API Server
- Admin Interface  
- All MCP Servers (Memory, Portkey, Base, Example)
- AI Context Service
- Frontend Services
"""

import asyncio
import subprocess
import psutil
import time
import json
import logging
import signal
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import requests
from dataclasses import dataclass, asdict

# Configure logging with rotation
from logging.handlers import RotatingFileHandler

log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log_file = 'orchestra_supervisor.log'

file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger = logging.getLogger('orchestra_supervisor')
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

@dataclass
class ServiceConfig:
    name: str
    command: List[str]
    cwd: str
    port: int
    health_url: str
    env: Dict[str, str]
    restart_delay: int = 5
    max_restarts: int = 10
    restart_window: int = 300
    required_for_system: bool = True
    dependencies: List[str] = None
    startup_timeout: int = 30
    health_check_retries: int = 5
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass 
class ServiceStatus:
    name: str
    pid: Optional[int] = None
    status: str = "stopped"
    last_started: Optional[datetime] = None
    restart_count: int = 0
    last_restart: Optional[datetime] = None
    health_status: str = "unknown"
    last_health_check: Optional[datetime] = None
    error_message: str = ""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0

class OrchestraEnhancedSupervisor:
    """Enhanced production supervisor for complete Orchestra AI system"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.running = False
        self.services: Dict[str, ServiceConfig] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.status: Dict[str, ServiceStatus] = {}
        
        # Load configuration
        if config_file and Path(config_file).exists():
            self.load_config(config_file)
        else:
            self.create_comprehensive_config()
        
        # Health check intervals
        self.health_check_interval = 30
        self.monitor_interval = 10
        self.metrics_interval = 60
        
        # Signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def create_comprehensive_config(self):
        """Create configuration for ALL Orchestra AI services"""
        base_dir = Path.cwd()
        venv_python = base_dir / "venv" / "bin" / "python"
        
        # Default environment
        default_env = {
            "PYTHONPATH": f"{base_dir}:{base_dir}/api:{base_dir}/mcp_servers:{os.environ.get('PYTHONPATH', '')}",
            "ENVIRONMENT": "production",
            "MAGIC_LIB": "/opt/homebrew/lib/libmagic.dylib",
            "PYTHONDONTWRITEBYTECODE": "1",
            "NODE_ENV": "production"
        }
        
        self.services = {
            # Core MCP Servers
            "mcp_memory": ServiceConfig(
                name="MCP Memory Server",
                command=[str(venv_python), "-m", "uvicorn", "memory_management_server:app", 
                        "--host", "0.0.0.0", "--port", "8003", "--workers", "2"],
                cwd=str(base_dir / "mcp_servers"),
                port=8003,
                health_url="http://localhost:8003/health",
                env=default_env,
                required_for_system=True
            ),
            
            "mcp_portkey": ServiceConfig(
                name="Portkey MCP Server",
                command=[str(venv_python), "-m", "uvicorn", "portkey_mcp:app",
                        "--host", "0.0.0.0", "--port", "8004", "--workers", "2"],
                cwd=str(base_dir / "packages" / "mcp-enhanced"),
                port=8004,
                health_url="http://localhost:8004/health",
                env=default_env,
                required_for_system=True
            ),
            
            # API Server
            "api_server": ServiceConfig(
                name="Orchestra AI API",
                command=[str(venv_python), "-m", "uvicorn", "main:app", 
                        "--host", "0.0.0.0", "--port", "8000", "--workers", "4"],
                cwd=str(base_dir / "api"),
                port=8000,
                health_url="http://localhost:8000/api/health",
                env=default_env,
                dependencies=["mcp_memory", "mcp_portkey"],
                required_for_system=True
            ),
            
            # AI Context Service
            "ai_context": ServiceConfig(
                name="AI Context Service",
                command=[str(venv_python), "context_service.py"],
                cwd=str(base_dir / ".ai-context"),
                port=8005,
                health_url="http://localhost:8005/health",
                env=default_env,
                dependencies=["api_server"],
                required_for_system=False
            ),
            
            # Admin Interface (if running locally)
            "admin_interface": ServiceConfig(
                name="Admin Interface",
                command=["npm", "run", "dev"],
                cwd=str(base_dir / "modern-admin"),
                port=3003,
                health_url="http://localhost:3003",
                env={**default_env, "PORT": "3003"},
                dependencies=["api_server"],
                required_for_system=False
            ),
            
            # Main Frontend
            "frontend": ServiceConfig(
                name="Orchestra Frontend",
                command=["npm", "run", "dev"],
                cwd=str(base_dir / "web"),
                port=3002,
                health_url="http://localhost:3002",
                env={**default_env, "PORT": "3002"},
                dependencies=["api_server"],
                required_for_system=False
            )
        }
        
        # Initialize status for all services
        for service_name in self.services:
            self.status[service_name] = ServiceStatus(name=service_name)
    
    def load_config(self, config_file: str):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            for name, data in config_data.get('services', {}).items():
                self.services[name] = ServiceConfig(**data)
                self.status[name] = ServiceStatus(name=name)
                
        except Exception as e:
            logger.error(f"Failed to load config from {config_file}: {e}")
            self.create_comprehensive_config()
    
    def save_config(self, config_file: str = "orchestra_supervisor_config.json"):
        """Save current configuration"""
        try:
            config_data = {
                'services': {name: asdict(service) for name, service in self.services.items()},
                'health_check_interval': self.health_check_interval,
                'monitor_interval': self.monitor_interval
            }
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"Configuration saved to {config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    async def check_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return False
            return True
        except:
            return True
    
    async def kill_port_process(self, port: int):
        """Kill process listening on a specific port"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    process = psutil.Process(conn.pid)
                    process.terminate()
                    await asyncio.sleep(1)
                    if process.is_running():
                        process.kill()
                    logger.info(f"Killed process on port {port}")
        except Exception as e:
            logger.error(f"Error killing process on port {port}: {e}")
    
    async def start_service(self, service_name: str) -> bool:
        """Start a single service with enhanced error handling"""
        if service_name not in self.services:
            logger.error(f"Unknown service: {service_name}")
            return False
        
        service = self.services[service_name]
        status = self.status[service_name]
        
        # Check dependencies
        for dep in service.dependencies:
            if dep not in self.status or self.status[dep].status != "running":
                logger.warning(f"Dependency {dep} not running for {service_name}")
                return False
        
        # Check port availability
        if not await self.check_port_available(service.port):
            logger.warning(f"Port {service.port} is in use, attempting to free it...")
            await self.kill_port_process(service.port)
            await asyncio.sleep(2)
        
        # Stop existing process if any
        await self.stop_service(service_name)
        
        try:
            logger.info(f"Starting {service.name}...")
            status.status = "starting"
            
            # Prepare environment
            env = os.environ.copy()
            env.update(service.env)
            
            # Create log files
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            stdout_log = open(log_dir / f"{service_name}.log", 'a')
            stderr_log = open(log_dir / f"{service_name}_error.log", 'a')
            
            # Start process
            process = subprocess.Popen(
                service.command,
                cwd=service.cwd,
                env=env,
                stdout=stdout_log,
                stderr=stderr_log,
                preexec_fn=os.setsid
            )
            
            self.processes[service_name] = process
            status.pid = process.pid
            status.last_started = datetime.now()
            
            # Wait for startup with timeout
            start_time = time.time()
            while time.time() - start_time < service.startup_timeout:
                if process.poll() is not None:
                    # Process died during startup
                    status.status = "failed"
                    status.error_message = "Process died during startup"
                    logger.error(f"❌ {service.name} failed to start")
                    return False
                
                # Try health check
                if await self.check_service_health(service_name):
                    status.status = "running"
                    logger.info(f"✅ {service.name} started successfully (PID: {process.pid})")
                    return True
                
                await asyncio.sleep(1)
            
            # Timeout reached
            status.status = "failed"
            status.error_message = "Startup timeout"
            logger.error(f"❌ {service.name} startup timeout")
            return False
            
        except Exception as e:
            status.status = "failed"
            status.error_message = str(e)
            logger.error(f"❌ Failed to start {service.name}: {e}")
            return False
    
    async def check_service_health(self, service_name: str) -> bool:
        """Enhanced health check with retries"""
        service = self.services[service_name]
        status = self.status[service_name]
        
        for attempt in range(service.health_check_retries):
            try:
                response = requests.get(service.health_url, timeout=5)
                if response.status_code == 200:
                    status.health_status = "healthy"
                    status.last_health_check = datetime.now()
                    return True
            except:
                if attempt < service.health_check_retries - 1:
                    await asyncio.sleep(1)
                    continue
        
        status.health_status = "unhealthy"
        return False
    
    async def collect_metrics(self):
        """Collect resource usage metrics"""
        for service_name, process in self.processes.items():
            if process.poll() is None:  # Process is running
                try:
                    proc = psutil.Process(process.pid)
                    self.status[service_name].cpu_percent = proc.cpu_percent(interval=0.1)
                    self.status[service_name].memory_mb = proc.memory_info().rss / 1024 / 1024
                except:
                    pass
    
    async def monitor_services(self):
        """Enhanced monitoring with metrics collection"""
        metrics_last_run = time.time()
        
        while self.running:
            try:
                # Collect metrics periodically
                if time.time() - metrics_last_run > self.metrics_interval:
                    await self.collect_metrics()
                    metrics_last_run = time.time()
                
                # Monitor services
                for service_name, service in self.services.items():
                    status = self.status[service_name]
                    
                    if status.status in ["stopped", "failed"]:
                        continue
                    
                    # Check process
                    if service_name in self.processes:
                        process = self.processes[service_name]
                        if process.poll() is not None:
                            logger.warning(f"⚠️  {service.name} process died")
                            await self.restart_service(service_name)
                            continue
                    
                    # Health check
                    if status.status == "running":
                        is_healthy = await self.check_service_health(service_name)
                        if not is_healthy:
                            logger.warning(f"⚠️  {service.name} health check failed")
                            await self.restart_service(service_name)
                
                await asyncio.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitor_interval)
    
    async def restart_service(self, service_name: str) -> bool:
        """Restart service with enhanced backoff"""
        status = self.status[service_name]
        service = self.services[service_name]
        
        # Check restart limits
        now = datetime.now()
        if status.last_restart and (now - status.last_restart).seconds < service.restart_window:
            if status.restart_count >= service.max_restarts:
                logger.error(f"❌ {service.name} exceeded max restarts")
                status.status = "failed"
                return False
        else:
            status.restart_count = 0
        
        status.status = "restarting"
        status.restart_count += 1
        status.last_restart = now
        
        # Calculate backoff delay
        backoff_delay = min(service.restart_delay * (2 ** (status.restart_count - 1)), 60)
        
        logger.info(f"🔄 Restarting {service.name} (attempt {status.restart_count}, delay {backoff_delay}s)")
        
        await self.stop_service(service_name)
        await asyncio.sleep(backoff_delay)
        
        return await self.start_service(service_name)
    
    async def stop_service(self, service_name: str, timeout: int = 30) -> bool:
        """Stop service gracefully"""
        if service_name not in self.processes:
            return True
        
        process = self.processes[service_name]
        status = self.status[service_name]
        
        try:
            if process.poll() is None:
                logger.info(f"Stopping {self.services[service_name].name}...")
                
                # Terminate process group
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    # Force kill
                    logger.warning(f"Force killing {service_name}")
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    process.wait()
            
            del self.processes[service_name]
            status.status = "stopped"
            status.pid = None
            logger.info(f"✅ {self.services[service_name].name} stopped")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to stop {service_name}: {e}")
            return False
    
    async def start_all_services(self):
        """Start all services in dependency order"""
        logger.info("🎼 Starting Orchestra AI Complete System...")
        
        # Save configuration for reference
        self.save_config()
        
        # Topological sort for dependencies
        started = set()
        to_start = list(self.services.keys())
        
        while to_start:
            progress_made = False
            
            for service_name in to_start[:]:
                service = self.services[service_name]
                
                # Check dependencies
                deps_ready = all(dep in started for dep in service.dependencies)
                
                if deps_ready:
                    success = await self.start_service(service_name)
                    if success:
                        started.add(service_name)
                        to_start.remove(service_name)
                        progress_made = True
                    elif service.required_for_system:
                        logger.error(f"Required service {service_name} failed to start")
                        return False
                    else:
                        # Optional service failed, continue
                        to_start.remove(service_name)
                        progress_made = True
            
            if not progress_made and to_start:
                logger.error("❌ Circular dependency or startup failure")
                return False
            
            await asyncio.sleep(1)
        
        logger.info("✅ All services started successfully")
        return True
    
    async def stop_all_services(self):
        """Stop all services gracefully"""
        logger.info("🛑 Stopping Orchestra AI Services...")
        
        # Stop in reverse dependency order
        service_names = list(self.services.keys())
        service_names.reverse()
        
        for service_name in service_names:
            await self.stop_service(service_name)
        
        logger.info("✅ All services stopped")
    
    def get_status_report(self) -> Dict:
        """Get comprehensive status report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "supervisor_uptime": time.time() - getattr(self, 'start_time', time.time()),
            "services": {}
        }
        
        for name, status in self.status.items():
            service = self.services[name]
            report["services"][name] = {
                "name": service.name,
                "status": status.status,
                "health": status.health_status,
                "pid": status.pid,
                "port": service.port,
                "restart_count": status.restart_count,
                "cpu_percent": status.cpu_percent,
                "memory_mb": status.memory_mb,
                "last_started": status.last_started.isoformat() if status.last_started else None,
                "last_health_check": status.last_health_check.isoformat() if status.last_health_check else None,
                "error_message": status.error_message
            }
        
        return report
    
    def write_status_file(self):
        """Write status to file for external monitoring"""
        try:
            status_file = Path("orchestra_status.json")
            with open(status_file, 'w') as f:
                json.dump(self.get_status_report(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write status file: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def run(self):
        """Main supervisor run loop"""
        self.running = True
        self.start_time = time.time()
        
        logger.info("🎼 Orchestra AI Enhanced Supervisor Starting...")
        logger.info("=" * 50)
        
        # Start all services
        if not await self.start_all_services():
            logger.error("❌ Failed to start all services")
            return False
        
        # Start monitoring
        monitor_task = asyncio.create_task(self.monitor_services())
        
        # Status reporting loop
        try:
            while self.running:
                # Write status file
                self.write_status_file()
                
                # Log summary every 5 minutes
                await asyncio.sleep(300)
                if self.running:
                    report = self.get_status_report()
                    logger.info("📊 Service Status Summary:")
                    logger.info("-" * 40)
                    
                    for name, service_status in report["services"].items():
                        status_icon = "✅" if service_status["status"] == "running" else "❌"
                        health_icon = "💚" if service_status["health"] == "healthy" else "💛"
                        
                        logger.info(
                            f"{status_icon} {name}: {service_status['status']} | "
                            f"{health_icon} Health: {service_status['health']} | "
                            f"CPU: {service_status['cpu_percent']:.1f}% | "
                            f"Memory: {service_status['memory_mb']:.1f}MB"
                        )
        
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        
        finally:
            # Cleanup
            monitor_task.cancel()
            await self.stop_all_services()
            logger.info("🎼 Orchestra AI Supervisor Stopped")
        
        return True

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Orchestra AI Enhanced Supervisor')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    args = parser.parse_args()
    
    # Create supervisor
    supervisor = OrchestraEnhancedSupervisor(args.config)
    
    # Run supervisor
    try:
        asyncio.run(supervisor.run())
    except KeyboardInterrupt:
        logger.info("Supervisor stopped by user")
    except Exception as e:
        logger.error(f"Supervisor failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 