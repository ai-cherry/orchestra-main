#!/usr/bin/env python3
"""
Configure Airbyte connections for AI Orchestrator
Sets up sources and destinations for data integration
"""

import os
import sys
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime

class AirbyteConfigurer:
    """Manages Airbyte configuration via API"""
    
    def __init__(self):
        self.api_url = os.environ.get('AIRBYTE_API_URL', 'https://api.airbyte.com')
        self.api_key = os.environ.get('AIRBYTE_API_KEY')
        self.workspace_id = os.environ.get('AIRBYTE_WORKSPACE_ID')
        
        if not self.api_key or not self.workspace_id:
            raise ValueError("AIRBYTE_API_KEY and AIRBYTE_WORKSPACE_ID must be set")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def create_postgres_source(self) -> str:
        """Create PostgreSQL source for orchestration data"""
        source_config = {
            "workspaceId": self.workspace_id,
            "name": "AI Orchestrator PostgreSQL",
            "sourceDefinitionId": "decd338e-5647-4c0b-adf4-da0e75f5a750",  # PostgreSQL source
            "connectionConfiguration": {
                "host": os.environ.get('POSTGRES_HOST'),
                "port": int(os.environ.get('POSTGRES_PORT', 5432)),
                "database": os.environ.get('POSTGRES_DB'),
                "username": os.environ.get('POSTGRES_USER'),
                "password": os.environ.get('POSTGRES_PASSWORD'),
                "ssl_mode": {
                    "mode": "require"
                },
                "replication_method": {
                    "method": "Standard"
                },
                "tunnel_method": {
                    "tunnel_method": "NO_TUNNEL"
                }
            }
        }
        
        print("Creating PostgreSQL source...")
        response = requests.post(
            f"{self.api_url}/v1/sources",
            headers=self.headers,
            json=source_config
        )
        
        if response.status_code == 200:
            source_id = response.json()['sourceId']
            print(f"✓ PostgreSQL source created: {source_id}")
            return source_id
        else:
            print(f"✗ Failed to create PostgreSQL source: {response.text}")
            raise Exception("Failed to create source")
    
    def create_weaviate_destination(self) -> str:
        """Create Weaviate destination for vector storage"""
        destination_config = {
            "workspaceId": self.workspace_id,
            "name": "AI Orchestrator Weaviate",
            "destinationDefinitionId": "7b7d7a0d-954c-45a0-bcfc-39a634b97736",  # Custom destination
            "connectionConfiguration": {
                "url": os.environ.get('WEAVIATE_URL'),
                "api_key": os.environ.get('WEAVIATE_API_KEY'),
                "batch_size": 100,
                "batch_timeout_ms": 1000
            }
        }
        
        print("Creating Weaviate destination...")
        response = requests.post(
            f"{self.api_url}/v1/destinations",
            headers=self.headers,
            json=destination_config
        )
        
        if response.status_code == 200:
            destination_id = response.json()['destinationId']
            print(f"✓ Weaviate destination created: {destination_id}")
            return destination_id
        else:
            print(f"✗ Failed to create Weaviate destination: {response.text}")
            raise Exception("Failed to create destination")
    
    def create_connection(self, source_id: str, destination_id: str) -> str:
        """Create connection between source and destination"""
        connection_config = {
            "sourceId": source_id,
            "destinationId": destination_id,
            "name": "PostgreSQL to Weaviate Sync",
            "namespaceDefinition": "source",
            "namespaceFormat": "${SOURCE_NAMESPACE}",
            "prefix": "orchestrator_",
            "syncCatalog": {
                "streams": [
                    {
                        "stream": {
                            "name": "orchestration_logs",
                            "jsonSchema": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "workflow_id": {"type": "string"},
                                    "task_id": {"type": "string"},
                                    "agent_role": {"type": "string"},
                                    "action": {"type": "string"},
                                    "status": {"type": "string"},
                                    "metadata": {"type": "object"},
                                    "error_message": {"type": "string"},
                                    "created_at": {"type": "string", "format": "date-time"}
                                }
                            },
                            "supportedSyncModes": ["full_refresh", "incremental"],
                            "defaultCursorField": ["created_at"],
                            "sourceDefinedPrimaryKey": [["id"]]
                        },
                        "config": {
                            "syncMode": "incremental",
                            "cursorField": ["created_at"],
                            "destinationSyncMode": "append_dedup",
                            "primaryKey": [["id"]],
                            "aliasName": "orchestration_logs",
                            "selected": True
                        }
                    }
                ]
            },
            "scheduleType": "manual",
            "status": "active",
            "geography": "auto"
        }
        
        print("Creating connection...")
        response = requests.post(
            f"{self.api_url}/v1/connections",
            headers=self.headers,
            json=connection_config
        )
        
        if response.status_code == 200:
            connection_id = response.json()['connectionId']
            print(f"✓ Connection created: {connection_id}")
            return connection_id
        else:
            print(f"✗ Failed to create connection: {response.text}")
            raise Exception("Failed to create connection")
    
    def create_sync_schedule(self, connection_id: str) -> None:
        """Create sync schedule for the connection"""
        schedule_config = {
            "connectionId": connection_id,
            "scheduleType": "cron",
            "cronExpression": "0 */6 * * *"  # Every 6 hours
        }
        
        print("Creating sync schedule...")
        response = requests.post(
            f"{self.api_url}/v1/connections/{connection_id}/schedule",
            headers=self.headers,
            json=schedule_config
        )
        
        if response.status_code == 200:
            print("✓ Sync schedule created (every 6 hours)")
        else:
            print(f"✗ Failed to create sync schedule: {response.text}")
    
    def test_connection(self, connection_id: str) -> bool:
        """Test the connection"""
        print(f"Testing connection {connection_id}...")
        response = requests.post(
            f"{self.api_url}/v1/connections/{connection_id}/sync",
            headers=self.headers
        )
        
        if response.status_code == 200:
            job_id = response.json()['job']['id']
            print(f"✓ Sync job started: {job_id}")
            return True
        else:
            print(f"✗ Failed to start sync job: {response.text}")
            return False

