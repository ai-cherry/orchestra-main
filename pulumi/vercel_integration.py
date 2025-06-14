"""
Orchestra AI - Pulumi Vercel Integration
Implements the user's Infrastructure-as-Code strategy with official Pulumi Vercel provider
"""

import pulumi
import pulumi_vercel as vercel
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

# Import enhanced secret manager
import sys
sys.path.append(str(Path(__file__).parent.parent))
from security.enhanced_secret_manager import secret_manager

class PulumiVercelIntegration:
    """Pulumi-based Vercel deployment following user's IaC strategy"""
    
    def __init__(self):
        # Get secrets from centralized manager
        self.vercel_token = secret_manager.get_secret("VERCEL_TOKEN")
        self.github_token = secret_manager.get_secret("GITHUB_TOKEN")
        self.lambda_backend_url = secret_manager.get_secret("LAMBDA_BACKEND_URL", "http://150.136.94.139:8000")
        
        # Project configuration
        self.project_name = secret_manager.get_secret("PROJECT_NAME", "orchestra-ai")
        self.environment = secret_manager.get_secret("ENVIRONMENT", "production")
        
        # Validate required secrets
        if not self.vercel_token:
            raise ValueError("VERCEL_TOKEN is required for Pulumi Vercel integration")
    
    def create_vercel_project(self) -> vercel.Project:
        """Create Vercel project with proper configuration"""
        
        # Environment variables for the frontend
        environment_variables = [
            vercel.ProjectEnvironmentVariableArgs(
                key="VITE_API_URL",
                value="",  # Empty for relative API calls through proxy
                targets=["production", "preview", "development"]
            ),
            vercel.ProjectEnvironmentVariableArgs(
                key="VITE_API_TIMEOUT",
                value="30000",
                targets=["production", "preview", "development"]
            ),
            vercel.ProjectEnvironmentVariableArgs(
                key="VITE_ENABLE_WEBSOCKET",
                value="false",
                targets=["production", "preview", "development"]
            ),
            vercel.ProjectEnvironmentVariableArgs(
                key="VITE_ENABLE_MONITORING",
                value="true",
                targets=["production", "preview", "development"]
            ),
            vercel.ProjectEnvironmentVariableArgs(
                key="VITE_ENABLE_AI_CHAT",
                value="true",
                targets=["production", "preview", "development"]
            ),
            vercel.ProjectEnvironmentVariableArgs(
                key="VITE_DEBUG",
                value="false",
                targets=["production"]
            ),
            vercel.ProjectEnvironmentVariableArgs(
                key="LAMBDA_BACKEND_URL",
                value=self.lambda_backend_url,
                targets=["production", "preview", "development"]
            )
        ]
        
        # Create the Vercel project
        project = vercel.Project(
            "orchestra-main",
            name="orchestra-main",
            framework="vite",
            build_command="cd modern-admin && npm install --legacy-peer-deps && npm run build",
            output_directory="modern-admin/dist",
            install_command="npm install --legacy-peer-deps",
            git_repository=vercel.ProjectGitRepositoryArgs(
                type="github",
                repo="ai-cherry/orchestra-main"
            ),
            environment_variables=environment_variables,
            opts=pulumi.ResourceOptions(
                protect=True  # Protect production project from accidental deletion
            )
        )
        
        return project
    
    def create_vercel_deployment(self, project: vercel.Project) -> vercel.Deployment:
        """Create production deployment"""
        
        deployment = vercel.Deployment(
            "orchestra-main-production",
            project_id=project.id,
            production=True,
            opts=pulumi.ResourceOptions(
                depends_on=[project]
            )
        )
        
        return deployment
    
    def create_preview_environments(self, project: vercel.Project) -> Dict[str, vercel.Deployment]:
        """Create preview environments for different branches"""
        
        preview_deployments = {}
        
        # Development preview
        dev_deployment = vercel.Deployment(
            "orchestra-main-dev",
            project_id=project.id,
            production=False,
            ref="develop",  # Deploy from develop branch
            opts=pulumi.ResourceOptions(
                depends_on=[project]
            )
        )
        preview_deployments["development"] = dev_deployment
        
        return preview_deployments
    
    def configure_custom_domains(self, project: vercel.Project) -> Optional[vercel.ProjectDomain]:
        """Configure custom domains if available"""
        
        custom_domain = secret_manager.get_secret("CUSTOM_DOMAIN")
        if not custom_domain:
            return None
        
        domain = vercel.ProjectDomain(
            "orchestra-custom-domain",
            project_id=project.id,
            domain=custom_domain,
            opts=pulumi.ResourceOptions(
                depends_on=[project]
            )
        )
        
        return domain
    
    def setup_webhook_integration(self, project: vercel.Project) -> vercel.Webhook:
        """Setup webhook for deployment notifications"""
        
        webhook_url = secret_manager.get_secret("WEBHOOK_URL")
        if not webhook_url:
            # Create a default webhook URL for notifications
            webhook_url = f"https://api.{self.project_name}.com/webhooks/vercel"
        
        webhook = vercel.Webhook(
            "orchestra-deployment-webhook",
            url=webhook_url,
            events=["deployment.created", "deployment.succeeded", "deployment.failed"],
            project_ids=[project.id],
            opts=pulumi.ResourceOptions(
                depends_on=[project]
            )
        )
        
        return webhook

