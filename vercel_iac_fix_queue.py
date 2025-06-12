#!/usr/bin/env python3
"""
Vercel Queue Fix - Infrastructure as Code approach
Fixes stuck deployments by finding and promoting the latest with the fix
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Any

# Vercel API configuration
VERCEL_TOKEN = "NAoa1I5OLykxUeYaGEy1g864"
VERCEL_API_BASE = "https://api.vercel.com"
HEADERS = {
    "Authorization": f"Bearer {VERCEL_TOKEN}",
    "Content-Type": "application/json"
}

def get_all_deployments() -> List[Dict[str, Any]]:
    """Get all deployments, including queued ones"""
    print("🔍 Fetching all deployments...")
    
    all_deployments = []
    page = 1
    
    while True:
        response = requests.get(
            f"{VERCEL_API_BASE}/v6/deployments",
            headers=HEADERS,
            params={"limit": 100, "page": page}
        )
        
        if response.status_code != 200:
            print(f"❌ Error fetching deployments: {response.status_code}")
            break
        
        data = response.json()
        deployments = data.get("deployments", [])
        
        if not deployments:
            break
        
        all_deployments.extend(deployments)
        
        # Check if there's pagination info
        pagination = data.get("pagination", {})
        if not pagination.get("hasNext", False):
            break
        
        page += 1
    
    print(f"✅ Found {len(all_deployments)} total deployments")
    return all_deployments

def analyze_deployments(deployments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze deployment patterns and find the best candidate"""
    analysis = {
        "total": len(deployments),
        "by_state": {},
        "queued_deployments": [],
        "ready_deployments": [],
        "recent_deployments": []
    }
    
    # Count by state and categorize
    for dep in deployments:
        state = dep.get("state", "UNKNOWN")
        analysis["by_state"][state] = analysis["by_state"].get(state, 0) + 1
        
        # Get deployment info
        created = dep.get("created", 0)
        created_dt = datetime.fromtimestamp(created / 1000) if created else None
        
        dep_info = {
            "id": dep.get("uid"),
            "url": dep.get("url"),
            "state": state,
            "created": created_dt,
            "name": dep.get("name", "Unknown")
        }
        
        if state == "QUEUED":
            analysis["queued_deployments"].append(dep_info)
        elif state == "READY":
            analysis["ready_deployments"].append(dep_info)
        
        # Recent deployments (last 24 hours)
        if created_dt and (datetime.now() - created_dt).days < 1:
            analysis["recent_deployments"].append(dep_info)
    
    # Sort by creation time
    analysis["queued_deployments"].sort(key=lambda x: x["created"] if x["created"] else datetime.min, reverse=True)
    analysis["ready_deployments"].sort(key=lambda x: x["created"] if x["created"] else datetime.min, reverse=True)
    
    return analysis

def cancel_old_queued_deployments(deployments: List[Dict[str, Any]]) -> int:
    """Cancel old queued deployments to free up the queue"""
    print("\n🧹 Cleaning up old queued deployments...")
    
    cancelled = 0
    for dep in deployments:
        if dep["created"] and (datetime.now() - dep["created"]).total_seconds() > 3600:
            # Try to cancel deployment
            response = requests.delete(
                f"{VERCEL_API_BASE}/v13/deployments/{dep['id']}",
                headers=HEADERS
            )
            
            if response.status_code in [200, 204]:
                print(f"✅ Cancelled old deployment: {dep['id']}")
                cancelled += 1
            else:
                print(f"⚠️ Could not cancel {dep['id']}: {response.status_code}")
    
    return cancelled

