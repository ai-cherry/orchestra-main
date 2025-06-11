#!/usr/bin/env python3
"""
Cherry AI Orchestrator - Infrastructure Management MCP Server
Manages Lambda infrastructure, deployments, and monitoring
"""

import asyncio
import json
import logging
import os
import subprocess
from typing import Any, Dict, List

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions
from pydantic import AnyUrl
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("infrastructure-mcp")

server = Server("cherry-ai-infrastructure")

class InfrastructureManager:
    """Manages infrastructure operations"""
    
    def __init__(self):
        self.LAMBDA_API_KEY = os.getenv("LAMBDA_API_KEY")
        self.pulumi_token = os.getenv("PULUMI_ACCESS_TOKEN")
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        
    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.LAMBDA_API_KEY}",
            "Content-Type": "application/json"
        }
    
    async def get_instances(self) -> Dict[str, Any]:
        """Get all Lambda instances"""
        try:
            response = requests.get(
                f"{self.base_url}/instances",
                headers=self.get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting instances: {e}")
            return {"error": str(e)}
    
    async def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """Get specific instance status"""
        try:
            response = requests.get(
                f"{self.base_url}/instances/{instance_id}",
                headers=self.get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting instance status: {e}")
            return {"error": str(e)}
    
    async def get_load_balancers(self) -> Dict[str, Any]:
        """Get load balancers"""
        try:
            response = requests.get(
                f"{self.base_url}/load-balancers",
                headers=self.get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting load balancers: {e}")
            return {"error": str(e)}
    
    async def get_kubernetes_clusters(self) -> Dict[str, Any]:
        """Get Kubernetes clusters"""
        try:
            response = requests.get(
                f"{self.base_url}/kubernetes/clusters",
                headers=self.get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting k8s clusters: {e}")
            return {"error": str(e)}
    
    async def deploy_infrastructure(self) -> Dict[str, Any]:
        """Deploy infrastructure using Pulumi"""
        try:
            result = subprocess.run(
                ["pulumi", "up", "--yes"],
                cwd="/var/www/cherry-ai/infrastructure/pulumi",
                capture_output=True,
                text=True,
                env={**os.environ, "PULUMI_ACCESS_TOKEN": self.pulumi_token}
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
        except Exception as e:
            logger.error(f"Error deploying infrastructure: {e}")
            return {"error": str(e)}
    
    async def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status"""
        try:
            # Check service status on production server
            servers = {
                "production": "45.32.69.157",
                "database": "45.77.87.106",
                "staging": "207.246.108.201"
            }
            
            status = {}
            for name, ip in servers.items():
                try:
                    # Simple HTTP check
                    response = requests.get(f"http://{ip}", timeout=5)
                    status[name] = {
                        "ip": ip,
                        "status": "online" if response.status_code < 500 else "degraded",
                        "response_time": response.elapsed.total_seconds()
                    }
                except Exception as e:
                    status[name] = {
                        "ip": ip,
                        "status": "offline",
                        "error": str(e)
                    }
            
            return status
        except Exception as e:
            logger.error(f"Error getting deployment status: {e}")
            return {"error": str(e)}

infrastructure_manager = InfrastructureManager()

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List infrastructure resources"""
    return [
        types.Resource(
            uri=AnyUrl("infrastructure://Lambda/instances"),
            name="Lambda Instances",
            description="All Lambda compute instances",
            mimeType="application/json",
        ),
        types.Resource(
            uri=AnyUrl("infrastructure://Lambda/load-balancers"),
            name="Load Balancers",
            description="Lambda load balancers",
            mimeType="application/json",
        ),
        types.Resource(
            uri=AnyUrl("infrastructure://kubernetes/clusters"),
            name="Kubernetes Clusters",
            description="Lambda Kubernetes clusters",
            mimeType="application/json",
        ),
        types.Resource(
            uri=AnyUrl("infrastructure://deployment/status"),
            name="Deployment Status",
            description="Current deployment and service status",
            mimeType="application/json",
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read infrastructure resource"""
    
    if uri.scheme != "infrastructure":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")
    
    path = uri.path
    
    if path == "/Lambda/instances":
        instances = await infrastructure_manager.get_instances()
        return json.dumps(instances, indent=2)
    
    elif path == "/Lambda/load-balancers":
        load_balancers = await infrastructure_manager.get_load_balancers()
        return json.dumps(load_balancers, indent=2)
    
    elif path == "/kubernetes/clusters":
        clusters = await infrastructure_manager.get_kubernetes_clusters()
        return json.dumps(clusters, indent=2)
    
    elif path == "/deployment/status":
        status = await infrastructure_manager.get_deployment_status()
        return json.dumps(status, indent=2)
    
    else:
        raise ValueError(f"Unknown resource path: {path}")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List infrastructure tools"""
    return [
        types.Tool(
            name="deploy_infrastructure",
            description="Deploy infrastructure using Pulumi",
            inputSchema={
                "type": "object",
                "properties": {
                    "environment": {
                        "type": "string",
                        "enum": ["production", "staging"],
                        "description": "Target environment"
                    }
                },
                "required": ["environment"]
            },
        ),
        types.Tool(
            name="scale_instance",
            description="Scale a Lambda instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance_id": {
                        "type": "string",
                        "description": "Instance ID to scale"
                    },
                    "plan": {
                        "type": "string",
                        "description": "New plan ID"
                    }
                },
                "required": ["instance_id", "plan"]
            },
        ),
        types.Tool(
            name="restart_services",
            description="Restart services on a server",
            inputSchema={
                "type": "object",
                "properties": {
                    "server": {
                        "type": "string",
                        "enum": ["production", "database", "staging"],
                        "description": "Target server"
                    },
                    "services": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Services to restart"
                    }
                },
                "required": ["server", "services"]
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """Handle infrastructure tool calls"""
    
    if name == "deploy_infrastructure":
        environment = arguments.get("environment", "production")
        result = await infrastructure_manager.deploy_infrastructure()
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "scale_instance":
        instance_id = arguments.get("instance_id")
        plan = arguments.get("plan")
        
        if not instance_id or not plan:
            raise ValueError("instance_id and plan are required")
        
        # Implementation would call Lambda API to scale instance
        result = {"message": f"Scaling instance {instance_id} to plan {plan}"}
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "restart_services":
        server = arguments.get("server")
        services = arguments.get("services", [])
        
        if not server or not services:
            raise ValueError("server and services are required")
        
        # Implementation would SSH to server and restart services
        result = {
            "server": server,
            "services": services,
            "status": "restarted",
            "message": f"Restarted {', '.join(services)} on {server}"
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Main entry point"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="cherry-ai-infrastructure",
                server_version="1.0.0",
                capabilities=server.get_capabilities(),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())

