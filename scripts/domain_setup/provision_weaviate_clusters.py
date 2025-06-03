#!/usr/bin/env python3
"""
Weaviate Cluster Provisioning Script
Automatically creates and configures Weaviate clusters for each domain
"""

import os
import json
import requests
from pathlib import Path

class WeaviateProvisioner:
    def __init__(self):
        self.wcs_api_key = os.getenv("WCS_API_KEY")
        self.wcs_url = "https://console.weaviate.cloud/api/v1"
        self.config_dir = Path("config/domains")
        
    def create_cluster(self, domain_config):
        """Create a Weaviate cluster via WCS API"""
        
        headers = {
            "Authorization": f"Bearer {self.wcs_api_key}",
            "Content-Type": "application/json"
        }
        
        cluster_data = {
            "name": domain_config["cluster_name"],
            "tier": "sandbox",  # Change to production tier as needed
            "modules": [
                "text2vec-openai",
                "generative-openai"
            ],
            "authentication": {
                "enabled": True,
                "apiKey": {
                    "enabled": True,
                    "allowedKeys": []
                }
            }
        }
        
        response = requests.post(
            f"{self.wcs_url}/clusters",
            headers=headers,
            json=cluster_data
        )
        
        if response.status_code == 201:
            cluster_info = response.json()
            print(f"✅ Created cluster: {cluster_info['name']}")
            return cluster_info
        else:
            print(f"❌ Failed to create cluster: {response.text}")
            return None
    
    def configure_collections(self, cluster_url, collections_config):
        """Configure collections in the Weaviate cluster"""
        
        headers = {
            "Content-Type": "application/json"
        }
        
        for collection_name, collection_config in collections_config.items():
            schema = {
                "class": collection_name,
                "description": collection_config["description"],
                "vectorizer": collection_config["vectorizer"],
                "properties": collection_config["properties"]
            }
            
            response = requests.post(
                f"{cluster_url}/v1/schema",
                headers=headers,
                json=schema
            )
            
            if response.status_code == 200:
                print(f"  ✅ Created collection: {collection_name}")
            else:
                print(f"  ❌ Failed to create collection: {response.text}")
    
    def provision_all_domains(self):
        """Provision clusters for all domains"""
        
        for config_file in self.config_dir.glob("*_weaviate.json"):
            with open(config_file) as f:
                config = json.load(f)
            
            print(f"\nProvisioning {config['domain']} domain...")
            
            # Create cluster
            cluster_info = self.create_cluster(config)
            
            if cluster_info:
                # Wait for cluster to be ready
                print("  ⏳ Waiting for cluster to be ready...")
                # In production, implement proper polling
                
                # Configure collections
                cluster_url = cluster_info["url"]
                self.configure_collections(cluster_url, config["collections"])
                
                # Update config with cluster URL
                config["cluster_url"] = cluster_url
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)

if __name__ == "__main__":
    provisioner = WeaviateProvisioner()
    provisioner.provision_all_domains()
