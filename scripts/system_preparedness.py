#!/usr/bin/env python3
"""
System Preparedness Script for EigenCode Integration
Validates all pre-installation requirements and ensures system readiness
"""

import os
import sys
import json
import subprocess
import platform
import shutil
import tempfile
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import psutil
import requests

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ai_components.orchestration.ai_orchestrator import DatabaseLogger, WeaviateManager
from ai_components.eigencode.mock_analyzer import get_mock_analyzer


class SystemPreparednessChecker:
    """Validates system readiness for EigenCode integration"""
    
    def __init__(self):
        self.db_logger = DatabaseLogger()
        self.weaviate_manager = WeaviateManager()
        self.mock_analyzer = get_mock_analyzer()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {},
            'requirements': {},
            'sandbox_test': {},
            'integration_readiness': {},
            'recommendations': []
        }
    
    async def run_full_check(self) -> Dict:
        """Run comprehensive system preparedness check"""
        print("🔍 Starting System Preparedness Check...")
        
        # 1. System Information
        print("\n1️⃣ Gathering System Information...")
        self.results['system_info'] = self._gather_system_info()
        
        # 2. Check Requirements
        print("\n2️⃣ Checking Pre-Installation Requirements...")
        self.results['requirements'] = await self._check_requirements()
        
        # 3. Sandbox Testing
        print("\n3️⃣ Running Sandbox Tests...")
        self.results['sandbox_test'] = await self._run_sandbox_tests()
        
        # 4. Integration Readiness
        print("\n4️⃣ Checking Integration Readiness...")
        self.results['integration_readiness'] = await self._check_integration_readiness()
        
        # 5. Generate Recommendations
        print("\n5️⃣ Generating Recommendations...")
        self.results['recommendations'] = self._generate_recommendations()
        
        # 6. Save Results
        self._save_results()
        
        # 7. Display Summary
        self._display_summary()
        
        return self.results
    
    def _gather_system_info(self) -> Dict:
        """Gather system information"""
        info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'python_version': sys.version,
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'memory_available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'network_available': self._check_network(),
            'current_directory': os.getcwd(),
            'user': os.environ.get('USER', 'unknown'),
            'environment_variables': self._get_relevant_env_vars()
        }
        return info
    
    def _check_network(self) -> bool:
        """Check network connectivity"""
        try:
            response = requests.get('https://api.github.com', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _get_relevant_env_vars(self) -> Dict:
        """Get relevant environment variables"""
        relevant_vars = [
            'PATH', 'PYTHONPATH', 'VIRTUAL_ENV', 'GITHUB_TOKEN',
            'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'WEAVIATE_URL',
            'POSTGRES_CONNECTION', 'AIRBYTE_API_KEY'
        ]
        
        env_vars = {}
        for var in relevant_vars:
            value = os.environ.get(var)
            if value:
                # Mask sensitive values
                if 'KEY' in var or 'TOKEN' in var or 'PASSWORD' in var:
                    env_vars[var] = '***' + value[-4:] if len(value) > 4 else '***'
                else:
                    env_vars[var] = value
        
        return env_vars
    
    async def _check_requirements(self) -> Dict:
        """Check pre-installation requirements"""
        requirements = {
            'python': {
                'required': '3.8+',
                'current': platform.python_version(),
                'satisfied': sys.version_info >= (3, 8)
            },
            'disk_space': {
                'required_gb': 2.0,
                'available_gb': round(psutil.disk_usage('/').free / (1024**3), 2),
                'satisfied': psutil.disk_usage('/').free / (1024**3) > 2.0
            },
            'memory': {
                'required_gb': 4.0,
                'available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
                'satisfied': psutil.virtual_memory().available / (1024**3) > 1.0  # Lower threshold for available
            },
            'network': {
                'required': True,
                'current': self.results['system_info']['network_available'],
                'satisfied': self.results['system_info']['network_available']
            },
            'permissions': {
                'write_access': self._check_write_permissions(),
                'execute_access': self._check_execute_permissions(),
                'satisfied': self._check_write_permissions() and self._check_execute_permissions()
            },
            'dependencies': await self._check_dependencies(),
            'api_keys': self._check_api_keys(),
            'database': await self._check_database_connection(),
            'weaviate': await self._check_weaviate_connection()
        }
        
        # Overall satisfaction
        requirements['all_satisfied'] = all(
            req.get('satisfied', False) 
            for req in requirements.values() 
            if isinstance(req, dict) and 'satisfied' in req
        )
        
        return requirements
    
    def _check_write_permissions(self) -> bool:
        """Check write permissions in current directory"""
        try:
            test_file = Path('test_write_permission.tmp')
            test_file.write_text('test')
            test_file.unlink()
            return True
        except:
            return False
    
    def _check_execute_permissions(self) -> bool:
        """Check execute permissions"""
        try:
            result = subprocess.run(['echo', 'test'], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    async def _check_dependencies(self) -> Dict:
        """Check Python dependencies"""
        dependencies = {
            'required': [
                'requests', 'psycopg2-binary', 'weaviate-client',
                'pulumi', 'prometheus-client', 'asyncio', 'aiohttp'
            ],
            'installed': [],
            'missing': [],
            'satisfied': False
        }
        
        # Check installed packages
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                installed_packages = json.loads(result.stdout)
                installed_names = {pkg['name'].lower() for pkg in installed_packages}
                
                for dep in dependencies['required']:
                    if dep.lower() in installed_names:
                        dependencies['installed'].append(dep)
                    else:
                        dependencies['missing'].append(dep)
                
                dependencies['satisfied'] = len(dependencies['missing']) == 0
        except:
            dependencies['error'] = 'Failed to check pip packages'
        
        return dependencies
    
    def _check_api_keys(self) -> Dict:
        """Check API key configuration"""
        api_keys = {
            'github_token': bool(os.environ.get('GITHUB_TOKEN')),
            'openai_api_key': bool(os.environ.get('OPENAI_API_KEY')),
            'anthropic_api_key': bool(os.environ.get('ANTHROPIC_API_KEY')),
            'weaviate_api_key': bool(os.environ.get('WEAVIATE_API_KEY')),
            'airbyte_api_key': bool(os.environ.get('AIRBYTE_API_KEY')),
            'satisfied': False
        }
        
        # At least one AI API key should be present
        api_keys['satisfied'] = (
            api_keys['openai_api_key'] or 
            api_keys['anthropic_api_key']
        )
        
        return api_keys
    
    async def _check_database_connection(self) -> Dict:
        """Check PostgreSQL connection"""
        db_check = {
            'connection_string': bool(os.environ.get('POSTGRES_CONNECTION')),
            'connected': False,
            'satisfied': False
        }
        
        if db_check['connection_string']:
            try:
                # Test connection using db_logger
                self.db_logger.log_action(
                    workflow_id="system_check",
                    task_id="db_test",
                    agent_role="system",
                    action="connection_test",
                    status="testing"
                )
                db_check['connected'] = True
                db_check['satisfied'] = True
            except Exception as e:
                db_check['error'] = str(e)
        
        return db_check
    
    async def _check_weaviate_connection(self) -> Dict:
        """Check Weaviate connection"""
        weaviate_check = {
            'url_configured': bool(os.environ.get('WEAVIATE_URL')),
            'connected': False,
            'satisfied': False
        }
        
        if weaviate_check['url_configured']:
            try:
                # Test connection
                test_data = self.weaviate_manager.retrieve_context(
                    workflow_id="system_check",
                    task_id="weaviate_test",
                    limit=1
                )
                weaviate_check['connected'] = True
                weaviate_check['satisfied'] = True
            except Exception as e:
                weaviate_check['error'] = str(e)
        
        return weaviate_check
    
    async def _run_sandbox_tests(self) -> Dict:
        """Run sandbox tests to validate system capabilities"""
        sandbox_results = {
            'tests_run': 0,
            'tests_passed': 0,
            'test_results': []
        }
        
        # Test 1: File Operations
        test_result = await self._test_file_operations()
        sandbox_results['test_results'].append(test_result)
        sandbox_results['tests_run'] += 1
        if test_result['passed']:
            sandbox_results['tests_passed'] += 1
        
        # Test 2: Process Execution
        test_result = await self._test_process_execution()
        sandbox_results['test_results'].append(test_result)
        sandbox_results['tests_run'] += 1
        if test_result['passed']:
            sandbox_results['tests_passed'] += 1
        
        # Test 3: Network Operations
        test_result = await self._test_network_operations()
        sandbox_results['test_results'].append(test_result)
        sandbox_results['tests_run'] += 1
        if test_result['passed']:
            sandbox_results['tests_passed'] += 1
        
        # Test 4: Mock Analyzer
        test_result = await self._test_mock_analyzer()
        sandbox_results['test_results'].append(test_result)
        sandbox_results['tests_run'] += 1
        if test_result['passed']:
            sandbox_results['tests_passed'] += 1
        
        # Test 5: Integration Components
        test_result = await self._test_integration_components()
        sandbox_results['test_results'].append(test_result)
        sandbox_results['tests_run'] += 1
        if test_result['passed']:
            sandbox_results['tests_passed'] += 1
        
        sandbox_results['all_passed'] = (
            sandbox_results['tests_passed'] == sandbox_results['tests_run']
        )
        
        return sandbox_results
    
    async def _test_file_operations(self) -> Dict:
        """Test file operations in sandbox"""
        test = {
            'name': 'File Operations',
            'passed': False,
            'details': []
        }
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Test file creation
                test_file = Path(tmpdir) / 'test.txt'
                test_file.write_text('Hello, EigenCode!')
                test['details'].append('✓ File creation successful')
                
                # Test file reading
                content = test_file.read_text()
                assert content == 'Hello, EigenCode!'
                test['details'].append('✓ File reading successful')
                
                # Test file modification
                test_file.write_text('Modified content')
                assert test_file.read_text() == 'Modified content'
                test['details'].append('✓ File modification successful')
                
                # Test directory operations
                sub_dir = Path(tmpdir) / 'subdir'
                sub_dir.mkdir()
                assert sub_dir.exists()
                test['details'].append('✓ Directory operations successful')
                
                test['passed'] = True
        except Exception as e:
            test['error'] = str(e)
        
        return test
    
    async def _test_process_execution(self) -> Dict:
        """Test process execution capabilities"""
        test = {
            'name': 'Process Execution',
            'passed': False,
            'details': []
        }
        
        try:
            # Test Python execution
            result = subprocess.run(
                [sys.executable, '-c', 'print("Hello from Python")'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            test['details'].append('✓ Python execution successful')
            
            # Test shell command
            result = subprocess.run(['echo', 'Hello from shell'], capture_output=True, text=True)
            assert result.returncode == 0
            test['details'].append('✓ Shell command execution successful')
            
            # Test async execution
            proc = await asyncio.create_subprocess_exec(
                'echo', 'Async test',
                stdout=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            assert proc.returncode == 0
            test['details'].append('✓ Async process execution successful')
            
            test['passed'] = True
        except Exception as e:
            test['error'] = str(e)
        
        return test
    
    async def _test_network_operations(self) -> Dict:
        """Test network operations"""
        test = {
            'name': 'Network Operations',
            'passed': False,
            'details': []
        }
        
        try:
            # Test HTTP request
            response = requests.get('https://api.github.com', timeout=10)
            assert response.status_code == 200
            test['details'].append('✓ HTTP request successful')
            
            # Test DNS resolution
            import socket
            socket.gethostbyname('github.com')
            test['details'].append('✓ DNS resolution successful')
            
            # Test connection to common ports
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('github.com', 443))
            sock.close()
            assert result == 0
            test['details'].append('✓ HTTPS port connection successful')
            
            test['passed'] = True
        except Exception as e:
            test['error'] = str(e)
        
        return test
    
    async def _test_mock_analyzer(self) -> Dict:
        """Test mock analyzer functionality"""
        test = {
            'name': 'Mock Analyzer',
            'passed': False,
            'details': []
        }
        
        try:
            # Create test code
            with tempfile.TemporaryDirectory() as tmpdir:
                test_file = Path(tmpdir) / 'test.py'
                test_file.write_text('''
def hello_world():
    """Test function"""
    print("Hello, World!")
    
if __name__ == "__main__":
    hello_world()
''')
                
                # Run analysis
                results = await self.mock_analyzer.analyze_codebase(tmpdir)
                
                assert results['status'] == 'completed'
                test['details'].append('✓ Mock analyzer execution successful')
                
                assert len(results['files']) > 0
                test['details'].append('✓ File analysis successful')
                
                assert 'metrics' in results
                test['details'].append('✓ Metrics generation successful')
                
                test['passed'] = True
        except Exception as e:
            test['error'] = str(e)
        
        return test
    
    async def _test_integration_components(self) -> Dict:
        """Test integration components"""
        test = {
            'name': 'Integration Components',
            'passed': False,
            'details': []
        }
        
        try:
            # Test orchestrator import
            from ai_components.orchestration.ai_orchestrator import WorkflowOrchestrator
            test['details'].append('✓ Orchestrator import successful')
            
            # Test CLI import
            from ai_components.orchestrator_cli_enhanced import EnhancedOrchestratorCLI
            test['details'].append('✓ CLI import successful')
            
            # Test configuration
            config_path = Path('config/orchestrator_config.json')
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
                test['details'].append('✓ Configuration file found')
            else:
                test['details'].append('⚠️ Configuration file not found')
            
            test['passed'] = True
        except Exception as e:
            test['error'] = str(e)
        
        return test
    
    async def _check_integration_readiness(self) -> Dict:
        """Check integration readiness"""
        readiness = {
            'eigencode_monitor': False,
            'mock_analyzer': False,
            'orchestrator': False,
            'database': False,
            'weaviate': False,
            'ci_cd': False,
            'documentation': False,
            'overall_score': 0
        }
        
        # Check EigenCode monitor
        monitor_script = Path('scripts/eigencode_monitor.py')
        readiness['eigencode_monitor'] = monitor_script.exists()
        
        # Check mock analyzer
        mock_analyzer_path = Path('ai_components/eigencode/mock_analyzer.py')
        readiness['mock_analyzer'] = mock_analyzer_path.exists()
        
        # Check orchestrator
        orchestrator_path = Path('ai_components/orchestration/ai_orchestrator.py')
        readiness['orchestrator'] = orchestrator_path.exists()
        
        # Check database readiness
        readiness['database'] = self.results['requirements'].get('database', {}).get('satisfied', False)
        
        # Check Weaviate readiness
        readiness['weaviate'] = self.results['requirements'].get('weaviate', {}).get('satisfied', False)
        
        # Check CI/CD
        workflow_path = Path('.github/workflows/ai_orchestrator_deployment.yml')
        readiness['ci_cd'] = workflow_path.exists()
        
        # Check documentation
        docs = [
            Path('AI_ORCHESTRATOR_GUIDE.md'),
            Path('docs/EIGENCODE_INTEGRATION_GUIDE.md')
        ]
        readiness['documentation'] = all(doc.exists() for doc in docs)
        
        # Calculate overall score
        components = [k for k in readiness.keys() if k != 'overall_score']
        ready_count = sum(1 for k in components if readiness[k])
        readiness['overall_score'] = (ready_count / len(components)) * 100
        
        return readiness
    
    def _generate_recommendations(self) -> List[Dict]:
        """Generate recommendations based on checks"""
        recommendations = []
        
        # System requirements
        if not self.results['requirements']['all_satisfied']:
            for req_name, req_data in self.results['requirements'].items():
                if isinstance(req_data, dict) and not req_data.get('satisfied', True):
                    recommendations.append({
                        'category': 'requirements',
                        'priority': 'high',
                        'issue': f'{req_name} requirement not satisfied',
                        'action': self._get_requirement_action(req_name, req_data)
                    })
        
        # Sandbox tests
        if not self.results['sandbox_test'].get('all_passed', False):
            for test in self.results['sandbox_test'].get('test_results', []):
                if not test['passed']:
                    recommendations.append({
                        'category': 'sandbox',
                        'priority': 'medium',
                        'issue': f'{test["name"]} test failed',
                        'action': f'Investigate and fix: {test.get("error", "Unknown error")}'
                    })
        
        # Integration readiness
        readiness = self.results['integration_readiness']
        if readiness.get('overall_score', 0) < 100:
            for component, ready in readiness.items():
                if component != 'overall_score' and not ready:
                    recommendations.append({
                        'category': 'integration',
                        'priority': 'medium',
                        'issue': f'{component} not ready',
                        'action': self._get_integration_action(component)
                    })
        
        # Performance recommendations
        if self.results['system_info']['memory_available_gb'] < 2:
            recommendations.append({
                'category': 'performance',
                'priority': 'medium',
                'issue': 'Low available memory',
                'action': 'Close unnecessary applications or increase system memory'
            })
        
        if self.results['system_info']['disk_usage_percent'] > 80:
            recommendations.append({
                'category': 'performance',
                'priority': 'medium',
                'issue': 'High disk usage',
                'action': 'Free up disk space for optimal performance'
            })
        
        return recommendations
    
    def _get_requirement_action(self, req_name: str, req_data: Dict) -> str:
        """Get action for requirement"""
        actions = {
            'python': f'Upgrade Python to version {req_data.get("required", "3.8+")}',
            'disk_space': f'Free up disk space (need {req_data.get("required_gb", 2)} GB)',
            'memory': 'Close applications to free up memory',
            'network': 'Check internet connection',
            'permissions': 'Ensure proper file permissions in the project directory',
            'dependencies': f'Install missing packages: {", ".join(req_data.get("missing", []))}',
            'api_keys': 'Configure required API keys in environment variables',
            'database': 'Set up PostgreSQL connection (POSTGRES_CONNECTION env var)',
            'weaviate': 'Configure Weaviate connection (WEAVIATE_URL env var)'
        }
        return actions.get(req_name, 'Check system requirements')
    
    def _get_integration_action(self, component: str) -> str:
        """Get action for integration component"""
        actions = {
            'eigencode_monitor': 'Ensure eigencode_monitor.py is properly configured',
            'mock_analyzer': 'Verify mock analyzer is functioning correctly',
            'orchestrator': 'Check orchestrator configuration and dependencies',
            'database': 'Set up and test PostgreSQL connection',
            'weaviate': 'Configure and test Weaviate connection',
            'ci_cd': 'Set up GitHub Actions workflow',
            'documentation': 'Ensure all documentation is up to date'
        }
        return actions.get(component, f'Configure {component}')
    
    def _save_results(self):
        """Save results to file"""
        results_file = Path('system_preparedness_report.json')
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Log to database
        self.db_logger.log_action(
            workflow_id="system_preparedness",
            task_id=f"check_{int(time.time())}",
            agent_role="system",
            action="preparedness_check",
            status="completed",
            metadata={
                'overall_score': self.results['integration_readiness'].get('overall_score', 0),
                'requirements_satisfied': self.results['requirements'].get('all_satisfied', False),
                'sandbox_tests_passed': self.results['sandbox_test'].get('all_passed', False)
            }
        )
    
    def _display_summary(self):
        """Display summary of results"""
        print("\n" + "="*60)
        print("📊 SYSTEM PREPAREDNESS SUMMARY")
        print("="*60)
        
        # System Info
        print(f"\n🖥️  System: {self.results['system_info']['platform']} "
              f"(Python {platform.python_version()})")
        print(f"💾 Memory: {self.results['system_info']['memory_available_gb']} GB available")
        print(f"💿 Disk: {100 - self.results['system_info']['disk_usage_percent']:.1f}% free")
        
        # Requirements
        req_satisfied = self.results['requirements']['all_satisfied']
        print(f"\n✅ Requirements: {'All Satisfied' if req_satisfied else 'Some Missing'}")
        if not req_satisfied:
            for req, data in self.results['requirements'].items():
                if isinstance(data, dict) and not data.get('satisfied', True):
                    print(f"   ❌ {req}")
        
        # Sandbox Tests
        sandbox = self.results['sandbox_test']
        print(f"\n🧪 Sandbox Tests: {sandbox['tests_passed']}/{sandbox['tests_run']} passed")
        
        # Integration Readiness
        readiness_score = self.results['integration_readiness']['overall_score']
        print(f"\n🔗 Integration Readiness: {readiness_score:.0f}%")
        
        # Recommendations
        if self.results['recommendations']:
            print(f"\n📋 Recommendations: {len(self.results['recommendations'])} items")
            for i, rec in enumerate(self.results['recommendations'][:3]):
                print(f"   {i+1}. [{rec['priority'].upper()}] {rec['issue']}")
            if len(self.results['recommendations']) > 3:
                print(f"   ... and {len(self.results['recommendations']) - 3} more")
        
        print(f"\n📄 Full report saved to: system_preparedness_report.json")
        print("="*60)


async def main():
    """Run system preparedness check"""
    checker = SystemPreparednessChecker()
    await checker.run_full_check()


if __name__ == "__main__":
    asyncio.run(main())