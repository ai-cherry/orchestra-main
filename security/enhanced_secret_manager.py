"""
Orchestra AI - Enhanced Secret Manager with Environment Integration
Centralized secret management with .env file support and AI agent accessibility
"""

import os
import json
import base64
import hashlib
from typing import Dict, Any, Optional, List
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import structlog
from dotenv import load_dotenv

logger = structlog.get_logger(__name__)

class EnhancedSecretManager:
    """Enhanced secret management with .env file support and AI agent accessibility"""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.secrets_cache: Dict[str, Any] = {}
        self._encryption_key = None
        
        # Load environment files in priority order
        self._load_environment_files()
        
    def _load_environment_files(self):
        """Load environment files in priority order"""
        env_files = [
            f".env.{self.environment}",
            ".env.local", 
            ".env"
        ]
        
        for env_file in env_files:
            env_path = Path(env_file)
            if env_path.exists():
                load_dotenv(env_path)
                logger.info(f"Loaded environment file: {env_file}")
    
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
        
        # 2. Check environment variables (from .env files)
        env_value = os.getenv(key)
        if env_value:
            self.secrets_cache[key] = env_value
            return env_value
        
        # 3. Check Pulumi config (if available)
        pulumi_value = self._get_pulumi_secret(key)
        if pulumi_value:
            self.secrets_cache[key] = pulumi_value
            return pulumi_value
        
        # 4. Check local encrypted secrets file
        local_value = self._get_local_secret(key)
        if local_value:
            self.secrets_cache[key] = local_value
            return local_value
        
        # 5. Return default if provided
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
    
    def get_all_secrets_for_ai_agents(self) -> Dict[str, str]:
        """Get all available secrets for AI agent context (masked for security)"""
        secrets_status = {}
        
        required_secrets = [
            "LAMBDA_API_KEY",
            "GITHUB_TOKEN", 
            "VERCEL_TOKEN",
            "OPENAI_API_KEY",
            "PORTKEY_API_KEY",
            "DATABASE_URL",
            "REDIS_URL",
            "PINECONE_API_KEY",
            "WEAVIATE_API_KEY",
            "NOTION_API_KEY"
        ]
        
        for secret in required_secrets:
            value = self.get_secret(secret)
            if value:
                # Mask the secret for AI agent context
                if len(value) > 8:
                    masked = value[:4] + "..." + value[-4:]
                else:
                    masked = "***"
                secrets_status[secret] = {
                    "available": True,
                    "masked_value": masked,
                    "length": len(value)
                }
            else:
                secrets_status[secret] = {
                    "available": False,
                    "masked_value": None,
                    "length": 0
                }
        
        return secrets_status
    
    def validate_all_secrets(self) -> Dict[str, bool]:
        """Validate all required secrets are available"""
        required_secrets = [
            "LAMBDA_API_KEY",
            "GITHUB_TOKEN", 
            "VERCEL_TOKEN",
            "OPENAI_API_KEY",
            "PORTKEY_API_KEY",
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
    
    def test_api_connections(self) -> Dict[str, Dict[str, Any]]:
        """Test API connections for health monitoring"""
        test_results = {}
        
        # Test Lambda Labs API
        lambda_key = self.get_secret("LAMBDA_API_KEY")
        if lambda_key:
            test_results["lambda_labs"] = self._test_lambda_api(lambda_key)
        
        # Test OpenAI API
        openai_key = self.get_secret("OPENAI_API_KEY")
        if openai_key:
            test_results["openai"] = self._test_openai_api(openai_key)
        
        # Test Portkey API
        portkey_key = self.get_secret("PORTKEY_API_KEY")
        if portkey_key:
            test_results["portkey"] = self._test_portkey_api(portkey_key)
        
        # Test Vercel API
        vercel_token = self.get_secret("VERCEL_TOKEN")
        if vercel_token:
            test_results["vercel"] = self._test_vercel_api(vercel_token)
        
        return test_results
    
    def _test_lambda_api(self, api_key: str) -> Dict[str, Any]:
        """Test Lambda Labs API connection"""
        try:
            import requests
            response = requests.get(
                "https://cloud.lambda.ai/api/v1/instances",
                auth=(api_key, ""),
                timeout=10
            )
            return {
                "status": "healthy" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response_time": None
            }
    
    def _test_openai_api(self, api_key: str) -> Dict[str, Any]:
        """Test OpenAI API connection"""
        try:
            import requests
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            return {
                "status": "healthy" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response_time": None
            }
    
    def _test_portkey_api(self, api_key: str) -> Dict[str, Any]:
        """Test Portkey API connection"""
        try:
            import requests
            response = requests.get(
                "https://api.portkey.ai/v1/health",
                headers={"x-portkey-api-key": api_key},
                timeout=10
            )
            return {
                "status": "healthy" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response_time": None
            }
    
    def _test_vercel_api(self, token: str) -> Dict[str, Any]:
        """Test Vercel API connection"""
        try:
            import requests
            response = requests.get(
                "https://api.vercel.com/v2/user",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            return {
                "status": "healthy" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response_time": None
            }

# Global instance for easy access
secret_manager = EnhancedSecretManager()

# AI Agent Helper Functions
def get_secrets_for_ai_context() -> Dict[str, str]:
    """Get masked secrets for AI agent context"""
    return secret_manager.get_all_secrets_for_ai_agents()

def validate_api_health() -> Dict[str, Dict[str, Any]]:
    """Test all API connections for health monitoring"""
    return secret_manager.test_api_connections()

def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Quick access to secrets for AI agents"""
    return secret_manager.get_secret(key, default)

