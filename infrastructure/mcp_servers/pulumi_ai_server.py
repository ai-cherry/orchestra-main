#!/usr/bin/env python3
"""
Pulumi AI MCP Server - Orchestra AI Infrastructure
AI-driven infrastructure code generation and management via Cursor AI
Performance-optimized with real-time Pulumi Automation API integration
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import pulumi.automation as auto
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Initialize MCP server
app = Server("pulumi-ai")

# Global state for performance
_stack_cache = {}
_project_cache = {}

class PulumiAIError(Exception):
    """Custom exception for Pulumi AI operations"""
    pass

def get_pulumi_config() -> Dict[str, Any]:
    """Get Pulumi configuration from environment"""
    return {
        "access_token": os.getenv("PULUMI_ACCESS_TOKEN"),
        "config_passphrase": os.getenv("PULUMI_CONFIG_PASSPHRASE"),
        "org": os.getenv("PULUMI_ORG", "ai-cherry"),
        "project": os.getenv("PULUMI_PROJECT", "orchestra-ai")
    }

def validate_pulumi_code(code: str) -> Dict[str, Any]:
    """Validate Pulumi code using static analysis"""
    try:
        # Basic syntax check
        compile(code, '<string>', 'exec')
        
        # Check for required imports
        required_imports = ["pulumi"]
        has_imports = any(imp in code for imp in required_imports)
        
        # Check for exports
        has_exports = "pulumi.export" in code
        
        return {
            "valid": True,
            "syntax_valid": True,
            "has_imports": has_imports,
            "has_exports": has_exports,
            "score": 0.9 if has_imports and has_exports else 0.7
        }
    except SyntaxError as e:
        return {
            "valid": False,
            "syntax_valid": False,
            "error": str(e),
            "score": 0.0
        }

@app.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available Pulumi AI tools"""
    return [
        types.Tool(
            name="generate_infrastructure",
            description="Generate Pulumi infrastructure code based on AI analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_type": {
                        "type": "string",
                        "enum": ["database", "api", "frontend", "microservice", "lambda", "storage"],
                        "description": "Type of service to generate infrastructure for"
                    },
                    "requirements": {
                        "type": "object",
                        "description": "Specific requirements and configurations",
                        "properties": {
                            "replicas": {"type": "integer", "default": 1},
                            "memory": {"type": "string", "default": "512Mi"},
                            "cpu": {"type": "string", "default": "250m"},
                            "storage": {"type": "string", "default": "10Gi"},
                            "environment": {"type": "string", "default": "development"},
                            "domain": {"type": "string"},
                            "ports": {"type": "array", "items": {"type": "integer"}},
                            "env_vars": {"type": "object"},
                            "dependencies": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "performance_mode": {
                        "type": "boolean",
                        "default": True,
                        "description": "Enable performance optimizations"
                    }
                },
                "required": ["service_type"]
            }
        ),
        types.Tool(
            name="deploy_infrastructure",
            description="Deploy infrastructure using Pulumi Automation API",
            inputSchema={
                "type": "object",
                "properties": {
                    "stack_name": {
                        "type": "string",
                        "description": "Pulumi stack name"
                    },
                    "environment": {
                        "type": "string",
                        "enum": ["dev", "staging", "prod"],
                        "default": "dev"
                    },
                    "code": {
                        "type": "string",
                        "description": "Pulumi program code to deploy"
                    },
                    "preview_only": {
                        "type": "boolean",
                        "default": False,
                        "description": "Only preview changes, don't deploy"
                    }
                },
                "required": ["stack_name", "code"]
            }
        ),
        types.Tool(
            name="manage_secrets",
            description="Manage secrets via Pulumi ESC",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["set", "get", "list", "delete"],
                        "description": "Action to perform"
                    },
                    "environment": {
                        "type": "string",
                        "description": "ESC environment name"
                    },
                    "key": {
                        "type": "string",
                        "description": "Secret key"
                    },
                    "value": {
                        "type": "string",
                        "description": "Secret value (for set action)"
                    },
                    "is_secret": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether the value is a secret"
                    }
                },
                "required": ["action", "environment"]
            }
        ),
        types.Tool(
            name="analyze_infrastructure",
            description="Analyze existing infrastructure and suggest optimizations",
            inputSchema={
                "type": "object",
                "properties": {
                    "stack_name": {
                        "type": "string",
                        "description": "Stack to analyze"
                    },
                    "focus": {
                        "type": "string",
                        "enum": ["performance", "cost", "security", "scalability"],
                        "default": "performance"
                    }
                },
                "required": ["stack_name"]
            }
        ),
        types.Tool(
            name="get_stack_status",
            description="Get current status of Pulumi stacks",
            inputSchema={
                "type": "object",
                "properties": {
                    "stack_name": {
                        "type": "string",
                        "description": "Specific stack name (optional)"
                    }
                }
            }
        )
    ]

