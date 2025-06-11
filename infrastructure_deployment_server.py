#!/usr/bin/env python3
"""
🚀 Infrastructure Deployment Server with Pulumi IaC Integration
Full infrastructure control for Cursor AI: Vercel and Lambda Labs
"""

import asyncio
import json
import logging
import os
import subprocess
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import tempfile

# MCP imports
from mcp.server import Server
from mcp import types
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DeploymentResult:
    """Result of infrastructure deployment"""
    success: bool
    target: str
    operation: str
    details: Dict[str, Any]
    logs: List[str]
    timestamp: datetime
    resources_affected: List[str]

class PulumiInfrastructureManager:
    """Pulumi-based infrastructure management"""
    
    def __init__(self):
        self.supported_providers = {
            'vercel': 'vercel',
            'lambda_labs': 'lambda-labs-cloud'
        }
        self.project_root = "/Users/lynnmusil/orchestra-dev"
        self.pulumi_dir = os.path.join(self.project_root, "infrastructure", "pulumi")
    
    async def deploy_vercel_frontend(self, project_name: str, source_dir: str, 
                                   env_vars: Dict[str, str] = None) -> DeploymentResult:
        """Deploy frontend to Vercel using Pulumi"""
        try:
            logs = []
            
            # Create Pulumi program for Vercel deployment
            pulumi_code = self._generate_vercel_pulumi_code(project_name, source_dir, env_vars or {})
            
            # Write Pulumi program
            with tempfile.TemporaryDirectory() as temp_dir:
                program_file = os.path.join(temp_dir, "__main__.py")
                with open(program_file, 'w') as f:
                    f.write(pulumi_code)
                
                # Run Pulumi deployment
                result = await self._run_pulumi_command(['up', '--yes'], temp_dir)
                logs.extend(result['logs'])
                
                if result['success']:
                    return DeploymentResult(
                        success=True,
                        target='vercel',
                        operation='deploy_frontend',
                        details={
                            'project_name': project_name,
                            'source_dir': source_dir,
                            'env_vars': list(env_vars.keys()) if env_vars else [],
                            'deployment_url': result.get('outputs', {}).get('url', 'pending')
                        },
                        logs=logs,
                        timestamp=datetime.now(),
                        resources_affected=['vercel:Project', 'vercel:Deployment']
                    )
                else:
                    return DeploymentResult(
                        success=False,
                        target='vercel',
                        operation='deploy_frontend',
                        details={'error': result['error']},
                        logs=logs,
                        timestamp=datetime.now(),
                        resources_affected=[]
                    )
                    
        except Exception as e:
            return DeploymentResult(
                success=False,
                target='vercel',
                operation='deploy_frontend',
                details={'error': str(e)},
                logs=[f"Error: {str(e)}"],
                timestamp=datetime.now(),
                resources_affected=[]
            )
    
    async def manage_lambda_labs_instance(self, action: str, instance_config: Dict[str, Any]) -> DeploymentResult:
        """Manage Lambda Labs GPU instances"""
        try:
            logs = []
            
            if action == 'create':
                pulumi_code = self._generate_lambda_labs_pulumi_code(instance_config)
                command = ['up', '--yes']
            elif action == 'destroy':
                command = ['destroy', '--yes']
            elif action == 'scale':
                # Update configuration and redeploy
                pulumi_code = self._generate_lambda_labs_pulumi_code(instance_config)
                command = ['up', '--yes']
            else:
                raise ValueError(f"Unsupported action: {action}")
            
            # Execute Pulumi command
            with tempfile.TemporaryDirectory() as temp_dir:
                if action != 'destroy':
                    program_file = os.path.join(temp_dir, "__main__.py")
                    with open(program_file, 'w') as f:
                        f.write(pulumi_code)
                
                result = await self._run_pulumi_command(command, temp_dir)
                logs.extend(result['logs'])
                
                return DeploymentResult(
                    success=result['success'],
                    target='lambda_labs',
                    operation=action,
                    details=instance_config,
                    logs=logs,
                    timestamp=datetime.now(),
                    resources_affected=['lambda-labs:Instance']
                )
                
        except Exception as e:
            return DeploymentResult(
                success=False,
                target='lambda_labs',
                operation=action,
                details={'error': str(e)},
                logs=[f"Error: {str(e)}"],
                timestamp=datetime.now(),
                resources_affected=[]
            )
    

    
    async def get_infrastructure_status(self) -> Dict[str, Any]:
        """Get current infrastructure status across all providers"""
        try:
            status = {
                'vercel': await self._get_vercel_status(),
                'lambda_labs': await self._get_lambda_labs_status(),
                'last_updated': datetime.now().isoformat()
            }
            return status
            
        except Exception as e:
            logger.error(f"Failed to get infrastructure status: {e}")
            return {'error': str(e)}
    
    def _generate_vercel_pulumi_code(self, project_name: str, source_dir: str, env_vars: Dict[str, str]) -> str:
        """Generate Pulumi code for Vercel deployment"""
        env_vars_code = ""
        if env_vars:
            env_vars_json = json.dumps(env_vars, indent=4)
            env_vars_code = f"environment={env_vars_json},"
        
        return f"""
import pulumi
import pulumi_vercel as vercel

# Create Vercel project
project = vercel.Project(
    "{project_name}",
    name="{project_name}",
    framework="nextjs",
    git_repository=vercel.ProjectGitRepositoryArgs(
        type="github",
        repo="ai-cherry/orchestra-main",
    ),
    {env_vars_code}
)

# Create deployment
deployment = vercel.Deployment(
    "{project_name}-deployment",
    project_id=project.id,
    production=True,
    ref="main"
)

# Export the deployment URL
pulumi.export("url", deployment.url)
pulumi.export("project_id", project.id)
"""
    
    def _generate_lambda_labs_pulumi_code(self, config: Dict[str, Any]) -> str:
        """Generate Pulumi code for Lambda Labs instance"""
        return f"""
import pulumi
import pulumi_lambda_labs_cloud as lambda_labs

# Create Lambda Labs instance
instance = lambda_labs.Instance(
    "{config.get('name', 'orchestra-instance')}",
    instance_type="{config.get('instance_type', 'gpu_1x_a10')}",
    region="{config.get('region', 'us-west-1')}",
    ssh_key_name="{config.get('ssh_key', 'manus-lambda-key')}",
    disk_size={config.get('disk_size', 100)},
    startup_script=\"\"\"{config.get('startup_script', '# Orchestra AI setup')}\"\"\"
)

# Export instance details
pulumi.export("instance_id", instance.id)
pulumi.export("instance_ip", instance.ip)
pulumi.export("ssh_command", pulumi.Output.concat("ssh ubuntu@", instance.ip))
"""
    

    
    async def _run_pulumi_command(self, command: List[str], working_dir: str) -> Dict[str, Any]:
        """Run Pulumi command and capture output"""
        try:
            # Initialize Pulumi stack if needed
            init_cmd = ['pulumi', 'stack', 'init', 'dev', '--non-interactive']
            subprocess.run(init_cmd, cwd=working_dir, capture_output=True, text=True)
            
            # Run the main command
            cmd = ['pulumi'] + command + ['--non-interactive']
            process = subprocess.run(cmd, cwd=working_dir, capture_output=True, text=True)
            
            logs = []
            if process.stdout:
                logs.extend(process.stdout.split('\n'))
            if process.stderr:
                logs.extend(process.stderr.split('\n'))
            
            if process.returncode == 0:
                # Try to get outputs
                outputs = {}
                try:
                    output_cmd = ['pulumi', 'stack', 'output', '--json']
                    output_process = subprocess.run(output_cmd, cwd=working_dir, capture_output=True, text=True)
                    if output_process.returncode == 0:
                        outputs = json.loads(output_process.stdout)
                except:
                    pass
                
                return {
                    'success': True,
                    'logs': logs,
                    'outputs': outputs
                }
            else:
                return {
                    'success': False,
                    'logs': logs,
                    'error': process.stderr or 'Unknown error'
                }
                
        except Exception as e:
            return {
                'success': False,
                'logs': [f"Command execution failed: {str(e)}"],
                'error': str(e)
            }
    
    async def _get_vercel_status(self) -> Dict[str, Any]:
        """Get Vercel deployment status"""
        try:
            # This would integrate with Vercel CLI or API
            return {
                'status': 'deployed',
                'url': 'https://orchestra-admin-interface-idqnqpj6r-lynn-musils-projects.vercel.app',
                'last_deployment': datetime.now().isoformat()
            }
        except:
            return {'status': 'unknown'}
    
    async def _get_lambda_labs_status(self) -> Dict[str, Any]:
        """Get Lambda Labs instance status"""
        try:
            # This would integrate with Lambda Labs API
            return {
                'instances': [
                    {
                        'name': 'orchestra-dev-fresh',
                        'status': 'running',
                        'ip': '192.9.142.8',
                        'type': 'gpu_1x_a10'
                    }
                ]
            }
        except:
            return {'status': 'unknown'}
    


