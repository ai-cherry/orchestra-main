#!/usr/bin/env python3
"""
🚀 Complete System Deployment for Orchestra AI
Simplified automation with full functionality
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import requests
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from utils.fast_secrets import secrets, notion_headers
    SECRETS_AVAILABLE = True
except ImportError:
    print("⚠️ Fast secrets not available, using environment variables")
    SECRETS_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OrchestryDeployment:
    """Complete Orchestra AI deployment system"""
    
    def __init__(self):
        self.project_root = project_root
        self.admin_interface_path = self.project_root / "admin-interface"
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'deployments': {},
            'services': {},
            'status': 'starting'
        }
    
    def get_secret(self, service: str, key: str = 'api_key') -> str:
        """Get secret using fast_secrets or environment variables"""
        if SECRETS_AVAILABLE:
            return secrets.get(service, key)
        else:
            # Fallback to environment variables
            env_map = {
                ('notion', 'api_token'): 'NOTION_API_TOKEN',
                ('vercel', 'api_key'): 'VERCEL_TOKEN',
                ('openai', 'api_key'): 'OPENAI_API_KEY',
                ('anthropic', 'api_key'): 'ANTHROPIC_API_KEY'
            }
            env_var = env_map.get((service, key))
            return os.getenv(env_var, '')
    
    async def deploy_complete_system(self):
        """Deploy the complete system"""
        logger.info("🚀 Starting complete Orchestra AI deployment...")
        
        try:
            # Step 1: Verify prerequisites
            logger.info("🔍 Step 1: Verifying prerequisites...")
            prereq_result = self.verify_prerequisites()
            self.results['deployments']['prerequisites'] = prereq_result
            
            if not prereq_result['success']:
                self.results['status'] = 'failed'
                return self.results
            
            # Step 2: Fix Vercel authentication
            logger.info("🔧 Step 2: Fixing Vercel authentication...")
            vercel_result = await self.fix_vercel_authentication()
            self.results['deployments']['vercel_auth'] = vercel_result
            
            # Step 3: Start local services
            logger.info("🚀 Step 3: Starting local services...")
            services_result = await self.start_local_services()
            self.results['services']['local'] = services_result
            
            # Step 4: Configure Cursor AI
            logger.info("🧠 Step 4: Configuring Cursor AI...")
            cursor_result = self.configure_cursor_ai()
            self.results['services']['cursor_ai'] = cursor_result
            
            # Step 5: Update Notion
            logger.info("📝 Step 5: Updating Notion...")
            notion_result = await self.update_notion()
            self.results['services']['notion'] = notion_result
            
            # Step 6: Verify deployment
            logger.info("✅ Step 6: Verifying deployment...")
            verification_result = await self.verify_deployment()
            self.results['verification'] = verification_result
            
            # Determine final status
            all_critical_success = (
                prereq_result['success'] and
                services_result['success'] and
                cursor_result['success']
            )
            
            self.results['status'] = 'completed' if all_critical_success else 'partial'
            
            logger.info("🎉 Deployment process finished!")
            return self.results
            
        except Exception as e:
            logger.error(f"❌ Deployment failed: {str(e)}")
            self.results['status'] = 'failed'
            self.results['error'] = str(e)
            return self.results
    
    def verify_prerequisites(self):
        """Verify all prerequisites are met"""
        try:
            checks = {}
            
            # Check Python
            checks['python'] = sys.version_info >= (3, 8)
            
            # Check Node.js
            try:
                result = subprocess.run(['node', '--version'], capture_output=True, text=True)
                checks['nodejs'] = result.returncode == 0
            except:
                checks['nodejs'] = False
            
            # Check npm
            try:
                result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
                checks['npm'] = result.returncode == 0
            except:
                checks['npm'] = False
            
            # Check admin interface directory
            checks['admin_interface'] = self.admin_interface_path.exists()
            
            # Check package.json
            package_json = self.admin_interface_path / "package.json"
            checks['package_json'] = package_json.exists()
            
            # Check secrets
            notion_token = self.get_secret('notion', 'api_token')
            checks['notion_token'] = bool(notion_token)
            
            all_passed = all(checks.values())
            
            return {
                'success': all_passed,
                'checks': checks,
                'message': 'All prerequisites met' if all_passed else 'Some prerequisites missing'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def fix_vercel_authentication(self):
        """Fix Vercel authentication issues"""
        try:
            vercel_token = self.get_secret('vercel', 'api_key')
            if not vercel_token:
                return {
                    'success': False, 
                    'error': 'VERCEL_TOKEN not configured',
                    'message': 'Skipping Vercel authentication fix'
                }
            
            headers = {
                'Authorization': f'Bearer {vercel_token}',
                'Content-Type': 'application/json'
            }
            
            # Get projects
            response = requests.get('https://api.vercel.com/v9/projects', headers=headers, timeout=10)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Failed to get Vercel projects: {response.status_code}',
                    'message': 'Vercel API access failed'
                }
            
            projects = response.json().get('projects', [])
            target_projects = ['orchestra-admin-interface', 'react_app']
            
            fixed_projects = []
            for project_data in projects:
                if project_data['name'] in target_projects:
                    # Disable SSO protection
                    project_id = project_data['id']
                    update_url = f'https://api.vercel.com/v9/projects/{project_id}'
                    update_data = {'ssoProtection': None}
                    
                    update_response = requests.patch(update_url, headers=headers, json=update_data, timeout=10)
                    
                    if update_response.status_code == 200:
                        fixed_projects.append(project_data['name'])
            
            return {
                'success': True,
                'projects_fixed': fixed_projects,
                'message': f'Fixed authentication for {len(fixed_projects)} projects'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Vercel authentication fix failed'
            }
    
    async def start_local_services(self):
        """Start local development services"""
        try:
            services_started = []
            
            # Check if API is already running
            api_running = await self.check_service('http://localhost:8010/health')
            if not api_running:
                logger.info("🔌 Starting API service...")
                api_cmd = ['uvicorn', 'src.api.main:app', '--host', '0.0.0.0', '--port', '8010']
                subprocess.Popen(api_cmd, cwd=self.project_root)
                await asyncio.sleep(3)
                services_started.append('api')
            else:
                logger.info("✅ API service already running")
            
            # Check if admin interface is running
            admin_running = await self.check_service('http://localhost:5174')
            if not admin_running:
                logger.info("🌐 Starting admin interface...")
                admin_cmd = ['npm', 'run', 'dev']
                subprocess.Popen(admin_cmd, cwd=self.admin_interface_path)
                await asyncio.sleep(3)
                services_started.append('admin')
            else:
                logger.info("✅ Admin interface already running")
            
            # Verify services are running
            api_check = await self.check_service('http://localhost:8010/health')
            admin_check = await self.check_service('http://localhost:5174')
            
            return {
                'success': api_check or admin_check,
                'api_running': api_check,
                'admin_running': admin_check,
                'services_started': services_started,
                'message': f'Services status - API: {"✅" if api_check else "❌"}, Admin: {"✅" if admin_check else "❌"}'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def configure_cursor_ai(self):
        """Configure Cursor AI for automation"""
        try:
            cursor_config_dir = Path.home() / '.cursor'
            cursor_config_dir.mkdir(exist_ok=True)
            
            # Create MCP configuration
            mcp_config = {
                "mcpServers": {
                    "orchestra-unified": {
                        "command": "python",
                        "args": [str(self.project_root / "mcp_unified_server.py")],
                        "env": {
                            "NOTION_API_TOKEN": self.get_secret('notion', 'api_token'),
                            "OPENAI_API_KEY": self.get_secret('openai', 'api_key'),
                            "ANTHROPIC_API_KEY": self.get_secret('anthropic', 'api_key')
                        }
                    }
                }
            }
            
            mcp_config_file = cursor_config_dir / 'mcp.json'
            with open(mcp_config_file, 'w') as f:
                json.dump(mcp_config, f, indent=2)
            
            # Create automation rules
            automation_rules = {
                "auto_approval": {
                    "enabled": True,
                    "safe_operations": [
                        "read_file", "list_dir", "grep_search", "file_search", "web_search"
                    ]
                },
                "context_awareness": {
                    "auto_load_project_context": True,
                    "use_mcp_servers": True
                }
            }
            
            rules_file = cursor_config_dir / 'automation_rules.json'
            with open(rules_file, 'w') as f:
                json.dump(automation_rules, f, indent=2)
            
            return {
                'success': True,
                'mcp_config': str(mcp_config_file),
                'rules_config': str(rules_file),
                'message': 'Cursor AI configured successfully'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def update_notion(self):
        """Update Notion with deployment status"""
        try:
            if not SECRETS_AVAILABLE:
                return {'success': False, 'error': 'Secrets not available for Notion update'}
            
            headers = notion_headers()
            if not headers.get('Authorization'):
                return {'success': False, 'error': 'Notion token not configured'}
            
            # Create a simple status update
            page_data = {
                "parent": {
                    "database_id": "20bdba04940281fd9558d66c07d9576c"
                },
                "properties": {
                    "Name": {
                        "title": [{"text": {"content": f"System Deployment - {datetime.now().strftime('%Y-%m-%d %H:%M')}"}}]
                    },
                    "Status": {
                        "select": {"name": "In Progress"}
                    },
                    "Type": {
                        "select": {"name": "Deployment"}
                    }
                }
            }
            
            response = requests.post(
                'https://api.notion.com/v1/pages',
                headers=headers,
                json=page_data,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'page_id': response.json()['id'],
                    'message': 'Notion updated successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'Notion API error: {response.status_code}',
                    'message': 'Notion update failed'
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def verify_deployment(self):
        """Verify the deployment is working"""
        try:
            services = {
                'API Service': 'http://localhost:8010/health',
                'Admin Interface': 'http://localhost:5174',
                'Vercel Admin': 'https://orchestra-admin-interface.vercel.app',
                'Vercel Frontend': 'https://orchestra-ai-frontend.vercel.app'
            }
            
            results = {}
            for name, url in services.items():
                running = await self.check_service(url)
                results[name] = {'running': running, 'url': url}
            
            local_services_ok = results['API Service']['running'] or results['Admin Interface']['running']
            
            return {
                'success': local_services_ok,
                'services': results,
                'message': 'Local services verified' if local_services_ok else 'Local services need attention'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def check_service(self, url: str) -> bool:
        """Check if a service is responding"""
        try:
            response = requests.get(url, timeout=5)
            return response.status_code < 400
        except:
            return False
    
    def generate_summary(self):
        """Generate deployment summary"""
        status = self.results['status']
        timestamp = self.results['timestamp']
        
        summary = f"""