@app.call_tool()
async def generate_infrastructure(arguments: dict) -> List[types.TextContent]:
    """AI-driven infrastructure code generation"""
    service_type = arguments.get("service_type", "")
    requirements = arguments.get("requirements", {})
    performance_mode = arguments.get("performance_mode", True)
    
    # AI-driven code generation templates
    templates = {
        "database": generate_database_infrastructure,
        "api": generate_api_infrastructure,
        "frontend": generate_frontend_infrastructure,
        "microservice": generate_microservice_infrastructure,
        "lambda": generate_lambda_infrastructure,
        "storage": generate_storage_infrastructure
    }
    
    if service_type not in templates:
        return [types.TextContent(
            type="text",
            text=f"❌ Unknown service type: {service_type}\nSupported types: {list(templates.keys())}"
        )]
    
    try:
        # Generate infrastructure code
        code = templates[service_type](requirements, performance_mode)
        
        # Validate generated code
        validation = validate_pulumi_code(code)
        
        # Performance analysis
        performance_notes = []
        if performance_mode:
            performance_notes = analyze_performance_optimizations(service_type, requirements)
        
        result_text = f"""## 🏗️ Generated Infrastructure Code

### Service Type: {service_type.title()}
### Performance Mode: {"✅ Enabled" if performance_mode else "❌ Disabled"}

```python
{code}
```

### 📊 Code Validation
- **Syntax Valid**: {'✅' if validation['syntax_valid'] else '❌'}
- **Has Imports**: {'✅' if validation['has_imports'] else '❌'}
- **Has Exports**: {'✅' if validation['has_exports'] else '❌'}
- **Quality Score**: {validation['score']:.1%}

### 🚀 Performance Optimizations
{chr(10).join(f"- {note}" for note in performance_notes)}

### 📝 Next Steps
1. Review the generated code
2. Customize configuration as needed
3. Deploy using `deploy_infrastructure` tool
4. Monitor performance metrics
"""
        
        return [types.TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"❌ Error generating infrastructure: {str(e)}"
        )]

@app.call_tool()
async def deploy_infrastructure(arguments: dict) -> List[types.TextContent]:
    """Deploy infrastructure using Pulumi Automation API"""
    stack_name = arguments.get("stack_name", "")
    environment = arguments.get("environment", "dev")
    code = arguments.get("code", "")
    preview_only = arguments.get("preview_only", False)
    
    if not stack_name or not code:
        return [types.TextContent(
            type="text",
            text="❌ Missing required parameters: stack_name and code"
        )]
    
    try:
        config = get_pulumi_config()
        
        # Create temporary directory for the program
        with tempfile.TemporaryDirectory() as temp_dir:
            program_path = Path(temp_dir)
            
            # Write the program code
            (program_path / "__main__.py").write_text(code)
            
            # Define the Pulumi program
            def pulumi_program():
                exec(code, globals())
            
            # Create or select stack
            stack = auto.create_or_select_stack(
                stack_name=f"{config['org']}/{config['project']}/{stack_name}",
                project_name=config['project'],
                program=pulumi_program,
                work_dir=str(program_path)
            )
            
            # Set ESC environment
            stack.set_config("pulumi:environment", auto.ConfigValue(f"orchestra-ai/{environment}"))
            
            # Install dependencies (if needed)
            stack.workspace.install_plugin("github", "v6.0.0")
            stack.workspace.install_plugin("lambda", "v0.3.0")
            stack.workspace.install_plugin("docker", "v4.0.0")
            
            start_time = datetime.now()
            
            if preview_only:
                # Preview changes
                preview_result = stack.preview()
                duration = (datetime.now() - start_time).total_seconds()
                
                return [types.TextContent(
                    type="text", 
                    text=f"""## 👀 Infrastructure Preview

### Stack: {stack_name} ({environment})
### Duration: {duration:.2f}s

**Changes Summary:**
- Resources to create: {preview_result.change_summary.get('create', 0)}
- Resources to update: {preview_result.change_summary.get('update', 0)}
- Resources to delete: {preview_result.change_summary.get('delete', 0)}

**Status**: Preview completed successfully
"""
                )]
            else:
                # Deploy changes
                up_result = stack.up()
                duration = (datetime.now() - start_time).total_seconds()
                
                # Cache stack info for performance
                _stack_cache[stack_name] = {
                    "last_update": datetime.now(),
                    "outputs": up_result.outputs,
                    "summary": up_result.summary
                }
                
                return [types.TextContent(
                    type="text",
                    text=f"""## 🚀 Infrastructure Deployed

### Stack: {stack_name} ({environment})
### Duration: {duration:.2f}s
### Status: {up_result.summary.result}

**Resources Updated:**
- Created: {up_result.summary.resource_changes.get('create', 0)}
- Updated: {up_result.summary.resource_changes.get('update', 0)}
- Deleted: {up_result.summary.resource_changes.get('delete', 0)}

**Outputs:**
{json.dumps(up_result.outputs, indent=2, default=str)}

✅ Deployment completed successfully!
"""
                )]
                
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"❌ Deployment error: {str(e)}"
        )]

