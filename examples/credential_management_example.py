#!/usr/bin/env python3
"""
Example script demonstrating how to use the AI Orchestra credential management system.

This script shows how to:
1. Access secrets from Secret Manager
2. Use service account credentials for GCP services
3. Integrate with FastAPI
4. Handle credential rotation

Usage:
    python credential_management_example.py

Requirements:
    - google-cloud-secret-manager
    - google-cloud-mongodb
    - google-cloud-aiplatform
    - fastapi
    - redis
"""

import asyncio
import json
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import the credential manager
from core.security.credential_manager import get_credential_manager

async def example_basic_usage():
    """Example of basic credential manager usage."""
    print("\n=== Basic Usage Example ===")

    # Get the credential manager
    credential_manager = get_credential_manager()

    # Get a secret
    try:
        # Note: This will fail if the secret doesn't exist
        api_key = credential_manager.get_secret("example-api-key")
        print(f"API Key: {api_key[:5]}...")  # Only show first 5 chars for security
    except Exception as e:
        print(f"Error getting secret: {str(e)}")
        print("Creating a mock secret for demonstration purposes...")
        api_key = "mock-api-key-12345"

    # Get a JSON secret
    try:
        # Note: This will fail if the secret doesn't exist
        config = credential_manager.get_json_secret("example-config")
        print(f"Config: {json.dumps(config, indent=2)}")
    except Exception as e:
        print(f"Error getting JSON secret: {str(e)}")
        print("Creating a mock config for demonstration purposes...")
        config = {
            "endpoint": "https://api.example.com",
            "timeout": 30,
            "retry_count": 3,
        }

    # Use the credentials
    print(f"\nUsing API key to make a request to {config.get('endpoint', 'https://api.example.com')}")
    print(f"Request headers: Authorization: Bearer {api_key[:3]}...")
    print(f"Request timeout: {config.get('timeout', 30)} seconds")
    print(f"Request retry count: {config.get('retry_count', 3)}")

    return api_key, config

async def example_gcp_services():
    """Example of using credentials with GCP services."""
    print("\n=== GCP Services Example ===")

    # Get the credential manager
    credential_manager = get_credential_manager()

    # Get service account credentials
    try:
        # Note: This will fail if the service account key doesn't exist
        vertex_credentials = credential_manager.get_service_account_key("vertex-ai-agent")
        print(f"Vertex AI Credentials: {vertex_credentials['client_email']}")
    except Exception as e:
        print(f"Error getting service account key: {str(e)}")
        print("Creating mock credentials for demonstration purposes...")
        vertex_credentials = {
            "type": "service_account",
            "project_id": "cherry-ai-project",
            "client_email": "vertex-ai-agent@cherry-ai-project.iam.gserviceaccount.com",
        }

    # Use the credentials with Vertex AI
    print("\nInitializing Vertex AI with credentials...")
    print(f"Project ID: {vertex_credentials.get('project_id', 'cherry-ai-project')}")
    print(
        f"Service Account: {vertex_credentials.get('client_email', 'vertex-ai-agent@cherry-ai-project.iam.gserviceaccount.com')}"
    )

    # This is just a demonstration - in a real application, you would do:
    #     # aiplatform.init(
    #     project=vertex_credentials["project_id"],
    #     location="us-central1",
    #     credentials=vertex_credentials
    # )

    return vertex_credentials

async def example_memory_system():
    """Example of using credentials with the memory system."""
    print("\n=== Memory System Example ===")

    # Get the credential manager
    credential_manager = get_credential_manager()

    # Get Redis credentials
    try:
        # Note: These will fail if the secrets don't exist
        redis_host = credential_manager.get_secret("redis-host")
        redis_port = credential_manager.get_secret("redis-port")
        redis_password = credential_manager.get_secret("redis-password")

        print(f"Redis Host: {redis_host}")
        print(f"Redis Port: {redis_port}")
        print(f"Redis Password: {'*' * len(redis_password)}")  # Don't print actual password
    except Exception as e:
        print(f"Error getting Redis credentials: {str(e)}")
        print("Creating mock Redis credentials for demonstration purposes...")
        redis_host = "redis-12345.c123.us-central1-1.gce.cloud.redislabs.com"
        redis_port = "12345"
        redis_password = "mock-password"

    # Get mongodb credentials
    try:
        # Note: This will fail if the service account key doesn't exist
        firestore_credentials = credential_manager.get_service_account_key("memory-system")
        print(f"\nFirestore Credentials: {firestore_credentials['client_email']}")
    except Exception as e:
        print(f"\nError getting mongodb credentials: {str(e)}")
        print("Creating mock mongodb credentials for demonstration purposes...")
        firestore_credentials = {
            "type": "service_account",
            "project_id": "cherry-ai-project",
            "client_email": "memory-system@cherry-ai-project.iam.gserviceaccount.com",
        }

    # Use the credentials with Redis
    print("\nConnecting to Redis...")
    print(f"Redis URI: redis://:{redis_password[:3]}...@{redis_host}:{redis_port}")

    # This is just a demonstration - in a real application, you would do:
    # import redis
    # r = redis.Redis(
    #     host=redis_host,
    #     port=int(redis_port),
    #     password=redis_password,
    #     ssl=True
    # )
    # r.set("test_key", "test_value")

    # Use the credentials with mongodb
    print("\nConnecting to mongodb...")
    print(f"Project ID: {firestore_credentials.get('project_id', 'cherry-ai-project')}")
    print(
        f"Service Account: {firestore_credentials.get('client_email', 'memory-system@cherry-ai-project.iam.gserviceaccount.com')}"
    )

    # This is just a demonstration - in a real application, you would do:
    #     # db = mongodb.Client(
    #     project=firestore_credentials["project_id"],
    #     credentials=firestore_credentials
    # )
    # doc_ref = db.collection("test").document("test_doc")
    # doc_ref.set({"test_field": "test_value"})

    return {
        "redis": {"host": redis_host, "port": redis_port, "password": redis_password},
        "mongodb": firestore_credentials,
    }

