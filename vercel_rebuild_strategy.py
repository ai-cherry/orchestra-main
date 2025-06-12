#!/usr/bin/env python3
"""
Vercel Rebuild Strategy - Analyze and rebuild deployments to match codebase
"""

import requests
import json
import os
from typing import Dict, List, Any
from datetime import datetime

# Vercel API configuration
VERCEL_TOKEN = "NAoa1I5OLykxUeYaGEy1g864"
VERCEL_API_BASE = "https://api.vercel.com"
HEADERS = {
    "Authorization": f"Bearer {VERCEL_TOKEN}",
    "Content-Type": "application/json"
}

def analyze_codebase_structure():
    """Analyze the codebase to identify all deployable projects"""
    print("🔍 Analyzing Codebase Structure")
    print("=" * 50)
    
    projects = {
        "admin-interface": {
            "path": "admin-interface",
            "type": "vite",
            "description": "Main admin interface (Vite + React)",
            "has_vercel_json": True,
            "package_json": "admin-interface/package.json",
            "build_command": "npm run build",
            "output_directory": "dist",
            "framework": "vite",
            "priority": 1
        },
        "dashboard": {
            "path": "dashboard",
            "type": "nextjs",
            "description": "AI Conductor Dashboard (Next.js)",
            "has_vercel_json": False,
            "package_json": "dashboard/package.json",
            "build_command": "npm run build",
            "output_directory": ".next",
            "framework": "nextjs",
            "priority": 2
        },
        "react-app": {
            "path": "src/ui/web/react_app",
            "type": "static",
            "description": "React app redirect page",
            "has_vercel_json": True,
            "package_json": "src/ui/web/react_app/package.json",
            "build_command": "npm run build",
            "output_directory": "build",
            "framework": None,
            "priority": 3
        }
    }
    
    print("\n📦 Identified Deployable Projects:")
    for name, info in projects.items():
        print(f"\n{name}:")
        print(f"  Path: {info['path']}")
        print(f"  Type: {info['type']}")
        print(f"  Description: {info['description']}")
        print(f"  Has vercel.json: {info['has_vercel_json']}")
        print(f"  Framework: {info['framework']}")
    
    return projects

def get_all_vercel_projects():
    """Get all existing Vercel projects"""
    print("\n\n🌐 Fetching Existing Vercel Projects")
    print("=" * 50)
    
    response = requests.get(
        f"{VERCEL_API_BASE}/v9/projects",
        headers=HEADERS
    )
    
    if response.status_code != 200:
        print(f"❌ Error fetching projects: {response.status_code}")
        return []
    
    projects = response.json().get("projects", [])
    print(f"\n✅ Found {len(projects)} Vercel projects:")
    
    for project in projects:
        print(f"\n  Project: {project.get('name')}")
        print(f"    ID: {project.get('id')}")
        print(f"    Framework: {project.get('framework', 'None')}")
        print(f"    Created: {datetime.fromtimestamp(project.get('createdAt', 0)/1000)}")
        
    return projects

def delete_vercel_project(project_id: str, project_name: str):
    """Delete a Vercel project"""
    print(f"\n🗑️ Deleting project: {project_name} ({project_id})")
    
    response = requests.delete(
        f"{VERCEL_API_BASE}/v9/projects/{project_id}",
        headers=HEADERS
    )
    
    if response.status_code in [200, 204]:
        print(f"✅ Successfully deleted {project_name}")
        return True
    else:
        print(f"❌ Failed to delete {project_name}: {response.status_code}")
        return False

def create_vercel_json(project_path: str, project_info: Dict[str, Any]):
    """Create optimized vercel.json for a project"""
    print(f"\n📝 Creating vercel.json for {project_path}")
    
    config = {
        "version": 2,
        "buildCommand": project_info["build_command"],
        "outputDirectory": project_info["output_directory"]
    }
    
    # Add framework-specific configurations
    if project_info["framework"]:
        config["framework"] = project_info["framework"]
    
    if project_info["type"] == "vite":
        config["installCommand"] = "npm ci"
        config["headers"] = [
            {
                "source": "/assets/(.*)",
                "headers": [
                    {
                        "key": "Cache-Control",
                        "value": "public, max-age=31536000, immutable"
                    }
                ]
            }
        ]
    elif project_info["type"] == "nextjs":
        config["functions"] = {
            "app/api/[...route]/route.ts": {
                "maxDuration": 10
            }
        }
    
    vercel_json_path = os.path.join(project_path, "vercel.json")
    print(f"  Configuration: {json.dumps(config, indent=2)}")
    
    return config

