"""
Orchestra AI - Enhanced Portkey Integration with Virtual Keys
Uses Portkey's pre-configured virtual keys instead of local API keys
"""

import os
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from portkey_ai import Portkey
    PORTKEY_AVAILABLE = True
except ImportError:
    PORTKEY_AVAILABLE = False
    print("⚠️ Portkey AI not installed. Run: pip install portkey-ai")

from security.enhanced_secret_manager import EnhancedSecretManager

class PortkeyVirtualKeyManager:
    """
    Enhanced Portkey manager using pre-configured virtual keys
    No need for local provider API keys - uses Portkey's virtual keys
    """
    
    # Virtual key mappings from Portkey discovery
    VIRTUAL_KEYS = {
        "openai": {
            "id": "ae81981f-b1c5-4bcd-a8e4-0bcf82b47b5e",
            "slug": "openai-api-key-345cc9",
            "name": "OPENAI_API_KEY"
        },
        "anthropic": {
            "id": "2b88ffdf-bbc2-47b6-a90a-bd1d4279b80a", 
            "slug": "anthropic-api-k-6feca8",
            "name": "ANTHROPIC_API_KEY"
        },
        "deepseek": {
            "id": "53465fcf-7126-4342-bffa-d9f094ca2a10",
            "slug": "deepseek-api-ke-e7859b", 
            "name": "DEEPSEEK_API_KEY"
        },
        "google": {
            "id": "251af14c-7b36-4c7a-8bb6-4f0ad93ef6ea",
            "slug": "gemini-api-key-1ea5a2",
            "name": "GEMINI_API_KEY"
        },
        "perplexity": {
            "id": "8c6a4f8d-cdda-4b63-8487-df26084d8a36",
            "slug": "perplexity-api-015025",
            "name": "PERPLEXITY_API_KEY"
        },
        "xai": {
            "id": "740b372b-2437-4c80-8357-79f4879e0314",
            "slug": "xai-api-key-a760a5",
            "name": "XAI_API_KEY"
        },
        "together": {
            "id": "f29384d2-f6c4-46b5-a121-885693328da8",
            "slug": "together-ai-670469",
            "name": "Together AI"
        },
        "openrouter": {
            "id": "67fb2ab4-9202-4086-a8c4-e014b67c70fc",
            "slug": "openrouter-api-15df95",
            "name": "OPENROUTER_API_KEY"
        }
    }
    
    def __init__(self):
        self.secret_manager = EnhancedSecretManager()
        self.portkey_client = None
        self.api_key = None
        self.config_id = None
        self._initialize_portkey()
    
    def _initialize_portkey(self):
        """Initialize Portkey client with credentials"""
        if not PORTKEY_AVAILABLE:
            print("❌ Portkey AI SDK not available")
            return
        
        # Get Portkey credentials
        self.api_key = self.secret_manager.get_secret("PORTKEY_API_KEY")
        self.config_id = self.secret_manager.get_secret("PORTKEY_CONFIG")
        
        if not self.api_key:
            print("❌ PORTKEY_API_KEY not found in secrets")
            return
        
        try:
            # Initialize Portkey client
            self.portkey_client = Portkey(
                api_key=self.api_key,
                config=self.config_id if self.config_id else None
            )
            print("✅ Portkey client initialized with virtual keys")
            
        except Exception as e:
            print(f"❌ Failed to initialize Portkey client: {e}")
    
    def is_available(self) -> bool:
        """Check if Portkey is available and configured"""
        return PORTKEY_AVAILABLE and self.portkey_client is not None
    
    def chat_completion_with_virtual_key(self, 
                                       messages: List[Dict[str, str]], 
                                       provider: str = "openai",
                                       model: str = None,
                                       **kwargs) -> Dict[str, Any]:
        """
        Create chat completion using Portkey virtual keys
        
        Args:
            messages: List of message dictionaries
            provider: AI provider (openai, anthropic, deepseek, etc.)
            model: AI model to use (auto-selected if not provided)
            **kwargs: Additional parameters
            
        Returns:
            Chat completion response
        """
        if not self.is_available():
            raise RuntimeError("Portkey not available or configured")
        
        # Get virtual key info for provider
        virtual_key_info = self.VIRTUAL_KEYS.get(provider.lower())
        if not virtual_key_info:
            raise RuntimeError(f"Virtual key not found for provider: {provider}")
        
        # Auto-select model if not provided
        if not model:
            model = self._get_default_model(provider)
        
        try:
            # Create Portkey client with virtual key
            client = Portkey(
                api_key=self.api_key,
                virtual_key=virtual_key_info["id"]
            )
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response
            
        except Exception as e:
            print(f"❌ Portkey virtual key chat completion failed: {e}")
            raise
    
    def _get_default_model(self, provider: str) -> str:
        """Get default model for each provider"""
        default_models = {
            "openai": "gpt-3.5-turbo",
            "anthropic": "claude-3-haiku-20240307",
            "deepseek": "deepseek-chat",
            "google": "gemini-pro",
            "perplexity": "llama-3.1-sonar-small-128k-online",
            "xai": "grok-beta",
            "together": "meta-llama/Llama-2-7b-chat-hf",
            "openrouter": "openai/gpt-3.5-turbo"
        }
        return default_models.get(provider.lower(), "gpt-3.5-turbo")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers from virtual keys"""
        return list(self.VIRTUAL_KEYS.keys())
    
    def get_virtual_key_info(self, provider: str) -> Optional[Dict[str, str]]:
        """Get virtual key information for a provider"""
        return self.VIRTUAL_KEYS.get(provider.lower())
    
    def test_virtual_key_connection(self, provider: str = "openai") -> Dict[str, Any]:
        """Test Portkey connection with virtual key"""
        result = {
            "portkey_available": PORTKEY_AVAILABLE,
            "client_initialized": self.portkey_client is not None,
            "api_key_configured": bool(self.api_key),
            "provider": provider,
            "virtual_key_available": provider.lower() in self.VIRTUAL_KEYS,
            "virtual_key_info": self.get_virtual_key_info(provider),
            "connection_test": False,
            "error": None,
            "timestamp": datetime.now().isoformat()
        }
        
        if not self.is_available():
            result["error"] = "Portkey not available or configured"
            return result
        
        if not result["virtual_key_available"]:
            result["error"] = f"Virtual key not available for provider '{provider}'"
            return result
        
        try:
            # Test with a simple chat completion using virtual key
            test_response = self.chat_completion_with_virtual_key(
                messages=[{"role": "user", "content": "Hello"}],
                provider=provider,
                max_tokens=10
            )
            
            if test_response:
                result["connection_test"] = True
                result["test_response"] = str(test_response)[:100] + "..."
            
        except Exception as e:
            result["error"] = str(e)
        
        return result

class PortkeyVirtualKeyIntegration:
    """
    Enhanced integration layer using Portkey virtual keys
    """
    
    def __init__(self):
        self.portkey_manager = PortkeyVirtualKeyManager()
        self.fallback_enabled = False  # No fallback needed with virtual keys
        self.default_provider = "openai"
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       provider: Optional[str] = None,
                       model: Optional[str] = None,
                       **kwargs):
        """Enhanced chat completion with virtual keys"""
        provider = provider or self.default_provider
        
        try:
            if self.portkey_manager.is_available():
                return self.portkey_manager.chat_completion_with_virtual_key(
                    messages, provider=provider, model=model, **kwargs
                )
            else:
                raise RuntimeError("Portkey virtual key integration not available")
                
        except Exception as e:
            print(f"❌ Portkey virtual key call failed: {e}")
            raise
    
    def get_available_providers(self) -> List[str]:
        """Get all available providers from virtual keys"""
        return self.portkey_manager.get_available_providers()
    
    def get_provider_models(self, provider: str) -> List[str]:
        """Get available models for a provider"""
        # This would typically call Portkey's models API
        # For now, return common models per provider
        provider_models = {
            "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            "deepseek": ["deepseek-chat", "deepseek-coder"],
            "google": ["gemini-pro", "gemini-pro-vision"],
            "perplexity": ["llama-3.1-sonar-small-128k-online", "llama-3.1-sonar-large-128k-online"],
            "xai": ["grok-beta"],
            "together": ["meta-llama/Llama-2-7b-chat-hf", "meta-llama/Llama-2-13b-chat-hf"],
            "openrouter": ["openai/gpt-3.5-turbo", "anthropic/claude-3-haiku"]
        }
        return provider_models.get(provider.lower(), [])
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status for Orchestra AI health monitoring"""
        available_providers = self.portkey_manager.get_available_providers()
        
        # Test connection with first available provider
        test_provider = available_providers[0] if available_providers else "openai"
        portkey_test = self.portkey_manager.test_virtual_key_connection(test_provider)
        
        return {
            "service": "portkey_virtual_key_integration",
            "status": "healthy" if portkey_test["connection_test"] else "degraded",
            "portkey_available": portkey_test["portkey_available"],
            "client_configured": portkey_test["client_initialized"],
            "available_providers": available_providers,
            "virtual_keys_count": len(available_providers),
            "test_provider": test_provider,
            "connection_test": portkey_test["connection_test"],
            "fallback_enabled": self.fallback_enabled,
            "error": portkey_test.get("error"),
            "timestamp": portkey_test["timestamp"]
        }