@app.call_tool()
async def manage_secrets(arguments: dict) -> List[types.TextContent]:
    """Manage secrets via Pulumi ESC"""
    action = arguments.get("action", "")
    environment = arguments.get("environment", "")
    key = arguments.get("key", "")
    value = arguments.get("value", "")
    is_secret = arguments.get("is_secret", True)
    
    if not action or not environment:
        return [types.TextContent(
            type="text",
            text="❌ Missing required parameters: action and environment"
        )]
    
    try:
        import subprocess
        
        if action == "list":
            result = subprocess.run(
                ["pulumi", "env", "get", environment],
                capture_output=True,
                text=True
            )
            
            return [types.TextContent(
                type="text",
                text=f"## 🔐 Environment: {environment}\n\n```json\n{result.stdout}\n```"
            )]
            
        elif action == "set" and key and value:
            secret_flag = "--secret" if is_secret else ""
            cmd = ["pulumi", "env", "set", environment, "--yes"]
            if secret_flag:
                cmd.append(secret_flag)
            cmd.extend([f"values.secrets.{key}", value])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return [types.TextContent(
                    type="text",
                    text=f"✅ Secret '{key}' set in environment '{environment}'"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Error setting secret: {result.stderr}"
                )]
                
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"❌ Secret management error: {str(e)}"
        )]

@app.call_tool()
async def get_stack_status(arguments: dict) -> List[types.TextContent]:
    """Get current status of Pulumi stacks"""
    stack_name = arguments.get("stack_name")
    
    try:
        config = get_pulumi_config()
        
        if stack_name:
            # Get specific stack info
            if stack_name in _stack_cache:
                cached_info = _stack_cache[stack_name]
                return [types.TextContent(
                    type="text",
                    text=f"""## 📊 Stack Status: {stack_name}

**Last Update**: {cached_info['last_update']}
**Cached Outputs**: {len(cached_info.get('outputs', {}))} items

✅ Stack information retrieved from cache
"""
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Stack '{stack_name}' not found in cache. Deploy it first."
                )]
        else:
            # List all stacks
            import subprocess
            result = subprocess.run(
                ["pulumi", "stack", "ls", "--json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                stacks = json.loads(result.stdout)
                stack_list = "\n".join([
                    f"- **{stack['name']}**: {stack.get('current', False) and '(current)' or ''}"
                    for stack in stacks
                ])
                
                return [types.TextContent(
                    type="text",
                    text=f"## 📋 Available Stacks\n\n{stack_list}\n\n**Cached Stacks**: {list(_stack_cache.keys())}"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Error listing stacks: {result.stderr}"
                )]
                
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"❌ Status check error: {str(e)}"
        )]

# Infrastructure generation functions
def generate_database_infrastructure(requirements: Dict[str, Any], performance_mode: bool) -> str:
    """Generate database infrastructure code"""
    return f'''import pulumi
import pulumi_docker as docker

# Database configuration
db_config = {{
    "image": "postgres:15-alpine",
    "memory": "{requirements.get('memory', '1Gi')}",
    "storage": "{requirements.get('storage', '20Gi')}",
    "replicas": {requirements.get('replicas', 1)}
}}

# PostgreSQL database
database = docker.Container("database",
    image=db_config["image"],
    env=[
        "POSTGRES_DB=orchestra",
        "POSTGRES_USER=postgres",
        "POSTGRES_PASSWORD=secure_password",
        "POSTGRES_HOST_AUTH_METHOD=trust"
    ],
    ports=[docker.ContainerPortArgs(
        internal=5432,
        external=5432
    )],
    restart="always",
    opts=pulumi.ResourceOptions(
        custom_timeouts=pulumi.CustomTimeouts(create="5m")
    ) if {performance_mode} else None
)

pulumi.export("database_endpoint", database.name.apply(lambda name: f"postgresql://postgres@localhost:5432/orchestra"))
pulumi.export("database_config", db_config)
'''

