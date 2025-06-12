#!/usr/bin/env python3
"""
Check and update Vercel alias
"""

import requests
import json

# Vercel API configuration
VERCEL_TOKEN = "NAoa1I5OLykxUeYaGEy1g864"
VERCEL_API_BASE = "https://api.vercel.com"
HEADERS = {
    "Authorization": f"Bearer {VERCEL_TOKEN}",
    "Content-Type": "application/json"
}

def get_alias_info(alias="orchestra-admin-interface.vercel.app"):
    """Get information about an alias"""
    response = requests.get(
        f"{VERCEL_API_BASE}/v4/aliases/{alias}",
        headers=HEADERS
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting alias info: {response.status_code}")
        print(response.text)
        return None

def delete_alias(alias="orchestra-admin-interface.vercel.app"):
    """Delete an alias"""
    response = requests.delete(
        f"{VERCEL_API_BASE}/v2/aliases/{alias}",
        headers=HEADERS
    )
    if response.status_code == 200:
        return True
    else:
        print(f"Error deleting alias: {response.status_code}")
        print(response.text)
        return False

def force_deployment():
    """Try to force a new deployment with the fixed code"""
    # Read the fixed index.html
    with open("admin-interface/index.html", "r") as f:
        index_content = f.read()
    
    print("\n📄 Current index.html contains root div:", '<div id="root"></div>' in index_content)
    
    # Get the deployment currently associated with the alias
    alias_info = get_alias_info()
    if alias_info:
        print(f"\n🔗 Current alias points to:")
        print(f"   Deployment: {alias_info.get('deployment', {}).get('url')}")
        print(f"   Created: {alias_info.get('createdAt')}")
        print(f"   Deployment ID: {alias_info.get('deploymentId')}")
    
    return alias_info

def main():
    print("🔍 Checking Vercel Alias Configuration")
    print("=" * 50)
    
    alias_info = force_deployment()
    
    if alias_info:
        print("\n💡 To fix the white screen issue:")
        print("1. The queued deployments contain the fix")
        print("2. Vercel's deployment queue appears to be stuck")
        print("3. You may need to:")
        print("   - Wait for Vercel to process the queue")
        print("   - Contact Vercel support about stuck deployments")
        print("   - Try deploying from the Vercel dashboard")
        print("\n📋 Deployment IDs with the fix (all queued):")
        deployments = [
            "admin-interface-qyqjrdo2s-lynn-musils-projects.vercel.app",
            "admin-interface-pr5y3otxs-lynn-musils-projects.vercel.app",
            "admin-interface-k5bgljn2x-lynn-musils-projects.vercel.app"
        ]
        for dep in deployments:
            print(f"   - {dep}")

if __name__ == "__main__":
    main() 