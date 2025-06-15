"""
Orchestra AI - CI/CD Automation with Pulumi Automation API
Implements user's Infrastructure-as-Code strategy with programmatic deployments
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
import structlog

# Import enhanced secret manager
import sys
sys.path.append(str(Path(__file__).parent.parent))
from security.enhanced_secret_manager import secret_manager

logger = structlog.get_logger(__name__)

class PulumiAutomationOrchestrator:
    """Orchestrates CI/CD deployments using Pulumi Automation API"""
    
    def __init__(self, project_name: str = "orchestra-ai"):
        self.project_name = project_name
        self.work_dir = Path(__file__).parent
        
        # Validate Pulumi Automation API availability
        try:
            import pulumi
            from pulumi import automation as auto
            self.auto = auto
            self.pulumi = pulumi
        except ImportError:
            raise ImportError("Pulumi Automation API not available. Install with: pip install pulumi[automation]")
    
    def create_stack_config(self, stack_name: str) -> Dict[str, Any]:
        """Create stack configuration with secrets"""
        config = {}
        
        # Vercel configuration
        vercel_token = secret_manager.get_secret("VERCEL_TOKEN")
        if vercel_token:
            config["vercel:token"] = self.auto.ConfigValue(value=vercel_token, secret=True)
        
        # Lambda Labs configuration
        lambda_key = secret_manager.get_secret("LAMBDA_API_KEY")
        if lambda_key:
            config["lambda:apiKey"] = self.auto.ConfigValue(value=lambda_key, secret=True)
        
        # GitHub configuration
        github_token = secret_manager.get_secret("GITHUB_TOKEN")
        if github_token:
            config["github:token"] = self.auto.ConfigValue(value=github_token, secret=True)
        
        # Environment configuration
        config["orchestra:environment"] = self.auto.ConfigValue(value=stack_name)
        config["orchestra:projectName"] = self.auto.ConfigValue(value=self.project_name)
        
        return config
    
    def create_production_program(self):
        """Create Pulumi program for production deployment"""
        def pulumi_program():
            # Import our infrastructure modules
            from pulumi.vercel_integration import PulumiVercelIntegration
            from pulumi.lambda_labs_integration import LambdaLabsInfrastructure
            
            # Deploy Vercel frontend
            vercel_integration = PulumiVercelIntegration()
            project = vercel_integration.create_vercel_project()
            deployment = vercel_integration.create_vercel_deployment(project)
            webhook = vercel_integration.setup_webhook_integration(project)
            
            # Deploy Lambda Labs backend
            lambda_infra = LambdaLabsInfrastructure()
            instances = lambda_infra.create_orchestra_cluster()
            
            # Setup software on instances
            setup_commands = {}
            for instance_type, instance in instances.items():
                setup_commands[instance_type] = lambda_infra.setup_instance_software(instance, instance_type)
            
            # Export outputs
            self.pulumi.export("vercel_project_id", project.id)
            self.pulumi.export("vercel_production_url", deployment.url)
            self.pulumi.export("lambda_instances", {
                name: {
                    "id": instance.id,
                    "ip": instance.ip,
                    "status": instance.status
                } for name, instance in instances.items()
            })
            self.pulumi.export("deployment_timestamp", str(self.auto.get_current_time()))
            self.pulumi.export("infrastructure_status", "deployed")
        
        return pulumi_program
    
    def create_preview_program(self, branch: str):
        """Create Pulumi program for preview deployment"""
        def pulumi_program():
            from pulumi.vercel_integration import PulumiVercelIntegration
            
            # Deploy only frontend for preview
            vercel_integration = PulumiVercelIntegration()
            project = vercel_integration.create_vercel_project()
            
            # Create preview deployment
            preview_deployment = self.pulumi.vercel.Deployment(
                f"orchestra-preview-{branch}",
                project_id=project.id,
                production=False,
                ref=branch,
                opts=self.pulumi.ResourceOptions(depends_on=[project])
            )
            
            # Export preview outputs
            self.pulumi.export("preview_url", preview_deployment.url)
            self.pulumi.export("branch", branch)
            self.pulumi.export("deployment_type", "preview")
        
        return pulumi_program
    
    async def deploy_production(self) -> Dict[str, Any]:
        """Deploy production infrastructure"""
        try:
            logger.info("Starting production deployment")
            
            # Create or select production stack
            stack = self.auto.create_or_select_stack(
                stack_name="production",
                project_name=self.project_name,
                program=self.create_production_program(),
                work_dir=str(self.work_dir)
            )
            
            # Set configuration
            config = self.create_stack_config("production")
            for key, value in config.items():
                stack.set_config(key, value)
            
            # Refresh stack state
            logger.info("Refreshing stack state")
            refresh_result = stack.refresh()
            
            # Deploy
            logger.info("Deploying production stack")
            up_result = stack.up()
            
            # Get outputs
            outputs = stack.outputs()
            
            result = {
                "status": "success",
                "stack_name": "production",
                "outputs": outputs,
                "summary": {
                    "resources_created": up_result.summary.resource_changes.get("create", 0),
                    "resources_updated": up_result.summary.resource_changes.get("update", 0),
                    "resources_deleted": up_result.summary.resource_changes.get("delete", 0)
                }
            }
            
            logger.info("Production deployment completed successfully", result=result)
            return result
            
        except Exception as e:
            logger.error("Production deployment failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "stack_name": "production"
            }
    
    async def deploy_preview(self, branch: str) -> Dict[str, Any]:
        """Deploy preview environment for branch"""
        try:
            logger.info(f"Starting preview deployment for branch: {branch}")
            
            # Create or select preview stack
            stack_name = f"preview-{branch.replace('/', '-')}"
            stack = self.auto.create_or_select_stack(
                stack_name=stack_name,
                project_name=self.project_name,
                program=self.create_preview_program(branch),
                work_dir=str(self.work_dir)
            )
            
            # Set configuration
            config = self.create_stack_config(stack_name)
            for key, value in config.items():
                stack.set_config(key, value)
            
            # Deploy
            logger.info(f"Deploying preview stack: {stack_name}")
            up_result = stack.up()
            
            # Get outputs
            outputs = stack.outputs()
            
            result = {
                "status": "success",
                "stack_name": stack_name,
                "branch": branch,
                "outputs": outputs,
                "preview_url": outputs.get("preview_url", {}).get("value"),
                "summary": {
                    "resources_created": up_result.summary.resource_changes.get("create", 0),
                    "resources_updated": up_result.summary.resource_changes.get("update", 0)
                }
            }
            
            logger.info("Preview deployment completed successfully", result=result)
            return result
            
        except Exception as e:
            logger.error(f"Preview deployment failed for branch {branch}", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "stack_name": stack_name,
                "branch": branch
            }
    
    async def destroy_preview(self, branch: str) -> Dict[str, Any]:
        """Destroy preview environment"""
        try:
            stack_name = f"preview-{branch.replace('/', '-')}"
            logger.info(f"Destroying preview stack: {stack_name}")
            
            # Select stack
            stack = self.auto.select_stack(
                stack_name=stack_name,
                project_name=self.project_name,
                program=self.create_preview_program(branch),
                work_dir=str(self.work_dir)
            )
            
            # Destroy
            destroy_result = stack.destroy()
            
            result = {
                "status": "success",
                "stack_name": stack_name,
                "branch": branch,
                "summary": {
                    "resources_deleted": destroy_result.summary.resource_changes.get("delete", 0)
                }
            }
            
            logger.info("Preview environment destroyed successfully", result=result)
            return result
            
        except Exception as e:
            logger.error(f"Failed to destroy preview environment for branch {branch}", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "stack_name": stack_name,
                "branch": branch
            }
    
    def get_stack_status(self, stack_name: str) -> Dict[str, Any]:
        """Get status of a stack"""
        try:
            stack = self.auto.select_stack(
                stack_name=stack_name,
                project_name=self.project_name,
                work_dir=str(self.work_dir)
            )
            
            # Get stack info
            info = stack.info()
            outputs = stack.outputs()
            
            return {
                "status": "success",
                "stack_name": stack_name,
                "last_update": info.last_update,
                "resource_count": info.resource_count,
                "outputs": outputs
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "stack_name": stack_name
            }

class GitHubActionsIntegration:
    """GitHub Actions integration for CI/CD"""
    
    def __init__(self):
        self.orchestrator = PulumiAutomationOrchestrator()
    
    def generate_workflow_file(self) -> str:
        """Generate GitHub Actions workflow file"""
        return """name: Orchestra AI - Infrastructure Deployment

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

