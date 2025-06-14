"""
Orchestra AI - Unified Secret Management System
Centralized, secure secret handling across all components
"""

import os
import json
import base64
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import structlog

logger = structlog.get_logger(__name__)

class SecretManager:
    """Unified secret management for Orchestra AI"""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.secrets_cache: Dict[str, Any] = {}
        self._encryption_key = None
        
    def _get_encryption_key(self) -> bytes:
        """Generate or retrieve encryption key"""
        if self._encryption_key:
            return self._encryption_key
            
        # Use environment-specific salt
        salt = f"orchestra-ai-{self.environment}".encode()
        
        # Get master password from environment or generate
        master_password = os.getenv('ORCHESTRA_MASTER_KEY', 'default-key-change-me').encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        self._encryption_key = base64.urlsafe_b64encode(kdf.derive(master_password))
        return self._encryption_key
    
    def encrypt_secret(self, value: str) -> str:
        """Encrypt a secret value"""
        try:
            f = Fernet(self._get_encryption_key())
            encrypted = f.encrypt(value.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error("Failed to encrypt secret", error=str(e))
            raise
    
    def decrypt_secret(self, encrypted_value: str) -> str:
        """Decrypt a secret value"""
        try:
            f = Fernet(self._get_encryption_key())
            decoded = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = f.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error("Failed to decrypt secret", error=str(e))
            raise
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from various sources in priority order"""
        
        # 1. Check cache first
        if key in self.secrets_cache:
            return self.secrets_cache[key]
        
        # 2. Check environment variables
        env_value = os.getenv(key)
        if env_value:
            self.secrets_cache[key] = env_value
            return env_value
        
        # 3. Check Pulumi config (if available)
        pulumi_value = self._get_pulumi_secret(key)
        if pulumi_value:
            self.secrets_cache[key] = pulumi_value
            return pulumi_value
        
        # 4. Check GitHub Secrets (in CI/CD context)
        github_value = self._get_github_secret(key)
        if github_value:
            self.secrets_cache[key] = github_value
            return github_value
        
        # 5. Check local encrypted secrets file
        local_value = self._get_local_secret(key)
        if local_value:
            self.secrets_cache[key] = local_value
            return local_value
        
        # 6. Return default if provided
        if default is not None:
            logger.warning(f"Using default value for secret: {key}")
            return default
        
        logger.error(f"Secret not found: {key}")
        return None
    
    def _get_pulumi_secret(self, key: str) -> Optional[str]:
        """Get secret from Pulumi config"""
        try:
            import pulumi
            config = pulumi.Config()
            return config.get_secret(key)
        except:
            return None
    
    def _get_github_secret(self, key: str) -> Optional[str]:
        """Get secret from GitHub Actions environment"""
        # GitHub Actions sets secrets as environment variables
        return os.getenv(key)
    
    def _get_local_secret(self, key: str) -> Optional[str]:
        """Get secret from local encrypted file"""
        try:
            secrets_file = Path(f".secrets.{self.environment}.json")
            if not secrets_file.exists():
                return None
                
            with open(secrets_file, 'r') as f:
                encrypted_secrets = json.load(f)
            
            if key in encrypted_secrets:
                return self.decrypt_secret(encrypted_secrets[key])
                
        except Exception as e:
            logger.error(f"Failed to read local secret {key}", error=str(e))
        
        return None
    
    def set_local_secret(self, key: str, value: str):
        """Store secret in local encrypted file"""
        try:
            secrets_file = Path(f".secrets.{self.environment}.json")
            
            # Load existing secrets
            encrypted_secrets = {}
            if secrets_file.exists():
                with open(secrets_file, 'r') as f:
                    encrypted_secrets = json.load(f)
            
            # Encrypt and store new secret
            encrypted_secrets[key] = self.encrypt_secret(value)
            
            # Write back to file
            with open(secrets_file, 'w') as f:
                json.dump(encrypted_secrets, f, indent=2)
            
            # Set restrictive permissions
            secrets_file.chmod(0o600)
            
            # Update cache
            self.secrets_cache[key] = value
            
            logger.info(f"Secret stored locally: {key}")
            
        except Exception as e:
            logger.error(f"Failed to store local secret {key}", error=str(e))
            raise
    
    def validate_secrets(self) -> Dict[str, bool]:
        """Validate all required secrets are available"""
        required_secrets = [
            "LAMBDA_API_KEY",
            "GITHUB_TOKEN", 
            "VERCEL_TOKEN",
            "DATABASE_URL",
            "REDIS_URL"
        ]
        
        validation_results = {}
        
        for secret in required_secrets:
            value = self.get_secret(secret)
            validation_results[secret] = value is not None and len(value) > 0
            
            if not validation_results[secret]:
                logger.error(f"Required secret missing or empty: {secret}")
        
        return validation_results
    
    def rotate_secret(self, key: str, new_value: str):
        """Rotate a secret value"""
        try:
            # Store old value for rollback
            old_value = self.get_secret(key)
            
            # Update with new value
            self.set_local_secret(f"{key}_OLD", old_value) if old_value else None
            self.set_local_secret(key, new_value)
            
            # Clear cache to force reload
            if key in self.secrets_cache:
                del self.secrets_cache[key]
            
            logger.info(f"Secret rotated: {key}")
            
        except Exception as e:
            logger.error(f"Failed to rotate secret {key}", error=str(e))
            raise
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration with secrets"""
        return {
            "DATABASE_URL": self.get_secret("DATABASE_URL", 
                f"postgresql://orchestra:{self.get_secret('DB_PASSWORD', 'orchestra_secure_2024')}@postgres:5432/orchestra_ai"),
            "REDIS_URL": self.get_secret("REDIS_URL", "redis://redis:6379"),
            "WEAVIATE_URL": self.get_secret("WEAVIATE_URL", "http://weaviate:8080"),
            "WEAVIATE_API_KEY": self.get_secret("WEAVIATE_API_KEY")
        }
    
    def get_api_config(self) -> Dict[str, str]:
        """Get API configuration with secrets"""
        return {
            "LAMBDA_API_KEY": self.get_secret("LAMBDA_API_KEY"),
            "GITHUB_TOKEN": self.get_secret("GITHUB_TOKEN"),
            "VERCEL_TOKEN": self.get_secret("VERCEL_TOKEN"),
            "OPENAI_API_KEY": self.get_secret("OPENAI_API_KEY"),
            "ANTHROPIC_API_KEY": self.get_secret("ANTHROPIC_API_KEY")
        }
    
    def get_deployment_config(self) -> Dict[str, str]:
        """Get deployment configuration with secrets"""
        return {
            "SSH_PRIVATE_KEY": self.get_secret("SSH_PRIVATE_KEY"),
            "SSH_PUBLIC_KEY": self.get_secret("SSH_PUBLIC_KEY"),
            "VERCEL_ORG_ID": self.get_secret("VERCEL_ORG_ID"),
            "VERCEL_PROJECT_ID": self.get_secret("VERCEL_PROJECT_ID")
        }

# Global secret manager instance
secret_manager = SecretManager(
    environment=os.getenv("ENVIRONMENT", "production")
)

# Convenience functions for common use cases
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a secret value"""
    return secret_manager.get_secret(key, default)

def get_database_url() -> str:
    """Get database URL with credentials"""
    return secret_manager.get_database_config()["DATABASE_URL"]

def get_redis_url() -> str:
    """Get Redis URL with credentials"""
    return secret_manager.get_database_config()["REDIS_URL"]

def validate_environment() -> bool:
    """Validate all required secrets are available"""
    results = secret_manager.validate_secrets()
    return all(results.values())

# Export for use in other modules
__all__ = [
    "SecretManager",
    "secret_manager", 
    "get_secret",
    "get_database_url",
    "get_redis_url",
    "validate_environment"
]

