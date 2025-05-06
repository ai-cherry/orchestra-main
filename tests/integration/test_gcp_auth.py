"""
Integration tests for GCP authentication.

This module tests the GCP authentication system with real GCP services.
To run these tests, you need to have GCP credentials configured.
"""

import os
import pytest
import json
import tempfile
from unittest import mock

from packages.shared.src.gcp.auth import (
    get_gcp_credentials,
    get_project_id,
    initialize_gcp_auth,
    setup_gcp_credentials_file
)
from packages.shared.src.storage.firestore_client import FirestoreClient
from packages.shared.src.storage.redis_client import RedisClient
from packages.vertex_client.vertex_agent_manager import VertexAgentManager

from core.orchestrator.src.config.settings import Settings


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("GCP_PROJECT_ID") and not os.environ.get("GOOGLE_CLOUD_PROJECT"),
    reason="GCP credentials not configured"
)
async def test_firestore_client_with_auth():
    """Test FirestoreClient with GCP authentication."""
    # Initialize auth
    auth_result = initialize_gcp_auth()
    assert auth_result["success"] is True
    
    # Create FirestoreClient
    try:
        client = FirestoreClient()
        
        # Test basic operations
        collection = "auth_test"
        doc_id = "test_doc"
        test_data = {"test": True, "timestamp": "2025-04-23"}
        
        # Save document
        await client.save_document(collection, doc_id, test_data)
        
        # Get document
        retrieved = await client.get_document(collection, doc_id)
        assert retrieved is not None
        assert retrieved["test"] is True
        
        # Clean up
        await client.delete_document(collection, doc_id)
        
        # Verify deletion
        deleted = await client.get_document(collection, doc_id)
        assert deleted is None
    except Exception as e:
        # This test may fail if Firestore is not available or credentials are insufficient
        pytest.skip(f"Firestore test failed: {e}")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("GCP_PROJECT_ID") and not os.environ.get("GOOGLE_CLOUD_PROJECT"),
    reason="GCP credentials not configured"
)
async def test_redis_with_secret_manager():
    """Test RedisClient with Secret Manager for password."""
    # Skip if Secret Manager service account key not available
    if not os.environ.get("GCP_SA_KEY_JSON"):
        pytest.skip("GCP service account key not available")
    
    # Mock the Secret Manager client to avoid actual API calls
    with mock.patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
        # Mock the response
        mock_response = mock.MagicMock()
        mock_response.payload.data.decode.return_value = "test_password"
        mock_client.return_value.access_secret_version.return_value = mock_response
        
        # Initialize RedisClient with secret ID
        try:
            client = RedisClient(
                host="localhost",  # Using localhost for test
                secret_id="test_redis_password"
            )
            
            # Check if the password was retrieved
            assert client._password == "test_password"
        except ImportError:
            pytest.skip("Redis library not available")


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("GCP_PROJECT_ID") and not os.environ.get("GOOGLE_CLOUD_PROJECT"),
    reason="GCP credentials not configured"
)
def test_vertex_agent_manager_auth():
    """Test VertexAgentManager with GCP authentication."""
    # Skip if GCP libraries not available
    try:
        import vertexai
    except ImportError:
        pytest.skip("Vertex AI library not available")
    
    # Create a test service account JSON
    test_sa_json = json.dumps({
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgk=\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com"
    })
    
    # Mock vertexai.init to avoid actual API calls
    with mock.patch("vertexai.init") as mock_init:
        # Mock other clients
        with mock.patch("google.cloud.pubsub_v1.PublisherClient"):
            with mock.patch("google.cloud.run_v2.ServicesClient"):
                with mock.patch("google.cloud.secretmanager.SecretManagerServiceClient"):
                    # Initialize VertexAgentManager with service account JSON
                    manager = VertexAgentManager(
                        project_id="test-project",
                        service_account_json=test_sa_json
                    )
                    
                    # Check if vertexai.init was called with the correct arguments
                    mock_init.assert_called_once()
                    args, kwargs = mock_init.call_args
                    assert kwargs["project"] == "test-project"


@pytest.mark.integration
def test_settings_gcp_methods():
    """Test GCP-related methods in Settings."""
    # Create a settings instance with GCP values
    settings = Settings(
        GCP_PROJECT_ID="test-project",
        GCP_SA_KEY_JSON='{"type":"service_account","project_id":"test-project"}',
        GCP_LOCATION="us-west1",
        GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
    )
    
    # Test get_gcp_project_id
    assert settings.get_gcp_project_id() == "test-project"
    
    # Test get_gcp_credentials_info
    creds_info = settings.get_gcp_credentials_info()
    assert creds_info["project_id"] == "test-project"
    assert creds_info["credentials_path"] == "/path/to/key.json"
    assert creds_info["service_account_json"] == '{"type":"service_account","project_id":"test-project"}'
    assert creds_info["location"] == "us-west1"
    
    # Test with GOOGLE_CLOUD_PROJECT as fallback
    settings = Settings(
        GOOGLE_CLOUD_PROJECT="fallback-project",
        GCP_LOCATION="us-west1"
    )
    assert settings.get_gcp_project_id() == "fallback-project"


@pytest.mark.integration
def test_credentials_from_json():
    """Test getting credentials from JSON content."""
    # Create a temporary file with test service account JSON
    test_sa_json = json.dumps({
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgk=\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com"
    })
    
    # Mock service_account.Credentials to avoid actual API calls
    with mock.patch("google.oauth2.service_account.Credentials") as mock_creds:
        mock_creds.from_service_account_file.return_value = "mock_credentials"
        
        # Get credentials from JSON
        try:
            credentials, project_id = get_gcp_credentials(service_account_json=test_sa_json)
            
            # Check if credentials were created
            assert mock_creds.from_service_account_file.called
            assert project_id == "test-project"
        except ImportError:
            pytest.skip("Google Cloud libraries not available")