class PulumiAutomationAPI:
    """Pulumi Automation API for programmatic deployments"""
    
    def __init__(self, stack_name: str = "production"):
        self.stack_name = stack_name
        self.project_name = "orchestra-ai"
        
    def create_or_select_stack(self):
        """Create or select Pulumi stack programmatically"""
        try:
            from pulumi import automation as auto
            
            # Define the Pulumi program
            def pulumi_program():
                # Initialize Vercel integration
                vercel_integration = PulumiVercelIntegration()
                
                # Create Vercel project
                project = vercel_integration.create_vercel_project()
                
                # Create production deployment
                deployment = vercel_integration.create_vercel_deployment(project)
                
                # Create preview environments
                preview_deployments = vercel_integration.create_preview_environments(project)
                
                # Configure custom domains
                custom_domain = vercel_integration.configure_custom_domains(project)
                
                # Setup webhooks
                webhook = vercel_integration.setup_webhook_integration(project)
                
                # Export important outputs
                pulumi.export("project_id", project.id)
                pulumi.export("project_name", project.name)
                pulumi.export("production_url", deployment.url)
                pulumi.export("preview_urls", {
                    name: dep.url for name, dep in preview_deployments.items()
                })
                
                if custom_domain:
                    pulumi.export("custom_domain", custom_domain.domain)
                
                pulumi.export("webhook_id", webhook.id)
            
            # Create stack
            stack = auto.create_or_select_stack(
                stack_name=self.stack_name,
                project_name=self.project_name,
                program=pulumi_program
            )
            
            return stack
            
        except ImportError:
            pulumi.log.error("Pulumi Automation API not available. Install with: pip install pulumi[automation]")
            return None
    
    def deploy_stack(self, stack):
        """Deploy the stack programmatically"""
        if not stack:
            return None
            
        try:
            # Set configuration
            stack.set_config("vercel:token", auto.ConfigValue(
                value=secret_manager.get_secret("VERCEL_TOKEN"),
                secret=True
            ))
            
            # Refresh stack state
            stack.refresh()
            
            # Deploy
            result = stack.up()
            
            return result
            
        except Exception as e:
            pulumi.log.error(f"Stack deployment failed: {str(e)}")
            return None

# Initialize and export resources if running directly
if __name__ == "__main__":
    # Initialize Vercel integration
    vercel_integration = PulumiVercelIntegration()
    
    # Create Vercel project
    project = vercel_integration.create_vercel_project()
    
    # Create production deployment
    deployment = vercel_integration.create_vercel_deployment(project)
    
    # Create preview environments
    preview_deployments = vercel_integration.create_preview_environments(project)
    
    # Configure custom domains
    custom_domain = vercel_integration.configure_custom_domains(project)
    
    # Setup webhooks
    webhook = vercel_integration.setup_webhook_integration(project)
    
    # Export important outputs
    pulumi.export("project_id", project.id)
    pulumi.export("project_name", project.name)
    pulumi.export("production_url", deployment.url)
    pulumi.export("preview_urls", {
        name: dep.url for name, dep in preview_deployments.items()
    })
    
    if custom_domain:
        pulumi.export("custom_domain", custom_domain.domain)
    
    pulumi.export("webhook_id", webhook.id)
    
    # Export deployment status
    pulumi.export("deployment_status", "configured_with_pulumi_vercel_provider")
    pulumi.export("infrastructure_approach", "pulumi_iac_with_official_providers")


