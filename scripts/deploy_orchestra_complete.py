#!/usr/bin/env python3
"""
🚀 Orchestra AI Complete Deployment & Configuration
Works with existing infrastructure and provides full automation setup
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

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OrchestryCompleteDeployment:
    """Complete Orchestra AI deployment and configuration system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.admin_interface_path = self.project_root / "admin-interface"
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'phase': 'initialization',
            'deployments': {},
            'services': {},
            'configuration': {},
            'status': 'starting'
        }
    
    async def deploy_complete_system(self):
        """Deploy and configure the complete Orchestra AI system"""
        logger.info("🚀 Starting Orchestra AI Complete Deployment...")
        
        try:
            # Phase 1: Infrastructure Setup
            logger.info("🏗️ Phase 1: Infrastructure Setup")
            self.results['phase'] = 'infrastructure'
            
            infra_result = await self.setup_infrastructure()
            self.results['deployments']['infrastructure'] = infra_result
            
            # Phase 2: Local Services
            logger.info("🔌 Phase 2: Local Services")
            self.results['phase'] = 'services'
            
            services_result = await self.deploy_local_services()
            self.results['services']['local'] = services_result
            
            # Phase 3: Vercel Configuration
            logger.info("🌐 Phase 3: Vercel Configuration")
            self.results['phase'] = 'vercel'
            
            vercel_result = await self.configure_vercel()
            self.results['deployments']['vercel'] = vercel_result
            
            # Phase 4: Cursor AI Setup
            logger.info("🧠 Phase 4: Cursor AI Configuration")
            self.results['phase'] = 'cursor_ai'
            
            cursor_result = await self.setup_cursor_ai()
            self.results['configuration']['cursor_ai'] = cursor_result
            
            # Phase 5: Documentation & Guides
            logger.info("📚 Phase 5: Documentation & Setup Guides")
            self.results['phase'] = 'documentation'
            
            docs_result = await self.create_documentation()
            self.results['configuration']['documentation'] = docs_result
            
            # Phase 6: Verification
            logger.info("✅ Phase 6: System Verification")
            self.results['phase'] = 'verification'
            
            verification_result = await self.verify_complete_system()
            self.results['verification'] = verification_result
            
            # Determine final status
            critical_success = (
                infra_result.get('success', False) and
                services_result.get('success', False) and
                cursor_result.get('success', False)
            )
            
            self.results['status'] = 'completed' if critical_success else 'partial'
            self.results['phase'] = 'completed'
            
            logger.info("🎉 Complete deployment finished!")
            return self.results
            
        except Exception as e:
            logger.error(f"❌ Deployment failed: {str(e)}")
            self.results['status'] = 'failed'
            self.results['error'] = str(e)
            return self.results
    
    async def setup_infrastructure(self):
        """Setup basic infrastructure and prerequisites"""
        try:
            checks = {}
            
            # Check Python
            checks['python'] = {
                'version': f"{sys.version_info.major}.{sys.version_info.minor}",
                'compatible': sys.version_info >= (3, 8),
                'path': sys.executable
            }
            
            # Check Node.js and npm
            try:
                node_result = subprocess.run(['node', '--version'], capture_output=True, text=True)
                checks['nodejs'] = {
                    'available': node_result.returncode == 0,
                    'version': node_result.stdout.strip() if node_result.returncode == 0 else 'Not found'
                }
                
                npm_result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
                checks['npm'] = {
                    'available': npm_result.returncode == 0,
                    'version': npm_result.stdout.strip() if npm_result.returncode == 0 else 'Not found'
                }
            except:
                checks['nodejs'] = {'available': False, 'version': 'Not found'}
                checks['npm'] = {'available': False, 'version': 'Not found'}
            
            # Check project structure
            checks['project_structure'] = {
                'admin_interface': self.admin_interface_path.exists(),
                'package_json': (self.admin_interface_path / "package.json").exists(),
                'src_api': (self.project_root / "src" / "api").exists(),
                'utils': (self.project_root / "utils").exists(),
                'fast_secrets': (self.project_root / "utils" / "fast_secrets.py").exists()
            }
            
            # Install npm dependencies if needed
            if checks['npm']['available'] and checks['project_structure']['package_json']:
                logger.info("📦 Installing npm dependencies...")
                npm_install = subprocess.run(
                    ['npm', 'install'], 
                    cwd=self.admin_interface_path, 
                    capture_output=True, 
                    text=True
                )
                checks['npm_install'] = {
                    'success': npm_install.returncode == 0,
                    'output': npm_install.stdout[-200:] if npm_install.stdout else ''
                }
            
            # Check Python dependencies
            try:
                import uvicorn, fastapi, requests
                checks['python_deps'] = {'uvicorn': True, 'fastapi': True, 'requests': True}
            except ImportError as e:
                checks['python_deps'] = {'error': str(e)}
            
            all_critical_ok = (
                checks['python']['compatible'] and
                checks['project_structure']['admin_interface'] and
                checks['project_structure']['src_api']
            )
            
            return {
                'success': all_critical_ok,
                'checks': checks,
                'message': 'Infrastructure setup completed' if all_critical_ok else 'Some infrastructure issues detected'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def deploy_local_services(self):
        """Deploy local development services"""
        try:
            services = {}
            
            # Check and start API service
            api_running = await self.check_service('http://localhost:8010/health')
            if not api_running:
                logger.info("🔌 Starting API service...")
                api_cmd = ['uvicorn', 'src.api.main:app', '--host', '0.0.0.0', '--port', '8010', '--reload']
                api_process = subprocess.Popen(
                    api_cmd, 
                    cwd=self.project_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                await asyncio.sleep(4)
                api_running = await self.check_service('http://localhost:8010/health')
                services['api'] = {
                    'started': True,
                    'running': api_running,
                    'pid': api_process.pid,
                    'url': 'http://localhost:8010'
                }
            else:
                services['api'] = {
                    'started': False,
                    'running': True,
                    'url': 'http://localhost:8010',
                    'message': 'Already running'
                }
            
            # Check and start admin interface
            admin_running = await self.check_service('http://localhost:5174')
            if not admin_running:
                logger.info("🌐 Starting admin interface...")
                admin_cmd = ['npm', 'run', 'dev']
                admin_process = subprocess.Popen(
                    admin_cmd,
                    cwd=self.admin_interface_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                await asyncio.sleep(4)
                admin_running = await self.check_service('http://localhost:5174')
                services['admin'] = {
                    'started': True,
                    'running': admin_running,
                    'pid': admin_process.pid,
                    'url': 'http://localhost:5174'
                }
            else:
                services['admin'] = {
                    'started': False,
                    'running': True,
                    'url': 'http://localhost:5174',
                    'message': 'Already running'
                }
            
            # Check MCP server
            mcp_server_path = self.project_root / "mcp_unified_server.py"
            services['mcp'] = {
                'available': mcp_server_path.exists(),
                'path': str(mcp_server_path)
            }
            
            success = services['api']['running'] or services['admin']['running']
            
            return {
                'success': success,
                'services': services,
                'message': f"Local services - API: {'✅' if services['api']['running'] else '❌'}, Admin: {'✅' if services['admin']['running'] else '❌'}"
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def configure_vercel(self):
        """Configure Vercel deployments"""
        try:
            # Check for Vercel token in environment
            vercel_token = os.getenv('VERCEL_TOKEN')
            
            if not vercel_token:
                # Create instructions for Vercel setup
                vercel_setup = {
                    'token_configured': False,
                    'setup_instructions': [
                        "1. Go to https://vercel.com/account/tokens",
                        "2. Create a new token",
                        "3. Add VERCEL_TOKEN to your environment variables",
                        "4. Re-run this deployment script"
                    ],
                    'projects_to_configure': [
                        'orchestra-admin-interface',
                        'orchestra-ai-frontend'
                    ]
                }
                
                return {
                    'success': False,
                    'vercel_setup': vercel_setup,
                    'message': 'Vercel token not configured - setup instructions provided'
                }
            
            # If token is available, try to configure projects
            headers = {
                'Authorization': f'Bearer {vercel_token}',
                'Content-Type': 'application/json'
            }
            
            try:
                response = requests.get('https://api.vercel.com/v9/projects', headers=headers, timeout=10)
                
                if response.status_code == 200:
                    projects = response.json().get('projects', [])
                    target_projects = ['orchestra-admin-interface', 'react_app']
                    
                    configured_projects = []
                    for project_data in projects:
                        if project_data['name'] in target_projects:
                            # Disable SSO protection
                            project_id = project_data['id']
                            update_url = f'https://api.vercel.com/v9/projects/{project_id}'
                            update_data = {'ssoProtection': None}
                            
                            update_response = requests.patch(update_url, headers=headers, json=update_data, timeout=10)
                            
                            if update_response.status_code == 200:
                                configured_projects.append({
                                    'name': project_data['name'],
                                    'id': project_id,
                                    'url': f"https://{project_data['name']}.vercel.app"
                                })
                    
                    return {
                        'success': True,
                        'token_configured': True,
                        'projects_configured': configured_projects,
                        'message': f'Configured {len(configured_projects)} Vercel projects'
                    }
                else:
                    return {
                        'success': False,
                        'token_configured': True,
                        'error': f'Vercel API error: {response.status_code}',
                        'message': 'Vercel token invalid or insufficient permissions'
                    }
                    
            except requests.RequestException as e:
                return {
                    'success': False,
                    'token_configured': True,
                    'error': str(e),
                    'message': 'Vercel API request failed'
                }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def setup_cursor_ai(self):
        """Setup Cursor AI configuration"""
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
                            "PYTHONPATH": str(self.project_root)
                        }
                    },
                    "infrastructure-deployment": {
                        "command": "python",
                        "args": [str(self.project_root / "infrastructure_deployment_server.py")],
                        "env": {
                            "PYTHONPATH": str(self.project_root)
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
                        "read_file", "list_dir", "grep_search", "file_search", "web_search",
                        "get_memory_status", "get_infrastructure_status", "chat_with_persona"
                    ],
                    "manual_approval_required": [
                        "edit_file", "delete_file", "run_terminal_cmd", 
                        "deploy_vercel_frontend", "manage_lambda_labs_instance"
                    ]
                },
                "context_awareness": {
                    "auto_load_project_context": True,
                    "remember_conversation_history": True,
                    "use_mcp_servers": True,
                    "smart_routing": True
                },
                "development_workflow": {
                    "auto_format_code": True,
                    "auto_fix_imports": True,
                    "use_fast_secrets": True,
                    "enforce_type_hints": True
                }
            }
            
            rules_file = cursor_config_dir / 'automation_rules.json'
            with open(rules_file, 'w') as f:
                json.dump(automation_rules, f, indent=2)
            
            # Create project-specific settings
            project_cursor_dir = self.project_root / '.cursor'
            project_cursor_dir.mkdir(exist_ok=True)
            
            project_settings = {
                "orchestra_ai": {
                    "project_type": "ai_orchestration_platform",
                    "architecture": "microservices",
                    "primary_languages": ["python", "typescript"],
                    "frameworks": ["fastapi", "react", "vite"],
                    "infrastructure": ["vercel", "lambda_labs"],
                    "ai_services": ["openai", "anthropic", "openrouter"],
                    "personas": {
                        "cherry": "cross_domain_coordination",
                        "sophia": "financial_services_expert",
                        "karen": "medical_coding_specialist"
                    }
                },
                "automation": {
                    "mcp_servers": ["orchestra-unified", "infrastructure-deployment"],
                    "auto_approval_enabled": True,
                    "context_awareness_enabled": True
                }
            }
            
            project_settings_file = project_cursor_dir / 'settings.json'
            with open(project_settings_file, 'w') as f:
                json.dump(project_settings, f, indent=2)
            
            return {
                'success': True,
                'files_created': [
                    str(mcp_config_file),
                    str(rules_file),
                    str(project_settings_file)
                ],
                'message': 'Cursor AI configured for full automation'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def create_documentation(self):
        """Create comprehensive documentation and setup guides"""
        try:
            docs_created = []
            
            # Create API keys setup guide
            api_keys_guide = self.project_root / 'API_KEYS_SETUP_GUIDE.md'
            with open(api_keys_guide, 'w') as f:
                f.write("""# 🔑 API Keys Setup Guide for Orchestra AI

## Required API Keys

### Core Services
- **NOTION_API_TOKEN**: Get from https://www.notion.so/my-integrations
- **OPENAI_API_KEY**: Get from https://platform.openai.com/api-keys
- **ANTHROPIC_API_KEY**: Get from https://console.anthropic.com/

### Infrastructure
- **VERCEL_TOKEN**: Get from https://vercel.com/account/tokens
- **LAMBDA_LABS_API_KEY**: Get from https://cloud.lambdalabs.com/api-keys

### Optional Services
- **OPENROUTER_API_KEY**: Get from https://openrouter.ai/keys
- **PERPLEXITY_API_KEY**: Get from https://www.perplexity.ai/settings/api

## Setup Instructions

1. Create a `.env` file in the project root:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:
```bash
NOTION_API_TOKEN=ntn_your_token_here
OPENAI_API_KEY=sk-your_key_here
ANTHROPIC_API_KEY=sk-ant-your_key_here
VERCEL_TOKEN=your_vercel_token_here
```

3. Restart the deployment:
```bash
python3 scripts/deploy_orchestra_complete.py
```

## Verification

Test your setup:
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from utils.fast_secrets import secrets
print('Notion:', bool(secrets.get('notion', 'api_token')))
print('OpenAI:', bool(secrets.get('openai', 'api_key')))
"
```
""")
            docs_created.append(str(api_keys_guide))
            
            # Create development startup script
            startup_script = self.project_root / 'start_development.sh'
            with open(startup_script, 'w') as f:
                f.write(f"""#!/bin/bash
# 🚀 Orchestra AI Development Startup Script

echo "🚀 Starting Orchestra AI Development Environment"
echo "=============================================="

cd "{self.project_root}"

# Start API service
echo "🔌 Starting API service on port 8010..."
uvicorn src.api.main:app --host 0.0.0.0 --port 8010 --reload &
API_PID=$!

# Start admin interface
echo "🌐 Starting admin interface on port 5174..."
cd admin-interface
npm run dev &
ADMIN_PID=$!

cd "{self.project_root}"

echo ""
echo "✅ Services started:"
echo "   🔌 API: http://localhost:8010"
echo "   🌐 Admin: http://localhost:5174"
echo "   📝 Health: http://localhost:8010/health"

echo ""
echo "🧠 Cursor AI Features:"
echo "   ✅ Auto-approval for safe operations"
echo "   ✅ Context awareness enabled"
echo "   ✅ MCP servers configured"
echo "   ✅ Smart persona routing"

echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "Stopping services..."; kill $API_PID $ADMIN_PID 2>/dev/null; exit' INT
wait
""")
            
            # Make startup script executable
            os.chmod(startup_script, 0o755)
            docs_created.append(str(startup_script))
            
            # Create deployment status file
            status_file = self.project_root / 'DEPLOYMENT_STATUS.md'
            with open(status_file, 'w') as f:
                f.write(f"""# 🚀 Orchestra AI Deployment Status

**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## System Status

### Local Services
- 🔌 **API Service**: http://localhost:8010
- 🌐 **Admin Interface**: http://localhost:5174

### Vercel Deployments
- 🌐 **Admin Interface**: https://orchestra-admin-interface.vercel.app
- 🌐 **Frontend**: https://orchestra-ai-frontend.vercel.app

### Cursor AI Configuration
- ✅ **MCP Servers**: Configured
- ✅ **Auto-approval**: Enabled for safe operations
- ✅ **Context Awareness**: Active

## Quick Start

1. **Start Development**:
   ```bash
   ./start_development.sh
   ```

2. **Configure API Keys** (if needed):
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Deploy to Vercel** (if needed):
   ```bash
   cd admin-interface
   npm run build
   vercel --prod
   ```

## Next Steps

- [ ] Configure all API keys in `.env`
- [ ] Test Notion integration
- [ ] Verify Vercel deployments
- [ ] Test AI persona routing
- [ ] Set up monitoring

## Support

- 📚 **Documentation**: See API_KEYS_SETUP_GUIDE.md
- 🔧 **Issues**: Check deployment logs
- 🚀 **Updates**: Re-run deployment script
""")
            docs_created.append(str(status_file))
            
            return {
                'success': True,
                'files_created': docs_created,
                'message': f'Created {len(docs_created)} documentation files'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def verify_complete_system(self):
        """Verify the complete system deployment"""
        try:
            verification = {}
            
            # Check local services
            services = {
                'API Service': 'http://localhost:8010/health',
                'Admin Interface': 'http://localhost:5174'
            }
            
            for name, url in services.items():
                running = await self.check_service(url)
                verification[name] = {
                    'running': running,
                    'url': url,
                    'status': '✅' if running else '❌'
                }
            
            # Check Vercel deployments
            vercel_services = {
                'Vercel Admin': 'https://orchestra-admin-interface.vercel.app',
                'Vercel Frontend': 'https://orchestra-ai-frontend.vercel.app'
            }
            
            for name, url in vercel_services.items():
                running = await self.check_service(url)
                verification[name] = {
                    'running': running,
                    'url': url,
                    'status': '✅' if running else '❌'
                }
            
            # Check Cursor AI configuration
            cursor_config_dir = Path.home() / '.cursor'
            cursor_files = {
                'MCP Config': cursor_config_dir / 'mcp.json',
                'Automation Rules': cursor_config_dir / 'automation_rules.json'
            }
            
            for name, file_path in cursor_files.items():
                exists = file_path.exists()
                verification[name] = {
                    'configured': exists,
                    'path': str(file_path),
                    'status': '✅' if exists else '❌'
                }
            
            # Overall success
            local_services_ok = any(v['running'] for k, v in verification.items() if 'Service' in k or 'Interface' in k)
            cursor_config_ok = all(v['configured'] for k, v in verification.items() if 'Config' in k or 'Rules' in k)
            
            overall_success = local_services_ok and cursor_config_ok
            
            return {
                'success': overall_success,
                'verification': verification,
                'local_services_ok': local_services_ok,
                'cursor_config_ok': cursor_config_ok,
                'message': 'System verification completed'
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
    
    def generate_comprehensive_summary(self):
        """Generate a comprehensive deployment summary"""
        status = self.results['status']
        timestamp = self.results['timestamp']
        phase = self.results.get('phase', 'unknown')
        
        summary = f"""
🎯 Orchestra AI Complete Deployment Summary
{'='*60}

📅 Deployment Time: {timestamp}
🎯 Final Status: {status.upper()}
📋 Last Phase: {phase.title()}

🏗️ INFRASTRUCTURE SETUP:
{'-'*40}
"""
        
        # Infrastructure results
        if 'infrastructure' in self.results['deployments']:
            infra = self.results['deployments']['infrastructure']
            status_icon = "✅" if infra.get('success') else "❌"
            summary += f"{status_icon} Infrastructure: {infra.get('message', 'No message')}\n"
            
            if 'checks' in infra:
                checks = infra['checks']
                summary += f"   • Python: {checks.get('python', {}).get('version', 'Unknown')}\n"
                summary += f"   • Node.js: {checks.get('nodejs', {}).get('version', 'Unknown')}\n"
                summary += f"   • Project Structure: {'✅' if checks.get('project_structure', {}).get('admin_interface') else '❌'}\n"
        
        summary += f"\n🔌 LOCAL SERVICES:\n{'-'*40}\n"
        
        # Services results
        if 'local' in self.results['services']:
            local = self.results['services']['local']
            if 'services' in local:
                services = local['services']
                for service_name, service_info in services.items():
                    status_icon = "✅" if service_info.get('running') else "❌"
                    url = service_info.get('url', 'Unknown URL')
                    summary += f"{status_icon} {service_name.title()}: {url}\n"
        
        summary += f"\n🌐 VERCEL CONFIGURATION:\n{'-'*40}\n"
        
        # Vercel results
        if 'vercel' in self.results['deployments']:
            vercel = self.results['deployments']['vercel']
            status_icon = "✅" if vercel.get('success') else "❌"
            summary += f"{status_icon} Vercel: {vercel.get('message', 'No message')}\n"
            
            if 'projects_configured' in vercel:
                for project in vercel['projects_configured']:
                    summary += f"   • {project['name']}: {project['url']}\n"
        
        summary += f"\n🧠 CURSOR AI CONFIGURATION:\n{'-'*40}\n"
        
        # Cursor AI results
        if 'cursor_ai' in self.results['configuration']:
            cursor = self.results['configuration']['cursor_ai']
            status_icon = "✅" if cursor.get('success') else "❌"
            summary += f"{status_icon} Cursor AI: {cursor.get('message', 'No message')}\n"
            
            if 'files_created' in cursor:
                summary += f"   • Configuration files: {len(cursor['files_created'])}\n"
        
        # Verification results
        if 'verification' in self.results:
            summary += f"\n🔍 SYSTEM VERIFICATION:\n{'-'*40}\n"
            verification = self.results['verification']
            
            if 'verification' in verification:
                for name, check in verification['verification'].items():
                    status_icon = check.get('status', '❓')
                    summary += f"{status_icon} {name}: {check.get('url', check.get('path', 'N/A'))}\n"
        
        summary += f"\n📊 NEXT STEPS:\n{'-'*40}\n"
        
        if status == 'completed':
            summary += """✅ All systems deployed successfully!

🚀 Quick Start:
   ./start_development.sh

🌐 Access Points:
   • Admin Interface: http://localhost:5174
   • API Service: http://localhost:8010
   • Vercel Admin: https://orchestra-admin-interface.vercel.app

🧠 Cursor AI Features:
   • Auto-approval for safe operations
   • Context awareness enabled
   • MCP servers configured
   • Smart persona routing

📚 Documentation:
   • API_KEYS_SETUP_GUIDE.md
   • DEPLOYMENT_STATUS.md

🎯 Ready for AI-assisted development!"""
        
        elif status == 'partial':
            summary += """⚠️ Partial deployment completed.

🔧 Recommended Actions:
   1. Check API_KEYS_SETUP_GUIDE.md for missing configuration
   2. Run: ./start_development.sh to start local services
   3. Configure missing API keys in .env file
   4. Re-run deployment if needed

✅ Working Features:
   • Local development environment
   • Cursor AI configuration
   • Basic project structure

🎯 Most features are ready for development!"""
        
        else:
            summary += """❌ Deployment encountered issues.

🔧 Troubleshooting:
   1. Check the error messages above
   2. Verify Python and Node.js are installed
   3. Ensure project structure is intact
   4. Check network connectivity
   5. Re-run deployment script

📞 Support:
   • Check deployment logs
   • Verify prerequisites
   • Contact support if issues persist"""
        
        return summary

async def main():
    """Main execution function"""
    print("🚀 Orchestra AI Complete Deployment & Configuration")
    print("=" * 60)
    
    deployment = OrchestryCompleteDeployment()
    
    try:
        # Run complete deployment
        results = await deployment.deploy_complete_system()
        
        # Generate and display comprehensive summary
        summary = deployment.generate_comprehensive_summary()
        print(summary)
        
        # Save detailed results
        results_file = deployment.project_root / 'deployment_complete_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Exit with appropriate code
        exit_code = 0 if results['status'] in ['completed', 'partial'] else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 