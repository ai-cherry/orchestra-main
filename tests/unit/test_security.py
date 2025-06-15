"""
Orchestra AI - Security Manager Unit Tests
Tests the secure secret management system
"""

import pytest
import os
import tempfile
import json
from pathlib import Path

# Add the project root to Python path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from security.secret_manager import SecretManager

class TestSecretManager:
    """Test secret management functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.test_env = "test"
        self.secret_manager = SecretManager(environment=self.test_env)
        
    def teardown_method(self):
        """Clean up test files"""
        secrets_file = Path(f".secrets.{self.test_env}.json")
        if secrets_file.exists():
            secrets_file.unlink()
    
    def test_encrypt_decrypt_secret(self):
        """Test secret encryption and decryption"""
        original_value = "test-secret-value-123"
        
        # Encrypt
        encrypted = self.secret_manager.encrypt_secret(original_value)
        assert encrypted != original_value
        assert len(encrypted) > 0
        
        # Decrypt
        decrypted = self.secret_manager.decrypt_secret(encrypted)
        assert decrypted == original_value
    
    def test_set_and_get_local_secret(self):
        """Test storing and retrieving local secrets"""
        key = "TEST_SECRET"
        value = "test-secret-value"
        
        # Store secret
        self.secret_manager.set_local_secret(key, value)
        
        # Retrieve secret
        retrieved = self.secret_manager.get_secret(key)
        assert retrieved == value
    
    def test_secret_file_permissions(self):
        """Test that secret files have secure permissions"""
        key = "PERMISSION_TEST"
        value = "test-value"
        
        self.secret_manager.set_local_secret(key, value)
        
        secrets_file = Path(f".secrets.{self.test_env}.json")
        assert secrets_file.exists()
        
        # Check file permissions (should be 600 - owner read/write only)
        file_mode = secrets_file.stat().st_mode & 0o777
        assert file_mode == 0o600
    
    def test_secret_not_found(self):
        """Test behavior when secret doesn't exist"""
        result = self.secret_manager.get_secret("NONEXISTENT_SECRET")
        assert result is None
    
    def test_secret_with_default(self):
        """Test getting secret with default value"""
        default_value = "default-value"
        result = self.secret_manager.get_secret("NONEXISTENT_SECRET", default_value)
        assert result == default_value
    
    def test_validate_secrets(self):
        """Test secret validation functionality"""
        # This will show missing secrets
        validation_results = self.secret_manager.validate_secrets()
        
        assert isinstance(validation_results, dict)
        assert "LAMBDA_API_KEY" in validation_results
        assert "GITHUB_TOKEN" in validation_results
        
        # Most secrets should be missing in test environment
        assert not all(validation_results.values())

class TestSecretEncryption:
    """Test encryption functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.secret_manager = SecretManager(environment="test")
    
    def test_encryption_key_generation(self):
        """Test encryption key generation"""
        key1 = self.secret_manager._get_encryption_key()
        key2 = self.secret_manager._get_encryption_key()
        
        # Should return same key when called multiple times
        assert key1 == key2
        assert len(key1) > 0
    
    def test_different_values_different_encryption(self):
        """Test that different values produce different encrypted results"""
        value1 = "secret1"
        value2 = "secret2"
        
        encrypted1 = self.secret_manager.encrypt_secret(value1)
        encrypted2 = self.secret_manager.encrypt_secret(value2)
        
        assert encrypted1 != encrypted2
        
        # But they should decrypt correctly
        assert self.secret_manager.decrypt_secret(encrypted1) == value1
        assert self.secret_manager.decrypt_secret(encrypted2) == value2
    
    def test_same_value_different_encryption(self):
        """Test that same value can produce different encrypted results"""
        value = "same-secret"
        
        encrypted1 = self.secret_manager.encrypt_secret(value)
        encrypted2 = self.secret_manager.encrypt_secret(value)
        
        # Encrypted values might be different due to random IV
        # But both should decrypt to the same value
        assert self.secret_manager.decrypt_secret(encrypted1) == value
        assert self.secret_manager.decrypt_secret(encrypted2) == value

class TestEnvironmentSecrets:
    """Test environment-based secret handling"""
    
    def test_environment_variable_secrets(self):
        """Test getting secrets from environment variables"""
        secret_manager = SecretManager()
        
        # Set a test environment variable
        test_key = "TEST_ENV_SECRET"
        test_value = "env-secret-value"
        os.environ[test_key] = test_value
        
        try:
            # Should retrieve from environment
            result = secret_manager.get_secret(test_key)
            assert result == test_value
        finally:
            # Clean up
            del os.environ[test_key]
    
    def test_secret_priority(self):
        """Test secret source priority (env > local > default)"""
        secret_manager = SecretManager(environment="test")
        
        key = "PRIORITY_TEST"
        env_value = "env-value"
        local_value = "local-value"
        default_value = "default-value"
        
        # Test with only default
        result = secret_manager.get_secret(key, default_value)
        assert result == default_value
        
        # Add local secret
        secret_manager.set_local_secret(key, local_value)
        # Clear cache to test fresh lookup
        secret_manager.secrets_cache.clear()
        result = secret_manager.get_secret(key, default_value)
        assert result == local_value
        
        # Add environment variable (should override local)
        os.environ[key] = env_value
        try:
            # Clear cache to test fresh lookup
            secret_manager.secrets_cache.clear()
            result = secret_manager.get_secret(key, default_value)
            assert result == env_value
        finally:
            del os.environ[key]
            # Clean up local secret file
            secrets_file = Path(f".secrets.test.json")
            if secrets_file.exists():
                secrets_file.unlink()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

