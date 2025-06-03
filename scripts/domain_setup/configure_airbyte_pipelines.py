#!/usr/bin/env python3
"""
Airbyte Configuration Automation
Sets up domain-specific data pipelines via Airbyte API
"""

import os
import json
import requests
from pathlib import Path

class AirbyteAutomator:
    def __init__(self):
        self.airbyte_url = os.getenv("AIRBYTE_URL", "http://localhost:8000")
        self.airbyte_api = f"{self.airbyte_url}/api/v1"
        self.config_dir = Path("config/domains")
        
    def create_source(self, source_config):
        """Create an Airbyte source"""
        
        endpoint = f"{self.airbyte_api}/sources/create"
        
        source_data = {
            "name": source_config["name"],
            "sourceDefinitionId": self.get_source_definition_id(source_config["type"]),
            "connectionConfiguration": source_config["config"]
        }
        
        response = requests.post(endpoint, json=source_data)
        
        if response.status_code == 200:
            return response.json()["sourceId"]
        else:
            print(f"Failed to create source: {response.text}")
            return None
    
    def create_destination(self, destination_config):
        """Create an Airbyte destination"""
        
        endpoint = f"{self.airbyte_api}/destinations/create"
        
        destination_data = {
            "name": destination_config["name"],
            "destinationDefinitionId": self.get_destination_definition_id(destination_config["type"]),
            "connectionConfiguration": destination_config["config"]
        }
        
        response = requests.post(endpoint, json=destination_data)
        
        if response.status_code == 200:
            return response.json()["destinationId"]
        else:
            print(f"Failed to create destination: {response.text}")
            return None
    
    def create_connection(self, connection_config, source_id, destination_id):
        """Create an Airbyte connection"""
        
        endpoint = f"{self.airbyte_api}/connections/create"
        
        connection_data = {
            "name": connection_config["name"],
            "sourceId": source_id,
            "destinationId": destination_id,
            "syncCatalog": {
                "streams": []  # Auto-discover streams
            },
            "schedule": connection_config.get("schedule", {
                "units": 24,
                "timeUnit": "hours"
            }),
            "namespaceDefinition": "customformat",
            "namespaceFormat": connection_config["namespace"]
        }
        
        response = requests.post(endpoint, json=connection_data)
        
        if response.status_code == 200:
            return response.json()["connectionId"]
        else:
            print(f"Failed to create connection: {response.text}")
            return None
    
    def get_source_definition_id(self, source_type):
        """Get source definition ID by type"""
        # In production, fetch from API
        definitions = {
            "postgres": "decd338e-5647-4c0b-adf4-da0e75f5a750",
            "http_api": "68e63de2-bb83-4714-b4c7-6f0b1b5bdc8e"
        }
        return definitions.get(source_type)
    
    def get_destination_definition_id(self, destination_type):
        """Get destination definition ID by type"""
        # In production, fetch from API
        definitions = {
            "postgres": "25c5221d-dce2-4163-ade9-739ef790f503",
            "weaviate": "7b96c012-e2c9-4d3c-b0f3-8b1f4f2e4b5e"
        }
        return definitions.get(destination_type)
    
    def configure_all_domains(self):
        """Configure Airbyte for all domains"""
        
        for config_file in self.config_dir.glob("*_airbyte.json"):
            with open(config_file) as f:
                config = json.load(f)
            
            print(f"\nConfiguring Airbyte for {config['namespace']} domain...")
            
            for connection in config["connections"]:
                # Create source
                source_id = self.create_source({
                    "name": f"{connection['name']}_source",
                    "type": connection["source"]["type"],
                    "config": connection["source"]
                })
                
                # Create destination
                destination_id = self.create_destination({
                    "name": f"{connection['name']}_destination",
                    "type": connection["destination"]["type"],
                    "config": connection["destination"]
                })
                
                # Create connection
                if source_id and destination_id:
                    connection_id = self.create_connection(
                        connection,
                        source_id,
                        destination_id
                    )
                    
                    if connection_id:
                        print(f"  ✅ Created connection: {connection['name']}")
                    else:
                        print(f"  ❌ Failed to create connection: {connection['name']}")

if __name__ == "__main__":
    automator = AirbyteAutomator()
    automator.configure_all_domains()
