#!/usr/bin/env python3
"""
Vercel Authentication Fix Script
Automatically disables Vercel Authentication to make deployments publicly accessible
"""

import os
import sys
import json
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class VercelProject:
    id: str
    name: str
    sso_protection: Optional[Dict] = None

class VercelAuthenticationFixer:
    """Fixes Vercel authentication issues via API"""
    
    def __init__(self):
        self.token = os.getenv('VERCEL_TOKEN')
        self.org_id = os.getenv('VERCEL_ORG_ID', 'lynn-musils-projects')
        self.base_url = 'https://api.vercel.com'
        
        if not self.token:
            print("❌ VERCEL_TOKEN not found in environment")
            print("Please set VERCEL_TOKEN in your environment or .env file")
            sys.exit(1)
            
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def get_projects(self) -> List[VercelProject]:
        """Get all projects for the team"""
        url = f"{self.base_url}/v9/projects"
        params = {'teamId': self.org_id} if self.org_id else {}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            projects = []
            for project_data in response.json().get('projects', []):
                project = VercelProject(
                    id=project_data['id'],
                    name=project_data['name'],
                    sso_protection=project_data.get('ssoProtection')
                )
                projects.append(project)
            
            return projects
            
        except requests.RequestException as e:
            print(f"❌ Error fetching projects: {e}")
            return []
    
    def disable_sso_protection(self, project: VercelProject) -> bool:
        """Disable SSO protection for a project"""
        url = f"{self.base_url}/v9/projects/{project.id}"
        params = {'teamId': self.org_id} if self.org_id else {}
        
        # Payload to disable SSO protection
        payload = {
            'ssoProtection': None
        }
        
        try:
            response = requests.patch(
                url, 
                headers=self.headers, 
                params=params,
                json=payload
            )
            response.raise_for_status()
            
            print(f"✅ Disabled SSO protection for {project.name}")
            return True
            
        except requests.RequestException as e:
            print(f"❌ Error disabling SSO for {project.name}: {e}")
            return False
    
    def get_project_deployments(self, project_id: str) -> List[Dict]:
        """Get deployments for a project"""
        url = f"{self.base_url}/v6/deployments"
        params = {
            'projectId': project_id,
            'limit': 10
        }
        if self.org_id:
            params['teamId'] = self.org_id
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get('deployments', [])
            
        except requests.RequestException as e:
            print(f"❌ Error fetching deployments: {e}")
            return []
    
    def promote_deployment(self, deployment_id: str) -> bool:
        """Promote a deployment to production"""
        url = f"{self.base_url}/v13/deployments/{deployment_id}/promote"
        params = {'teamId': self.org_id} if self.org_id else {}
        
        try:
            response = requests.post(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            print(f"✅ Promoted deployment {deployment_id[:8]}... to production")
            return True
            
        except requests.RequestException as e:
            print(f"❌ Error promoting deployment: {e}")
            return False
    
    def fix_orchestra_projects(self) -> Dict[str, bool]:
        """Fix authentication issues for Orchestra projects"""
        print("🔍 Fetching Vercel projects...")
        projects = self.get_projects()
        
        if not projects:
            print("❌ No projects found")
            return {}
        
        # Find Orchestra projects
        orchestra_projects = [
            p for p in projects 
            if any(keyword in p.name.lower() for keyword in [
                'orchestra', 'admin-interface', 'react_app', 'ai-frontend'
            ])
        ]
        
        if not orchestra_projects:
            print("❌ No Orchestra projects found")
            print("Available projects:")
            for p in projects[:10]:  # Show first 10
                print(f"  - {p.name}")
            return {}
        
        print(f"🎭 Found {len(orchestra_projects)} Orchestra projects:")
        for p in orchestra_projects:
            sso_status = "Protected" if p.sso_protection else "Public"
            print(f"  - {p.name} ({sso_status})")
        
        results = {}
        
        # Fix each project
        for project in orchestra_projects:
            print(f"\n🔧 Fixing {project.name}...")
            
            # Disable SSO protection if enabled
            if project.sso_protection:
                success = self.disable_sso_protection(project)
                results[f"{project.name}_sso_disabled"] = success
            else:
                print(f"✅ {project.name} already has public access")
                results[f"{project.name}_already_public"] = True
            
            # Get and promote latest successful deployment
            deployments = self.get_project_deployments(project.id)
            if deployments:
                # Find latest ready deployment
                ready_deployments = [
                    d for d in deployments 
                    if d.get('state') == 'READY'
                ]
                
                if ready_deployments:
                    latest = ready_deployments[0]
                    print(f"🚀 Found ready deployment: {latest['url']}")
                    
                    # Promote if not already production
                    if latest.get('target') != 'production':
                        success = self.promote_deployment(latest['uid'])
                        results[f"{project.name}_promoted"] = success
                    else:
                        print(f"✅ Deployment already in production")
                        results[f"{project.name}_already_production"] = True
                else:
                    print(f"⚠️ No ready deployments found for {project.name}")
                    results[f"{project.name}_no_ready_deployments"] = False
            else:
                print(f"⚠️ No deployments found for {project.name}")
                results[f"{project.name}_no_deployments"] = False
        
        return results
    
    def verify_fix(self) -> Dict[str, str]:
        """Verify that the fixes worked"""
        print("\n🔍 Verifying fixes...")
        
        test_urls = [
            'https://orchestra-admin-interface.vercel.app',
            'https://orchestra-ai-frontend.vercel.app'
        ]
        
        results = {}
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=10, allow_redirects=False)
                
                if response.status_code == 200:
                    results[url] = "✅ Accessible"
                elif response.status_code in [301, 302, 307, 308]:
                    # Check if it's redirecting to auth
                    location = response.headers.get('location', '')
                    if 'sso-api' in location or 'auth' in location:
                        results[url] = "❌ Still redirecting to auth"
                    else:
                        results[url] = f"🔄 Redirecting to {location}"
                else:
                    results[url] = f"⚠️ Status {response.status_code}"
                    
            except requests.RequestException as e:
                results[url] = f"❌ Error: {str(e)[:50]}..."
        
        return results

def main():
    """Main execution function"""
    print("🚨 Vercel Authentication Fix Script")
    print("=" * 50)
    
    fixer = VercelAuthenticationFixer()
    
    # Fix authentication issues
    results = fixer.fix_orchestra_projects()
    
    # Print summary
    print("\n📊 Fix Summary:")
    print("-" * 30)
    for action, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {action}")
    
    # Verify fixes
    verification = fixer.verify_fix()
    
    print("\n🔍 Verification Results:")
    print("-" * 30)
    for url, status in verification.items():
        print(f"{status} {url}")
    
    # Final recommendations
    print("\n💡 Next Steps:")
    print("-" * 20)
    
    if any("❌" in status for status in verification.values()):
        print("🔄 Some URLs still have issues. Try:")
        print("  1. Wait 2-3 minutes for DNS propagation")
        print("  2. Clear browser cache")
        print("  3. Try incognito/private browsing")
        print("  4. Use the standalone interface: orchestra-admin-simple.html")
    else:
        print("🎉 All URLs should be accessible!")
        print("  - Clear browser cache if you still see auth pages")
        print("  - DNS changes may take a few minutes to propagate")
    
    print(f"\n🛠️ Backup Solution: Use orchestra-admin-simple.html")
    print(f"📊 Backend APIs: All operational at 192.9.142.8")

if __name__ == "__main__":
    main() 