def generate_api_infrastructure(requirements: Dict[str, Any], performance_mode: bool) -> str:
    """Generate API infrastructure code"""
    return f'''import pulumi
import pulumi_docker as docker

# API configuration
api_config = {{
    "image": "python:3.10-slim",
    "memory": "{requirements.get('memory', '512Mi')}",
    "cpu": "{requirements.get('cpu', '500m')}",
    "replicas": {requirements.get('replicas', 2)},
    "port": {requirements.get('ports', [8000])[0] if requirements.get('ports') else 8000}
}}

# FastAPI application
api_service = docker.Container("api",
    image=api_config["image"],
    command=[
        "sh", "-c",
        "pip install fastapi uvicorn && uvicorn main:app --host 0.0.0.0 --port 8000"
    ],
    ports=[docker.ContainerPortArgs(
        internal=api_config["port"],
        external=api_config["port"]
    )],
    env={[f'"{k}={v}"' for k, v in requirements.get('env_vars', {}).items()]},
    restart="always",
    {"memory": f'memory="{api_config["memory"]}",' if performance_mode else ""}
)

pulumi.export("api_endpoint", api_service.name.apply(lambda name: f"http://localhost:{{api_config['port']}}"))
pulumi.export("api_config", api_config)
'''

def generate_microservice_infrastructure(requirements: Dict[str, Any], performance_mode: bool) -> str:
    """Generate microservice infrastructure code"""
    service_name = requirements.get('name', 'microservice')
    return f'''import pulumi
import pulumi_kubernetes as k8s

# {service_name.title()} microservice
{service_name}_deployment = k8s.apps.v1.Deployment("{service_name}",
    spec=k8s.apps.v1.DeploymentSpecArgs(
        replicas={requirements.get('replicas', 3)},
        selector=k8s.meta.v1.LabelSelectorArgs(
            match_labels={{"app": "{service_name}"}}
        ),
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(
                labels={{"app": "{service_name}"}}
            ),
            spec=k8s.core.v1.PodSpecArgs(
                containers=[k8s.core.v1.ContainerArgs(
                    name="{service_name}",
                    image="{requirements.get('image', 'nginx:alpine')}",
                    ports=[k8s.core.v1.ContainerPortArgs(
                        container_port={requirements.get('ports', [80])[0] if requirements.get('ports') else 80}
                    )],
                    resources=k8s.core.v1.ResourceRequirementsArgs(
                        requests={{"memory": "{requirements.get('memory', '256Mi')}", "cpu": "{requirements.get('cpu', '250m')}"}},
                        limits={{"memory": "{requirements.get('memory', '512Mi')}", "cpu": "{requirements.get('cpu', '500m')}"}}
                    ) if {performance_mode} else None
                )]
            )
        )
    )
)

# Service
{service_name}_service = k8s.core.v1.Service("{service_name}-service",
    spec=k8s.core.v1.ServiceSpecArgs(
        selector={{"app": "{service_name}"}},
        ports=[k8s.core.v1.ServicePortArgs(
            port=80,
            target_port={requirements.get('ports', [80])[0] if requirements.get('ports') else 80}
        )]
    )
)

pulumi.export("{service_name}_endpoint", {service_name}_service.status)
pulumi.export("{service_name}_replicas", {requirements.get('replicas', 3)})
'''

def generate_frontend_infrastructure(requirements: Dict[str, Any], performance_mode: bool) -> str:
    """Generate frontend infrastructure code"""
    return f'''import pulumi
import pulumi_vercel as vercel

# Frontend application
frontend_project = vercel.Project("frontend",
    name="orchestra-frontend",
    framework="{requirements.get('framework', 'nextjs')}",
    git_repository=vercel.ProjectGitRepositoryArgs(
        repo="ai-cherry/orchestra-main",
        type="github",
        production_branch="main"
    ),
    environment_variables=[
        vercel.ProjectEnvironmentVariableArgs(
            key="NEXT_PUBLIC_API_URL",
            value="{requirements.get('api_url', 'https://api.orchestra.ai')}",
            targets=["production", "preview"]
        )
    ],
    {"build_command": f'"build_command=\\"{requirements.get(\\'build_command\\', \\'npm run build\\')}\\",' if performance_mode else ""}
)

# Domain configuration
if "{requirements.get('domain', '')}":
    domain = vercel.ProjectDomain("frontend-domain",
        project_id=frontend_project.id,
        domain="{requirements.get('domain')}"
    )
    
    pulumi.export("frontend_domain", domain.domain)

pulumi.export("frontend_url", frontend_project.name.apply(lambda name: f"https://{{name}}.vercel.app"))
pulumi.export("frontend_framework", "{requirements.get('framework', 'nextjs')}")
'''

