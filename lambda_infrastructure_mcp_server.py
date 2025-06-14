"""
Updated Lambda Infrastructure MCP Server with Secure Secret Management
"""

import os
import asyncio
import json
import logging
import subprocess
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

# MCP Server imports
from mcp.server import Server
from mcp.types import Tool, TextContent

# Import secure secret management
from security.secret_manager import secret_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LambdaLabsInfrastructureServer:
    def __init__(self):
        self.server = Server("lambda-infrastructure")
        
        # Get API key securely
        self.api_key = secret_manager.get_secret('LAMBDA_API_KEY')
        if not self.api_key:
            logger.error("Lambda Labs API key not found in secure storage")
            raise ValueError("LAMBDA_API_KEY required")
        
        self.base_url = "https://cloud.lambda.ai/api/v1"
        self.production_ip = secret_manager.get_secret('PRODUCTION_IP', "150.136.94.139")
        
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
                            "database": {"type": "string", "enum": ["postgresql", "redis", "weaviate"]}
                        },
                        "required": ["action", "database"]
                    }
                ),
                Tool(
                    name="rotate_secrets",
                    description="Rotate infrastructure secrets",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "secret_type": {"type": "string", "enum": ["database", "api_keys", "ssh_keys", "all"]}
                        },
                        "required": ["secret_type"]
                    }
                ),
                Tool(
                    name="security_audit",
                    description="Run security audit on infrastructure",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "scope": {"type": "string", "enum": ["network", "services", "secrets", "all"]}
                        },
                        "required": []
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
                elif name == "rotate_secrets":
                    return await self.rotate_secrets(arguments)
                elif name == "security_audit":
                    return await self.security_audit(arguments)
                elif name == "monitor_resources":
                    return await self.monitor_resources(arguments)
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
                auth=(self.api_key, ""),
                timeout=30
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
        """Deploy code to production instance with secure authentication"""
        try:
            branch = arguments.get("branch", "main")
            restart_services = arguments.get("restart_services", True)
            
            # Get SSH private key securely
            ssh_key = secret_manager.get_secret('SSH_PRIVATE_KEY')
            if not ssh_key:
                return [TextContent(type="text", text="❌ SSH private key not found in secure storage")]
            
            # Write SSH key to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as f:
                f.write(ssh_key)
                ssh_key_file = f.name
            
            try:
                # Set proper permissions
                os.chmod(ssh_key_file, 0o600)
                
                # SSH commands for deployment
                ssh_commands = [
                    "cd /opt/orchestra-main",
                    f"git fetch origin",
                    f"git checkout {branch}",
                    f"git pull origin {branch}",
                    "source venv/bin/activate",
                    "pip install -r requirements.txt"
                ]
                
                if restart_services:
                    ssh_commands.extend([
                        "sudo systemctl restart orchestra-mcp",
                        "sudo systemctl restart nginx"
                    ])
                
                # Execute deployment
                ssh_command = f"ssh -i {ssh_key_file} -o StrictHostKeyChecking=no ubuntu@{self.production_ip} '{'; '.join(ssh_commands)}'"
                
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
                
            finally:
                # Clean up temporary SSH key file
                os.unlink(ssh_key_file)
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Deployment error: {str(e)}")]
    
    async def rotate_secrets(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Rotate infrastructure secrets"""
        try:
            secret_type = arguments["secret_type"]
            
            results = []
            
            if secret_type in ["database", "all"]:
                # Generate new database password
                import secrets
                import string
                new_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
                
                # Update secret
                secret_manager.rotate_secret("POSTGRES_PASSWORD", new_password)
                results.append("✅ Database password rotated")
            
            if secret_type in ["api_keys", "all"]:
                # Note: API keys typically need to be rotated in the external service
                results.append("⚠️ API keys require manual rotation in external services")
            
            if secret_type in ["ssh_keys", "all"]:
                # Generate new SSH key pair
                ssh_result = subprocess.run(
                    ["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", "/tmp/new_key", "-N", ""],
                    capture_output=True,
                    text=True
                )
                
                if ssh_result.returncode == 0:
                    with open("/tmp/new_key", "r") as f:
                        private_key = f.read()
                    with open("/tmp/new_key.pub", "r") as f:
                        public_key = f.read()
                    
                    secret_manager.rotate_secret("SSH_PRIVATE_KEY", private_key)
                    secret_manager.rotate_secret("SSH_PUBLIC_KEY", public_key)
                    
                    # Clean up
                    os.unlink("/tmp/new_key")
                    os.unlink("/tmp/new_key.pub")
                    
                    results.append("✅ SSH keys rotated")
                else:
                    results.append("❌ Failed to generate new SSH keys")
            
            response = f"🔄 **Secret Rotation - {secret_type.title()}**\n\n"
            response += "\n".join(results)
            
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Secret rotation error: {str(e)}")]
    
    async def security_audit(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Run security audit on infrastructure"""
        try:
            scope = arguments.get("scope", "all")
            
            audit_results = []
            
            if scope in ["secrets", "all"]:
                # Validate all secrets are present
                validation = secret_manager.validate_secrets()
                missing_secrets = [k for k, v in validation.items() if not v]
                
                if missing_secrets:
                    audit_results.append(f"❌ Missing secrets: {', '.join(missing_secrets)}")
                else:
                    audit_results.append("✅ All required secrets present")
            
            if scope in ["network", "all"]:
                # Check firewall status
                try:
                    ssh_key = secret_manager.get_secret('SSH_PRIVATE_KEY')
                    if ssh_key:
                        # Check UFW status
                        result = subprocess.run(
                            f"ssh -o StrictHostKeyChecking=no ubuntu@{self.production_ip} 'sudo ufw status'",
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        
                        if "Status: active" in result.stdout:
                            audit_results.append("✅ Firewall is active")
                        else:
                            audit_results.append("❌ Firewall is not active")
                    else:
                        audit_results.append("⚠️ Cannot check network security - SSH key not available")
                except:
                    audit_results.append("❌ Network security check failed")
            
            if scope in ["services", "all"]:
                # Check service health
                health_result = await self.check_health()
                if health_result and "❌" not in health_result[0].text:
                    audit_results.append("✅ All services healthy")
                else:
                    audit_results.append("❌ Some services unhealthy")
            
            response = f"🔒 **Security Audit - {scope.title()}**\n\n"
            response += "\n".join(audit_results)
            
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Security audit error: {str(e)}")]
    
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
            
            # Check MCP server
            try:
                response = requests.get(f"http://{self.production_ip}:8003/health", timeout=10)
                health_checks.append(f"✅ MCP Memory: Active")
            except:
                health_checks.append("❌ MCP Memory: Down")
            
            result = "🏥 **Production Health Check**\n\n" + "\n".join(health_checks)
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Health check error: {str(e)}")]
    
    async def manage_database(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Manage production databases with secure credentials"""
        try:
            action = arguments["action"]
            database = arguments["database"]
            
            # Get database credentials securely
            db_config = secret_manager.get_database_config()
            
            commands = {
                "postgresql": {
                    "backup": f"PGPASSWORD='{secret_manager.get_secret('POSTGRES_PASSWORD')}' pg_dump -h postgres -U orchestra orchestra_ai > /tmp/backup_$(date +%Y%m%d_%H%M%S).sql",
                    "status": "systemctl status postgresql"
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
                
                # Execute command securely
                ssh_key = secret_manager.get_secret('SSH_PRIVATE_KEY')
                if not ssh_key:
                    return [TextContent(type="text", text="❌ SSH key not available for database management")]
                
                # Use temporary SSH key file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as f:
                    f.write(ssh_key)
                    ssh_key_file = f.name
                
                try:
                    os.chmod(ssh_key_file, 0o600)
                    
                    result = subprocess.run(
                        f"ssh -i {ssh_key_file} -o StrictHostKeyChecking=no ubuntu@{self.production_ip} '{command}'",
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
                    
                finally:
                    os.unlink(ssh_key_file)
            else:
                return [TextContent(type="text", text=f"❌ Unsupported action '{action}' for database '{database}'")]
                
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Database management error: {str(e)}")]
    
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
            
            ssh_key = secret_manager.get_secret('SSH_PRIVATE_KEY')
            if not ssh_key:
                return [TextContent(type="text", text="❌ SSH key not available for monitoring")]
            
            # Use temporary SSH key file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as f:
                f.write(ssh_key)
                ssh_key_file = f.name
            
            try:
                os.chmod(ssh_key_file, 0o600)
                
                if metric == "all":
                    results = []
                    for m, cmd in commands.items():
                        try:
                            result = subprocess.run(
                                f"ssh -i {ssh_key_file} -o StrictHostKeyChecking=no ubuntu@{self.production_ip} '{cmd}'",
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
                            f"ssh -i {ssh_key_file} -o StrictHostKeyChecking=no ubuntu@{self.production_ip} '{commands[metric]}'",
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        response = f"📊 **{metric.upper()} Monitoring**\n\n```\n{result.stdout}\n```"
                    else:
                        response = f"❌ Unknown metric: {metric}"
                
                return [TextContent(type="text", text=response)]
                
            finally:
                os.unlink(ssh_key_file)
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Monitoring error: {str(e)}")]

# Initialize server
if __name__ == "__main__":
    server = LambdaLabsInfrastructureServer()
    asyncio.run(server.server.run())

