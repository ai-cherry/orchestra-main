#!/usr/bin/env python3
"""
Vercel Infrastructure Monitoring and Troubleshooting
Direct API usage to fix deployment issues
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Vercel API configuration
VERCEL_TOKEN = "NAoa1I5OLykxUeYaGEy1g864"
VERCEL_API_BASE = "https://api.vercel.com"
HEADERS = {
    "Authorization": f"Bearer {VERCEL_TOKEN}",
    "Content-Type": "application/json"
}

def get_project_deployments(project_name: str = "admin-interface") -> Dict[str, Any]:
    """Get all deployments for a project"""
    print(f"🔍 Checking deployments for project: {project_name}")
    
    # Get deployments
    response = requests.get(
        f"{VERCEL_API_BASE}/v6/deployments",
        headers=HEADERS,
        params={"projectId": project_name, "limit": 20}
    )
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None
    
    data = response.json()
    deployments = data.get("deployments", [])
    
    # Analyze deployment states
    states = {}
    for dep in deployments:
        state = dep.get("state", "UNKNOWN")
        states[state] = states.get(state, 0) + 1
    
    print(f"\n📊 Deployment Status Summary:")
    print(f"Total deployments: {len(deployments)}")
    for state, count in states.items():
        print(f"  - {state}: {count}")
    
    return deployments

def find_working_deployment(deployments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Find the most recent working deployment with the fix"""
    print("\n🔍 Searching for working deployment with root div fix...")
    
    # Look for deployments created after the fix was applied
    fix_time = datetime(2025, 6, 12, 16, 0, 0)  # Approximate time when fix was applied
    
    for dep in deployments:
        created = dep.get("created", 0) / 1000  # Convert from milliseconds
        created_dt = datetime.fromtimestamp(created)
        
        if dep.get("state") == "READY" and created_dt > fix_time:
            print(f"✅ Found working deployment: {dep.get('url')}")
            print(f"   Created: {created_dt}")
            print(f"   ID: {dep.get('uid')}")
            return dep
    
    # If no recent deployment, look for any READY deployment
    for dep in deployments:
        if dep.get("state") == "READY":
            print(f"⚠️ Found older READY deployment: {dep.get('url')}")
            return dep
    
    return None

def update_alias(deployment_url: str, alias: str = "orchestra-admin-interface.vercel.app") -> bool:
    """Update the alias to point to a working deployment"""
    print(f"\n🔧 Updating alias {alias} to point to {deployment_url}...")
    
    # First, try to delete existing alias
    delete_response = requests.delete(
        f"{VERCEL_API_BASE}/v4/aliases/{alias}",
        headers=HEADERS
    )
    
    if delete_response.status_code == 200:
        print(f"✅ Removed old alias")
    
    # Create new alias
    create_response = requests.post(
        f"{VERCEL_API_BASE}/v2/aliases",
        headers=HEADERS,
        json={
            "alias": alias,
            "deployment": deployment_url
        }
    )
    
    if create_response.status_code == 200:
        print(f"✅ Successfully updated alias!")
        return True
    else:
        print(f"❌ Failed to create alias: {create_response.status_code} - {create_response.text}")
        return False

def check_deployment_logs(deployment_id: str) -> None:
    """Check deployment logs for errors"""
    print(f"\n📋 Checking logs for deployment {deployment_id}...")
    
    response = requests.get(
        f"{VERCEL_API_BASE}/v2/deployments/{deployment_id}/events",
        headers=HEADERS
    )
    
    if response.status_code == 200:
        events = response.json()
        for event in events[-10:]:  # Last 10 events
            print(f"  {event.get('created')} - {event.get('text', '')}")

def force_new_deployment() -> Dict[str, Any]:
    """Force a new deployment from the fixed code"""
    print("\n🚀 Forcing new deployment from fixed code...")
    
    # This would typically use git integration, but we'll create a deployment
    response = requests.post(
        f"{VERCEL_API_BASE}/v13/deployments",
        headers=HEADERS,
        json={
            "name": "admin-interface",
            "project": "admin-interface",
            "gitSource": {
                "type": "github",
                "repoId": "orchestra-ai",
                "ref": "main"
            }
        }
    )
    
    if response.status_code in [200, 201]:
        deployment = response.json()
        print(f"✅ Created new deployment: {deployment.get('url')}")
        return deployment
    else:
        print(f"❌ Failed to create deployment: {response.status_code} - {response.text}")
        return None

def main():
    """Main troubleshooting workflow"""
    print("🎯 Vercel Infrastructure Troubleshooting")
    print("=" * 50)
    
    # 1. Get current deployments
    deployments = get_project_deployments()
    if not deployments:
        return
    
    # 2. Find a working deployment
    working_deployment = find_working_deployment(deployments)
    
    if working_deployment:
        # 3. Update the alias to point to working deployment
        success = update_alias(working_deployment.get("url"))
        
        if success:
            print("\n🎉 Success! The site should now be working.")
            print(f"✅ Visit https://orchestra-admin-interface.vercel.app to verify")
            print("\n📝 Next Steps:")
            print("1. Check if the white screen issue is resolved")
            print("2. Clear your browser cache if needed")
            print("3. If still showing white screen, wait 2-3 minutes for DNS propagation")
    else:
        print("\n⚠️ No working deployments found!")
        print("Attempting to force a new deployment...")
        
        # Try to force a new deployment
        new_deployment = force_new_deployment()
        if new_deployment:
            print("\n⏳ New deployment created. Wait for it to complete...")
            print("Run this script again in 2-3 minutes to update the alias.")
    
    # 4. Show current alias status
    print("\n📍 Checking current alias configuration...")
    alias_response = requests.get(
        f"{VERCEL_API_BASE}/v4/aliases",
        headers=HEADERS,
        params={"domain": "orchestra-admin-interface.vercel.app"}
    )
    
    if alias_response.status_code == 200:
        aliases = alias_response.json().get("aliases", [])
        for alias in aliases:
            if alias.get("alias") == "orchestra-admin-interface.vercel.app":
                print(f"Current alias points to: {alias.get('deployment', {}).get('url', 'Unknown')}")
                print(f"Deployment ID: {alias.get('deploymentId', 'Unknown')}")

if __name__ == "__main__":
    main() 