def main():
    """Main configuration function"""
    print("Airbyte Configuration for AI Orchestrator")
    print("=" * 40)
    
    try:
        configurer = AirbyteConfigurer()
        
        # Check if connections already exist
        print("Checking existing connections...")
        response = requests.get(
            f"{configurer.api_url}/v1/connections",
            headers=configurer.headers,
            params={"workspaceId": configurer.workspace_id}
        )
        
        existing_connections = response.json().get('connections', [])
        orchestrator_connection = None
        
        for conn in existing_connections:
            if conn['name'] == "PostgreSQL to Weaviate Sync":
                orchestrator_connection = conn
                print(f"Found existing connection: {conn['connectionId']}")
                break
        
        if not orchestrator_connection:
            # Create new configuration
            print("\nCreating new Airbyte configuration...")
            
            # Create source
            source_id = configurer.create_postgres_source()
            
            # Create destination
            destination_id = configurer.create_weaviate_destination()
            
            # Create connection
            connection_id = configurer.create_connection(source_id, destination_id)
            
            # Create schedule
            configurer.create_sync_schedule(connection_id)
            
            # Test connection
            configurer.test_connection(connection_id)
        else:
            print("\nConnection already exists, testing...")
            configurer.test_connection(orchestrator_connection['connectionId'])
        
        print("\n" + "=" * 40)
        print("✓ Airbyte configuration completed successfully!")
        
        # Save configuration
        config_data = {
            "workspace_id": configurer.workspace_id,
            "connection_id": orchestrator_connection['connectionId'] if orchestrator_connection else connection_id,
            "configured_at": datetime.now().isoformat(),
            "sync_schedule": "0 */6 * * *"
        }
        
        config_path = "ai_components/configs/airbyte_config.json"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        print(f"Configuration saved to {config_path}")
        
    except Exception as e:
        print(f"\nError configuring Airbyte: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()