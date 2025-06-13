#!/usr/bin/env python3
"""
Unified API Client for Orchestra AI IaC Agent
Provides a single interface to all external services
"""

import os
import json
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Import service-specific clients
import pulumi
import pulumi.automation as auto
from github import Github
import pinecone
import weaviate
from portkey_ai import Portkey
import redis

@dataclass
class ServiceStatus:
    """Status of an external service"""
    name: str
    available: bool
    message: str
    last_check: datetime

class UnifiedAPIClient:
    """Unified client for all Orchestra AI external services"""
    
    def __init__(self):
        """Initialize all service clients"""
        self.services = {}
        self.status = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize all external service clients"""
        
        # Lambda Labs
        try:
            self.services['lambda_labs'] = {
                'api_key': os.environ.get('LAMBDA_LABS_API_KEY'),
                'base_url': 'https://cloud.lambdalabs.com/api/v1',
                'headers': {
                    'Authorization': f"Bearer {os.environ.get('LAMBDA_LABS_API_KEY')}"
                }
            }
            self._check_service('lambda_labs')
        except Exception as e:
            self.status['lambda_labs'] = ServiceStatus(
                'lambda_labs', False, str(e), datetime.now()
            )
        
        # Pulumi
        try:
            self.services['pulumi'] = {
                'token': os.environ.get('PULUMI_ACCESS_TOKEN'),
                'backend': os.environ.get('PULUMI_BACKEND_URL', 'file://~/.pulumi')
            }
            self._check_service('pulumi')
        except Exception as e:
            self.status['pulumi'] = ServiceStatus(
                'pulumi', False, str(e), datetime.now()
            )
        
        # GitHub
        try:
            token = os.environ.get('GITHUB_TOKEN')
            if token:
                self.services['github'] = Github(token)
                self._check_service('github')
        except Exception as e:
            self.status['github'] = ServiceStatus(
                'github', False, str(e), datetime.now()
            )
        
        # Pinecone
        try:
            api_key = os.environ.get('PINECONE_API_KEY')
            if api_key:
                pinecone.init(
                    api_key=api_key,
                    environment=os.environ.get('PINECONE_ENVIRONMENT', 'us-west1-gcp')
                )
                self.services['pinecone'] = pinecone
                self._check_service('pinecone')
        except Exception as e:
            self.status['pinecone'] = ServiceStatus(
                'pinecone', False, str(e), datetime.now()
            )
        
        # Weaviate
        try:
            weaviate_url = os.environ.get('WEAVIATE_URL', 'http://localhost:8080')
            weaviate_key = os.environ.get('WEAVIATE_API_KEY')
            
            if weaviate_key:
                auth_config = weaviate.AuthApiKey(api_key=weaviate_key)
                self.services['weaviate'] = weaviate.Client(
                    url=weaviate_url,
                    auth_client_secret=auth_config
                )
            else:
                self.services['weaviate'] = weaviate.Client(url=weaviate_url)
            
            self._check_service('weaviate')
        except Exception as e:
            self.status['weaviate'] = ServiceStatus(
                'weaviate', False, str(e), datetime.now()
            )
        
        # Portkey
        try:
            api_key = os.environ.get('PORTKEY_API_KEY')
            if api_key:
                self.services['portkey'] = Portkey(
                    api_key=api_key,
                    mode="single"
                )
                self._check_service('portkey')
        except Exception as e:
            self.status['portkey'] = ServiceStatus(
                'portkey', False, str(e), datetime.now()
            )
        
        # Redis
        try:
            self.services['redis'] = redis.Redis(
                host=os.environ.get('REDIS_HOST', 'localhost'),
                port=int(os.environ.get('REDIS_PORT', 6379)),
                decode_responses=True
            )
            self._check_service('redis')
        except Exception as e:
            self.status['redis'] = ServiceStatus(
                'redis', False, str(e), datetime.now()
            )
    
    def _check_service(self, service_name: str) -> bool:
        """Check if a service is available"""
        try:
            if service_name == 'lambda_labs':
                resp = requests.get(
                    f"{self.services['lambda_labs']['base_url']}/instance-types",
                    headers=self.services['lambda_labs']['headers']
                )
                available = resp.status_code == 200
                
            elif service_name == 'pulumi':
                # Simple check - can we access Pulumi CLI
                available = os.system('pulumi version > /dev/null 2>&1') == 0
                
            elif service_name == 'github':
                # Check GitHub authentication
                user = self.services['github'].get_user()
                available = user.login is not None
                
            elif service_name == 'pinecone':
                # List indexes to check connection
                indexes = pinecone.list_indexes()
                available = True
                
            elif service_name == 'weaviate':
                # Check if Weaviate is ready
                available = self.services['weaviate'].is_ready()
                
            elif service_name == 'portkey':
                # Portkey doesn't have a simple health check
                available = self.services['portkey'] is not None
                
            elif service_name == 'redis':
                # Ping Redis
                available = self.services['redis'].ping()
            
            else:
                available = False
            
            self.status[service_name] = ServiceStatus(
                service_name, available, 
                "Connected" if available else "Connection failed",
                datetime.now()
            )
            return available
            
        except Exception as e:
            self.status[service_name] = ServiceStatus(
                service_name, False, str(e), datetime.now()
            )
            return False
    
    # Lambda Labs Operations
    def lambda_list_instances(self) -> List[Dict]:
        """List all Lambda Labs instances"""
        if 'lambda_labs' not in self.services:
            raise Exception("Lambda Labs not configured")
        
        resp = requests.get(
            f"{self.services['lambda_labs']['base_url']}/instances",
            headers=self.services['lambda_labs']['headers']
        )
        return resp.json().get('data', [])
    
    def lambda_create_instance(self, instance_type: str, region: str, 
                             ssh_key: str, **kwargs) -> Dict:
        """Create a Lambda Labs instance"""
        if 'lambda_labs' not in self.services:
            raise Exception("Lambda Labs not configured")
        
        data = {
            "instance_type_name": instance_type,
            "region_name": region,
            "ssh_key_names": [ssh_key],
            **kwargs
        }
        
        resp = requests.post(
            f"{self.services['lambda_labs']['base_url']}/instance-operations/launch",
            headers=self.services['lambda_labs']['headers'],
            json=data
        )
        return resp.json()
    
    # Pulumi Operations
    def pulumi_create_stack(self, stack_name: str, project_dir: str) -> auto.Stack:
        """Create or select a Pulumi stack"""
        if 'pulumi' not in self.services:
            raise Exception("Pulumi not configured")
        
        # Create workspace
        workspace = auto.LocalWorkspace(
            work_dir=project_dir,
            pulumi_home=os.path.expanduser("~/.pulumi")
        )
        
        # Create or select stack
        try:
            stack = auto.create_stack(stack_name, workspace)
        except auto.StackAlreadyExistsError:
            stack = auto.select_stack(stack_name, workspace)
        
        return stack
    
    def pulumi_preview(self, stack: auto.Stack) -> auto.PreviewResult:
        """Preview Pulumi changes"""
        return stack.preview()
    
    def pulumi_up(self, stack: auto.Stack) -> auto.UpResult:
        """Apply Pulumi changes"""
        return stack.up()
    
    # Pinecone Operations
    def pinecone_create_index(self, name: str, dimension: int, 
                            metric: str = "cosine", **kwargs) -> None:
        """Create a Pinecone index"""
        if 'pinecone' not in self.services:
            raise Exception("Pinecone not configured")
        
        pinecone.create_index(
            name=name,
            dimension=dimension,
            metric=metric,
            **kwargs
        )
    
    def pinecone_list_indexes(self) -> List[str]:
        """List all Pinecone indexes"""
        if 'pinecone' not in self.services:
            raise Exception("Pinecone not configured")
        
        return pinecone.list_indexes()
    
    # Weaviate Operations
    def weaviate_create_class(self, class_config: Dict) -> None:
        """Create a Weaviate class"""
        if 'weaviate' not in self.services:
            raise Exception("Weaviate not configured")
        
        self.services['weaviate'].schema.create_class(class_config)
    
    def weaviate_get_schema(self) -> Dict:
        """Get Weaviate schema"""
        if 'weaviate' not in self.services:
            raise Exception("Weaviate not configured")
        
        return self.services['weaviate'].schema.get()
    
    # Portkey Operations
    def portkey_create_gateway(self, config: Dict) -> Dict:
        """Create a Portkey gateway configuration"""
        if 'portkey' not in self.services:
            raise Exception("Portkey not configured")
        
        # Portkey configuration would go here
        return {"status": "configured", "config": config}
    
    # Status and Health
    def get_all_status(self) -> Dict[str, ServiceStatus]:
        """Get status of all services"""
        # Refresh status for all services
        for service_name in self.services.keys():
            self._check_service(service_name)
        
        return self.status
    
    def get_service_status(self, service_name: str) -> ServiceStatus:
        """Get status of a specific service"""
        if service_name in self.status:
            # Refresh if status is older than 5 minutes
            if (datetime.now() - self.status[service_name].last_check).seconds > 300:
                self._check_service(service_name)
        else:
            self._check_service(service_name)
        
        return self.status.get(service_name, ServiceStatus(
            service_name, False, "Service not configured", datetime.now()
        ))
    
    def generate_status_report(self) -> str:
        """Generate a comprehensive status report"""
        report = ["Orchestra AI External Services Status Report"]
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        all_status = self.get_all_status()
        
        for service_name, status in all_status.items():
            emoji = "✅" if status.available else "❌"
            report.append(f"{emoji} {service_name.title()}: {status.message}")
        
        report.append("")
        report.append("Configuration:")
        report.append(f"  Pulumi Backend: {self.services.get('pulumi', {}).get('backend', 'Not configured')}")
        report.append(f"  Weaviate URL: {os.environ.get('WEAVIATE_URL', 'http://localhost:8080')}")
        report.append(f"  Redis Host: {os.environ.get('REDIS_HOST', 'localhost')}")
        
        return "\n".join(report)


# CLI Interface
if __name__ == "__main__":
    import sys
    
    client = UnifiedAPIClient()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            print(client.generate_status_report())
            
        elif command == "lambda-list":
            instances = client.lambda_list_instances()
            print(json.dumps(instances, indent=2))
            
        elif command == "pinecone-list":
            indexes = client.pinecone_list_indexes()
            print("Pinecone Indexes:", indexes)
            
        elif command == "weaviate-schema":
            schema = client.weaviate_get_schema()
            print(json.dumps(schema, indent=2))
            
        else:
            print("Available commands:")
            print("  status         - Show status of all services")
            print("  lambda-list    - List Lambda Labs instances")
            print("  pinecone-list  - List Pinecone indexes")
            print("  weaviate-schema - Show Weaviate schema")
    else:
        # Interactive mode
        print(client.generate_status_report()) 