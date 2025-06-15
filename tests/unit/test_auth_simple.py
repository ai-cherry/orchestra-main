"""
Orchestra AI - Simplified Authentication Unit Tests
Tests JWT authentication without complex dependencies
"""

import pytest
import os
import sys
from datetime import datetime, timedelta
from jose import jwt

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from auth.authentication import (
    verify_password, 
    get_password_hash, 
    authenticate_user,
    create_access_token,
    SECRET_KEY,
    ALGORITHM
)

class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_password_hashing(self):
        """Test password hashing works correctly"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

    def test_different_passwords_different_hashes(self):
        """Test that same password generates different hashes"""
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

class TestUserAuthentication:
    """Test user authentication logic"""
    
    def test_authenticate_valid_user(self):
        """Test authentication with valid credentials"""
        user = authenticate_user("admin", "admin123")
        assert user is not None
        assert user["username"] == "admin"
        assert user["user_id"] == "admin-001"

    def test_authenticate_invalid_username(self):
        """Test authentication with invalid username"""
        user = authenticate_user("nonexistent", "password")
        assert user is None

    def test_authenticate_invalid_password(self):
        """Test authentication with invalid password"""
        user = authenticate_user("admin", "wrong_password")
        assert user is None

class TestJWTTokens:
    """Test JWT token creation and validation"""
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        data = {"sub": "admin"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "admin"
        assert "exp" in payload

    def test_token_expiration(self):
        """Test token expiration handling"""
        data = {"sub": "admin"}
        expires_delta = timedelta(seconds=1)
        token = create_access_token(data, expires_delta)
        
        # Token should be valid immediately
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "admin"
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Token should be expired
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

class TestSecurityFeatures:
    """Test security features and edge cases"""
    
    def test_secret_key_exists(self):
        """Test that secret key is configured"""
        assert SECRET_KEY is not None
        assert len(SECRET_KEY) > 0
        assert SECRET_KEY != "your-secret-key-change-in-production"

    def test_algorithm_is_secure(self):
        """Test that secure algorithm is used"""
        assert ALGORITHM == "HS256"

    def test_token_structure(self):
        """Test JWT token structure"""
        data = {"sub": "test_user"}
        token = create_access_token(data)
        
        # JWT tokens have 3 parts separated by dots
        parts = token.split('.')
        assert len(parts) == 3
        
        # Each part should be base64 encoded
        for part in parts:
            assert len(part) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