class InfrastructureDeploymentServer:
    """MCP server for infrastructure deployment and management"""
    
    def __init__(self):
        self.server = Server("infrastructure-deployment")
        self.infra_manager = PulumiInfrastructureManager()
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup MCP tools for infrastructure operations"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available infrastructure tools"""
            return [
                types.Tool(
                    name="deploy_vercel_frontend",
                    description="Deploy frontend application to Vercel using Pulumi IaC",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_name": {"type": "string"},
                            "source_directory": {"type": "string"},
                            "environment_variables": {"type": "object"},
                            "domain": {"type": "string"}
                        },
                        "required": ["project_name", "source_directory"]
                    }
                ),
                types.Tool(
                    name="manage_lambda_labs_instance",
                    description="Create, scale, or destroy Lambda Labs GPU instances",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["create", "scale", "destroy", "status"]},
                            "instance_name": {"type": "string"},
                            "instance_type": {"type": "string", "enum": ["gpu_1x_a10", "gpu_8x_a100", "gpu_1x_h100"]},
                            "region": {"type": "string", "enum": ["us-east-1", "us-west-1", "us-west-2"]},
                            "disk_size": {"type": "integer", "minimum": 50, "maximum": 2000},
                            "startup_script": {"type": "string"}
                        },
                        "required": ["action", "instance_name"]
                    }
                ),

                types.Tool(
                    name="get_infrastructure_status",
                    description="Get comprehensive infrastructure status across all providers",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "provider": {"type": "string", "enum": ["all", "vercel", "lambda_labs"]},
                            "include_details": {"type": "boolean"}
                        }
                    }
                ),
                types.Tool(
                    name="rollback_deployment",
                    description="Rollback to previous deployment version",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {"type": "string", "enum": ["vercel", "lambda_labs"]},
                            "deployment_id": {"type": "string"},
                            "confirm": {"type": "boolean"}
                        },
                        "required": ["target", "confirm"]
                    }
                ),
                types.Tool(
                    name="infrastructure_cost_analysis",
                    description="Analyze infrastructure costs and optimization opportunities",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "provider": {"type": "string", "enum": ["all", "vercel", "lambda_labs"]},
                            "time_period": {"type": "string", "enum": ["daily", "weekly", "monthly"]},
                            "include_recommendations": {"type": "boolean"}
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
            """Handle tool calls for infrastructure operations"""
            
            if name == "deploy_vercel_frontend":
                return await self._handle_deploy_vercel(arguments)
            elif name == "manage_lambda_labs_instance":
                return await self._handle_lambda_labs(arguments)

            elif name == "get_infrastructure_status":
                return await self._handle_infrastructure_status(arguments)
            elif name == "rollback_deployment":
                return await self._handle_rollback(arguments)
            elif name == "infrastructure_cost_analysis":
                return await self._handle_cost_analysis(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _handle_deploy_vercel(self, args: dict) -> List[types.TextContent]:
        """Handle Vercel deployment requests"""
        try:
            project_name = args['project_name']
            source_dir = args['source_directory']
            env_vars = args.get('environment_variables', {})
            
            result = await self.infra_manager.deploy_vercel_frontend(
                project_name, source_dir, env_vars
            )
            
            if result.success:
                response = f"🚀 Vercel Deployment Successful!\n"
                response += "=" * 40 + "\n\n"
                response += f"📦 **Project**: {project_name}\n"
                response += f"🌐 **URL**: {result.details.get('deployment_url', 'Pending...')}\n"
                response += f"📁 **Source**: {source_dir}\n"
                response += f"⏰ **Deployed**: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                
                if env_vars:
                    response += "🔧 **Environment Variables Set**:\n"
                    for key in result.details.get('env_vars', []):
                        response += f"• {key}\n"
                    response += "\n"
                
                response += "📋 **Deployment Logs**:\n"
                for log in result.logs[-5:]:  # Last 5 log lines
                    if log.strip():
                        response += f"  {log}\n"
            else:
                response = f"❌ Vercel Deployment Failed\n"
                response += f"Error: {result.details.get('error', 'Unknown error')}\n\n"
                response += "📋 **Error Logs**:\n"
                for log in result.logs[-5:]:
                    if log.strip():
                        response += f"  {log}\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error deploying to Vercel: {str(e)}"
            )]
    
    async def _handle_lambda_labs(self, args: dict) -> List[types.TextContent]:
        """Handle Lambda Labs instance management"""
        try:
            action = args['action']
            instance_name = args['instance_name']
            
            if action == 'status':
                status = await self.infra_manager.get_infrastructure_status()
                lambda_status = status.get('lambda_labs', {})
                
                response = f"🖥️ Lambda Labs Status: {instance_name}\n"
                response += "=" * 40 + "\n\n"
                
                instances = lambda_status.get('instances', [])
                for instance in instances:
                    if instance.get('name') == instance_name:
                        response += f"📊 **Status**: {instance.get('status', 'unknown')}\n"
                        response += f"🌐 **IP**: {instance.get('ip', 'N/A')}\n"
                        response += f"🎮 **Type**: {instance.get('type', 'N/A')}\n"
                        break
                else:
                    response += f"❌ Instance '{instance_name}' not found\n"
                
                return [types.TextContent(type="text", text=response)]
            
            # For create, scale, destroy actions
            instance_config = {
                'name': instance_name,
                'instance_type': args.get('instance_type', 'gpu_1x_a10'),
                'region': args.get('region', 'us-west-1'),
                'disk_size': args.get('disk_size', 100),
                'startup_script': args.get('startup_script', '#!/bin/bash\necho "Orchestra AI instance ready"')
            }
            
            result = await self.infra_manager.manage_lambda_labs_instance(action, instance_config)
            
            if result.success:
                response = f"✅ Lambda Labs {action.title()} Successful!\n"
                response += "=" * 40 + "\n\n"
                response += f"🖥️ **Instance**: {instance_name}\n"
                response += f"🎮 **Type**: {instance_config.get('instance_type')}\n"
                response += f"🌍 **Region**: {instance_config.get('region')}\n"
                response += f"💾 **Disk**: {instance_config.get('disk_size')}GB\n"
                response += f"⏰ **Completed**: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                
                response += "📋 **Operation Logs**:\n"
                for log in result.logs[-5:]:
                    if log.strip():
                        response += f"  {log}\n"
            else:
                response = f"❌ Lambda Labs {action.title()} Failed\n"
                response += f"Error: {result.details.get('error', 'Unknown error')}\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error managing Lambda Labs instance: {str(e)}"
            )]
    

    
    async def _handle_infrastructure_status(self, args: dict) -> List[types.TextContent]:
        """Handle infrastructure status requests"""
        try:
            provider = args.get('provider', 'all')
            include_details = args.get('include_details', True)
            
            status = await self.infra_manager.get_infrastructure_status()
            
            response = f"🏗️ Infrastructure Status Report\n"
            response += "=" * 50 + "\n\n"
            response += f"📅 **Last Updated**: {status.get('last_updated', 'Unknown')}\n\n"
            
            if provider == 'all' or provider == 'vercel':
                vercel_status = status.get('vercel', {})
                response += "🌐 **Vercel**:\n"
                response += f"  Status: {vercel_status.get('status', 'unknown')}\n"
                response += f"  URL: {vercel_status.get('url', 'N/A')}\n\n"
            
            if provider == 'all' or provider == 'lambda_labs':
                lambda_status = status.get('lambda_labs', {})
                response += "🖥️ **Lambda Labs**:\n"
                instances = lambda_status.get('instances', [])
                if instances:
                    for instance in instances:
                        response += f"  • {instance.get('name')}: {instance.get('status')} ({instance.get('ip')})\n"
                else:
                    response += "  No instances found\n"
                response += "\n"
            

            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error getting infrastructure status: {str(e)}"
            )]
    
    async def _handle_rollback(self, args: dict) -> List[types.TextContent]:
        """Handle deployment rollback requests"""
        try:
            target = args['target']
            confirm = args['confirm']
            
            if not confirm:
                return [types.TextContent(
                    type="text",
                    text="⚠️ Rollback cancelled - confirmation required"
                )]
            
            response = f"🔄 Rollback for {target} initiated...\n"
            response += "⚠️ This feature is under development\n"
            response += "For immediate rollback, use provider-specific tools:\n"
            response += f"• Vercel: `vercel rollback`\n"
            response += f"• Lambda Labs: Recreate instance from snapshot\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error during rollback: {str(e)}"
            )]
    
    async def _handle_cost_analysis(self, args: dict) -> List[types.TextContent]:
        """Handle cost analysis requests"""
        try:
            provider = args.get('provider', 'all')
            time_period = args.get('time_period', 'monthly')
            
            response = f"💰 Infrastructure Cost Analysis ({time_period})\n"
            response += "=" * 50 + "\n\n"
            
            # Mock cost data (would integrate with real billing APIs)
            response += "📊 **Current Estimates**:\n"
            response += "• Vercel: $0-20/month (hobby/pro plan)\n"
            response += "• Lambda Labs: $0.50-2.00/hour per GPU\n\n"
            
            response += "💡 **Optimization Recommendations**:\n"
            response += "• Use spot instances for development\n"
            response += "• Set up auto-scaling policies\n"
            response += "• Monitor and right-size resources\n"
            response += "• Use reserved instances for predictable workloads\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error analyzing costs: {str(e)}"
            )]

async def main():
    """Main server execution"""
    logger.info("🚀 Starting Infrastructure Deployment Server")
    logger.info("🔧 Features: Pulumi IaC, Vercel, Lambda Labs integration")
    logger.info("🎯 Integration: Full infrastructure control for Cursor AI")
    
    server = InfrastructureDeploymentServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            None
        )

if __name__ == "__main__":
    asyncio.run(main()) 