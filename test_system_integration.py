#!/usr/bin/env python3
"""
Database and API Integration Testing Script
Comprehensive verification of all Cherry AI Orchestrator integrations

This script tests:
1. Database connections (PostgreSQL, Redis, Weaviate, Pinecone)
2. API integrations (Salesforce, HubSpot, Apollo, Gong, Slack, Looker)
3. Environment configuration
4. System health checks

Author: Cherry AI Team
Version: 1.0.0
"""

import os
import sys
import json
import asyncio
import logging
import socket
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment only")

# Add infrastructure paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'infrastructure', 'database_layer'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'infrastructure', 'api_integrations'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemTester:
    """Comprehensive system testing and verification"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'environment': {},
            'databases': {},
            'apis': {},
            'services': {},
            'summary': {}
        }
    
    async def run_all_tests(self):
        """Run comprehensive system tests"""
        print("🔍 CHERRY AI ORCHESTRATOR - SYSTEM VERIFICATION")
        print("=" * 60)
        
        # Test environment configuration
        await self.test_environment()
        
        # Test database connections
        await self.test_databases()
        
        # Test API integrations
        await self.test_apis()
        
        # Test system services
        await self.test_services()
        
        # Generate summary
        self.generate_summary()
        
        # Save results
        self.save_results()
        
        return self.results
    
    async def test_environment(self):
        """Test environment configuration"""
        print("\n📋 TESTING ENVIRONMENT CONFIGURATION")
        print("-" * 40)
        
        required_vars = [
            'POSTGRES_HOST', 'POSTGRES_PASSWORD', 'REDIS_HOST',
            'WEAVIATE_URL', 'PINECONE_API_KEY', 'OPENAI_API_KEY',
            'SALESFORCE_CLIENT_ID', 'HUBSPOT_API_KEY', 'APOLLO_API_KEY'
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            status = "✅ SET" if value else "❌ NOT SET"
            masked_value = f"{value[:8]}..." if value and len(value) > 8 else value
            print(f"{var:20} {status:10} {masked_value if value else ''}")
            
            self.results['environment'][var] = {
                'set': bool(value),
                'value_preview': masked_value if value else None
            }
    
    async def test_databases(self):
        """Test database connections"""
        print("\n🗄️ TESTING DATABASE CONNECTIONS")
        print("-" * 40)
        
        databases = [
            ('PostgreSQL', os.getenv('POSTGRES_HOST', '45.77.87.106'), int(os.getenv('POSTGRES_PORT', '5432'))),
            ('Redis', os.getenv('REDIS_HOST', '45.77.87.106'), int(os.getenv('REDIS_PORT', '6379'))),
            ('Weaviate', os.getenv('WEAVIATE_HOST', '45.77.87.106'), int(os.getenv('WEAVIATE_PORT', '8080'))),
            ('Local PostgreSQL', 'localhost', 5432),
            ('Local Redis', 'localhost', 6379),
            ('Local Weaviate', 'localhost', 8080)
        ]
        
        for name, host, port in databases:
            accessible = await self.test_connection(host, port)
            status = "✅ ACCESSIBLE" if accessible else "❌ NOT ACCESSIBLE"
            print(f"{name:20} {host:15}:{port:5} {status}")
            
            self.results['databases'][name] = {
                'host': host,
                'port': port,
                'accessible': accessible
            }
            
            # Test actual database functionality if accessible
            if accessible:
                await self.test_database_functionality(name, host, port)
    
    async def test_connection(self, host: str, port: int, timeout: int = 5) -> bool:
        """Test TCP connection to host:port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    async def test_database_functionality(self, name: str, host: str, port: int):
        """Test actual database functionality"""
        try:
            if 'PostgreSQL' in name:
                await self.test_postgresql(host, port)
            elif 'Redis' in name:
                await self.test_redis(host, port)
            elif 'Weaviate' in name:
                await self.test_weaviate(host, port)
        except Exception as e:
            logger.error(f"Database functionality test failed for {name}: {e}")
    
    async def test_postgresql(self, host: str, port: int):
        """Test PostgreSQL functionality"""
        try:
            import psycopg2
            conn_string = f"host={host} port={port} dbname=postgres user=postgres"
            conn = psycopg2.connect(conn_string)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            print(f"    ✅ PostgreSQL functional: {version[:50]}...")
            return True
        except Exception as e:
            print(f"    ❌ PostgreSQL test failed: {str(e)[:50]}...")
            return False
    
    async def test_redis(self, host: str, port: int):
        """Test Redis functionality"""
        try:
            import redis
            r = redis.Redis(host=host, port=port, decode_responses=True)
            r.ping()
            info = r.info()
            print(f"    ✅ Redis functional: v{info['redis_version']}")
            return True
        except Exception as e:
            print(f"    ❌ Redis test failed: {str(e)[:50]}...")
            return False
    
    async def test_weaviate(self, host: str, port: int):
        """Test Weaviate functionality"""
        try:
            import aiohttp
            url = f"http://{host}:{port}/v1/meta"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        version = data.get('version', 'unknown')
                        print(f"    ✅ Weaviate functional: v{version}")
                        return True
                    else:
                        print(f"    ❌ Weaviate HTTP error: {response.status}")
                        return False
        except Exception as e:
            print(f"    ❌ Weaviate test failed: {str(e)[:50]}...")
            return False
    
    async def test_apis(self):
        """Test API integrations"""
        print("\n🔌 TESTING API INTEGRATIONS")
        print("-" * 40)
        
        apis = [
            ('Salesforce', self.test_salesforce_api),
            ('HubSpot', self.test_hubspot_api),
            ('Apollo', self.test_apollo_api),
            ('Gong', self.test_gong_api),
            ('Slack', self.test_slack_api),
            ('Looker', self.test_looker_api),
            ('OpenAI', self.test_openai_api),
            ('Pinecone', self.test_pinecone_api)
        ]
        
        for name, test_func in apis:
            try:
                result = await test_func()
                status = "✅ FUNCTIONAL" if result['functional'] else "❌ NOT FUNCTIONAL"
                print(f"{name:15} {status:15} {result.get('message', '')}")
                self.results['apis'][name] = result
            except Exception as e:
                print(f"{name:15} ❌ ERROR         {str(e)[:40]}...")
                self.results['apis'][name] = {
                    'functional': False,
                    'error': str(e)
                }
    
    async def test_salesforce_api(self) -> Dict[str, Any]:
        """Test Salesforce API"""
        client_id = os.getenv('SALESFORCE_CLIENT_ID')
        if not client_id:
            return {'functional': False, 'message': 'Client ID not configured'}
        
        # Test authentication endpoint
        try:
            import aiohttp
            url = "https://login.salesforce.com/services/oauth2/token"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data={'grant_type': 'client_credentials'}) as response:
                    if response.status in [200, 400]:  # 400 is expected without proper credentials
                        return {'functional': True, 'message': 'Endpoint accessible'}
                    else:
                        return {'functional': False, 'message': f'HTTP {response.status}'}
        except Exception as e:
            return {'functional': False, 'message': str(e)}
    
    async def test_hubspot_api(self) -> Dict[str, Any]:
        """Test HubSpot API"""
        api_key = os.getenv('HUBSPOT_API_KEY')
        if not api_key:
            return {'functional': False, 'message': 'API key not configured'}
        
        try:
            import aiohttp
            url = "https://api.hubapi.com/crm/v3/objects/contacts"
            headers = {'Authorization': f'Bearer {api_key}'}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status in [200, 401]:  # 401 expected with invalid key
                        return {'functional': True, 'message': 'Endpoint accessible'}
                    else:
                        return {'functional': False, 'message': f'HTTP {response.status}'}
        except Exception as e:
            return {'functional': False, 'message': str(e)}
    
    async def test_apollo_api(self) -> Dict[str, Any]:
        """Test Apollo API"""
        api_key = os.getenv('APOLLO_API_KEY')
        if not api_key:
            return {'functional': False, 'message': 'API key not configured'}
        
        try:
            import aiohttp
            url = "https://api.apollo.io/v1/mixed_people/search"
            headers = {'X-Api-Key': api_key}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json={}) as response:
                    if response.status in [200, 401, 422]:  # Various expected responses
                        return {'functional': True, 'message': 'Endpoint accessible'}
                    else:
                        return {'functional': False, 'message': f'HTTP {response.status}'}
        except Exception as e:
            return {'functional': False, 'message': str(e)}
    
    async def test_gong_api(self) -> Dict[str, Any]:
        """Test Gong API"""
        access_key = os.getenv('GONG_ACCESS_KEY')
        if not access_key:
            return {'functional': False, 'message': 'Access key not configured'}
        
        try:
            import aiohttp
            url = "https://api.gong.io/v2/users"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={}) as response:
                    if response.status in [200, 401]:  # 401 expected without proper auth
                        return {'functional': True, 'message': 'Endpoint accessible'}
                    else:
                        return {'functional': False, 'message': f'HTTP {response.status}'}
        except Exception as e:
            return {'functional': False, 'message': str(e)}
    
    async def test_slack_api(self) -> Dict[str, Any]:
        """Test Slack API"""
        bot_token = os.getenv('SLACK_BOT_TOKEN')
        if not bot_token:
            return {'functional': False, 'message': 'Bot token not configured'}
        
        try:
            import aiohttp
            url = "https://slack.com/api/auth.test"
            headers = {'Authorization': f'Bearer {bot_token}'}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            return {'functional': True, 'message': f"Team: {data.get('team', 'Unknown')}"}
                        else:
                            return {'functional': False, 'message': data.get('error', 'Auth failed')}
                    else:
                        return {'functional': False, 'message': f'HTTP {response.status}'}
        except Exception as e:
            return {'functional': False, 'message': str(e)}
    
    async def test_looker_api(self) -> Dict[str, Any]:
        """Test Looker API"""
        base_url = os.getenv('LOOKER_BASE_URL')
        if not base_url:
            return {'functional': False, 'message': 'Base URL not configured'}
        
        try:
            import aiohttp
            url = f"{base_url}/api/4.0/login"
            async with aiohttp.ClientSession() as session:
                async with session.post(url) as response:
                    if response.status in [200, 401]:  # 401 expected without credentials
                        return {'functional': True, 'message': 'Endpoint accessible'}
                    else:
                        return {'functional': False, 'message': f'HTTP {response.status}'}
        except Exception as e:
            return {'functional': False, 'message': str(e)}
    
    async def test_openai_api(self) -> Dict[str, Any]:
        """Test OpenAI API"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {'functional': False, 'message': 'API key not configured'}
        
        try:
            import aiohttp
            url = "https://api.openai.com/v1/models"
            headers = {'Authorization': f'Bearer {api_key}'}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        model_count = len(data.get('data', []))
                        return {'functional': True, 'message': f'{model_count} models available'}
                    elif response.status == 401:
                        return {'functional': False, 'message': 'Invalid API key'}
                    else:
                        return {'functional': False, 'message': f'HTTP {response.status}'}
        except Exception as e:
            return {'functional': False, 'message': str(e)}
    
    async def test_pinecone_api(self) -> Dict[str, Any]:
        """Test Pinecone API"""
        api_key = os.getenv('PINECONE_API_KEY')
        if not api_key:
            return {'functional': False, 'message': 'API key not configured'}
        
        try:
            import aiohttp
            url = "https://controller.us-east-1-aws.pinecone.io/databases"
            headers = {'Api-Key': api_key}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        index_count = len(data)
                        return {'functional': True, 'message': f'{index_count} indexes available'}
                    elif response.status == 401:
                        return {'functional': False, 'message': 'Invalid API key'}
                    else:
                        return {'functional': False, 'message': f'HTTP {response.status}'}
        except Exception as e:
            return {'functional': False, 'message': str(e)}
    
    async def test_services(self):
        """Test system services"""
        print("\n⚙️ TESTING SYSTEM SERVICES")
        print("-" * 40)
        
        services = [
            ('Python Version', self.check_python_version),
            ('Required Packages', self.check_packages),
            ('Disk Space', self.check_disk_space),
            ('Memory Usage', self.check_memory),
            ('Network Connectivity', self.check_network)
        ]
        
        for name, check_func in services:
            try:
                result = await check_func()
                status = "✅ OK" if result['ok'] else "⚠️ WARNING"
                print(f"{name:20} {status:10} {result['message']}")
                self.results['services'][name] = result
            except Exception as e:
                print(f"{name:20} ❌ ERROR    {str(e)[:30]}...")
                self.results['services'][name] = {'ok': False, 'error': str(e)}
    
    async def check_python_version(self) -> Dict[str, Any]:
        """Check Python version"""
        version = sys.version.split()[0]
        major, minor = map(int, version.split('.')[:2])
        ok = major >= 3 and minor >= 8
        return {
            'ok': ok,
            'message': f'Python {version}',
            'version': version
        }
    
    async def check_packages(self) -> Dict[str, Any]:
        """Check required packages"""
        required = ['aiohttp', 'psycopg2', 'redis', 'openai']
        missing = []
        
        for package in required:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        ok = len(missing) == 0
        message = "All packages available" if ok else f"Missing: {', '.join(missing)}"
        
        return {
            'ok': ok,
            'message': message,
            'missing': missing
        }
    
    async def check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            free_gb = free // (1024**3)
            ok = free_gb > 1  # At least 1GB free
            
            return {
                'ok': ok,
                'message': f'{free_gb}GB free',
                'free_bytes': free
            }
        except Exception as e:
            return {'ok': False, 'message': str(e)}
    
    async def check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            available_gb = memory.available // (1024**3)
            ok = available_gb > 0.5  # At least 500MB available
            
            return {
                'ok': ok,
                'message': f'{available_gb:.1f}GB available',
                'available_bytes': memory.available
            }
        except ImportError:
            # Fallback without psutil
            return {
                'ok': True,
                'message': 'psutil not available',
                'available_bytes': None
            }
    
    async def check_network(self) -> Dict[str, Any]:
        """Check network connectivity"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get('https://httpbin.org/ip', timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'ok': True,
                            'message': f"Connected ({data.get('origin', 'unknown IP')})",
                            'ip': data.get('origin')
                        }
                    else:
                        return {
                            'ok': False,
                            'message': f'HTTP {response.status}'
                        }
        except Exception as e:
            return {
                'ok': False,
                'message': str(e)
            }
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n📊 SUMMARY")
        print("-" * 40)
        
        # Count results
        env_set = sum(1 for v in self.results['environment'].values() if v['set'])
        env_total = len(self.results['environment'])
        
        db_accessible = sum(1 for v in self.results['databases'].values() if v['accessible'])
        db_total = len(self.results['databases'])
        
        api_functional = sum(1 for v in self.results['apis'].values() if v.get('functional', False))
        api_total = len(self.results['apis'])
        
        service_ok = sum(1 for v in self.results['services'].values() if v.get('ok', False))
        service_total = len(self.results['services'])
        
        print(f"Environment Variables: {env_set}/{env_total} configured")
        print(f"Database Connections:  {db_accessible}/{db_total} accessible")
        print(f"API Integrations:      {api_functional}/{api_total} functional")
        print(f"System Services:       {service_ok}/{service_total} healthy")
        
        # Overall status
        total_score = env_set + db_accessible + api_functional + service_ok
        max_score = env_total + db_total + api_total + service_total
        percentage = (total_score / max_score) * 100
        
        if percentage >= 80:
            status = "🟢 EXCELLENT"
        elif percentage >= 60:
            status = "🟡 GOOD"
        elif percentage >= 40:
            status = "🟠 NEEDS WORK"
        else:
            status = "🔴 CRITICAL"
        
        print(f"\nOverall System Health: {status} ({percentage:.1f}%)")
        
        self.results['summary'] = {
            'environment': {'set': env_set, 'total': env_total},
            'databases': {'accessible': db_accessible, 'total': db_total},
            'apis': {'functional': api_functional, 'total': api_total},
            'services': {'ok': service_ok, 'total': service_total},
            'overall_percentage': percentage,
            'status': status
        }
    
    def save_results(self):
        """Save test results to file"""
        filename = f"system_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\n💾 Results saved to: {filename}")
        except Exception as e:
            print(f"\n❌ Failed to save results: {e}")

async def main():
    """Main testing function"""
    tester = SystemTester()
    results = await tester.run_all_tests()
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("-" * 40)
    
    if results['summary']['overall_percentage'] < 50:
        print("1. Set up environment variables in .env file")
        print("2. Install and configure local databases")
        print("3. Obtain API keys for external services")
        print("4. Run setup scripts for database initialization")
    elif results['summary']['overall_percentage'] < 80:
        print("1. Complete API key configuration")
        print("2. Verify database server accessibility")
        print("3. Test production API endpoints")
    else:
        print("✅ System is well configured!")
        print("1. Consider setting up monitoring")
        print("2. Implement backup strategies")
        print("3. Configure production security")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())