env:
  PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
  VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
  LAMBDA_API_KEY: ${{ secrets.LAMBDA_API_KEY }}
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

jobs:
  preview:
    name: Preview Deployment
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pulumi[automation]
          
      - name: Setup Pulumi
        uses: pulumi/actions@v4
        
      - name: Deploy Preview
        run: |
          python -c "
          import asyncio
          from pulumi.ci_cd_automation import PulumiAutomationOrchestrator
          
          async def main():
              orchestrator = PulumiAutomationOrchestrator()
              result = await orchestrator.deploy_preview('${{ github.head_ref }}')
              print(f'Preview URL: {result.get(\"preview_url\", \"N/A\")}')
          
          asyncio.run(main())
          "
          
      - name: Comment PR
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '🚀 Preview deployment completed! Check the logs for the preview URL.'
            })

  production:
    name: Production Deployment
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pulumi[automation]
          
      - name: Setup Pulumi
        uses: pulumi/actions@v4
        
      - name: Deploy Production
        run: |
          python -c "
          import asyncio
          from pulumi.ci_cd_automation import PulumiAutomationOrchestrator
          
          async def main():
              orchestrator = PulumiAutomationOrchestrator()
              result = await orchestrator.deploy_production()
              print(f'Production deployment: {result[\"status\"]}')
              if result[\"status\"] == \"success\":
                  print(f'Vercel URL: {result[\"outputs\"].get(\"vercel_production_url\", {}).get(\"value\", \"N/A\")}')
          
          asyncio.run(main())
          "

  cleanup:
    name: Cleanup Preview
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request' && github.event.action == 'closed'
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pulumi[automation]
          
      - name: Setup Pulumi
        uses: pulumi/actions@v4
        
      - name: Destroy Preview
        run: |
          python -c "
          import asyncio
          from pulumi.ci_cd_automation import PulumiAutomationOrchestrator
          
          async def main():
              orchestrator = PulumiAutomationOrchestrator()
              result = await orchestrator.destroy_preview('${{ github.head_ref }}')
              print(f'Preview cleanup: {result[\"status\"]}')
          
          asyncio.run(main())
          "
"""

class WebhookHandler:
    """Handle deployment webhooks"""
    
    def __init__(self):
        self.orchestrator = PulumiAutomationOrchestrator()
    
    async def handle_github_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GitHub webhook events"""
        event_type = payload.get("action")
        ref = payload.get("ref", "")
        
        if event_type == "push" and ref == "refs/heads/main":
            # Deploy to production
            return await self.orchestrator.deploy_production()
        
        elif event_type == "pull_request":
            action = payload.get("action")
            branch = payload.get("pull_request", {}).get("head", {}).get("ref")
            
            if action in ["opened", "synchronize"]:
                # Deploy preview
                return await self.orchestrator.deploy_preview(branch)
            elif action == "closed":
                # Cleanup preview
                return await self.orchestrator.destroy_preview(branch)
        
        return {"status": "ignored", "reason": "No action required"}
    
    async def handle_vercel_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Vercel deployment webhooks"""
        event_type = payload.get("type")
        
        if event_type == "deployment.succeeded":
            # Log successful deployment
            logger.info("Vercel deployment succeeded", payload=payload)
            return {"status": "logged"}
        
        elif event_type == "deployment.failed":
            # Handle deployment failure
            logger.error("Vercel deployment failed", payload=payload)
            return {"status": "error_logged"}
        
        return {"status": "ignored"}

# CLI interface for manual operations
class PulumiCLI:
    """Command-line interface for Pulumi operations"""
    
    def __init__(self):
        self.orchestrator = PulumiAutomationOrchestrator()
    
    async def deploy_production_cli(self):
        """CLI command to deploy production"""
        print("🚀 Starting production deployment...")
        result = await self.orchestrator.deploy_production()
        
        if result["status"] == "success":
            print("✅ Production deployment completed successfully!")
            print(f"Vercel URL: {result['outputs'].get('vercel_production_url', {}).get('value', 'N/A')}")
        else:
            print(f"❌ Production deployment failed: {result['error']}")
    
    async def deploy_preview_cli(self, branch: str):
        """CLI command to deploy preview"""
        print(f"🚀 Starting preview deployment for branch: {branch}")
        result = await self.orchestrator.deploy_preview(branch)
        
        if result["status"] == "success":
            print("✅ Preview deployment completed successfully!")
            print(f"Preview URL: {result.get('preview_url', 'N/A')}")
        else:
            print(f"❌ Preview deployment failed: {result['error']}")
    
    def get_status_cli(self, stack_name: str):
        """CLI command to get stack status"""
        result = self.orchestrator.get_stack_status(stack_name)
        
        if result["status"] == "success":
            print(f"📊 Stack Status: {stack_name}")
            print(f"Last Update: {result['last_update']}")
            print(f"Resource Count: {result['resource_count']}")
            print("Outputs:")
            for key, value in result["outputs"].items():
                print(f"  {key}: {value.get('value', 'N/A')}")
        else:
            print(f"❌ Failed to get stack status: {result['error']}")

# Export main classes
__all__ = [
    "PulumiAutomationOrchestrator",
    "GitHubActionsIntegration", 
    "WebhookHandler",
    "PulumiCLI"
]

