#!/usr/bin/env python3
"""
Force Vercel deployment using API
"""

import requests
import json
import time
import os

# Vercel API configuration
VERCEL_TOKEN = "NAoa1I5OLykxUeYaGEy1g864"
VERCEL_API_BASE = "https://api.vercel.com"
HEADERS = {
    "Authorization": f"Bearer {VERCEL_TOKEN}",
    "Content-Type": "application/json"
}

def get_project_info(project_name="admin-interface"):
    """Get project information"""
    response = requests.get(
        f"{VERCEL_API_BASE}/v9/projects/{project_name}",
        headers=HEADERS
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting project info: {response.status_code}")
        print(response.text)
        return None

def list_deployments(project_name="admin-interface"):
    """List all deployments for the project"""
    response = requests.get(
        f"{VERCEL_API_BASE}/v6/deployments",
        headers=HEADERS,
        params={"projectId": project_name, "limit": 10}
    )
    if response.status_code == 200:
        return response.json().get("deployments", [])
    else:
        print(f"Error listing deployments: {response.status_code}")
        return []

def promote_deployment(deployment_id, project_name="admin-interface"):
    """Promote a deployment to production"""
    response = requests.post(
        f"{VERCEL_API_BASE}/v1/deployments/{deployment_id}/promote",
        headers=HEADERS,
        json={"target": "production"}
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error promoting deployment: {response.status_code}")
        print(response.text)
        return None

def create_alias(deployment_url, alias="orchestra-admin-interface.vercel.app"):
    """Create alias for deployment"""
    response = requests.post(
        f"{VERCEL_API_BASE}/v2/aliases",
        headers=HEADERS,
        json={
            "alias": alias,
            "deployment": deployment_url
        }
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error creating alias: {response.status_code}")
        print(response.text)
        return None

def main():
    print("🚀 Forcing Vercel Deployment")
    print("=" * 50)
    
    # Get project info
    print("\n📦 Getting project info...")
    project = get_project_info()
    if project:
        print(f"✅ Project found: {project.get('name')}")
        print(f"   ID: {project.get('id')}")
    
    # List deployments
    print("\n📋 Listing recent deployments...")
    deployments = list_deployments()
    
    if deployments:
        print(f"Found {len(deployments)} deployments:")
        for i, dep in enumerate(deployments[:5]):
            state = dep.get("state", "unknown")
            url = dep.get("url", "no-url")
            created = dep.get("created", 0)
            created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created/1000))
            print(f"{i+1}. {url} - {state} - {created_time}")
        
        # Find a ready deployment or the latest one
        ready_deployment = None
        for dep in deployments:
            if dep.get("state") == "READY":
                ready_deployment = dep
                break
        
        if not ready_deployment:
            # Use the latest deployment
            ready_deployment = deployments[0] if deployments else None
        
        if ready_deployment:
            deployment_url = ready_deployment.get("url")
            deployment_id = ready_deployment.get("uid")
            
            print(f"\n🎯 Attempting to alias deployment: {deployment_url}")
            
            # Try to create alias
            alias_result = create_alias(deployment_url)
            if alias_result:
                print(f"✅ Alias created successfully!")
                print(f"   URL: https://orchestra-admin-interface.vercel.app")
            else:
                print("❌ Failed to create alias")
                
                # Try to promote to production
                print("\n🔄 Trying to promote deployment...")
                promote_result = promote_deployment(deployment_id)
                if promote_result:
                    print("✅ Deployment promoted to production!")
                else:
                    print("❌ Failed to promote deployment")
    else:
        print("❌ No deployments found")
    
    print("\n✨ Done!")

if __name__ == "__main__":
    main() 