async def example_fastapi_integration():
    """Example of integrating with FastAPI."""
    print("\n=== FastAPI Integration Example ===")

    # This is just a demonstration of how the FastAPI integration would work
    print("In a FastAPI application, you would use the dependencies like this:")
    print("\nfrom fastapi import Depends, FastAPI")
    print("from core.orchestrator.src.api.dependencies.credentials import (")
    print("    get_openai_credentials,")
    print("    get_gemini_credentials,")
    print("    get_redis_credentials,")
    print(")")
    print("\napp = FastAPI()")
    print("\n@app.post('/vertex/predict')")
    print("async def predict(")
    print("    request: PredictRequest,")
    print("    credentials: dict = Depends(get_openai_credentials)")
    print("):")
    print("    # Initialize Vertex AI with credentials")
    print("    aiplatform.init(")
    print("        project=credentials['project_id'],")
    print("        location='us-central1',")
    print("        credentials=credentials")
    print("    )")
    print("    # Use Vertex AI...")
    print("    return {'prediction': 'result'}")

async def example_credential_rotation():
    """Example of handling credential rotation."""
    print("\n=== Credential Rotation Example ===")

    # Get the credential manager
    credential_manager = get_credential_manager()

    print("When credentials are rotated, the credential manager automatically picks up the new credentials.")
    print("This is because it always fetches the latest version from Secret Manager.")

    print("\nSimulating credential rotation...")
    print("1. First access (original credential):")

    # Clear the cache to simulate a fresh access
    credential_manager._cache.clear()

    # Get a secret (this will be cached)
    try:
        # Note: This will fail if the secret doesn't exist
        api_key = credential_manager.get_secret("example-api-key")
        print(f"   API Key: {api_key[:5]}...")  # Only show first 5 chars for security
    except Exception as e:
        print(f"   Error getting secret: {str(e)}")
        print("   Creating a mock secret for demonstration purposes...")
        api_key = "mock-api-key-12345"

    print("\n2. Second access (cached credential):")
    try:
        # This should use the cached value
        api_key = credential_manager.get_secret("example-api-key")
        print(f"   API Key: {api_key[:5]}...")
    except Exception as e:
        print(f"   Error getting secret: {str(e)}")
        api_key = "mock-api-key-12345"

    print("\n3. After rotation (new credential):")
    # Clear the cache to simulate credential rotation
    credential_manager._cache.clear()

    # In a real scenario, the credential would have been rotated in Secret Manager
    # Here we're just simulating by clearing the cache
    try:
        # This should fetch the new value
        api_key = credential_manager.get_secret("example-api-key")
        print(f"   API Key: {api_key[:5]}...")
    except Exception as e:
        print(f"   Error getting secret: {str(e)}")
        api_key = "mock-api-key-67890"  # Simulate a new key
        print(f"   API Key: {api_key[:5]}...")

    print(
        "\nIn a production environment, credentials are automatically rotated using Cloud Scheduler and Cloud Functions."
    )
    print("The rotation schedule is defined in the Pulumi configuration.")

async def main():
    """Main function to run all examples."""
    print("AI Orchestra Credential Management System Examples")
    print("================================================")

    # Run the examples
    await example_basic_usage()
    await example_gcp_services()
    await example_memory_system()
    await example_fastapi_integration()
    await example_credential_rotation()

    print("\nAll examples completed successfully!")

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
