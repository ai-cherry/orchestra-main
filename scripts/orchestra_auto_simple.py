#!/usr/bin/env python3
"""
Orchestra Simple Automation System
Zero-dependency intelligent automation
"""

import asyncio
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleOrchestrator:
    """Simple orchestration without external dependencies"""
    
    def __init__(self):
        self.running = True
        self.services = {}
        self.start_time = datetime.now()
        
    async def start(self):
        """Start the orchestration system"""
        logger.info("🚀 Starting Simple Orchestra Automation")
        
        # Ensure services are running
        await self.ensure_services()
        
        # Start monitoring
        await self.monitor_loop()
    
    async def ensure_services(self):
        """Ensure all services are running"""
        logger.info("Checking Docker services...")
        
        # Check which compose file to use
        compose_file = "docker-compose.production.yml"
        if not Path(compose_file).exists():
            compose_file = "docker-compose.local.yml"
        
        # Check if services are running
        result = subprocess.run(
            ["docker-compose", "-f", compose_file, "ps", "-q"],
            capture_output=True,
            text=True
        )
        
        if not result.stdout.strip():
            logger.info("Starting Docker services...")
            subprocess.run(["docker-compose", "-f", compose_file, "up", "-d"])
            await asyncio.sleep(30)
        
        # Check individual service health
        services = ["postgres", "redis", "weaviate"]
        for service in services:
            await self.check_service(service)
    
    async def check_service(self, service_name: str) -> bool:
        """Check if a service is healthy"""
        try:
            result = subprocess.run(
                ["docker", "inspect", f"cherry_ai_{service_name}", "--format", "{{.State.Health.Status}}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                health = result.stdout.strip()
                self.services[service_name] = health
                
                if health != "healthy":
                    logger.warning(f"Service {service_name} is {health}")
                    return False
                return True
            else:
                logger.error(f"Service {service_name} not found")
                return False
                
        except Exception as e:
            logger.error(f"Error checking {service_name}: {e}")
            return False
    
    async def heal_service(self, service_name: str):
        """Attempt to heal an unhealthy service"""
        logger.info(f"Attempting to heal {service_name}...")
        
        compose_file = "docker-compose.production.yml"
        if not Path(compose_file).exists():
            compose_file = "docker-compose.local.yml"
        
        # Restart the service
        subprocess.run(["docker-compose", "-f", compose_file, "restart", service_name])
        await asyncio.sleep(30)
        
        # Check if it's healthy now
        if await self.check_service(service_name):
            logger.info(f"✅ Successfully healed {service_name}")
        else:
            logger.error(f"Failed to heal {service_name}")
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                logger.info("Running health checks...")
                
                # Check all services
                unhealthy = []
                for service in ["postgres", "redis", "weaviate"]:
                    if not await self.check_service(service):
                        unhealthy.append(service)
                
                # Heal unhealthy services
                for service in unhealthy:
                    await self.heal_service(service)
                
                # Start MCP servers if not running
                await self.ensure_mcp_servers()
                
                # Wait before next check
                await asyncio.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                self.running = False
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(60)
    
    async def ensure_mcp_servers(self):
        """Ensure MCP servers are running"""
        mcp_servers = [
            ("memory_server", "mcp_server/servers/memory_server.py", 8003),
            ("tools_server", "mcp_server/servers/tools_server.py", 8006),
        ]
        
        for name, script, port in mcp_servers:
            if Path(script).exists():
                # Check if port is in use
                result = subprocess.run(
                    ["lsof", "-i", f":{port}"],
                    capture_output=True
                )
                
                if result.returncode != 0:
                    # Port not in use, start server
                    logger.info(f"Starting {name}...")
                    subprocess.Popen(
                        ["python3", script],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )


def main():
    """Main entry point"""
    orchestrator = SimpleOrchestrator()
    
    print("🎼 Orchestra Simple Automation")
    print("============================")
    print("This system will:")
    print("  • Monitor service health")
    print("  • Auto-restart failed services")
    print("  • Start MCP servers")
    print("  • Run continuously")
    print("\nPress Ctrl+C to stop")
    print("")
    
    asyncio.run(orchestrator.start())


if __name__ == "__main__":
    main()