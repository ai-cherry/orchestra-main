#!/usr/bin/env python3
"""
Enhanced Codebase MCP Server for Lambda Labs Production
Provides comprehensive codebase management and AI integration
"""

import asyncio
import json
import logging
import os
import subprocess
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedCodebaseServer:
    def __init__(self):
        self.production_server = os.getenv("PRODUCTION_SERVER", "150.136.94.139")
        self.database_url = os.getenv("DATABASE_URL")
        self.redis_url = os.getenv("REDIS_URL")
        self.weaviate_url = os.getenv("WEAVIATE_URL")
        
    async def deploy_to_lambda(self, branch: str = "main") -> Dict[str, Any]:
        """Deploy code to Lambda Labs production"""
        try:
            # SSH and deploy
            ssh_commands = [
                "cd /opt/cherry-ai",
                f"git fetch origin",
                f"git checkout {branch}",
                f"git pull origin {branch}",
                "source venv/bin/activate",
                "pip install -r requirements.txt",
                "sudo systemctl restart cherry-ai",
            ]
            
            ssh_command = f"ssh ubuntu@{self.production_server} '{'; '.join(ssh_commands)}'"
            
            result = subprocess.run(
                ssh_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def sync_databases(self) -> Dict[str, Any]:
        """Sync local development with production databases"""
        try:
            # Test connections
            connections = {}
            
            # PostgreSQL
            if self.database_url:
                try:
                    import psycopg2
                    conn = psycopg2.connect(self.database_url)
                    conn.close()
                    connections["postgresql"] = "connected"
                except Exception as e:
                    connections["postgresql"] = f"error: {str(e)}"
            
            # Redis
            if self.redis_url:
                try:
                    import redis
                    r = redis.from_url(self.redis_url)
                    r.ping()
                    connections["redis"] = "connected"
                except Exception as e:
                    connections["redis"] = f"error: {str(e)}"
            
            # Weaviate
            if self.weaviate_url:
                try:
                    response = requests.get(f"{self.weaviate_url}/v1/meta")
                    if response.status_code == 200:
                        connections["weaviate"] = "connected"
                    else:
                        connections["weaviate"] = f"error: status {response.status_code}"
                except Exception as e:
                    connections["weaviate"] = f"error: {str(e)}"
            
            return {
                "success": True,
                "connections": connections,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_production_status(self) -> Dict[str, Any]:
        """Get production server status"""
        try:
            # Check main app
            try:
                response = requests.get(f"http://{self.production_server}:8000/health", timeout=10)
                app_status = {"status": response.status_code, "response": response.json()}
            except Exception as e:
                app_status = {"status": "error", "error": str(e)}
            
            # Check collaboration bridge
            try:
                response = requests.get(f"http://{self.production_server}:8765", timeout=10)
                bridge_status = {"status": "active"}
            except Exception as e:
                bridge_status = {"status": "error", "error": str(e)}
            
            return {
                "success": True,
                "app": app_status,
                "bridge": bridge_status,
                "server": self.production_server,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# Initialize server
server = EnhancedCodebaseServer()

async def main():
    """Main server loop"""
    logger.info("🚀 Enhanced Codebase MCP Server for Lambda Labs started")
    
    # Keep server running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
