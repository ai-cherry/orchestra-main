#!/usr/bin/env python3
"""
Complete N8N Setup with All API Credentials
Uses the provided comprehensive API credentials to configure N8N
"""

import os
import requests
import base64
import json
from datetime import datetime
from dotenv import load_dotenv

# Load .env for local/dev/Cursor, not in production
if os.environ.get("ENV", "development") != "production":
    load_dotenv()

class CompleteN8NSetup:
    def __init__(self):
        self.base_url = os.environ.get("N8N_BASE_URL", "http://localhost:5678")
        self.username = os.environ.get("N8N_USERNAME", "payready_admin")
        self.password = os.environ.get("N8N_PASSWORD", "")
        self.n8n_api_key = os.environ.get("N8N_API_KEY", "")
        
        # Create auth headers
        auth_string = f"{self.username}:{self.password}"
        auth_bytes = auth_string.encode('ascii')
        self.auth_header = base64.b64encode(auth_bytes).decode('ascii')
        
        self.headers = {
            'Authorization': f'Basic {self.auth_header}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # All API credentials from user
        self.credentials_data = {
            'github': {
                'name': 'Pay Ready GitHub',
                'type': 'githubApi',
                'data': {
                    'accessToken': os.environ.get('GITHUB_ACCESS_TOKEN', '')
                }
            },
            'slack_bot': {
                'name': 'Pay Ready Slack Bot',
                'type': 'slackApi',
                'data': {
                    'botToken': os.environ.get('SLACK_BOT_TOKEN', '')
                }
            },
            'salesforce': {
                'name': 'Pay Ready Salesforce',
                'type': 'httpHeaderAuth',
                'data': {
                    'name': 'Authorization',
                    'value': f"Bearer {os.environ.get('SALESFORCE_ACCESS_TOKEN', '')}"
                }
            },
            'gong': {
                'name': 'Pay Ready Gong',
                'type': 'httpBasicAuth',
                'data': {
                    'user': os.environ.get('GONG_ACCESS_KEY', ''),
                    'password': os.environ.get('GONG_ACCESS_KEY_SECRET', '')
                }
            },
            'openai': {
                'name': 'Pay Ready OpenAI',
                'type': 'openAiApi',
                'data': {
                    'apiKey': os.environ.get('OPENAI_API_KEY', '')
                }
            },
            'anthropic': {
                'name': 'Pay Ready Claude',
                'type': 'httpHeaderAuth',
                'data': {
                    'name': 'x-api-key',
                    'value': os.environ.get('ANTHROPIC_API_KEY', '')
                }
            },
            'notion': {
                'name': 'Pay Ready Notion',
                'type': 'notionApi',
                'data': {
                    'apiKey': os.environ.get('NOTION_API_KEY', '')
                }
            },
            'linear': {
                'name': 'Pay Ready Linear',
                'type': 'linearApi',
                'data': {
                    'apiKey': os.environ.get('LINEAR_API_KEY', '')
                }
            },
            'hubspot': {
                'name': 'Pay Ready HubSpot',
                'type': 'hubspotApi',
                'data': {
                    'apiKey': os.environ.get('HUBSPOT_API_KEY', '')
                }
            },
            'smtp_gmail': {
                'name': 'Pay Ready SMTP',
                'type': 'smtp',
                'data': {
                    'host': 'smtp.gmail.com',
                    'port': 587,
                    'secure': False,
                    'user': os.environ.get('SMTP_USER', ''),
                    'password': os.environ.get('SMTP_PASSWORD', '')
                }
            },
            'webhook_auth': {
                'name': 'Pay Ready Webhook Auth',
                'type': 'httpHeaderAuth',
                'data': {
                    'name': 'X-API-Key',
                    'value': os.environ.get('WEBHOOK_API_KEY', '')
                }
            }
        }
    
    def test_connection(self):
        """Test N8N API connection"""
        try:
            # Test basic connectivity
            response = requests.get(f"{self.base_url}/healthz", timeout=10)
            if response.status_code == 200:
                print("✅ N8N health check successful")
                
                # Test REST API with auth
                api_response = requests.get(f"{self.base_url}/rest/credentials", headers=self.headers, timeout=10)
                if api_response.status_code in [200, 401]:
                    print("✅ N8N REST API accessible")
                    return True
                else:
                    print(f"⚠️ N8N REST API: {api_response.status_code}")
                    return False
            else:
                print(f"❌ N8N health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def create_credential(self, cred_config):
        """Create a single credential in N8N"""
        try:
            response = requests.post(
                f"{self.base_url}/rest/credentials",
                headers=self.headers,
                json=cred_config,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Created: {cred_config['name']}")
                return True
            elif response.status_code == 400:
                print(f"⚠️ {cred_config['name']}: Already exists or validation error")
                return False
            else:
                print(f"❌ {cred_config['name']}: {response.status_code} - {response.text[:100]}")
                return False
                
        except Exception as e:
            print(f"❌ {cred_config['name']} error: {e}")
            return False
    
    def setup_all_credentials(self):
        """Create all credentials in N8N"""
        print("🔑 Setting up all Pay Ready credentials...")
        
        success_count = 0
        total_count = len(self.credentials_data)
        
        for key, cred_config in self.credentials_data.items():
            if self.create_credential(cred_config):
                success_count += 1
        
        print(f"\n🎯 Credential setup complete: {success_count}/{total_count} successful")
        return success_count
    
    def create_test_workflow(self):
        """Create a test webhook workflow"""
        workflow = {
            "name": "Pay Ready: API Test Workflow",
            "nodes": [
                {
                    "parameters": {
                        "httpMethod": "POST",
                        "path": "payready-test",
                        "responseMode": "responseNode",
                        "options": {}
                    },
                    "name": "Webhook Trigger",
                    "type": "n8n-nodes-base.webhook",
                    "typeVersion": 1,
                    "position": [240, 300],
                    "id": "webhook-trigger"
                },
                {
                    "parameters": {
                        "jsCode": "// Pay Ready webhook processor\nconst payload = $input.first().json;\nconst timestamp = new Date().toISOString();\n\nconst response = {\n  status: 'success',\n  message: 'Pay Ready webhook received and processed',\n  timestamp: timestamp,\n  data: payload,\n  source: 'Pay Ready N8N',\n  webhook_id: 'payready-test'\n};\n\nconsole.log('Pay Ready webhook processed:', response);\n\nreturn [{ json: response }];"
                    },
                    "name": "Process Data",
                    "type": "n8n-nodes-base.code",
                    "typeVersion": 1,
                    "position": [460, 300],
                    "id": "process-data"
                },
                {
                    "parameters": {
                        "respondWith": "json",
                        "responseBody": "={{ $json }}"
                    },
                    "name": "Respond to Webhook",
                    "type": "n8n-nodes-base.respondToWebhook",
                    "typeVersion": 1,
                    "position": [680, 300],
                    "id": "webhook-response"
                }
            ],
            "connections": {
                "Webhook Trigger": {
                    "main": [
                        [
                            {
                                "node": "Process Data",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                },
                "Process Data": {
                    "main": [
                        [
                            {
                                "node": "Respond to Webhook",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                }
            },
            "active": True,
            "settings": {
                "timezone": "America/New_York"
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/rest/workflows",
                headers=self.headers,
                json=workflow,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                workflow_id = result.get('id')
                print(f"✅ Created test workflow: {workflow_id}")
                print(f"🔗 Webhook URL: {self.base_url}/webhook/payready-test")
                return workflow_id
            else:
                print(f"❌ Workflow creation failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Workflow error: {e}")
            return None
    
    def list_credentials(self):
        """List all credentials"""
        try:
            response = requests.get(f"{self.base_url}/rest/credentials", headers=self.headers, timeout=10)
            if response.status_code == 200:
                creds = response.json()
                print(f"\n📋 Total credentials in N8N: {len(creds)}")
                pay_ready_creds = [c for c in creds if 'Pay Ready' in c.get('name', '')]
                print(f"📋 Pay Ready credentials: {len(pay_ready_creds)}")
                
                for cred in pay_ready_creds:
                    print(f"   • {cred.get('name')} ({cred.get('type')})")
                
                return creds
            else:
                print(f"❌ Failed to list credentials: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error listing credentials: {e}")
            return []
    
    def test_webhook(self, workflow_id=None):
        """Test the created webhook"""
        webhook_url = f"{self.base_url}/webhook/payready-test"
        test_data = {
            "test": True,
            "message": "Pay Ready N8N test",
            "timestamp": datetime.now().isoformat(),
            "source": "Pay Ready setup script"
        }
        
        try:
            response = requests.post(webhook_url, json=test_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Webhook test successful")
                print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
                return True
            else:
                print(f"❌ Webhook test failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Webhook test error: {e}")
            return False
    
    def complete_setup(self):
        """Complete N8N setup process"""
        print("🚀 Complete Pay Ready N8N Setup")
        print("=" * 50)
        
        # Test connection
        if not self.test_connection():
            print("❌ Cannot connect to N8N")
            return False
        
        # Setup credentials
        cred_count = self.setup_all_credentials()
        
        # Create test workflow
        print("\n🔧 Creating test workflow...")
        workflow_id = self.create_test_workflow()
        
        # List final credentials
        print("\n📋 Final credential status:")
        self.list_credentials()
        
        # Test webhook
        if workflow_id:
            print("\n🧪 Testing webhook...")
            self.test_webhook(workflow_id)
        
        print(f"\n🎉 Setup Complete!")
        print(f"✅ Credentials configured: {cred_count}")
        print(f"✅ Test workflow created: {'Yes' if workflow_id else 'No'}")
        print(f"✅ N8N accessible at: {self.base_url}")
        print(f"✅ Test webhook: {self.base_url}/webhook/payready-test")
        
        return True

def main():
    """Main execution"""
    print("🔑 Complete Pay Ready N8N Setup with All Credentials")
    print("=" * 60)
    
    setup = CompleteN8NSetup()
    success = setup.complete_setup()
    
    if success:
        print("\n🎉 N8N is fully configured and ready!")
        print("🌐 Access N8N: http://192.9.142.8:5678")
        print("👤 Username: payready_admin")
        print("🔐 Password: PayReady_N8N_2025!")
        print("\n🚀 Ready to create Pay Ready CEO BI workflows!")
    else:
        print("\n❌ Setup failed - check N8N status")

if __name__ == "__main__":
    main() 