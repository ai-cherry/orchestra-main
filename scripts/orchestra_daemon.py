#!/usr/bin/env python3
"""Orchestra Automation Daemon - Simple and Reliable"""

import asyncio
import subprocess
import logging
import json
import os
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/orchestra_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class OrchestraDaemon:
    def __init__(self):
        self.running = True
        self.services = ["postgres", "redis", "weaviate"]
        self.mcp_servers = {
            "memory": {"script": "mcp_server/servers/memory_server.py", "port": 8003},
            "tools": {"script": "mcp_server/servers/tools_server.py", "port": 8006}
        }
        
    async def run(self):
        logger.info("🚀 Orchestra Daemon Started")
        
        while self.running:
            try:
                # Check Docker services
                for service in self.services:
                    await self.check_docker_service(service)
                
                # Check MCP servers
                for name, config in self.mcp_servers.items():
                    await self.check_mcp_server(name, config)
                
                # Wait before next check
                await asyncio.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                self.running = False
            except Exception as e:
                logger.error(f"Daemon error: {e}")
                await asyncio.sleep(60)
    
    async def check_docker_service(self, service):
        """Check and heal Docker service"""
        try:
            result = subprocess.run(
                ["docker", "inspect", f"cherry_ai_{service}", "--format", "{{.State.Health.Status}}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0 or result.stdout.strip() != "healthy":
                logger.warning(f"Service {service} unhealthy, restarting...")
                
                if service == "weaviate":
                    subprocess.run(["docker-compose", "-f", "docker-compose.weaviate-fix.yml", "restart", service])
                else:
                    subprocess.run(["docker-compose", "-f", "docker-compose.production.yml", "restart", service])
                    
        except Exception as e:
            logger.error(f"Error checking {service}: {e}")
    
    async def check_mcp_server(self, name, config):
        """Check and start MCP server if needed"""
        try:
            # Check if port is in use
            result = subprocess.run(
                ["lsof", "-i", f":{config['port']}"],
                capture_output=True
            )
            
            if result.returncode != 0 and Path(config['script']).exists():
                logger.info(f"Starting MCP {name} server...")
                subprocess.Popen(
                    ["python3", config['script']],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except Exception as e:
            logger.error(f"Error checking MCP {name}: {e}")


if __name__ == "__main__":
    daemon = OrchestraDaemon()
    asyncio.run(daemon.run())