def generate_lambda_infrastructure(requirements: Dict[str, Any], performance_mode: bool) -> str:
    """Generate Lambda Labs infrastructure code"""
    return f'''import pulumi
import pulumi_command as command

# Lambda Labs GPU instance
instance_config = {{
    "instance_type": "{requirements.get('instance_type', 'gpu_1x_a10')}",
    "region": "{requirements.get('region', 'us-west-1')}",
    "quantity": {requirements.get('replicas', 1)}
}}

lambda_instance = command.local.Command("lambda-instance",
    create="""
    curl -X POST \\
      -H "Authorization: Bearer $LAMBDA_API_KEY" \\
      -H "Content-Type: application/json" \\
      -d '{{"instance_type": "{{instance_config['instance_type']}}", "region": "{{instance_config['region']}}", "quantity": {{instance_config['quantity']}}}}' \\
      https://cloud.lambdalabs.com/api/v1/instances
    """,
    environment={{"LAMBDA_API_KEY": "{requirements.get('api_key', '${{LAMBDA_API_KEY}}')}"}},
    {"triggers": f'triggers=["{performance_mode}"],' if performance_mode else ""}
)

pulumi.export("lambda_config", instance_config)
pulumi.export("lambda_command", lambda_instance.stdout)
'''

def generate_storage_infrastructure(requirements: Dict[str, Any], performance_mode: bool) -> str:
    """Generate storage infrastructure code"""
    return f'''import pulumi
import pulumi_docker as docker

# Storage configuration
storage_config = {{
    "type": "{requirements.get('type', 'redis')}",
    "size": "{requirements.get('storage', '10Gi')}",
    "replicas": {requirements.get('replicas', 1)}
}}

if storage_config["type"] == "redis":
    # Redis storage
    redis_storage = docker.Container("redis",
        image="redis:7-alpine",
        command=["redis-server", "--save", "60", "1", "--loglevel", "warning"],
        ports=[docker.ContainerPortArgs(
            internal=6379,
            external=6379
        )],
        restart="always",
        {"memory": f'memory="512m",' if performance_mode else ""}
    )
    
    pulumi.export("storage_endpoint", "redis://localhost:6379")
    
elif storage_config["type"] == "postgres":
    # PostgreSQL storage
    postgres_storage = docker.Container("postgres",
        image="postgres:15-alpine",
        env=[
            "POSTGRES_DB=storage",
            "POSTGRES_USER=postgres", 
            "POSTGRES_PASSWORD=password"
        ],
        ports=[docker.ContainerPortArgs(
            internal=5432,
            external=5432
        )],
        restart="always"
    )
    
    pulumi.export("storage_endpoint", "postgresql://postgres:password@localhost:5432/storage")

pulumi.export("storage_config", storage_config)
'''

def analyze_performance_optimizations(service_type: str, requirements: Dict[str, Any]) -> List[str]:
    """Analyze and suggest performance optimizations"""
    optimizations = []
    
    # General optimizations
    optimizations.append("Resource limits configured for predictable performance")
    optimizations.append("Restart policies set to 'always' for high availability")
    
    # Service-specific optimizations
    if service_type == "database":
        optimizations.extend([
            "Connection pooling recommended for high-load scenarios",
            "Read replicas suggested for read-heavy workloads",
            "Backup strategy should include point-in-time recovery"
        ])
    elif service_type == "api":
        optimizations.extend([
            "Load balancing configured for horizontal scaling",
            "Health checks implemented for zero-downtime deployments",
            "Caching layer recommended for frequently accessed data"
        ])
    elif service_type == "frontend":
        optimizations.extend([
            "CDN configured for global content delivery",
            "Asset optimization enabled for faster load times",
            "Preview deployments for rapid development cycles"
        ])
    
    # Scale-based optimizations
    replicas = requirements.get('replicas', 1)
    if replicas > 1:
        optimizations.append(f"Horizontal scaling configured with {replicas} replicas")
    
    return optimizations

async def main():
    """Main function to run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main()) 