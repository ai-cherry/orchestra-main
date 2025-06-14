#!/usr/bin/env python3
"""
Setup Script for AI Agent Integration
Configures Orchestra AI for optimal AI agent development
"""
import os
import json
import yaml
from pathlib import Path
import subprocess
import sys

def setup_ai_context():
    """Generate AI context files"""
    print("🤖 Setting up AI context system...")
    
    # Import and run context loader
    sys.path.append(str(Path(__file__).parent.parent))
    from ai_context.context_loader import ai_context
    
    ai_context.export_for_cursor()
    print("✅ AI context exported to .cursor/project_context.json")

def setup_cursor_rules():
    """Ensure Cursor rules are in place"""
    print("📋 Setting up Cursor AI rules...")
    
    cursor_dir = Path(".cursor")
    cursor_dir.mkdir(exist_ok=True)
    
    rules_dir = cursor_dir / "rules"
    rules_dir.mkdir(exist_ok=True)
    
    if (rules_dir / "orchestra_ai_rules.yaml").exists():
        print("✅ Cursor rules already configured")
    else:
        print("❌ Please create .cursor/rules/orchestra_ai_rules.yaml")

def setup_vercel_config():
    """Configure Vercel deployment"""
    print("🚀 Setting up Vercel configuration...")
    
    vercel_config = {
        "framework": "vite",
        "buildCommand": "npm run build",
        "outputDirectory": "dist",
        "devCommand": "npm run dev",
        "installCommand": "npm install",
        "functions": {
            "api/*.py": {
                "runtime": "python3.11",
                "maxDuration": 30
            }
        },
        "env": [
            "DATABASE_URL",
            "REDIS_URL",
            "PINECONE_API_KEY",
            "WEAVIATE_URL",
            "PORTKEY_API_KEY",
            "OPENROUTER_API_KEY",
            "PULUMI_ACCESS_TOKEN"
        ]
    }
    
    with open("vercel.json", "w") as f:
        json.dump(vercel_config, f, indent=2)
    
    print("✅ Vercel configuration created")

def setup_pulumi_ai_config():
    """Configure Pulumi for AI-friendly operations"""
    print("🏗️ Setting up Pulumi AI configuration...")
    
    pulumi_dir = Path("pulumi")
    pulumi_dir.mkdir(exist_ok=True)
    
    # Create AI-friendly Pulumi configuration
    ai_config = {
        "name": "orchestra-ai",
        "runtime": "python",
        "description": "Orchestra AI Infrastructure",
        "config": {
            "ai:preview_before_deploy": True,
            "ai:auto_tag_resources": True,
            "ai:cost_tracking": True
        }
    }
    
    with open(pulumi_dir / "Pulumi.ai.yaml", "w") as f:
        yaml.dump(ai_config, f)
    
    print("✅ Pulumi AI configuration created")

def create_ai_templates():
    """Create template files for AI agents"""
    print("📝 Creating AI agent templates...")
    
    templates_dir = Path(".ai-templates")
    templates_dir.mkdir(exist_ok=True)
    
    # API endpoint template
    api_template = '''"""
{description}

AI Agent Instructions:
1. Validate all inputs with Pydantic
2. Use async/await patterns
3. Include comprehensive error handling
4. Add structured logging
5. Return standardized responses
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import structlog
from typing import Dict, Any

logger = structlog.get_logger()
router = APIRouter()

class {model_name}Request(BaseModel):
    # Define request model
    pass

class {model_name}Response(BaseModel):
    # Define response model
    pass

@router.post("/{endpoint_path}")
async def {function_name}(request: {model_name}Request) -> {model_name}Response:
    """
    {description}
    """
    try:
        # Implementation here
        logger.info("{function_name} called", request=request.dict())
        
        # Process request
        result = await process_{function_name}(request)
        
        return {model_name}Response(**result)
        
    except Exception as e:
        logger.error("{function_name} failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

async def process_{function_name}(request: {model_name}Request) -> Dict[str, Any]:
    """Process the {function_name} request"""
    # Implementation logic
    return {{}}
'''
    
    with open(templates_dir / "api_endpoint.py.template", "w") as f:
        f.write(api_template)
    
    # Pulumi resource template
    pulumi_template = '''"""
{description}

AI Agent Instructions:
1. Use Pulumi's async patterns
2. Tag all resources appropriately
3. Include cost estimates
4. Set up monitoring
5. Configure auto-scaling
"""
import pulumi
from pulumi import Output
import pulumi_aws as aws
from typing import Dict, Any

class {resource_name}(pulumi.ComponentResource):
    """
    {description}
    """
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        opts: pulumi.ResourceOptions = None
    ):
        super().__init__("{resource_type}", name, None, opts)
        
        # Default tags
        default_tags = {{
            "Project": "Orchestra-AI",
            "ManagedBy": "Pulumi",
            "Environment": pulumi.get_stack(),
            "Component": name
        }}
        
        # Create resources
        self.create_resources(config, default_tags)
        
        # Register outputs
        self.register_outputs({{
            "id": self.id,
            "arn": self.arn,
            "endpoint": self.endpoint
        }})
    
    def create_resources(self, config: Dict[str, Any], tags: Dict[str, str]):
        """Create the actual cloud resources"""
        # Implementation here
        pass
'''
    
    with open(templates_dir / "pulumi_resource.py.template", "w") as f:
        f.write(pulumi_template)
    
    print("✅ AI templates created")

def setup_git_hooks():
    """Setup git hooks for AI agent workflows"""
    print("🔗 Setting up git hooks...")
    
    hooks_dir = Path(".git/hooks")
    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    # Pre-commit hook for AI validation
    pre_commit = '''#!/bin/bash
# AI Agent Pre-commit Hook

echo "🤖 Running AI agent validations..."

# Update AI context
python scripts/setup_ai_agents.py --update-context

# Run Python formatting
black . --check

# Run type checking
mypy .

# Validate Pulumi configs
if [ -d "pulumi" ]; then
    cd pulumi && pulumi preview --non-interactive
fi

echo "✅ AI validations passed"
'''
    
    hook_path = hooks_dir / "pre-commit"
    with open(hook_path, "w") as f:
        f.write(pre_commit)
    
    # Make executable
    os.chmod(hook_path, 0o755)
    
    print("✅ Git hooks configured")

def main():
    """Main setup function"""
    print("🎼 Orchestra AI - AI Agent Setup")
    print("================================")
    
    # Check if we're in the right directory
    if not Path("docker-compose.yml").exists():
        print("❌ Please run this script from the Orchestra AI root directory")
        sys.exit(1)
    
    # Run setup steps
    setup_ai_context()
    setup_cursor_rules()
    setup_vercel_config()
    setup_pulumi_ai_config()
    create_ai_templates()
    setup_git_hooks()
    
    print("\n✅ AI Agent setup complete!")
    print("\n📚 Next steps:")
    print("1. Review .cursor/project_context.json")
    print("2. Configure your AI agents with the context")
    print("3. Use templates in .ai-templates/ for new code")
    print("4. Deploy with: vercel --prod")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup AI agents for Orchestra AI")
    parser.add_argument("--update-context", action="store_true", help="Only update AI context")
    
    args = parser.parse_args()
    
    if args.update_context:
        setup_ai_context()
    else:
        main() 