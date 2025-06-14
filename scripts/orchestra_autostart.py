#!/usr/bin/env python3
"""
Orchestra AI Autostart Manager
Automatically runs all necessary scripts and services
"""

import os
import sys
import subprocess
import time
import signal
import json
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import asyncio
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/autostart.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OrchestraAutostart:
    """Manages automatic startup of all Orchestra AI services"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.processes: Dict[str, subprocess.Popen] = {}
        self.config = self.load_config()
        
    def load_config(self) -> dict:
        """Load autostart configuration"""
        config_path = self.project_root / "orchestra_autostart.json"
        
        if not config_path.exists():
            # Create default configuration
            default_config = {
                "services": {
                    "ai_context": {
                        "name": "AI Context Loader",
                        "command": "python scripts/setup_ai_agents.py --update-context",
                        "type": "oneshot",
                        "enabled": True,
                        "priority": 1
                    },
                    "api": {
                        "name": "API Server",
                        "command": "./start_api.sh",
                        "type": "daemon",
                        "enabled": True,
                        "priority": 2,
                        "health_check": "http://localhost:8000/health",
                        "startup_delay": 3
                    },
                    "frontend": {
                        "name": "Frontend Server",
                        "command": "./start_frontend.sh",
                        "type": "daemon",
                        "enabled": True,
                        "priority": 3,
                        "health_check": "http://localhost:3000",
                        "startup_delay": 2
                    },
                    "mcp_memory": {
                        "name": "MCP Memory Server",
                        "command": "./start_mcp_memory_server.sh start",
                        "type": "daemon",
                        "enabled": True,
                        "priority": 4,
                        "health_check": "http://localhost:8003/health",
                        "startup_delay": 2
                    },
                    "monitor": {
                        "name": "System Monitor",
                        "command": "./monitor_orchestra.sh",
                        "type": "periodic",
                        "enabled": True,
                        "priority": 5,
                        "interval": 300  # 5 minutes
                    }
                },
                "startup_checks": {
                    "check_dependencies": True,
                    "check_ports": True,
                    "check_database": True
                },
                "restart_policy": {
                    "max_retries": 3,
                    "retry_delay": 10,
                    "backoff_multiplier": 2
                }
            }
            
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            logger.info(f"Created default configuration at {config_path}")
            return default_config
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def check_dependencies(self) -> bool:
        """Check if all dependencies are installed"""
        logger.info("Checking dependencies...")
        
        checks = {
            "Python 3.11+": self.check_python_version(),
            "Virtual Environment": (self.project_root / "venv").exists(),
            "Node.js": self.check_command_exists("node"),
            "npm": self.check_command_exists("npm"),
            "Docker": self.check_command_exists("docker"),
        }
        
        all_ok = True
        for name, status in checks.items():
            if status:
                logger.info(f"✅ {name}")
            else:
                logger.error(f"❌ {name}")
                all_ok = False
        
        return all_ok
    
    def check_python_version(self) -> bool:
        """Check if Python version is 3.11+"""
        version = sys.version_info
        return version.major == 3 and version.minor >= 11
    
    def check_command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH"""
        try:
            subprocess.run([command, "--version"], 
                         capture_output=True, 
                         check=False)
            return True
        except FileNotFoundError:
            return False
    
    def check_ports(self) -> Dict[int, bool]:
        """Check if required ports are available"""
        ports = {
            8000: "API Server",
            3000: "Frontend",
            8003: "MCP Memory Server",
            5432: "PostgreSQL",
            6379: "Redis"
        }
        
        results = {}
        for port, service in ports.items():
            if self.is_port_in_use(port):
                logger.warning(f"Port {port} ({service}) is already in use")
                results[port] = False
            else:
                logger.info(f"Port {port} ({service}) is available")
                results[port] = True
        
        return results
    
    def is_port_in_use(self, port: int) -> bool:
        """Check if a port is in use"""
        try:
            # Try using psutil first
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return True
            return False
        except (psutil.AccessDenied, PermissionError):
            # Fallback for macOS permission issues - test by trying to bind
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('', port))
                sock.close()
                return False
            except OSError:
                return True
    
    def setup_environment(self):
        """Setup environment variables"""
        logger.info("Setting up environment...")
        
        env_vars = {
            "PYTHONPATH": f"{self.project_root}:{self.project_root}/api",
            "ORCHESTRA_AI_ENV": "development",
            "DATABASE_URL": "postgresql+asyncpg://postgres:password@localhost:5432/orchestra_ai",
            "REDIS_URL": "redis://localhost:6379",
            "NODE_ENV": "development"
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value
            logger.info(f"Set {key}")
    
    def run_oneshot_service(self, service_id: str, config: dict):
        """Run a one-shot service (runs once and exits)"""
        logger.info(f"Running one-shot service: {config['name']}")
        
        try:
            result = subprocess.run(
                config['command'],
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {config['name']} completed successfully")
            else:
                logger.error(f"❌ {config['name']} failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Failed to run {config['name']}: {e}")
    
    def start_daemon_service(self, service_id: str, config: dict):
        """Start a daemon service"""
        logger.info(f"Starting daemon service: {config['name']}")
        
        try:
            # Check if already running
            if service_id in self.processes and self.processes[service_id].poll() is None:
                logger.info(f"{config['name']} is already running")
                return
            
            # Start the process
            process = subprocess.Popen(
                config['command'],
                shell=True,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            self.processes[service_id] = process
            
            # Wait for startup
            if 'startup_delay' in config:
                time.sleep(config['startup_delay'])
            
            # Check health if configured
            if 'health_check' in config:
                if self.check_health(config['health_check']):
                    logger.info(f"✅ {config['name']} started successfully")
                else:
                    logger.warning(f"⚠️ {config['name']} started but health check failed")
            else:
                logger.info(f"✅ {config['name']} started")
                
        except Exception as e:
            logger.error(f"Failed to start {config['name']}: {e}")
    
    def check_health(self, url: str, timeout: int = 10) -> bool:
        """Check service health via HTTP endpoint"""
        import requests
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    return True
            except:
                pass
            time.sleep(1)
        
        return False
    
    def start_all_services(self):
        """Start all enabled services in priority order"""
        logger.info("Starting all Orchestra AI services...")
        
        # Sort services by priority
        services = sorted(
            [(k, v) for k, v in self.config['services'].items() if v['enabled']],
            key=lambda x: x[1].get('priority', 999)
        )
        
        for service_id, config in services:
            if config['type'] == 'oneshot':
                self.run_oneshot_service(service_id, config)
            elif config['type'] == 'daemon':
                self.start_daemon_service(service_id, config)
            elif config['type'] == 'periodic':
                # Periodic services are handled by cron or similar
                logger.info(f"Skipping periodic service: {config['name']}")
    
    def stop_all_services(self):
        """Stop all running services"""
        logger.info("Stopping all services...")
        
        for service_id, process in self.processes.items():
            if process.poll() is None:
                logger.info(f"Stopping {service_id}...")
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    process.wait(timeout=10)
                except:
                    process.kill()
    
    def monitor_services(self):
        """Monitor running services and restart if needed"""
        while True:
            time.sleep(30)  # Check every 30 seconds
            
            for service_id, config in self.config['services'].items():
                if config['type'] != 'daemon' or not config['enabled']:
                    continue
                
                process = self.processes.get(service_id)
                if process and process.poll() is not None:
                    logger.warning(f"{config['name']} has stopped, restarting...")
                    self.start_daemon_service(service_id, config)
    
    def run(self):
        """Main run method"""
        logger.info("🎼 Orchestra AI Autostart Manager")
        logger.info("=================================")
        
        # Check dependencies
        if self.config['startup_checks']['check_dependencies']:
            if not self.check_dependencies():
                logger.error("Dependency check failed. Please install missing dependencies.")
                return
        
        # Check ports
        if self.config['startup_checks']['check_ports']:
            self.check_ports()
        
        # Setup environment
        self.setup_environment()
        
        # Start all services
        self.start_all_services()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, lambda s, f: self.shutdown())
        signal.signal(signal.SIGTERM, lambda s, f: self.shutdown())
        
        logger.info("\n✅ All services started!")
        logger.info("Press Ctrl+C to stop all services\n")
        
        # Monitor services
        try:
            self.monitor_services()
        except KeyboardInterrupt:
            self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("\n🛑 Shutting down Orchestra AI...")
        self.stop_all_services()
        logger.info("Goodbye! 👋")
        sys.exit(0)

def main():
    """Main entry point"""
    autostart = OrchestraAutostart()
    autostart.run()

if __name__ == "__main__":
    main() 