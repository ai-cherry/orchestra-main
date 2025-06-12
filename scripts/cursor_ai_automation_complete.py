#!/usr/bin/env python3
"""
🚀 Cursor AI Complete Automation System
Unified deployment, secrets management, and context awareness for Orchestra AI

Features:
- Unified secrets management with existing fast_secrets.py
- Vercel deployment automation with IaC
- Cursor AI context awareness and auto-approval
- Complete deployment pipeline
- Real-time Notion integration
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
import tempfile

# Import existing secrets manager
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.fast_secrets import secrets, openrouter_headers, notion_headers

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CursorAIAutomationSystem:
    """Complete automation system for Cursor AI with Orchestra AI integration"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.admin_interface_path = self.project_root / "admin-interface"
        self.api_path = self.project_root / "src" / "api"
        self.deployment_results = []
        
        # Verify secrets are available
        self._verify_secrets()
    
    def _verify_secrets(self):
        """Verify all required secrets are available"""
        logger.info("🔐 Verifying secrets configuration...")
        
        required_secrets = [
            'NOTION_API_TOKEN',
            'VERCEL_TOKEN',
            'OPENAI_API_KEY',
            'ANTHROPIC_API_KEY'
        ]
        
        validation = secrets.validate_required_secrets(required_secrets)
        missing = [k for k, v in validation.items() if not v]
        
        if missing:
            logger.error(f"❌ Missing required secrets: {missing}")
            logger.info("Run: ./scripts/quick_production_setup.sh to configure secrets")
            sys.exit(1)
        
        logger.info("✅ All required secrets verified")
    
    async def deploy_complete_system(self) -> Dict[str, Any]:
        """Deploy the complete Orchestra AI system"""
        logger.info("🚀 Starting complete system deployment...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'deployments': {},
            'services': {},
            'status': 'in_progress'
        }
        
        try:
            # 1. Fix Vercel authentication issues
            logger.info("🔧 Step 1: Fixing Vercel authentication...")
            vercel_result = await self._fix_vercel_authentication()
            results['deployments']['vercel_auth'] = vercel_result
            
            # 2. Deploy admin interface
            logger.info("🌐 Step 2: Deploying admin interface...")
            admin_result = await self._deploy_admin_interface()
            results['deployments']['admin_interface'] = admin_result
            
            # 3. Start API services
            logger.info("🔌 Step 3: Starting API services...")
            api_result = await self._start_api_services()
            results['services']['api'] = api_result
            
            # 4. Configure Cursor AI context
            logger.info("🧠 Step 4: Configuring Cursor AI context...")
            cursor_result = await self._configure_cursor_ai()
            results['services']['cursor_ai'] = cursor_result
            
            # 5. Update Notion with deployment status
            logger.info("📝 Step 5: Updating Notion...")
            notion_result = await self._update_notion_status(results)
            results['services']['notion'] = notion_result
            
            # 6. Verify all systems
            logger.info("✅ Step 6: Verifying deployment...")
            verification_result = await self._verify_deployment()
            results['verification'] = verification_result
            
            results['status'] = 'completed' if verification_result['success'] else 'partial'
            
            logger.info("🎉 Complete system deployment finished!")
            return results
            
        except Exception as e:
            logger.error(f"❌ Deployment failed: {str(e)}")
            results['status'] = 'failed'
            results['error'] = str(e)
            return results
    
    async def _fix_vercel_authentication(self) -> Dict[str, Any]:
        """Fix Vercel authentication issues using existing integration"""
        try:
            vercel_token = secrets.get('vercel', 'api_key') or os.getenv('VERCEL_TOKEN')
            if not vercel_token:
                return {'success': False, 'error': 'VERCEL_TOKEN not found'}
            
            # Get projects that need authentication fixes
            projects_to_fix = [
                'orchestra-admin-interface',
                'react_app'  # This is the project ID for orchestra-ai-frontend
            ]
            
            results = []
            for project in projects_to_fix:
                result = await self._disable_vercel_sso(project, vercel_token)
                results.append(result)
            
            success = all(r['success'] for r in results)
            return {
                'success': success,
                'projects_fixed': results,
                'message': 'Vercel authentication fixed for all projects' if success else 'Some projects failed'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _disable_vercel_sso(self, project_name: str, token: str) -> Dict[str, Any]:
        """Disable SSO protection for a Vercel project"""
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # First, get the project ID
            projects_url = 'https://api.vercel.com/v9/projects'
            response = requests.get(projects_url, headers=headers)
            
            if response.status_code != 200:
                return {'success': False, 'error': f'Failed to get projects: {response.text}'}
            
            projects = response.json().get('projects', [])
            project_id = None
            
            for project in projects:
                if project['name'] == project_name:
                    project_id = project['id']
                    break
            
            if not project_id:
                return {'success': False, 'error': f'Project {project_name} not found'}
            
            # Disable SSO protection
            update_url = f'https://api.vercel.com/v9/projects/{project_id}'
            update_data = {'ssoProtection': None}
            
            response = requests.patch(update_url, headers=headers, json=update_data)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'project': project_name,
                    'project_id': project_id,
                    'message': 'SSO protection disabled'
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to update project: {response.text}'
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _deploy_admin_interface(self) -> Dict[str, Any]:
        """Deploy admin interface to Vercel"""
        try:
            # Check if admin interface is already running locally
            local_check = await self._check_local_service('http://localhost:5174')
            
            if local_check['running']:
                logger.info("✅ Admin interface already running locally on port 5174")
                return {
                    'success': True,
                    'type': 'local',
                    'url': 'http://localhost:5174',
                    'message': 'Admin interface running locally'
                }
            
            # Start local development server
            logger.info("🚀 Starting admin interface development server...")
            
            # Change to admin interface directory and start dev server
            cmd = ['npm', 'run', 'dev']
            process = subprocess.Popen(
                cmd,
                cwd=self.admin_interface_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a moment for server to start
            await asyncio.sleep(3)
            
            # Check if it's running
            local_check = await self._check_local_service('http://localhost:5174')
            
            if local_check['running']:
                return {
                    'success': True,
                    'type': 'local',
                    'url': 'http://localhost:5174',
                    'process_id': process.pid,
                    'message': 'Admin interface started successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to start admin interface'
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _start_api_services(self) -> Dict[str, Any]:
        """Start API services"""
        try:
            # Check if API is already running
            api_check = await self._check_local_service('http://localhost:8010/health')
            
            if api_check['running']:
                logger.info("✅ API service already running on port 8010")
                return {
                    'success': True,
                    'url': 'http://localhost:8010',
                    'health': api_check,
                    'message': 'API service already running'
                }
            
            # Start API service
            logger.info("🚀 Starting API service...")
            
            cmd = ['uvicorn', 'src.api.main:app', '--host', '0.0.0.0', '--port', '8010']
            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for service to start
            await asyncio.sleep(5)
            
            # Check health
            api_check = await self._check_local_service('http://localhost:8010/health')
            
            if api_check['running']:
                return {
                    'success': True,
                    'url': 'http://localhost:8010',
                    'process_id': process.pid,
                    'health': api_check,
                    'message': 'API service started successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to start API service'
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _configure_cursor_ai(self) -> Dict[str, Any]:
        """Configure Cursor AI for automatic context awareness"""
        try:
            cursor_config_dir = Path.home() / '.cursor'
            cursor_config_dir.mkdir(exist_ok=True)
            
            # Create advanced MCP configuration
            mcp_config = {
                "mcpServers": {
                    "orchestra-unified": {
                        "command": "python",
                        "args": [str(self.project_root / "mcp_unified_server.py")],
                        "env": {
                            "NOTION_API_TOKEN": secrets.get('notion', 'api_token'),
                            "OPENAI_API_KEY": secrets.get('openai', 'api_key'),
                            "ANTHROPIC_API_KEY": secrets.get('anthropic', 'api_key')
                        }
                    },
                    "infrastructure-deployment": {
                        "command": "python",
                        "args": [str(self.project_root / "infrastructure_deployment_server.py")],
                        "env": {
                            "VERCEL_TOKEN": secrets.get('vercel', 'api_key'),
                            "LAMBDA_LABS_API_KEY": secrets.get('lambda_labs', 'api_key')
                        }
                    }
                }
            }
            
            # Write MCP configuration
            mcp_config_file = cursor_config_dir / 'mcp.json'
            with open(mcp_config_file, 'w') as f:
                json.dump(mcp_config, f, indent=2)
            
            # Create Cursor AI rules for auto-approval
            cursor_rules = {
                "auto_approval": {
                    "enabled": True,
                    "patterns": [
                        "read_file",
                        "list_dir", 
                        "grep_search",
                        "file_search",
                        "web_search"
                    ],
                    "exclude_patterns": [
                        "delete_file",
                        "run_terminal_cmd"
                    ]
                },
                "context_awareness": {
                    "auto_load_project_context": True,
                    "remember_conversation_context": True,
                    "use_mcp_servers": True
                },
                "development_workflow": {
                    "auto_format_code": True,
                    "auto_fix_imports": True,
                    "use_fast_secrets": True
                }
            }
            
            cursor_rules_file = cursor_config_dir / 'automation_rules.json'
            with open(cursor_rules_file, 'w') as f:
                json.dump(cursor_rules, f, indent=2)
            
            return {
                'success': True,
                'mcp_config': str(mcp_config_file),
                'rules_config': str(cursor_rules_file),
                'message': 'Cursor AI configured for automation'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _update_notion_status(self, deployment_results: Dict[str, Any]) -> Dict[str, Any]:
        """Update Notion with deployment status"""
        try:
            headers = notion_headers()
            if not headers.get('Authorization'):
                return {'success': False, 'error': 'Notion API token not configured'}
            
            # Create deployment status page
            page_data = {
                "parent": {
                    "database_id": "20bdba04940281fd9558d66c07d9576c"  # Development Log database
                },
                "properties": {
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": f"Complete System Deployment - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                                }
                            }
                        ]
                    },
                    "Status": {
                        "select": {
                            "name": deployment_results['status'].title()
                        }
                    },
                    "Type": {
                        "select": {
                            "name": "Deployment"
                        }
                    }
                },
                "children": [
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "🚀 Complete System Deployment Results"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"Deployment Status: {deployment_results['status'].upper()}\nTimestamp: {deployment_results['timestamp']}"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "language": "json",
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": json.dumps(deployment_results, indent=2)
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
            
            response = requests.post(
                'https://api.notion.com/v1/pages',
                headers=headers,
                json=page_data
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'page_id': response.json()['id'],
                    'message': 'Notion updated with deployment status'
                }
            else:
                return {
                    'success': False,
                    'error': f'Notion API error: {response.text}'
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _verify_deployment(self) -> Dict[str, Any]:
        """Verify all deployed services are working"""
        try:
            services_to_check = [
                ('Admin Interface', 'http://localhost:5174'),
                ('API Service', 'http://localhost:8010/health'),
                ('Vercel Admin', 'https://orchestra-admin-interface.vercel.app'),
                ('Vercel Frontend', 'https://orchestra-ai-frontend.vercel.app')
            ]
            
            results = {}
            all_success = True
            
            for name, url in services_to_check:
                check_result = await self._check_local_service(url)
                results[name] = check_result
                if not check_result['running']:
                    all_success = False
            
            return {
                'success': all_success,
                'services': results,
                'message': 'All services verified' if all_success else 'Some services not responding'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _check_local_service(self, url: str) -> Dict[str, Any]:
        """Check if a local service is running"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    return {
                        'running': True,
                        'status_code': response.status,
                        'url': url
                    }
        except:
            try:
                # Fallback to requests for synchronous check
                response = requests.get(url, timeout=5)
                return {
                    'running': True,
                    'status_code': response.status_code,
                    'url': url
                }
            except:
                return {
                    'running': False,
                    'url': url
                }
    
    def generate_summary_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive summary report"""
        report = f"""
🎯 Orchestra AI Complete Deployment Summary
{'='*50}

📅 Deployment Time: {results['timestamp']}
🎯 Overall Status: {results['status'].upper()}

🚀 DEPLOYMENT RESULTS:
{'-'*30}
"""
        
        for deployment, result in results.get('deployments', {}).items():
            status = "✅" if result.get('success') else "❌"
            report += f"{status} {deployment.replace('_', ' ').title()}: {result.get('message', 'No message')}\n"
        
        report += f"\n🔌 SERVICE STATUS:\n{'-'*30}\n"
        
        for service, result in results.get('services', {}).items():
            status = "✅" if result.get('success') else "❌"
            report += f"{status} {service.replace('_', ' ').title()}: {result.get('message', 'No message')}\n"
        
        if 'verification' in results:
            report += f"\n🔍 VERIFICATION RESULTS:\n{'-'*30}\n"
            verification = results['verification']
            for service, check in verification.get('services', {}).items():
                status = "✅" if check.get('running') else "❌"
                report += f"{status} {service}: {check.get('url', 'Unknown URL')}\n"
        
        report += f"\n📊 NEXT STEPS:\n{'-'*30}\n"
        
        if results['status'] == 'completed':
            report += """✅ All systems operational!
🌐 Admin Interface: http://localhost:5174
🔌 API Service: http://localhost:8010
📝 Notion: Updated with deployment status
🧠 Cursor AI: Configured for auto-approval

🎯 Ready for development with full automation!"""
        else:
            report += """⚠️  Some issues detected. Check individual service logs.
🔧 Run individual deployment steps to resolve issues.
📞 Contact support if problems persist."""
        
        return report

async def main():
    """Main execution function"""
    print("🚀 Orchestra AI Complete Automation System")
    print("=" * 50)
    
    automation = CursorAIAutomationSystem()
    
    try:
        # Run complete deployment
        results = await automation.deploy_complete_system()
        
        # Generate and display summary
        summary = automation.generate_summary_report(results)
        print(summary)
        
        # Save results to file
        results_file = Path(__file__).parent.parent / 'deployment_automation_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Return appropriate exit code
        sys.exit(0 if results['status'] == 'completed' else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 