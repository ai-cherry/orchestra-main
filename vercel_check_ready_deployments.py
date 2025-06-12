#!/usr/bin/env python3
"""
Check for READY deployments and force alias update
"""

import requests
import json
from datetime import datetime

# Vercel API configuration
VERCEL_TOKEN = "NAoa1I5OLykxUeYaGEy1g864"
VERCEL_API_BASE = "https://api.vercel.com"
HEADERS = {
    "Authorization": f"Bearer {VERCEL_TOKEN}",
    "Content-Type": "application/json"
}

def find_ready_deployments():
    """Find all READY deployments"""
    print("🔍 Searching for READY deployments...")
    
    response = requests.get(
        f"{VERCEL_API_BASE}/v6/deployments",
        headers=HEADERS,
        params={"state": "READY", "limit": 100}
    )
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return []
    
    deployments = response.json().get("deployments", [])
    print(f"✅ Found {len(deployments)} READY deployments")
    
    return deployments

def check_current_alias():
    """Check what the current alias points to"""
    print("\n📍 Checking current alias...")
    
    response = requests.get(
        f"{VERCEL_API_BASE}/v4/aliases",
        headers=HEADERS
    )
    
    if response.status_code == 200:
        aliases = response.json().get("aliases", [])
        for alias in aliases:
            if "orchestra-admin-interface.vercel.app" in alias.get("alias", ""):
                print(f"Current alias: {alias.get('alias')}")
                print(f"Points to: {alias.get('deployment', {}).get('url', 'Unknown')}")
                print(f"Created: {alias.get('created')}")
                return alias
    
    return None

def update_to_newest_ready(deployments):
    """Update alias to newest READY deployment"""
    if not deployments:
        print("❌ No READY deployments found")
        return
    
    # Sort by creation time, newest first
    deployments.sort(key=lambda x: x.get("created", 0), reverse=True)
    newest = deployments[0]
    
    print(f"\n🎯 Newest READY deployment:")
    print(f"URL: {newest.get('url')}")
    print(f"Created: {datetime.fromtimestamp(newest.get('created', 0)/1000)}")
    print(f"Name: {newest.get('name')}")
    
    # Check if it's the admin-interface project
    if "admin-interface" in newest.get("name", ""):
        print("✅ This is an admin-interface deployment!")
        
        # Delete old alias
        print("\n🗑️ Removing old alias...")
        delete_resp = requests.delete(
            f"{VERCEL_API_BASE}/v4/aliases/orchestra-admin-interface.vercel.app",
            headers=HEADERS
        )
        
        # Create new alias
        print("🔧 Creating new alias...")
        create_resp = requests.post(
            f"{VERCEL_API_BASE}/v2/aliases",
            headers=HEADERS,
            json={
                "alias": "orchestra-admin-interface.vercel.app",
                "deployment": newest.get("url")
            }
        )
        
        if create_resp.status_code in [200, 201]:
            print("✅ SUCCESS! Alias updated!")
            print(f"\n🎉 Visit https://orchestra-admin-interface.vercel.app")
            print("The white screen issue should be resolved!")
        else:
            print(f"❌ Failed: {create_resp.status_code} - {create_resp.text}")
    else:
        print("⚠️ Newest READY deployment is not admin-interface")
        
        # Look for admin-interface in READY deployments
        for dep in deployments:
            if "admin-interface" in dep.get("name", ""):
                print(f"\n✅ Found admin-interface deployment: {dep.get('url')}")
                print("Updating alias to this deployment...")
                
                # Create alias
                create_resp = requests.post(
                    f"{VERCEL_API_BASE}/v2/aliases",
                    headers=HEADERS,
                    json={
                        "alias": "orchestra-admin-interface.vercel.app",
                        "deployment": dep.get("url")
                    }
                )
                
                if create_resp.status_code in [200, 201]:
                    print("✅ SUCCESS! Alias updated!")
                    return
                else:
                    print(f"❌ Failed: {create_resp.status_code}")
                    break

def main():
    print("🎯 Vercel READY Deployment Check")
    print("=" * 50)
    
    # Check current alias
    current = check_current_alias()
    
    # Find READY deployments
    ready_deployments = find_ready_deployments()
    
    if ready_deployments:
        update_to_newest_ready(ready_deployments)
    else:
        print("\n⚠️ No READY deployments available")
        print("All deployments may be stuck in queue")
        print("\n📝 Recommendation:")
        print("1. Check Vercel dashboard manually")
        print("2. Wait for queue to clear")
        print("3. Or contact Vercel support")

if __name__ == "__main__":
    main() 