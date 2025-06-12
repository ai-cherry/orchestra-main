#!/usr/bin/env python3
"""
Vercel Infrastructure Monitoring and Troubleshooting with Pulumi
Uses IaC to monitor and fix deployment issues
"""

import pulumi
import requests
import json
import time
from typing import Dict, List, Any

# Get Vercel configuration
config = pulumi.Config()
VERCEL_TOKEN = config.require_secret("vercel:apiToken")

# Vercel API configuration
VERCEL_API_BASE = "https://api.vercel.com"

def get_headers(token: str) -> Dict[str, str]:
    """Get headers for Vercel API requests"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def monitor_deployments(token: str, project_name: str = "admin-interface") -> Dict[str, Any]:
    """Monitor current deployment status"""
    headers = get_headers(token)
    
    # Get project info
    project_response = requests.get(
        f"{VERCEL_API_BASE}/v9/projects/{project_name}",
        headers=headers
    )
    
    if project_response.status_code != 200:
        return {"error": f"Failed to get project: {project_response.text}"}
    
    project = project_response.json()
    
    # Get deployments
    deployments_response = requests.get(
        f"{VERCEL_API_BASE}/v6/deployments",
        headers=headers,
        params={"projectId": project_name, "limit": 10}
    )
    
    if deployments_response.status_code != 200:
        return {"error": f"Failed to get deployments: {deployments_response.text}"}
    
    deployments = deployments_response.json().get("deployments", [])
    
    # Analyze deployment status
    status = {
        "project": project,
        "deployments": {
            "total": len(deployments),
            "queued": sum(1 for d in deployments if d.get("state") == "QUEUED"),
            "ready": sum(1 for d in deployments if d.get("state") == "READY"),
            "error": sum(1 for d in deployments if d.get("state") == "ERROR"),
            "building": sum(1 for d in deployments if d.get("state") == "BUILDING")
        },
        "latest_deployments": []
    }
    
    # Get details of latest 5 deployments
    for dep in deployments[:5]:
        created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(dep.get("created", 0)/1000))
        status["latest_deployments"].append({
            "url": dep.get("url"),
            "state": dep.get("state"),
            "created": created_time,
            "id": dep.get("uid"),
            "alias": dep.get("alias", [])
        })
    
    return status

def troubleshoot_deployments(token: str, status: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Analyze deployment issues and suggest fixes"""
    issues = []
    
    # Check for stuck deployments
    if status["deployments"]["queued"] > 0:
        queued_time = []
        for dep in status["latest_deployments"]:
            if dep["state"] == "QUEUED":
                # Calculate how long it's been queued
                created = dep["created"]
                queued_time.append(created)
        
        issues.append({
            "issue": "Stuck Deployments",
            "severity": "high",
            "details": f"{status['deployments']['queued']} deployments stuck in queue",
            "queued_since": queued_time,
            "fixes": [
                "Check Vercel status page for platform issues",
                "Verify account quotas and limits",
                "Try canceling and redeploying",
                "Contact Vercel support with deployment IDs"
            ]
        })
    
    # Check for no ready deployments
    if status["deployments"]["ready"] == 0:
        issues.append({
            "issue": "No Ready Deployments",
            "severity": "critical",
            "details": "No deployments are in READY state",
            "fixes": [
                "All deployments may be stuck in queue",
                "Check build logs for errors",
                "Verify project configuration"
            ]
        })
    
    # Check for build errors
    if status["deployments"]["error"] > 0:
        issues.append({
            "issue": "Build Errors",
            "severity": "medium",
            "details": f"{status['deployments']['error']} deployments failed",
            "fixes": [
                "Check build logs for specific errors",
                "Verify dependencies are installed",
                "Check for missing environment variables"
            ]
        })
    
    return issues

def attempt_fixes(token: str, project_name: str, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Attempt to fix identified issues"""
    headers = get_headers(token)
    fixes_applied = []
    
    for issue in issues:
        if issue["issue"] == "Stuck Deployments":
            # Try to find a ready deployment to alias
            deployments_response = requests.get(
                f"{VERCEL_API_BASE}/v6/deployments",
                headers=headers,
                params={"projectId": project_name, "limit": 50, "state": "READY"}
            )
            
            if deployments_response.status_code == 200:
                ready_deployments = deployments_response.json().get("deployments", [])
                if ready_deployments:
                    # Try to alias the most recent ready deployment
                    latest_ready = ready_deployments[0]
                    alias_response = requests.post(
                        f"{VERCEL_API_BASE}/v2/aliases",
                        headers=headers,
                        json={
                            "alias": "orchestra-admin-interface.vercel.app",
                            "deployment": latest_ready["url"]
                        }
                    )
                    
                    if alias_response.status_code == 200:
                        fixes_applied.append({
                            "fix": "Aliased ready deployment",
                            "deployment": latest_ready["url"],
                            "success": True
                        })
                    else:
                        fixes_applied.append({
                            "fix": "Failed to alias deployment",
                            "error": alias_response.text,
                            "success": False
                        })
    
    return {"fixes_applied": fixes_applied}

# Main execution when run with Pulumi
if __name__ == "__main__":
    # Get the token from Pulumi config
    token = VERCEL_TOKEN.apply(lambda t: t)
    
    # Monitor deployments
    def monitor_and_report(token_value: str):
        print("🔍 Monitoring Vercel Deployments with Pulumi IaC")
        print("=" * 50)
        
        status = monitor_deployments(token_value)
        
        if "error" in status:
            print(f"❌ Error: {status['error']}")
            return status
        
        print(f"\n📊 Deployment Status:")
        print(f"Project: {status['project']['name']}")
        print(f"Total Deployments: {status['deployments']['total']}")
        print(f"  - Queued: {status['deployments']['queued']}")
        print(f"  - Ready: {status['deployments']['ready']}")
        print(f"  - Building: {status['deployments']['building']}")
        print(f"  - Error: {status['deployments']['error']}")
        
        print(f"\n📋 Latest Deployments:")
        for dep in status['latest_deployments']:
            print(f"  {dep['url']} - {dep['state']} - {dep['created']}")
        
        # Troubleshoot issues
        issues = troubleshoot_deployments(token_value, status)
        
        if issues:
            print(f"\n⚠️ Issues Detected:")
            for issue in issues:
                print(f"\n  🔴 {issue['issue']} (Severity: {issue['severity']})")
                print(f"     {issue['details']}")
                print(f"     Suggested Fixes:")
                for fix in issue['fixes']:
                    print(f"       - {fix}")
            
            # Attempt fixes
            print(f"\n🔧 Attempting Automated Fixes...")
            fix_results = attempt_fixes(token_value, "admin-interface", issues)
            
            for fix in fix_results['fixes_applied']:
                if fix['success']:
                    print(f"  ✅ {fix['fix']}")
                else:
                    print(f"  ❌ {fix['fix']}: {fix.get('error', 'Unknown error')}")
        else:
            print(f"\n✅ No issues detected!")
        
        return status
    
    # Export monitoring results
    monitoring_result = token.apply(monitor_and_report)
    pulumi.export("vercel_monitoring_status", monitoring_result) 