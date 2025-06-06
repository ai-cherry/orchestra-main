#!/usr/bin/env python3
"""
Pinecone Setup Automation
"""

import os
import json
from pathlib import Path

def setup_pinecone_config():
    """Setup Pinecone configuration"""
    
    config = {
        "api_key": os.getenv("PINECONE_API_KEY", ""),
        "environment": os.getenv("PINECONE_ENV", "us-west1-gcp"),
        "indexes": {
            "vectors": {
                "dimension": 1536,
                "metric": "cosine",
                "pods": 1,
                "replicas": 1
            },
            "agent_memory": {
                "dimension": 768,
                "metric": "euclidean",
                "pods": 1,
                "replicas": 1
            }
        }
    }
    
    # Save configuration
    config_path = Path("config/pinecone_config.json")
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Pinecone configuration saved to {config_path}")
    
    # Create environment template
    env_template = """# Pinecone Configuration
PINECONE_API_KEY=your_api_key_here
PINECONE_ENV=us-west1-gcp

# Vector Database Selection
VECTOR_DB_PRIMARY=pinecone
VECTOR_DB_SECONDARY=weaviate
"""
    
    with open(".env.template", 'w') as f:
        f.write(env_template)
    
    print("Environment template created: .env.template")

if __name__ == "__main__":
    setup_pinecone_config()