# Global instance for easy import
portkey_virtual_integration = PortkeyVirtualKeyIntegration()

def get_portkey_virtual_client():
    """Get configured Portkey virtual key client"""
    return portkey_virtual_integration.portkey_manager.portkey_client

def chat_completion_with_virtual_keys(messages: List[Dict[str, str]], **kwargs):
    """Convenience function for chat completion through Portkey virtual keys"""
    return portkey_virtual_integration.chat_completion(messages, **kwargs)

def get_available_ai_providers():
    """Get all available AI providers through virtual keys"""
    return portkey_virtual_integration.get_available_providers()

if __name__ == "__main__":
    # Test Portkey virtual key integration
    print("🧪 Testing Portkey Virtual Key Integration...")
    
    manager = PortkeyVirtualKeyManager()
    available_providers = manager.get_available_providers()
    
    print(f"\n📋 Available Providers via Virtual Keys: {available_providers}")
    print(f"📊 Total Virtual Keys: {len(available_providers)}")
    
    # Test each provider
    for provider in available_providers[:3]:  # Test first 3 providers
        print(f"\n🔍 Testing provider: {provider}")
        
        virtual_key_info = manager.get_virtual_key_info(provider)
        print(f"  Virtual Key ID: {virtual_key_info['id']}")
        print(f"  Virtual Key Name: {virtual_key_info['name']}")
        
        test_result = manager.test_virtual_key_connection(provider)
        
        if test_result["connection_test"]:
            print(f"  ✅ {provider} virtual key working!")
        else:
            print(f"  ❌ {provider} virtual key failed: {test_result.get('error', 'Unknown error')}")
    
    # Test integration layer
    print("\n🔄 Testing Virtual Key Integration Layer...")
    integration = PortkeyVirtualKeyIntegration()
    health = integration.get_health_status()
    
    print(f"\n🏥 Health Status: {health['status']}")
    print(f"📊 Virtual Keys Available: {health['virtual_keys_count']}")
    print(f"🔧 Available Providers: {health['available_providers']}")
    
    if health['status'] == 'healthy':
        print("\n✅ Portkey Virtual Key Integration fully operational!")
    else:
        print(f"\n❌ Integration issues: {health.get('error', 'Unknown error')}")