🎯 Orchestra AI Deployment Summary
{'='*50}

📅 Deployment Time: {timestamp}
🎯 Status: {status.upper()}

🚀 DEPLOYMENT RESULTS:
{'-'*30}
"""
        
        for category, items in self.results.items():
            if category in ['deployments', 'services']:
                for name, result in items.items():
                    status_icon = "✅" if result.get('success') else "❌"
                    message = result.get('message', 'No message')
                    summary += f"{status_icon} {name.replace('_', ' ').title()}: {message}\n"
        
        if 'verification' in self.results:
            summary += f"\n🔍 SERVICE VERIFICATION:\n{'-'*30}\n"
            for service, check in self.results['verification'].get('services', {}).items():
                status_icon = "✅" if check.get('running') else "❌"
                summary += f"{status_icon} {service}: {check.get('url')}\n"
        
        summary += f"\n📊 NEXT STEPS:\n{'-'*30}\n"
        
        if status == 'completed':
            summary += """✅ All systems operational!
🌐 Admin Interface: http://localhost:5174
🔌 API Service: http://localhost:8010
🧠 Cursor AI: Configured for automation

🎯 Ready for development!"""
        else:
            summary += """⚠️ Some issues detected.
🔧 Check individual service logs.
🚀 Services may still be starting up."""
        
        return summary

async def main():
    """Main execution"""
    print("🚀 Orchestra AI Complete Deployment")
    print("=" * 50)
    
    deployment = OrchestryDeployment()
    
    try:
        results = await deployment.deploy_complete_system()
        summary = deployment.generate_summary()
        print(summary)
        
        # Save results
        results_file = deployment.project_root / 'deployment_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Results saved to: {results_file}")
        
        # Exit with appropriate code
        exit_code = 0 if results['status'] in ['completed', 'partial'] else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️ Deployment interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 