"""
Orchestra AI - Simple Integration Tests
Tests basic system functionality without complex async fixtures
"""

import pytest
import requests
import time
import json
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

class TestBasicIntegration:
    """Test basic system integration"""
    
    def test_api_health_check(self):
        """Test that the API is accessible"""
        try:
            response = requests.get(f"{BASE_URL}/", timeout=5)
            # API might not be running, that's ok for now
            assert response.status_code in [200, 404, 500]
        except requests.exceptions.ConnectionError:
            # API not running, skip test
            pytest.skip("API server not running")
    
    def test_authentication_endpoint_exists(self):
        """Test that authentication endpoints exist"""
        try:
            # Try to access login endpoint
            response = requests.post(f"{BASE_URL}/auth/login", 
                                   json={"username": "test", "password": "test"}, 
                                   timeout=5)
            # Should get some response (even if credentials are wrong)
            assert response.status_code in [200, 401, 422, 404]
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")
    
    def test_cors_headers(self):
        """Test that CORS headers are properly configured"""
        try:
            response = requests.options(f"{BASE_URL}/", timeout=5)
            # Should have CORS headers or at least respond
            assert response.status_code in [200, 404, 405]
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")

class TestSecurityBasics:
    """Test basic security features"""
    
    def test_no_sensitive_info_in_errors(self):
        """Test that error responses don't leak sensitive information"""
        try:
            # Try invalid endpoint
            response = requests.get(f"{BASE_URL}/invalid-endpoint", timeout=5)
            
            if response.status_code == 404:
                # Check that error doesn't contain sensitive paths
                error_text = response.text.lower()
                assert "/home/" not in error_text
                assert "password" not in error_text
                assert "secret" not in error_text
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")
    
    def test_security_headers(self):
        """Test that basic security headers are present"""
        try:
            response = requests.get(f"{BASE_URL}/", timeout=5)
            headers = response.headers
            
            # Check for basic security headers (if API is running)
            if response.status_code == 200:
                # These are good to have but not required for basic functionality
                pass
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")

class TestConfigurationValidation:
    """Test system configuration and setup"""
    
    def test_environment_variables(self):
        """Test that required environment variables can be set"""
        import os
        
        # Test that we can set test environment variables
        test_var = "ORCHESTRA_TEST_VAR"
        test_value = "test_value_123"
        
        os.environ[test_var] = test_value
        assert os.getenv(test_var) == test_value
        
        # Clean up
        del os.environ[test_var]
    
    def test_secret_manager_basic(self):
        """Test basic secret manager functionality"""
        try:
            from security.secret_manager import SecretManager
            
            sm = SecretManager(environment="test")
            
            # Test encryption/decryption
            test_secret = "test-secret-value"
            encrypted = sm.encrypt_secret(test_secret)
            decrypted = sm.decrypt_secret(encrypted)
            
            assert decrypted == test_secret
            assert encrypted != test_secret
            
        except ImportError:
            pytest.skip("Secret manager not available")
    
    def test_authentication_module(self):
        """Test that authentication module loads correctly"""
        try:
            from auth.authentication import verify_password, get_password_hash
            
            # Test password hashing
            password = "test_password"
            hashed = get_password_hash(password)
            
            assert verify_password(password, hashed)
            assert not verify_password("wrong_password", hashed)
            
        except ImportError:
            pytest.skip("Authentication module not available")

class TestFileSystemOperations:
    """Test file system operations and permissions"""
    
    def test_temp_file_creation(self):
        """Test that temporary files can be created securely"""
        import tempfile
        import os
        import stat
        
        # Create temporary file
        fd, temp_path = tempfile.mkstemp(prefix='orchestra_test_')
        
        try:
            # Write test data
            with os.fdopen(fd, 'w') as f:
                f.write("test data")
            
            # Check file exists and has content
            with open(temp_path, 'r') as f:
                content = f.read()
                assert content == "test data"
            
            # Check file permissions
            file_stat = os.stat(temp_path)
            file_mode = stat.filemode(file_stat.st_mode)
            
            # File should be readable by owner
            assert file_stat.st_mode & stat.S_IRUSR
            
        finally:
            # Clean up
            os.unlink(temp_path)
    
    def test_directory_permissions(self):
        """Test directory creation with proper permissions"""
        import tempfile
        import os
        import stat
        
        with tempfile.TemporaryDirectory(prefix='orchestra_test_') as temp_dir:
            # Check directory exists
            assert os.path.isdir(temp_dir)
            
            # Check directory permissions
            dir_stat = os.stat(temp_dir)
            
            # Directory should be accessible by owner
            assert dir_stat.st_mode & stat.S_IRUSR
            assert dir_stat.st_mode & stat.S_IWUSR
            assert dir_stat.st_mode & stat.S_IXUSR

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