def create_deployment_plan(codebase_projects: Dict, vercel_projects: List):
    """Create a deployment plan"""
    print("\n\n📋 Creating Deployment Plan")
    print("=" * 50)
    
    plan = {
        "delete": [],
        "create": [],
        "update": []
    }
    
    # Map existing Vercel projects
    vercel_project_names = {p["name"]: p for p in vercel_projects}
    
    # Check which projects need to be deleted
    for vercel_project in vercel_projects:
        name = vercel_project["name"]
        if name not in ["admin-interface", "dashboard", "orchestra-ai-frontend"]:
            plan["delete"].append({
                "id": vercel_project["id"],
                "name": name,
                "reason": "Not matching current codebase structure"
            })
    
    # Check which projects need to be created or updated
    for proj_name, proj_info in codebase_projects.items():
        vercel_name = {
            "admin-interface": "admin-interface",
            "dashboard": "orchestra-dashboard",
            "react-app": "orchestra-ai-frontend"
        }.get(proj_name, proj_name)
        
        if vercel_name in vercel_project_names:
            plan["update"].append({
                "name": vercel_name,
                "local_name": proj_name,
                "info": proj_info
            })
        else:
            plan["create"].append({
                "name": vercel_name,
                "local_name": proj_name,
                "info": proj_info
            })
    
    print("\n🗑️ Projects to Delete:")
    for item in plan["delete"]:
        print(f"  - {item['name']}: {item['reason']}")
    
    print("\n➕ Projects to Create:")
    for item in plan["create"]:
        print(f"  - {item['name']} (from {item['local_name']})")
    
    print("\n🔄 Projects to Update:")
    for item in plan["update"]:
        print(f"  - {item['name']} (from {item['local_name']})")
    
    return plan

def generate_rebuild_script(plan: Dict):
    """Generate a script to rebuild Vercel deployments"""
    print("\n\n📝 Generating Rebuild Script")
    print("=" * 50)
    
    script_content = """#!/bin/bash
# Vercel Rebuild Script - Generated on {}
# This script will rebuild Vercel deployments to match the current codebase

set -e

echo "🚀 Starting Vercel Rebuild Process"
echo "================================="

# Export Vercel token
export VERCEL_TOKEN="{}"

""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), VERCEL_TOKEN)
    
    # Add deletion commands
    if plan["delete"]:
        script_content += "# Delete outdated projects\n"
        script_content += "echo '\\n🗑️ Deleting outdated projects...'\n"
        for item in plan["delete"]:
            script_content += f"echo 'Deleting {item['name']}...'\n"
            script_content += f"# vercel remove {item['name']} --yes || true\n\n"
    
    # Add creation/update commands
    for action in ["create", "update"]:
        if plan[action]:
            script_content += f"\n# {action.capitalize()} projects\n"
            script_content += f"echo '\\n{'➕' if action == 'create' else '🔄'} {action.capitalize()}ing projects...'\n"
            
            for item in plan[action]:
                proj_info = item["info"]
                script_content += f"\n# {item['name']}\n"
                script_content += f"echo '\\nProcessing {item['name']}...'\n"
                script_content += f"cd {proj_info['path']}\n"
                
                # Create vercel.json if needed
                if not proj_info["has_vercel_json"]:
                    script_content += f"echo 'Creating vercel.json...'\n"
                    config = create_vercel_json(proj_info["path"], proj_info)
                    script_content += f"cat > vercel.json << 'EOF'\n"
                    script_content += json.dumps(config, indent=2)
                    script_content += "\nEOF\n"
                
                # Deploy command
                script_content += f"echo 'Deploying to Vercel...'\n"
                script_content += f"npx vercel --prod --yes --name {item['name']}\n"
                script_content += f"cd ..\n"
                if proj_info["path"].count("/") > 0:
                    script_content += f"cd {'../' * proj_info['path'].count('/')}\n"
    
    script_content += """
echo "\\n✅ Vercel Rebuild Complete!"
echo "============================"
echo ""
echo "📝 Next Steps:"
echo "1. Check deployments at https://vercel.com/dashboard"
echo "2. Update DNS/aliases as needed"
echo "3. Test all deployments"
"""
    
    with open("rebuild_vercel_deployments.sh", "w") as f:
        f.write(script_content)
    
    print("\n✅ Generated rebuild_vercel_deployments.sh")
    return script_content

def main():
    """Main execution"""
    print("🎯 Vercel Configuration Review & Rebuild Strategy")
    print("=" * 50)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. Analyze codebase
    codebase_projects = analyze_codebase_structure()
    
    # 2. Get existing Vercel projects
    vercel_projects = get_all_vercel_projects()
    
    # 3. Create deployment plan
    plan = create_deployment_plan(codebase_projects, vercel_projects)
    
    # 4. Generate rebuild script
    generate_rebuild_script(plan)
    
    print("\n\n📊 Summary")
    print("=" * 50)
    print(f"Codebase Projects: {len(codebase_projects)}")
    print(f"Vercel Projects: {len(vercel_projects)}")
    print(f"Projects to Delete: {len(plan['delete'])}")
    print(f"Projects to Create: {len(plan['create'])}")
    print(f"Projects to Update: {len(plan['update'])}")
    
    print("\n\n🎯 Recommendations:")
    print("1. Review the generated rebuild_vercel_deployments.sh script")
    print("2. Make it executable: chmod +x rebuild_vercel_deployments.sh")
    print("3. Run it to rebuild Vercel deployments: ./rebuild_vercel_deployments.sh")
    print("4. Consider setting up GitHub integration for automatic deployments")
    print("5. Configure custom domains for each project as needed")
    
    print("\n\n📝 Project Naming Convention:")
    print("- admin-interface: Main admin dashboard")
    print("- orchestra-dashboard: Next.js AI conductor dashboard")
    print("- orchestra-ai-frontend: Redirect/landing page")

if __name__ == "__main__":
    main() 