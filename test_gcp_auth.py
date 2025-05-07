#!/usr/bin/env python3
"""
Simple test script to diagnose GCP authentication issues.
"""

import os
import sys
import json
import logging
from google.cloud import firestore
from google.oauth2 import service_account

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('gcp_auth_test')

def test_service_account_key(key_path):
    """Test if the service account key file can be properly parsed."""
    try:
        with open(key_path, 'r') as f:
            key_data = json.load(f)
            logger.info(f"Successfully parsed key file: {key_path}")
            logger.info(f"Key type: {key_data.get('type')}")
            logger.info(f"Project ID: {key_data.get('project_id')}")
            logger.info(f"Client email: {key_data.get('client_email')}")
            return key_data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse key file as JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading key file: {e}")
        return None

def test_auth_with_credentials_object(key_data):
    """Test authentication using a credentials object created from key data."""
    try:
        # Create credentials object from key data
        credentials = service_account.Credentials.from_service_account_info(
            key_data,
            scopes=["https://www.googleapis.com/auth/datastore"]
        )
        logger.info("Successfully created credentials object")
        
        # Create a Firestore client with these credentials
        project_id = key_data.get('project_id')
        db = firestore.Client(project=project_id, credentials=credentials)
        logger.info(f"Successfully created Firestore client for project: {project_id}")
        
        # List collections to test connectivity
        collections = list(db.collections())
        logger.info(f"Successfully listed {len(collections)} collections")
        for i, collection in enumerate(collections):
            logger.info(f"Collection {i+1}: {collection.id}")
        
        return True
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return False

def test_auth_with_key_path(key_path):
    """Test authentication directly using the key file path."""
    try:
        # Create a Firestore client with the key file
        project_id = os.environ.get('GCP_PROJECT_ID', 'cherry-ai-project')
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_path
        
        db = firestore.Client(project=project_id)
        logger.info(f"Successfully created Firestore client for project: {project_id}")
        
        # List collections to test connectivity
        collections = list(db.collections())
        logger.info(f"Successfully listed {len(collections)} collections")
        for i, collection in enumerate(collections):
            logger.info(f"Collection {i+1}: {collection.id}")
        
        return True
    except Exception as e:
        logger.error(f"Authentication failed with key path: {e}")
        return False

def main():
    """Main entry point."""
    # Check for environment variables
    key_path = os.environ.get('GCP_SA_KEY_PATH', '/tmp/vertex-agent-key.json')
    project_id = os.environ.get('GCP_PROJECT_ID', 'cherry-ai-project')
    
    logger.info(f"Testing GCP authentication with key path: {key_path}")
    logger.info(f"Project ID: {project_id}")
    
    # Test reading and parsing the key file
    key_data = test_service_account_key(key_path)
    if not key_data:
        logger.error("Failed to read/parse service account key file")
        sys.exit(1)
    
    # Test authentication using the credentials object
    logger.info("\nTesting authentication with credentials object...")
    success1 = test_auth_with_credentials_object(key_data)
    
    # Test authentication using the key file path
    logger.info("\nTesting authentication with key file path...")
    success2 = test_auth_with_key_path(key_path)
    
    if success1 and success2:
        logger.info("\n✅ Authentication successful with both methods!")
        sys.exit(0)
    elif success1:
        logger.info("\n⚠️ Authentication successful with credentials object but failed with key path")
        sys.exit(0)
    elif success2:
        logger.info("\n⚠️ Authentication successful with key path but failed with credentials object")
        sys.exit(0)
    else:
        logger.error("\n❌ Authentication failed with both methods")
        sys.exit(1)

if __name__ == "__main__":
    main()
