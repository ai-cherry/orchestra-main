"""
Orchestra AI - Enhanced Pulumi Main Configuration
Integrates all infrastructure components following user's IaC strategy
"""

import pulumi
import os
from pathlib import Path

# Import our infrastructure modules
import sys
sys.path.append(str(Path(__file__).parent))

from vercel_integration import PulumiVercelIntegration
from lambda_labs_integration import LambdaLabsInfrastructure
from ci_cd_automation import PulumiAutomationOrchestrator

# Import enhanced secret manager
sys.path.append(str(Path(__file__).parent.parent))
from security.enhanced_secret_manager import secret_manager

class OrchestraAIInfrastructure:
    """Complete Orchestra AI infrastructure using Pulumi IaC"""
    
    def __init__(self):
        self.environment = secret_manager.get_secret("ENVIRONMENT", "production")
        self.project_name = secret_manager.get_secret("PROJECT_NAME", "orchestra-ai")
        
        # Validate secrets
        validation_results = secret_manager.validate_all_secrets()
        missing_secrets = [key for key, valid in validation_results.items() if not valid]
        
        if missing_secrets:
            pulumi.log.warn(f"Missing secrets: {missing_secrets}")
            pulumi.log.info("Some features may be limited without all secrets")
        else:
            pulumi.log.info("All required secrets validated successfully")
    
    def deploy_complete_infrastructure(self):
        """Deploy complete Orchestra AI infrastructure"""
        
        # 1. Deploy Vercel Frontend (if token available)
        vercel_resources = None
        vercel_token = secret_manager.get_secret("VERCEL_TOKEN")
        if vercel_token:
            try:
                vercel_integration = PulumiVercelIntegration()
                
                # Create Vercel project
                vercel_project = vercel_integration.create_vercel_project()
                
                # Create production deployment
                vercel_deployment = vercel_integration.create_vercel_deployment(vercel_project)
                
                # Setup webhooks
                vercel_webhook = vercel_integration.setup_webhook_integration(vercel_project)
                
                vercel_resources = {
                    "project": vercel_project,
                    "deployment": vercel_deployment,
                    "webhook": vercel_webhook
                }
                
                pulumi.log.info("Vercel frontend infrastructure configured")
                
            except Exception as e:
                pulumi.log.error(f"Vercel deployment failed: {str(e)}")
        else:
            pulumi.log.warn("VERCEL_TOKEN not found - skipping Vercel deployment")
        
        # 2. Deploy Lambda Labs Backend (if API key available)
        lambda_resources = None
        lambda_key = secret_manager.get_secret("LAMBDA_API_KEY")
        if lambda_key:
            try:
                lambda_infra = LambdaLabsInfrastructure()
                
                # Create Lambda Labs cluster
                lambda_instances = lambda_infra.create_orchestra_cluster()
                
                # Setup software on instances
                lambda_setup_commands = {}
                for instance_type, instance in lambda_instances.items():
                    lambda_setup_commands[instance_type] = lambda_infra.setup_instance_software(instance, instance_type)
                
                lambda_resources = {
                    "instances": lambda_instances,
                    "setup_commands": lambda_setup_commands
                }
                
                pulumi.log.info("Lambda Labs backend infrastructure configured")
                
            except Exception as e:
                pulumi.log.error(f"Lambda Labs deployment failed: {str(e)}")
        else:
            pulumi.log.warn("LAMBDA_API_KEY not found - skipping Lambda Labs deployment")
        
        return {
            "vercel": vercel_resources,
            "lambda_labs": lambda_resources
        }

# Initialize and deploy infrastructure
infrastructure = OrchestraAIInfrastructure()
deployed_resources = infrastructure.deploy_complete_infrastructure()

# Export outputs based on what was successfully deployed
if deployed_resources["vercel"]:
    vercel_resources = deployed_resources["vercel"]
    pulumi.export("vercel_project_id", vercel_resources["project"].id)
    pulumi.export("vercel_project_name", vercel_resources["project"].name)
    pulumi.export("vercel_production_url", vercel_resources["deployment"].url)
    pulumi.export("vercel_webhook_id", vercel_resources["webhook"].id)

if deployed_resources["lambda_labs"]:
    lambda_resources = deployed_resources["lambda_labs"]
    
    # Export instance information
    for instance_type, instance in lambda_resources["instances"].items():
        pulumi.export(f"lambda_{instance_type}_id", instance.id)
        pulumi.export(f"lambda_{instance_type}_ip", instance.ip)
        pulumi.export(f"lambda_{instance_type}_status", instance.status)
    
    # Export cluster information
    pulumi.export("lambda_cluster_size", len(lambda_resources["instances"]))

# Export deployment metadata
pulumi.export("environment", infrastructure.environment)
pulumi.export("project_name", infrastructure.project_name)
pulumi.export("infrastructure_approach", "pulumi_iac_multi_cloud")
pulumi.export("deployment_timestamp", pulumi.get_current_time())

# Export deployment status
deployment_status = {
    "vercel_deployed": deployed_resources["vercel"] is not None,
    "lambda_labs_deployed": deployed_resources["lambda_labs"] is not None,
    "secrets_validated": len(secret_manager.validate_all_secrets()) > 0
}
pulumi.export("deployment_status", deployment_status)

# Export URLs for easy access
urls = {}
if deployed_resources["vercel"]:
    urls["frontend"] = deployed_resources["vercel"]["deployment"].url

if deployed_resources["lambda_labs"]:
    api_server = deployed_resources["lambda_labs"]["instances"].get("api_server")
    if api_server:
        urls["api"] = pulumi.Output.concat("http://", api_server.ip, ":8000")

pulumi.export("service_urls", urls)

# Export health check information
health_endpoints = {}
if deployed_resources["vercel"]:
    health_endpoints["frontend"] = pulumi.Output.concat(deployed_resources["vercel"]["deployment"].url, "/health")

if deployed_resources["lambda_labs"]:
    api_server = deployed_resources["lambda_labs"]["instances"].get("api_server")
    if api_server:
        health_endpoints["api"] = pulumi.Output.concat("http://", api_server.ip, ":8000/health")

pulumi.export("health_endpoints", health_endpoints)

pulumi.log.info("Orchestra AI infrastructure deployment completed")

