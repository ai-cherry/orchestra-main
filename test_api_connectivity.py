#!/usr/bin/env python3
"""
Orchestra AI - API Connectivity and Secret Management Test
Tests all API connections and validates secret configuration
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import secret managers
try:
    from security.enhanced_secret_manager import EnhancedSecretManager
    secret_manager = EnhancedSecretManager()
    print("✅ Using Enhanced Secret Manager")
except ImportError:
    from security.secret_manager import SecretManager
    secret_manager = SecretManager()
    print("✅ Using Standard Secret Manager")

class APIConnectivityTester:
    """Test API connectivity and secret management"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "secret_sources": [],
            "api_tests": {},
            "missing_secrets": [],
            "recommendations": []
        }
    
    def check_secret_sources(self):
        """Check available secret sources"""
        print("\n🔍 Checking Secret Sources...")
        
        # Check .env file
        env_file = Path(".env")
        if env_file.exists():
            self.results["secret_sources"].append(".env file")
            print("✅ Found .env file")
            
            # Count configured keys
            with open(env_file) as f:
                lines = f.readlines()
                api_keys = [l for l in lines if "API_KEY" in l or "TOKEN" in l]
                print(f"   - Contains {len(api_keys)} API key/token entries")
        else:
            print("❌ No .env file found")
        
        # Check encrypted secrets
        for env in ["production", "development", "test"]:
            secrets_file = Path(f".secrets.{env}.json")
            if secrets_file.exists():
                self.results["secret_sources"].append(f".secrets.{env}.json")
                print(f"✅ Found encrypted secrets: .secrets.{env}.json")
        
        # Check Pulumi config
        pulumi_yaml = Path("pulumi/Pulumi.yaml")
        if pulumi_yaml.exists():
            self.results["secret_sources"].append("Pulumi configuration")
            print("✅ Found Pulumi configuration")
    
    def test_lambda_labs_api(self):
        """Test Lambda Labs API connectivity"""
        print("\n🧪 Testing Lambda Labs API...")
        
        api_key = secret_manager.get_secret("LAMBDA_API_KEY")
        
        if not api_key:
            print("❌ LAMBDA_API_KEY not found")
            self.results["missing_secrets"].append("LAMBDA_API_KEY")
            self.results["api_tests"]["lambda_labs"] = {
                "status": "missing_key",
                "error": "API key not configured"
            }
            return
        
        try:
            response = requests.get(
                "https://cloud.lambda.ai/api/v1/instances",
                auth=(api_key, ""),
                timeout=10
            )
            
            if response.status_code == 200:
                instances = response.json().get("data", [])
                print(f"✅ Lambda Labs API connected - {len(instances)} instances found")
                
                # Check for Orchestra instances
                orchestra_instances = [i for i in instances if "orchestra" in i.get("name", "").lower()]
                if orchestra_instances:
                    print(f"   - Found {len(orchestra_instances)} Orchestra instances")
                    for inst in orchestra_instances:
                        print(f"     • {inst['name']} ({inst['ip_address']}) - {inst['status']}")
                
                self.results["api_tests"]["lambda_labs"] = {
                    "status": "connected",
                    "instances": len(instances),
                    "orchestra_instances": len(orchestra_instances)
                }
            else:
                print(f"❌ Lambda Labs API error: {response.status_code}")
                self.results["api_tests"]["lambda_labs"] = {
                    "status": "error",
                    "status_code": response.status_code,
                    "error": response.text[:200]
                }
                
        except Exception as e:
            print(f"❌ Lambda Labs connection failed: {str(e)}")
            self.results["api_tests"]["lambda_labs"] = {
                "status": "connection_failed",
                "error": str(e)
            }
    
    def test_github_api(self):
        """Test GitHub API connectivity"""
        print("\n🧪 Testing GitHub API...")
        
        token = secret_manager.get_secret("GITHUB_TOKEN")
        
        if not token:
            print("❌ GITHUB_TOKEN not found")
            self.results["missing_secrets"].append("GITHUB_TOKEN")
            self.results["api_tests"]["github"] = {
                "status": "missing_key",
                "error": "Token not configured"
            }
            return
        
        try:
            response = requests.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ GitHub API connected - User: {user_data.get('login')}")
                self.results["api_tests"]["github"] = {
                    "status": "connected",
                    "user": user_data.get("login"),
                    "scopes": response.headers.get("X-OAuth-Scopes", "").split(", ")
                }
            else:
                print(f"❌ GitHub API error: {response.status_code}")
                self.results["api_tests"]["github"] = {
                    "status": "error",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            print(f"❌ GitHub connection failed: {str(e)}")
            self.results["api_tests"]["github"] = {
                "status": "connection_failed",
                "error": str(e)
            }
    
    def test_vercel_api(self):
        """Test Vercel API connectivity"""
        print("\n🧪 Testing Vercel API...")
        
        token = secret_manager.get_secret("VERCEL_TOKEN")
        
        if not token:
            print("❌ VERCEL_TOKEN not found")
            self.results["missing_secrets"].append("VERCEL_TOKEN")
            self.results["api_tests"]["vercel"] = {
                "status": "missing_key",
                "error": "Token not configured"
            }
            return
        
        try:
            response = requests.get(
                "https://api.vercel.com/v2/user",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Vercel API connected - User: {user_data.get('username')}")
                
                # Check for Orchestra deployments
                deployments_response = requests.get(
                    "https://api.vercel.com/v6/deployments",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"limit": 10},
                    timeout=10
                )
                
                if deployments_response.status_code == 200:
                    deployments = deployments_response.json().get("deployments", [])
                    orchestra_deployments = [d for d in deployments if "orchestra" in d.get("name", "").lower()]
                    print(f"   - Found {len(orchestra_deployments)} Orchestra deployments")
                
                self.results["api_tests"]["vercel"] = {
                    "status": "connected",
                    "user": user_data.get("username")
                }
            else:
                print(f"❌ Vercel API error: {response.status_code}")
                self.results["api_tests"]["vercel"] = {
                    "status": "error",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            print(f"❌ Vercel connection failed: {str(e)}")
            self.results["api_tests"]["vercel"] = {
                "status": "connection_failed",
                "error": str(e)
            }
    
    def test_openai_api(self):
        """Test OpenAI API connectivity"""
        print("\n🧪 Testing OpenAI API...")
        
        api_key = secret_manager.get_secret("OPENAI_API_KEY")
        
        if not api_key:
            print("❌ OPENAI_API_KEY not found")
            self.results["missing_secrets"].append("OPENAI_API_KEY")
            self.results["api_tests"]["openai"] = {
                "status": "missing_key",
                "error": "API key not configured"
            }
            return
        
        try:
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            
            if response.status_code == 200:
                models = response.json().get("data", [])
                gpt4_models = [m for m in models if "gpt-4" in m["id"]]
                print(f"✅ OpenAI API connected - {len(models)} models available")
                print(f"   - GPT-4 models: {len(gpt4_models)}")
                
                self.results["api_tests"]["openai"] = {
                    "status": "connected",
                    "total_models": len(models),
                    "gpt4_models": len(gpt4_models)
                }
            else:
                print(f"❌ OpenAI API error: {response.status_code}")
                self.results["api_tests"]["openai"] = {
                    "status": "error",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            print(f"❌ OpenAI connection failed: {str(e)}")
            self.results["api_tests"]["openai"] = {
                "status": "connection_failed",
                "error": str(e)
            }
    
    def test_portkey_api(self):
        """Test Portkey API connectivity"""
        print("\n🧪 Testing Portkey API...")
        
        api_key = secret_manager.get_secret("PORTKEY_API_KEY")
        
        if not api_key:
            print("❌ PORTKEY_API_KEY not found")
            self.results["missing_secrets"].append("PORTKEY_API_KEY")
            self.results["api_tests"]["portkey"] = {
                "status": "missing_key",
                "error": "API key not configured"
            }
            return
        
        try:
            response = requests.get(
                "https://api.portkey.ai/v1/health",
                headers={"x-portkey-api-key": api_key},
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Portkey API connected")
                self.results["api_tests"]["portkey"] = {
                    "status": "connected"
                }
            else:
                print(f"❌ Portkey API error: {response.status_code}")
                self.results["api_tests"]["portkey"] = {
                    "status": "error",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            print(f"❌ Portkey connection failed: {str(e)}")
            self.results["api_tests"]["portkey"] = {
                "status": "connection_failed",
                "error": str(e)
            }
    
    def test_infrastructure_connectivity(self):
        """Test connectivity to deployed infrastructure"""
        print("\n🧪 Testing Infrastructure Connectivity...")
        
        # Test Lambda Labs instances
        production_ip = secret_manager.get_secret("PRODUCTION_IP", "150.136.94.139")
        
        print(f"   Testing Orchestra API at {production_ip}:8000...")
        try:
            response = requests.get(
                f"http://{production_ip}:8000/health",
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"   ✅ Orchestra API is healthy")
                self.results["api_tests"]["orchestra_backend"] = {
                    "status": "healthy",
                    "ip": production_ip
                }
            else:
                print(f"   ❌ Orchestra API returned: {response.status_code}")
                self.results["api_tests"]["orchestra_backend"] = {
                    "status": "unhealthy",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            print(f"   ❌ Cannot reach Orchestra API: {str(e)}")
            self.results["api_tests"]["orchestra_backend"] = {
                "status": "unreachable",
                "error": str(e)
            }
    
    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        print("\n📋 Generating Recommendations...")
        
        if self.results["missing_secrets"]:
            self.results["recommendations"].append({
                "priority": "HIGH",
                "action": "Configure missing API keys",
                "details": f"Missing keys: {', '.join(self.results['missing_secrets'])}"
            })
        
        # Check for failed connections
        failed_apis = [api for api, result in self.results["api_tests"].items() 
                      if result.get("status") not in ["connected", "healthy"]]
        
        if failed_apis:
            self.results["recommendations"].append({
                "priority": "HIGH",
                "action": "Fix API connectivity issues",
                "details": f"Failed APIs: {', '.join(failed_apis)}"
            })
        
        # Infrastructure recommendations
        if self.results["api_tests"].get("orchestra_backend", {}).get("status") != "healthy":
            self.results["recommendations"].append({
                "priority": "MEDIUM",
                "action": "Deploy or restart Orchestra backend",
                "details": "Backend API is not accessible"
            })
        
        # Security recommendations
        if ".env" in self.results["secret_sources"] and not any(".secrets" in s for s in self.results["secret_sources"]):
            self.results["recommendations"].append({
                "priority": "MEDIUM",
                "action": "Consider using encrypted secrets",
                "details": "Currently using plain .env file only"
            })
    
    def save_results(self):
        """Save test results to file"""
        output_file = Path("api_connectivity_test_results.json")
        
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
    
    def run_all_tests(self):
        """Run all connectivity tests"""
        print("🚀 Orchestra AI API Connectivity Test")
        print("=" * 50)
        
        # Check secret sources
        self.check_secret_sources()
        
        # Test each API
        self.test_lambda_labs_api()
        self.test_github_api() 
        self.test_vercel_api()
        self.test_openai_api()
        self.test_portkey_api()
        
        # Test infrastructure
        self.test_infrastructure_connectivity()
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Print summary
        print("\n📊 Test Summary")
        print("=" * 50)
        print(f"Environment: {self.results['environment']}")
        print(f"Secret Sources: {', '.join(self.results['secret_sources']) or 'None found'}")
        print(f"Missing Secrets: {len(self.results['missing_secrets'])}")
        
        # API status summary
        print("\nAPI Status:")
        for api, result in self.results["api_tests"].items():
            status = result.get("status", "unknown")
            emoji = "✅" if status in ["connected", "healthy"] else "❌"
            print(f"  {emoji} {api}: {status}")
        
        # Recommendations
        if self.results["recommendations"]:
            print("\n⚠️  Recommendations:")
            for rec in self.results["recommendations"]:
                print(f"  [{rec['priority']}] {rec['action']}")
                print(f"         {rec['details']}")
        
        # Save results
        self.save_results()

if __name__ == "__main__":
    tester = APIConnectivityTester()
    tester.run_all_tests() 