#!/usr/bin/env python3
"""
Fast Secrets Manager for Orchestra AI
Performance-optimized secret access with caching and validation

Author: Orchestra AI Team
Version: 1.0.0
"""

import os
import logging
from functools import lru_cache
from typing import Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

@lru_cache(maxsize=128)
def get_secret(key: str) -> str:
    """
    Fast cached secret access with fallback chain
    
    Priority order:
    1. Environment variables
    2. .env file (if exists)
    3. Empty string (with warning)
    """
    value = os.getenv(key)
    if value:
        return value
    
    # Try loading from .env file if not in environment
    env_file = Path('.env')
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith(f'{key}='):
                        return line.split('=', 1)[1].strip().strip('"\'')
        except Exception as e:
            logger.warning(f"Error reading .env file: {e}")
    
    logger.warning(f"Secret not found: {key}")
    return ''

@lru_cache(maxsize=32)
def get_api_config(service: str) -> Dict[str, Any]:
    """
    Fast cached API configuration for common services
    
    Args:
        service: Service name (notion, openai, anthropic, openrouter, etc.)
        
    Returns:
        Dictionary with API configuration
    """
    configs = {
        'notion': {
            'api_token': get_secret('NOTION_API_TOKEN'),
            'workspace_id': get_secret('NOTION_WORKSPACE_ID'),
            'base_url': 'https://api.notion.com/v1',
            'version': '2022-06-28'
        },
        'openai': {
            'api_key': get_secret('OPENAI_API_KEY'),
            'base_url': 'https://api.openai.com/v1',
            'organization': get_secret('OPENAI_ORG_ID')
        },
        'anthropic': {
            'api_key': get_secret('ANTHROPIC_API_KEY'),
            'base_url': 'https://api.anthropic.com',
            'version': '2023-06-01'
        },
        'openrouter': {
            'api_key': get_secret('OPENROUTER_API_KEY'),
            'base_url': 'https://openrouter.ai/api/v1',
            'site_url': get_secret('OPENROUTER_SITE_URL') or 'https://orchestra-ai.dev',
            'app_name': get_secret('OPENROUTER_APP_NAME') or 'Orchestra AI'
        },
        'perplexity': {
            'api_key': get_secret('PERPLEXITY_API_KEY'),
            'base_url': 'https://api.perplexity.ai'
        },
        'phantombuster': {
            'api_key': get_secret('PHANTOMBUSTER_API_KEY'),
            'base_url': 'https://api.phantombuster.com/api/v2'
        },
        'apify': {
            'api_token': get_secret('APIFY_API_TOKEN'),
            'base_url': 'https://api.apify.com/v2'
        },
        'zenrows': {
            'api_key': get_secret('ZENROWS_API_KEY'),
            'base_url': 'https://api.zenrows.com/v1'
        },
        'lambda_labs': {
            'api_key': get_secret('LAMBDA_LABS_API_KEY'),
            'base_url': 'https://cloud.lambdalabs.com/api/v1'
        },
        'database': {
            'url': get_secret('DATABASE_URL'),
            'redis_password': get_secret('REDIS_PASSWORD'),
            'weaviate_key': get_secret('WEAVIATE_API_KEY')
        }
    }
    
    return configs.get(service, {})

