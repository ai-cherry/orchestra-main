#!/usr/bin/env python3
"""
Test script for the credential management system.

This script tests the credential management system by:
1. Loading credentials from files
2. Securing the credentials
3. Retrieving the credentials
4. Verifying that the credentials are correct

Usage:
    python test_credential_system.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the credential manager
try:
    from core.security.credential_manager import CredentialManager, ServiceAccountInfo
except ImportError:
    print("Error: Could not import CredentialManager. Make sure the core/security directory exists.")
    sys.exit(1)


def print_header(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_success(message):
    """Print a success message."""
    print(f"✅ {message}")


def print_error(message):
    """Print an error message."""
    print(f"❌ {message}")


def print_info(message):
    """Print an info message."""
    print(f"ℹ️ {message}")


def create_test_service_account_key():
    """Create a test service account key file."""
    print_header("Creating Test Service Account Key")
    
    # Create a temporary directory for the test
    temp_dir = tempfile.mkdtemp()
    key_path = os.path.join(temp_dir, "test-service-account-key.json")
    
    # Create a test service account key
    test_key = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-private-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nTEST_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
        "client_email": "test-service-account@test-project.iam.gserviceaccount.com",
        "client_id": "test-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test-service-account%40test-project.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }
    
    # Write the test key to a file
    with open(key_path, "w") as f:
        json.dump(test_key, f, indent=2)
    
    print_success(f"Created test service account key at {key_path}")
    return key_path, test_key


def test_load_from_file():
    """Test loading credentials from a file."""
    print_header("Testing Loading Credentials from File")
    
    # Create a test service account key
    key_path, test_key = create_test_service_account_key()
    
    # Create a credential manager
    credential_manager = CredentialManager()
    
    # Load the service account key from the file
    success = credential_manager.load_service_account_from_file(key_path)
    
    if success:
        print_success("Successfully loaded service account key from file")
    else:
        print_error("Failed to load service account key from file")
        return False
    
    # Get the service account key
    service_account_info = credential_manager.get_service_account_key()
    
    if service_account_info:
        print_success("Successfully retrieved service account key")
    else:
        print_error("Failed to retrieve service account key")
        return False
    
    # Verify the service account key
    if service_account_info.project_id == test_key["project_id"]:
        print_success("Project ID matches")
    else:
        print_error(f"Project ID mismatch: {service_account_info.project_id} != {test_key['project_id']}")
        return False
    
    if service_account_info.client_email == test_key["client_email"]:
        print_success("Client email matches")
    else:
        print_error(f"Client email mismatch: {service_account_info.client_email} != {test_key['client_email']}")
        return False
    
    if service_account_info.private_key_id == test_key["private_key_id"]:
        print_success("Private key ID matches")
    else:
        print_error(f"Private key ID mismatch: {service_account_info.private_key_id} != {test_key['private_key_id']}")
        return False
    
    # Clean up
    os.remove(key_path)
    os.rmdir(os.path.dirname(key_path))
    
    return True


def test_secure_service_account_key():
    """Test securing a service account key."""
    print_header("Testing Securing Service Account Key")
    
    # Create a test service account key
    key_path, test_key = create_test_service_account_key()
    
    # Create a credential manager
    credential_manager = CredentialManager()
    
    # Secure the service account key
    success = credential_manager.secure_service_account_key(key_path)
    
    if success:
        print_success("Successfully secured service account key")
    else:
        print_error("Failed to secure service account key")
        return False
    
    # Verify that the file has been removed
    if not os.path.exists(key_path):
        print_success("Service account key file has been removed")
    else:
        print_error("Service account key file still exists")
        return False
    
    # Get the service account key
    service_account_info = credential_manager.get_service_account_key()
    
    if service_account_info:
        print_success("Successfully retrieved service account key")
    else:
        print_error("Failed to retrieve service account key")
        return False
    
    # Verify the service account key
    if service_account_info.project_id == test_key["project_id"]:
        print_success("Project ID matches")
    else:
        print_error(f"Project ID mismatch: {service_account_info.project_id} != {test_key['project_id']}")
        return False
    
    # Clean up
    os.rmdir(os.path.dirname(key_path))
    
    return True


def test_get_service_account_key_path():
    """Test getting a path to a service account key file."""
    print_header("Testing Getting Service Account Key Path")
    
    # Create a test service account key
    key_path, test_key = create_test_service_account_key()
    
    # Create a credential manager
    credential_manager = CredentialManager()
    
    # Load the service account key from the file
    success = credential_manager.load_service_account_from_file(key_path)
    
    if success:
        print_success("Successfully loaded service account key from file")
    else:
        print_error("Failed to load service account key from file")
        return False
    
    # Get a path to the service account key
    service_account_path = credential_manager.get_service_account_key_path()
    
    if service_account_path:
        print_success(f"Successfully got service account key path: {service_account_path}")
    else:
        print_error("Failed to get service account key path")
        return False
    
    # Verify that the file exists
    if os.path.exists(service_account_path):
        print_success("Service account key file exists")
    else:
        print_error("Service account key file does not exist")
        return False
    
    # Verify that the file contains the correct data
    try:
        with open(service_account_path, "r") as f:
            key_data = json.load(f)
        
        if key_data["project_id"] == test_key["project_id"]:
            print_success("Project ID matches")
        else:
            print_error(f"Project ID mismatch: {key_data['project_id']} != {test_key['project_id']}")
            return False
        
        print_success("Service account key file contains correct data")
    except Exception as e:
        print_error(f"Failed to read service account key file: {e}")
        return False
    
    # Clean up
    credential_manager.cleanup()
    os.remove(key_path)
    os.rmdir(os.path.dirname(key_path))
    
    # Verify that the temporary file has been removed
    if not os.path.exists(service_account_path):
        print_success("Temporary service account key file has been removed")
    else:
        print_error("Temporary service account key file still exists")
        os.remove(service_account_path)
        return False
    
    return True


def test_get_project_id():
    """Test getting the project ID."""
    print_header("Testing Getting Project ID")
    
    # Create a test service account key
    key_path, test_key = create_test_service_account_key()
    
    # Create a credential manager
    credential_manager = CredentialManager()
    
    # Load the service account key from the file
    success = credential_manager.load_service_account_from_file(key_path)
    
    if success:
        print_success("Successfully loaded service account key from file")
    else:
        print_error("Failed to load service account key from file")
        return False
    
    # Get the project ID
    project_id = credential_manager.get_project_id()
    
    if project_id:
        print_success(f"Successfully got project ID: {project_id}")
    else:
        print_error("Failed to get project ID")
        return False
    
    # Verify the project ID
    if project_id == test_key["project_id"]:
        print_success("Project ID matches")
    else:
        print_error(f"Project ID mismatch: {project_id} != {test_key['project_id']}")
        return False
    
    # Clean up
    os.remove(key_path)
    os.rmdir(os.path.dirname(key_path))
    
    return True


def test_load_from_env():
    """Test loading credentials from environment variables."""
    print_header("Testing Loading Credentials from Environment Variables")
    
    # Create a test service account key
    _, test_key = create_test_service_account_key()
    
    # Set the environment variable
    os.environ["ORCHESTRA_SERVICE_ACCOUNT_JSON"] = json.dumps(test_key)
    
    # Create a credential manager
    credential_manager = CredentialManager()
    
    # Get the service account key
    service_account_info = credential_manager.get_service_account_key()
    
    if service_account_info:
        print_success("Successfully retrieved service account key from environment variable")
    else:
        print_error("Failed to retrieve service account key from environment variable")
        return False
    
    # Verify the service account key
    if service_account_info.project_id == test_key["project_id"]:
        print_success("Project ID matches")
    else:
        print_error(f"Project ID mismatch: {service_account_info.project_id} != {test_key['project_id']}")
        return False
    
    # Clean up
    del os.environ["ORCHESTRA_SERVICE_ACCOUNT_JSON"]
    
    return True


def main():
    """Run the tests."""
    print_header("Testing Credential Management System")
    
    # Run the tests
    tests = [
        test_load_from_file,
        test_secure_service_account_key,
        test_get_service_account_key_path,
        test_get_project_id,
        test_load_from_env,
    ]
    
    success_count = 0
    failure_count = 0
    
    for test in tests:
        if test():
            success_count += 1
        else:
            failure_count += 1
    
    # Print the results
    print_header("Test Results")
    print(f"Total tests: {len(tests)}")
    print(f"Successful tests: {success_count}")
    print(f"Failed tests: {failure_count}")
    
    if failure_count == 0:
        print_success("All tests passed!")
        return 0
    else:
        print_error(f"{failure_count} tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())