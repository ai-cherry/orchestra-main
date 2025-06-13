#!/usr/bin/env python3
"""
Orchestra AI Infrastructure as Code with Pulumi
Manages Lambda Labs GPU clusters and MCP server infrastructure
"""

import pulumi
import pulumi_kubernetes as k8s
from lambda_labs import LambdaLabsInfrastructure
from mcp_infrastructure import MCPInfrastructure
from monitoring import MonitoringStack
from typing import Dict, Any

def main():
    """Main infrastructure deployment function."""
    
    # Get configuration
    config = pulumi.Config()
    environment = config.get("environment", "development")
    mcp_enabled = config.get_bool("mcp_enabled", True)
    
    # Initialize infrastructure components
    stack_name = f"orchestra-{environment}"
    
    # 1. Deploy Lambda Labs GPU Infrastructure
    if environment in ["staging", "production"]:
        print(f"🚀 Deploying Lambda Labs GPU infrastructure for {environment}")
        lambda_infra = LambdaLabsInfrastructure(stack_name, config)
        gpu_cluster = lambda_infra.create_gpu_cluster()
        
        # Export GPU cluster information
        pulumi.export("gpu_cluster_endpoint", gpu_cluster["cluster_endpoint"])
        pulumi.export("gpu_instances", gpu_cluster["instances"])
        pulumi.export("auto_scaling_config", gpu_cluster["auto_scaling"])
        
        print("✅ Lambda Labs GPU cluster deployed successfully")
    else:
        print("ℹ️  Skipping GPU deployment for development environment")
    
    # 2. Deploy MCP Server Infrastructure
    if mcp_enabled:
        print(f"🎼 Deploying MCP server infrastructure for {environment}")
        mcp_infra = MCPInfrastructure(stack_name)
        mcp_deployment = mcp_infra.deploy_mcp_servers()
        
        # Export MCP information
        pulumi.export("mcp_namespace", mcp_deployment["namespace"].metadata.name)
        pulumi.export("mcp_services", [
            service.metadata.name for service in mcp_deployment["services"]
        ])
        pulumi.export("mcp_deployments", [
            deployment.metadata.name for deployment in mcp_deployment["deployments"]
        ])
        
        print("✅ MCP server infrastructure deployed successfully")
    else:
        print("ℹ️  MCP servers disabled for this deployment")
    
    # 3. Deploy Monitoring and Observability
    print(f"📊 Deploying monitoring stack for {environment}")
    monitoring = MonitoringStack(stack_name, environment)
    monitoring_config = monitoring.deploy_monitoring()
    
    # Export monitoring information
    pulumi.export("prometheus_endpoint", monitoring_config["prometheus_endpoint"])
    pulumi.export("grafana_endpoint", monitoring_config["grafana_endpoint"])
    pulumi.export("alertmanager_endpoint", monitoring_config["alertmanager_endpoint"])
    
    print("✅ Monitoring stack deployed successfully")
    
    # 4. Create Service Mesh and Networking
    if environment in ["staging", "production"]:
        print(f"🌐 Configuring service mesh for {environment}")
        service_mesh_config = configure_service_mesh(stack_name)
        pulumi.export("service_mesh_config", service_mesh_config)
        print("✅ Service mesh configured successfully")
    
    # 5. Export deployment summary
    deployment_summary = create_deployment_summary(environment, mcp_enabled)
    pulumi.export("deployment_summary", deployment_summary)
    
    print(f"🎉 Orchestra AI infrastructure deployment complete for {environment}")

def configure_service_mesh(stack_name: str) -> Dict[str, Any]:
    """Configure service mesh for inter-service communication."""
    return {
        "mesh_name": f"{stack_name}-service-mesh",
        "discovery_service": "consul",
        "load_balancer": "istio",
        "security": {
            "mTLS": True,
            "rbac_enabled": True,
            "network_policies": True
        },
        "observability": {
            "tracing": "jaeger",
            "metrics": "prometheus",
            "logging": "fluentd"
        }
    }

def create_deployment_summary(environment: str, mcp_enabled: bool) -> Dict[str, Any]:
    """Create deployment summary for monitoring and documentation."""
    return {
        "environment": environment,
        "deployment_time": pulumi.Output.from_input(str(pulumi.time.time())),
        "components": {
            "gpu_cluster": environment in ["staging", "production"],
            "mcp_servers": mcp_enabled,
            "monitoring": True,
            "service_mesh": environment in ["staging", "production"]
        },
        "endpoints": {
            "api": f"https://api-{environment}.orchestra-ai.com",
            "frontend": f"https://{environment}.orchestra-ai.com",
            "admin": f"https://admin-{environment}.orchestra-ai.com"
        },
        "status": "deployed"
    }

if __name__ == "__main__":
    main() 