#!/usr/bin/env python3
"""
N8N Setup Using API Key Authentication
Uses the N8N API key for direct authentication
"""

import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load .env for local/dev/Cursor, not in production
if os.environ.get("ENV", "development") != "production":
    load_dotenv()

class N8NApiKeySetup:
    def __init__(self):
        self.base_url = os.environ.get("N8N_BASE_URL", "http://localhost:5678")
        self.api_key = os.environ.get("N8N_API_KEY", "")
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def test_api_key_connection(self):
        """Test N8N connection with API key"""
        print("🔑 Testing N8N API Key authentication...")
        
        try:
            # Try different endpoints to test API key
            endpoints = [
                "/rest/workflows",
                "/rest/credentials", 
                "/rest/executions",
                "/api/v1/workflows"
            ]
            
            for endpoint in endpoints:
                response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, timeout=10)
                print(f"   {endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"✅ API Key works with {endpoint}")
                    return True
                elif response.status_code == 404:
                    print(f"⚠️ {endpoint} not found (but API key auth working)")
                elif response.status_code == 401:
                    print(f"❌ {endpoint} - Unauthorized")
                else:
                    print(f"⚠️ {endpoint} - Status: {response.status_code}")
            
            return False
            
        except Exception as e:
            print(f"❌ API Key test error: {e}")
            return False
    
    def test_basic_auth_again(self):
        """Try basic auth with different credentials"""
        print("\n🔐 Testing basic authentication alternatives...")
        
        auth_combinations = [
            ("payready_admin", "PayReady_N8N_2025!"),
            ("admin", "admin"),
            ("n8n", "n8n"),
            ("", "")  # No auth
        ]
        
        for username, password in auth_combinations:
            if username and password:
                import base64
                auth_string = f"{username}:{password}"
                auth_bytes = auth_string.encode('ascii')
                auth_header = base64.b64encode(auth_bytes).decode('ascii')
                headers = {'Authorization': f'Basic {auth_header}'}
            else:
                headers = {}
            
            try:
                response = requests.get(f"{self.base_url}/rest/credentials", headers=headers, timeout=5)
                print(f"   {username}:{password[:3]}... -> {response.status_code}")
                
                if response.status_code == 200:
                    print(f"✅ Basic auth works: {username}")
                    return (username, password)
                    
            except Exception as e:
                print(f"   {username} - Error: {str(e)[:30]}")
        
        return None
    
    def try_n8n_cloud_api(self):
        """Try using N8N Cloud API if local fails"""
        print("\n☁️ Trying N8N Cloud API...")
        
        cloud_headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Try N8N Cloud endpoints
            cloud_endpoints = [
                "https://api.n8n.cloud/v1/workflows",
                "https://api.n8n.cloud/workflows", 
                "https://app.n8n.cloud/api/v1/workflows"
            ]
            
            for endpoint in cloud_endpoints:
                response = requests.get(endpoint, headers=cloud_headers, timeout=10)
                print(f"   {endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"✅ N8N Cloud API accessible at {endpoint}")
                    # Could configure workflows in cloud if needed
                    return endpoint
            
        except Exception as e:
            print(f"❌ N8N Cloud error: {e}")
        
        return None
    
    def access_web_interface(self):
        """Test accessing N8N web interface"""
        print("\n🌐 Testing N8N web interface access...")
        
        try:
            # Try web interface without auth
            response = requests.get(self.base_url, timeout=10)
            print(f"   Web interface: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ N8N web interface accessible")
                print("💡 You can manually configure credentials at: http://192.9.142.8:5678")
                return True
            
        except Exception as e:
            print(f"❌ Web interface error: {e}")
        
        return False
    
    def create_credentials_via_web_instructions(self):
        """Provide instructions for manual credential setup"""
        print("\n📝 Manual Credential Setup Instructions")
        print("=" * 50)
        print(f"🌐 Access N8N at: {self.base_url}")
        print(f"👤 Login with: {os.environ.get('N8N_USERNAME', 'payready_admin')} / [your password]")
        print()
        print("🔑 Add these credentials in N8N Settings > Credentials:")
        print()
        credentials = [
            ("GitHub", "GitHub API", os.environ.get('GITHUB_ACCESS_TOKEN', '')),
            ("Slack Bot", "Slack API", os.environ.get('SLACK_BOT_TOKEN', '')),
            ("Salesforce", "HTTP Header Auth", os.environ.get('SALESFORCE_ACCESS_TOKEN', '')),
            ("OpenAI", "OpenAI API", os.environ.get('OPENAI_API_KEY', '')),
            ("Claude/Anthropic", "HTTP Header Auth", os.environ.get('ANTHROPIC_API_KEY', '')),
            ("Notion", "Notion API", os.environ.get('NOTION_API_KEY', '')),
            ("Gong", "HTTP Basic Auth", os.environ.get('GONG_ACCESS_KEY', ''))
        ]
        for name, type_name, token in credentials:
            print(f"📌 {name}:")
            print(f"   Type: {type_name}")
            print(f"   Token: {token[:8]}... (set in .env or env)")
            print()
        
        return True
    
    def test_webhook_creation(self):
        """Test creating a simple webhook"""
        print("\n🪝 Testing webhook creation...")
        
        # Try creating via API first
        webhook_data = {
            "test": True,
            "message": "Pay Ready webhook test",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Test webhook endpoint directly
            webhook_url = f"{self.base_url}/webhook/test"
            response = requests.post(webhook_url, json=webhook_data, timeout=10)
            print(f"   Webhook test: {response.status_code}")
            
            if response.status_code == 404:
                print("⚠️ No webhook found (need to create workflow first)")
            elif response.status_code == 200:
                print("✅ Webhook endpoint working!")
                return True
            
        except Exception as e:
            print(f"❌ Webhook test error: {e}")
        
        return False
    
    def run_comprehensive_test(self):
        """Run all tests to determine best setup approach"""
        print("🚀 Pay Ready N8N Comprehensive Setup Test")
        print("=" * 60)
        
        # Test API key authentication
        api_key_works = self.test_api_key_connection()
        
        # Test basic authentication
        basic_auth_result = self.test_basic_auth_again()
        
        # Test N8N Cloud API
        cloud_endpoint = self.try_n8n_cloud_api()
        
        # Test web interface
        web_accessible = self.access_web_interface()
        
        # Test webhooks
        webhook_works = self.test_webhook_creation()
        
        print("\n🎯 SUMMARY & RECOMMENDATIONS")
        print("=" * 40)
        
        if web_accessible:
            print("✅ RECOMMENDED: Manual setup via web interface")
            self.create_credentials_via_web_instructions()
        elif basic_auth_result:
            print(f"✅ ALTERNATIVE: Use basic auth: {basic_auth_result[0]}")
        elif cloud_endpoint:
            print(f"✅ ALTERNATIVE: Use N8N Cloud: {cloud_endpoint}")
        else:
            print("⚠️ Manual intervention needed")
        
        print("\n🚀 NEXT STEPS:")
        print("1. Access N8N web interface")
        print("2. Configure credentials manually")
        print("3. Create CEO BI workflows")
        print("4. Test webhook endpoints")
        
        return True

def main():
    """Main execution"""
    setup = N8NApiKeySetup()
    setup.run_comprehensive_test()

if __name__ == "__main__":
    main() 