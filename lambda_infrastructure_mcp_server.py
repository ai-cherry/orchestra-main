import os
#!/usr/bin/env python3
"""
Enhanced MCP Server for Lambda Labs Infrastructure
Provides infrastructure management and deployment capabilities
"""

import asyncio
import json
import logging
import subprocess
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

# MCP Server imports (you'll need to install mcp package)
from mcp.server import Server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LambdaLabsInfrastructureServer:
    def __init__(self):
        self.server = Server("lambda-infrastructure")
self.api_key = os.getenv('ORCHESTRA_APP_API_KEY')
        self.base_url = "https://cloud.lambda.ai/api/v1"
        self.production_ip = "150.136.94.139"
        
        # Register tools
        self.register_tools()
    
    def register_tools(self):
        """Register all available tools"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="list_instances",
                    description="List all Lambda Labs instances",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="deploy_code",
                    description="Deploy code to production Lambda Labs instance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "branch": {"type": "string", "description": "Git branch to deploy"},
                            "restart_services": {"type": "boolean", "description": "Restart services after deployment"}
                        },
                        "required": ["branch"]
                    }
                ),
                Tool(
                    name="check_health",
                    description="Check health of production services",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="manage_database",
                    description="Manage production databases",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["backup", "restore", "migrate", "status"]},
                            "database": {"type": "string", "enum": ["postgresql", "redis", "weaviate", "pinecone"]}
                        },
                        "required": ["action", "database"]
                    }
                ),
                Tool(
                    name="scale_instance",
                    description="Scale Lambda Labs instance up or down",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "instance_type": {"type": "string", "description": "Target instance type"},
                            "action": {"type": "string", "enum": ["scale_up", "scale_down"]}
                        },
                        "required": ["instance_type", "action"]
                    }
                ),
                Tool(
                    name="monitor_resources",
                    description="Monitor Lambda Labs instance resources",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "metric": {"type": "string", "enum": ["cpu", "memory", "gpu", "disk", "network"]}
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="manage_ssl",
                    description="Manage SSL certificates",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["renew", "status", "install"]},
                            "domain": {"type": "string", "description": "Domain name"}
                        },
                        "required": ["action"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "list_instances":
                    return await self.list_instances()
                elif name == "deploy_code":
                    return await self.deploy_code(arguments)
                elif name == "check_health":
                    return await self.check_health()
                elif name == "manage_database":
                    return await self.manage_database(arguments)
                elif name == "scale_instance":
                    return await self.scale_instance(arguments)
                elif name == "monitor_resources":
                    return await self.monitor_resources(arguments)
                elif name == "manage_ssl":
                    return await self.manage_ssl(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def list_instances(self) -> List[TextContent]:
        """List all Lambda Labs instances"""
        try:
            response = requests.get(
                f"{self.base_url}/instances",
                auth=(self.api_key, "")
            )
            response.raise_for_status()
            
            instances = response.json()["data"]
            
            result = "🖥️ **Lambda Labs Instances:**\n\n"
            for instance in instances:
                result += f"**{instance['name']}**\n"
                result += f"- ID: {instance['id']}\n"
                result += f"- IP: {instance.get('ip', 'N/A')}\n"
                result += f"- Status: {instance['status']}\n"
                result += f"- Type: {instance['instance_type']['description']}\n"
                result += f"- Cost: ${instance['instance_type']['price_cents_per_hour']/100:.2f}/hour\n\n"
            
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error listing instances: {str(e)}")]
    
    async def deploy_code(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Deploy code to production instance"""
        try:
            branch = arguments.get("branch", "main")
            restart_services = arguments.get("restart_services", True)
            
            # SSH command to deploy
            ssh_commands = [
                "cd /opt/cherry-ai",
                f"git fetch origin",
                f"git checkout {branch}",
                f"git pull origin {branch}",
                "source venv/bin/activate",
                "pip install -r requirements.txt"
            ]
            
            if restart_services:
                ssh_commands.extend([
                    "sudo systemctl restart cherry-ai",
                    "sudo systemctl restart nginx"
                ])
            
            # Execute deployment
            ssh_command = f"ssh ubuntu@{self.production_ip} '{'; '.join(ssh_commands)}'"
            
            result = subprocess.run(
                ssh_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                response = f"✅ **Deployment Successful**\n\n"
                response += f"- Branch: {branch}\n"
                response += f"- Services restarted: {restart_services}\n"
                response += f"- Timestamp: {datetime.now().isoformat()}\n\n"
                response += f"**Output:**\n```\n{result.stdout}\n```"
            else:
                response = f"❌ **Deployment Failed**\n\n"
                response += f"**Error:**\n```\n{result.stderr}\n```"
            
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Deployment error: {str(e)}")]
    
    async def check_health(self) -> List[TextContent]:
        """Check health of production services"""
        try:
            health_checks = []
            
            # Check main application
            try:
                response = requests.get(f"http://{self.production_ip}:8000/health", timeout=10)
                health_checks.append(f"✅ Main App: {response.status_code}")
            except:
                health_checks.append("❌ Main App: Unreachable")
            
            # Check collaboration bridge
            try:
                response = requests.get(f"http://{self.production_ip}:8765", timeout=10)
                health_checks.append(f"✅ Collaboration Bridge: Active")
            except:
                health_checks.append("❌ Collaboration Bridge: Down")
            
            # Check databases via SSH
            ssh_checks = [
                "systemctl is-active postgresql",
                "systemctl is-active redis-server",
                "systemctl is-active nginx",
                "docker ps | grep weaviate"
            ]
            
            for check in ssh_checks:
                try:
                    result = subprocess.run(
                        f"ssh ubuntu@{self.production_ip} '{check}'",
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    service = check.split()[-1]
                    status = "✅" if result.returncode == 0 else "❌"
                    health_checks.append(f"{status} {service}: {result.stdout.strip()}")
                except:
                    health_checks.append(f"❌ {check}: Check failed")
            
            result = "🏥 **Production Health Check**\n\n" + "\n".join(health_checks)
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Health check error: {str(e)}")]
    
    async def manage_database(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Manage production databases"""
        try:
            action = arguments["action"]
            database = arguments["database"]
            
            commands = {
                "postgresql": {
                    "backup": "pg_dump cherry_ai_production > /tmp/backup_$(date +%Y%m%d_%H%M%S).sql",
                    "status": "systemctl status postgresql",
                    "migrate": "cd /opt/cherry-ai && python manage.py migrate"
                },
                "redis": {
                    "backup": "redis-cli BGSAVE",
                    "status": "systemctl status redis-server"
                },
                "weaviate": {
                    "backup": "docker exec weaviate weaviate-tool backup",
                    "status": "docker ps | grep weaviate"
                }
            }
            
            if database in commands and action in commands[database]:
                command = commands[database][action]
                
                result = subprocess.run(
                    f"ssh ubuntu@{self.production_ip} '{command}'",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                response = f"🗄️ **Database {action.title()} - {database.title()}**\n\n"
                if result.returncode == 0:
                    response += f"✅ Success\n\n**Output:**\n```\n{result.stdout}\n```"
                else:
                    response += f"❌ Failed\n\n**Error:**\n```\n{result.stderr}\n```"
                
                return [TextContent(type="text", text=response)]
            else:
                return [TextContent(type="text", text=f"❌ Unsupported action '{action}' for database '{database}'")]
                
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Database management error: {str(e)}")]
    
    async def scale_instance(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Scale Lambda Labs instance"""
        # This would require terminating current instance and launching new one
        # Implementation depends on specific scaling requirements
        return [TextContent(type="text", text="🔧 Instance scaling feature coming soon")]
    
    async def monitor_resources(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Monitor instance resources"""
        try:
            metric = arguments.get("metric", "all")
            
            commands = {
                "cpu": "top -bn1 | grep 'Cpu(s)'",
                "memory": "free -h",
                "gpu": "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits",
                "disk": "df -h",
                "network": "ss -tuln"
            }
            
            if metric == "all":
                results = []
                for m, cmd in commands.items():
                    try:
                        result = subprocess.run(
                            f"ssh ubuntu@{self.production_ip} '{cmd}'",
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        results.append(f"**{m.upper()}:**\n```\n{result.stdout}\n```")
                    except:
                        results.append(f"**{m.upper()}:** Error getting data")
                
                response = "📊 **Resource Monitoring**\n\n" + "\n\n".join(results)
            else:
                if metric in commands:
                    result = subprocess.run(
                        f"ssh ubuntu@{self.production_ip} '{commands[metric]}'",
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    response = f"📊 **{metric.upper()} Monitoring**\n\n```\n{result.stdout}\n```"
                else:
                    response = f"❌ Unknown metric: {metric}"
            
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Monitoring error: {str(e)}")]
    
    async def manage_ssl(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Manage SSL certificates"""
        try:
            action = arguments["action"]
            domain = arguments.get("domain", "cherry-ai.me")
            
            commands = {
                "status": f"certbot certificates",
                "renew": f"certbot renew --nginx",
                "install": f"certbot --nginx -d {domain} --non-interactive --agree-tos --email admin@{domain}"
            }
            
            if action in commands:
                result = subprocess.run(
                    f"ssh ubuntu@{self.production_ip} 'sudo {commands[action]}'",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                response = f"🔒 **SSL {action.title()}**\n\n"
                if result.returncode == 0:
                    response += f"✅ Success\n\n**Output:**\n```\n{result.stdout}\n```"
                else:
                    response += f"❌ Failed\n\n**Error:**\n```\n{result.stderr}\n```"
                
                return [TextContent(type="text", text=response)]
            else:
                return [TextContent(type="text", text=f"❌ Unknown SSL action: {action}")]
                
        except Exception as e:
            return [TextContent(type="text", text=f"❌ SSL management error: {str(e)}")]

async def main():
    """Run the Lambda Labs Infrastructure MCP Server"""
    server_instance = LambdaLabsInfrastructureServer()
    
    # Run the server
    async with server_instance.server.run_stdio() as streams:
        await server_instance.server.run(
            streams[0], streams[1], server_instance.server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())