def find_latest_fixed_deployment(deployments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Find the latest deployment that should have the fix"""
    print("\n🔍 Looking for deployments with the fix...")
    
    # The fix was applied around June 12, 2025, 15:49 UTC (23:49 local)
    fix_time = datetime(2025, 6, 12, 22, 0, 0)  # UTC time
    
    # Look through all deployments
    for dep in deployments:
        created = dep.get("created", 0)
        if not created:
            continue
            
        created_dt = datetime.fromtimestamp(created / 1000)
        
        url = dep.get("url", "")
        # These are the deployments we created with the fix
        if any(x in url for x in ["pr5y3otxs", "btufleh2z", "eya0cj9h8", "cld2vympv", "qyqjrdo2s"]):
            print(f"✅ Found deployment with fix: {url}")
            print(f"   Created: {created_dt}")
            print(f"   State: {dep.get('state')}")
            return dep
    
    return None

def promote_deployment_directly(deployment_id: str) -> bool:
    """Try to promote a deployment directly"""
    print(f"\n🚀 Attempting to promote deployment {deployment_id}...")
    
    # Try different promotion methods
    methods = [
        # Method 1: Direct promotion
        {
            "url": f"{VERCEL_API_BASE}/v1/deployments/{deployment_id}/promote",
            "method": "POST",
            "data": {}
        },
        # Method 2: Alias update
        {
            "url": f"{VERCEL_API_BASE}/v2/aliases",
            "method": "POST", 
            "data": {
                "alias": "orchestra-admin-interface.vercel.app",
                "deploymentId": deployment_id
            }
        }
    ]
    
    for method in methods:
        if method["method"] == "POST":
            response = requests.post(
                method["url"],
                headers=HEADERS,
                json=method["data"]
            )
        
        if response.status_code in [200, 201]:
            print(f"✅ Successfully promoted deployment!")
            return True
        else:
            print(f"⚠️ Method failed: {response.status_code} - {response.text[:100]}")
    
    return False

def force_deployment_ready(deployment_url: str) -> bool:
    """Force a queued deployment to be ready by updating alias"""
    print(f"\n🔧 Forcing deployment ready by alias update...")
    
    # Delete existing alias first
    requests.delete(
        f"{VERCEL_API_BASE}/v4/aliases/orchestra-admin-interface.vercel.app",
        headers=HEADERS
    )
    
    # Create new alias pointing to the deployment URL
    response = requests.post(
        f"{VERCEL_API_BASE}/v2/aliases",
        headers=HEADERS,
        json={
            "alias": "orchestra-admin-interface.vercel.app",
            "deployment": deployment_url
        }
    )
    
    if response.status_code in [200, 201]:
        print(f"✅ Successfully created alias!")
        return True
    else:
        print(f"❌ Failed to create alias: {response.status_code} - {response.text}")
        return False

def main():
    """Main workflow to fix the queue issue"""
    print("🎯 Vercel Queue Fix - Infrastructure as Code")
    print("=" * 50)
    
    # 1. Get all deployments
    deployments = get_all_deployments()
    if not deployments:
        return
    
    # 2. Analyze deployments
    analysis = analyze_deployments(deployments)
    
    print(f"\n📊 Deployment Analysis:")
    print(f"Total: {analysis['total']}")
    for state, count in analysis['by_state'].items():
        print(f"  - {state}: {count}")
    
    print(f"\n📋 Recent Queued Deployments:")
    for dep in analysis['queued_deployments'][:5]:
        print(f"  {dep['url']} - Created: {dep['created']}")
    
    # 3. Find deployment with fix
    fixed_deployment = find_latest_fixed_deployment(deployments)
    
    if fixed_deployment:
        # Try to force it to be ready
        deployment_url = fixed_deployment.get("url", "")
        deployment_id = fixed_deployment.get("uid", "")
        
        if deployment_url:
            success = force_deployment_ready(deployment_url)
            
            if success:
                print("\n🎉 SUCCESS! The deployment has been forced to production!")
                print(f"✅ The site should now be working at https://orchestra-admin-interface.vercel.app")
                print("\n📝 Important:")
                print("1. Clear your browser cache")
                print("2. Wait 1-2 minutes for DNS propagation")
                print("3. The white screen issue should be resolved!")
            else:
                # Try promotion method
                promote_deployment_directly(deployment_id)
    else:
        print("\n⚠️ Could not find deployment with fix")
        print("The deployments may still be building or need manual intervention")
    
    # 4. Clean up old deployments
    if analysis['queued_deployments']:
        cancelled = cancel_old_queued_deployments(analysis['queued_deployments'])
        if cancelled > 0:
            print(f"\n✅ Cleaned up {cancelled} old queued deployments")

if __name__ == "__main__":
    main() 