class StreamlinedSecretsManager:
    """
    High-performance secrets manager with caching and validation
    Optimized for single-developer workflow with reasonable security
    """
    
    def __init__(self):
        self._cache = {}
        self._validated = False
    
    def get(self, service: str, key: str = 'api_key') -> str:
        """
        Get secret for a specific service and key
        
        Args:
            service: Service name (notion, openai, etc.)
            key: Specific key within service (api_key, workspace_id, etc.)
            
        Returns:
            Secret value or empty string if not found
        """
        cache_key = f"{service}.{key}"
        
        if cache_key not in self._cache:
            config = get_api_config(service)
            self._cache[cache_key] = config.get(key, '')
        
        return self._cache[cache_key]
    
    def get_headers(self, service: str) -> Dict[str, str]:
        """
        Get standard headers for API requests
        
        Args:
            service: Service name
            
        Returns:
            Dictionary with authorization headers
        """
        headers = {'Content-Type': 'application/json'}
        
        if service == 'notion':
            token = self.get('notion', 'api_token')
            if token:
                headers.update({
                    'Authorization': f'Bearer {token}',
                    'Notion-Version': '2022-06-28'
                })
        
        elif service == 'openai':
            key = self.get('openai', 'api_key')
            if key:
                headers['Authorization'] = f'Bearer {key}'
        
        elif service == 'anthropic':
            key = self.get('anthropic', 'api_key')
            if key:
                headers.update({
                    'x-api-key': key,
                    'anthropic-version': '2023-06-01'
                })
        
        elif service == 'openrouter':
            key = self.get('openrouter', 'api_key')
            if key:
                headers.update({
                    'Authorization': f'Bearer {key}',
                    'HTTP-Referer': self.get('openrouter', 'site_url'),
                    'X-Title': self.get('openrouter', 'app_name')
                })
        
        elif service == 'perplexity':
            key = self.get('perplexity', 'api_key')
            if key:
                headers['Authorization'] = f'Bearer {key}'
        
        elif service == 'phantombuster':
            key = self.get('phantombuster', 'api_key')
            if key:
                headers['X-Phantombuster-Key'] = key
        
        elif service == 'apify':
            token = self.get('apify', 'api_token')
            if token:
                headers['Authorization'] = f'Bearer {token}'
        
        elif service == 'zenrows':
            # ZenRows uses query parameters, not headers
            pass
        
        elif service == 'lambda_labs':
            key = self.get('lambda_labs', 'api_key')
            if key:
                headers['Authorization'] = f'Bearer {key}'
        
        return headers
    
    def validate_required_secrets(self, required: list = None) -> Dict[str, bool]:
        """
        Validate that required secrets are present
        
        Args:
            required: List of required secret keys
            
        Returns:
            Dictionary with validation results
        """
        if required is None:
            required = [
                'NOTION_API_TOKEN',
                'OPENAI_API_KEY'
            ]
        
        results = {}
        for key in required:
            value = get_secret(key)
            results[key] = bool(value and len(value) > 10)
        
        self._validated = all(results.values())
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all configured services
        
        Returns:
            Dictionary with service status information
        """
        services = ['notion', 'openai', 'anthropic', 'openrouter', 'perplexity', 'phantombuster', 'apify', 'zenrows', 'lambda_labs']
        status = {}
        
        for service in services:
            config = get_api_config(service)
            has_key = bool(config.get('api_key') or config.get('api_token'))
            status[service] = {
                'configured': has_key,
                'config': {k: bool(v) for k, v in config.items() if k not in ['base_url', 'version']}
            }
        
        return status
    
    def clear_cache(self):
        """Clear all cached secrets (useful for testing or key rotation)"""
        self._cache.clear()
        get_secret.cache_clear()
        get_api_config.cache_clear()
        self._validated = False

# Global instance for easy access
secrets = StreamlinedSecretsManager()

# Convenience functions for common patterns
def notion_headers() -> Dict[str, str]:
    """Get Notion API headers"""
    return secrets.get_headers('notion')

def openai_headers() -> Dict[str, str]:
    """Get OpenAI API headers"""
    return secrets.get_headers('openai')

def anthropic_headers() -> Dict[str, str]:
    """Get Anthropic API headers"""
    return secrets.get_headers('anthropic')

def openrouter_headers() -> Dict[str, str]:
    """Get OpenRouter API headers"""
    return secrets.get_headers('openrouter')

def perplexity_headers() -> Dict[str, str]:
    """Get Perplexity API headers"""
    return secrets.get_headers('perplexity')

def lambda_labs_headers() -> Dict[str, str]:
    """Get Lambda Labs API headers"""
    return secrets.get_headers('lambda_labs')

def validate_setup() -> bool:
    """Quick validation of basic setup"""
    results = secrets.validate_required_secrets()
    missing = [k for k, v in results.items() if not v]
    
    if missing:
        logger.error(f"Missing required secrets: {missing}")
        logger.info("Run: cp .env.example .env and add your API keys")
        return False
    
    return True

# Performance monitoring
def get_cache_info() -> Dict[str, Any]:
    """Get cache performance information"""
    return {
        'get_secret_cache': get_secret.cache_info()._asdict(),
        'get_api_config_cache': get_api_config.cache_info()._asdict(),
        'manager_cache_size': len(secrets._cache)
    }

if __name__ == "__main__":
    # Test the secrets manager
    print("🔐 Orchestra AI Secrets Manager Test")
    
    # Test validation
    results = secrets.validate_required_secrets()
    print(f"Validation Results: {results}")
    
    # Test status
    status = secrets.get_status()
    print(f"Service Status: {status}")
    
    # Test cache performance
    cache_info = get_cache_info()
    print(f"Cache Performance: {cache_info}")
    
    # Test specific service
    notion_config = get_api_config('notion')
    print(f"Notion Config: {notion_config}")
    
    # Test OpenRouter
    openrouter_config = get_api_config('openrouter')
    print(f"OpenRouter Config: {openrouter_config}") 