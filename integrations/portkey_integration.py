"""
Orchestra AI - Enhanced Portkey Integration
Fixed configuration and provider setup
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

class PortkeyManager:
    """
    Enhanced Portkey manager with proper provider configuration
    """
    
    def __init__(self):
        self.secret_manager = EnhancedSecretManager()
        self.portkey_client = None
        self.config_id = None
        self.api_key = None
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
            # Initialize Portkey client with basic configuration
            self.portkey_client = Portkey(
                api_key=self.api_key
            )
            print("✅ Portkey client initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize Portkey client: {e}")
    
    def is_available(self) -> bool:
        """Check if Portkey is available and configured"""
        return PORTKEY_AVAILABLE and self.portkey_client is not None
    
    def chat_completion_with_provider(self, 
                                    messages: List[Dict[str, str]], 
                                    provider: str = "openai",
                                    model: str = "gpt-3.5-turbo",
                                    **kwargs) -> Dict[str, Any]:
        """
        Create chat completion through Portkey with explicit provider
        
        Args:
            messages: List of message dictionaries
            provider: AI provider (openai, anthropic, etc.)
            model: AI model to use
            **kwargs: Additional parameters
            
        Returns:
            Chat completion response
        """
        if not self.is_available():
            raise RuntimeError("Portkey not available or configured")
        
        try:
            # Get provider API key
            provider_key = self._get_provider_key(provider)
            if not provider_key:
                raise RuntimeError(f"API key for provider '{provider}' not found")
            
            # Create Portkey client with provider configuration
            client = Portkey(
                api_key=self.api_key,
                provider=provider,
                Authorization=f"Bearer {provider_key}"
            )
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response
            
        except Exception as e:
            print(f"❌ Portkey chat completion failed: {e}")
            raise
    
    def _get_provider_key(self, provider: str) -> Optional[str]:
        """Get API key for specific provider"""
        provider_key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY"
        }
        
        key_name = provider_key_map.get(provider.lower())
        if not key_name:
            return None
        
        return self.secret_manager.get_secret(key_name)
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers based on configured API keys"""
        providers = []
        
        provider_keys = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY", 
            "deepseek": "DEEPSEEK_API_KEY"
        }
        
        for provider, key_name in provider_keys.items():
            if self.secret_manager.get_secret(key_name):
                providers.append(provider)
        
        return providers
    
    def test_connection(self, provider: str = "openai") -> Dict[str, Any]:
        """Test Portkey connection with specific provider"""
        result = {
            "portkey_available": PORTKEY_AVAILABLE,
            "client_initialized": self.portkey_client is not None,
            "api_key_configured": bool(self.api_key),
            "provider": provider,
            "provider_key_available": bool(self._get_provider_key(provider)),
            "connection_test": False,
            "error": None,
            "timestamp": datetime.now().isoformat()
        }
        
        if not self.is_available():
            result["error"] = "Portkey not available or not configured"
            return result
        
        if not self._get_provider_key(provider):
            result["error"] = f"API key for provider '{provider}' not found"
            return result
        
        try:
            # Test with a simple chat completion
            test_response = self.chat_completion_with_provider(
                messages=[{"role": "user", "content": "Hello"}],
                provider=provider,
                model="gpt-3.5-turbo" if provider == "openai" else "claude-3-haiku",
                max_tokens=10
            )
            
            if test_response:
                result["connection_test"] = True
                result["test_response"] = str(test_response)[:100] + "..."
            
        except Exception as e:
            result["error"] = str(e)
        
        return result

class PortkeyIntegration:
    """
    Enhanced integration layer for Orchestra AI with Portkey
    """
    
    def __init__(self):
        self.portkey_manager = PortkeyManager()
        self.fallback_enabled = True
        self.default_provider = "openai"  # Note: For virtual keys, use portkey_virtual_keys.py with openrouter
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       provider: Optional[str] = None,
                       **kwargs):
        """Enhanced chat completion with provider selection"""
        provider = provider or self.default_provider
        
        try:
            if self.portkey_manager.is_available():
                return self.portkey_manager.chat_completion_with_provider(
                    messages, provider=provider, **kwargs
                )
            elif self.fallback_enabled:
                return self._fallback_call(messages, provider, **kwargs)
            else:
                raise RuntimeError("Portkey unavailable and fallback disabled")
                
        except Exception as e:
            if self.fallback_enabled:
                print(f"⚠️ Portkey failed, using fallback: {e}")
                return self._fallback_call(messages, provider, **kwargs)
            else:
                raise
    
    def _fallback_call(self, messages: List[Dict[str, str]], provider: str, **kwargs):
        """Fallback to direct API calls"""
        try:
            if provider == "openai":
                return self._fallback_openai_call(messages, **kwargs)
            elif provider == "anthropic":
                return self._fallback_anthropic_call(messages, **kwargs)
            else:
                raise RuntimeError(f"Fallback not implemented for provider: {provider}")
                
        except Exception as e:
            print(f"❌ Fallback call failed: {e}")
            raise
    
    def _fallback_openai_call(self, messages: List[Dict[str, str]], **kwargs):
        """Fallback to direct OpenAI API call"""
        try:
            import openai
            
            openai_key = self.portkey_manager.secret_manager.get_secret("OPENAI_API_KEY")
            if not openai_key:
                raise RuntimeError("OpenAI API key not found")
            
            client = openai.OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                messages=messages,
                **kwargs
            )
            return response
            
        except Exception as e:
            print(f"❌ Fallback OpenAI call failed: {e}")
            raise
    
    def _fallback_anthropic_call(self, messages: List[Dict[str, str]], **kwargs):
        """Fallback to direct Anthropic API call"""
        try:
            import anthropic
            
            anthropic_key = self.portkey_manager.secret_manager.get_secret("ANTHROPIC_API_KEY")
            if not anthropic_key:
                raise RuntimeError("Anthropic API key not found")
            
            client = anthropic.Anthropic(api_key=anthropic_key)
            # Convert OpenAI format to Anthropic format
            anthropic_messages = []
            for msg in messages:
                if msg["role"] != "system":
                    anthropic_messages.append(msg)
            
            response = client.messages.create(
                model=kwargs.get("model", "claude-3-haiku-20240307"),
                max_tokens=kwargs.get("max_tokens", 1000),
                messages=anthropic_messages
            )
            return response
            
        except Exception as e:
            print(f"❌ Fallback Anthropic call failed: {e}")
            raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status for Orchestra AI health monitoring"""
        available_providers = self.portkey_manager.get_available_providers()
        
        # Test connection with first available provider
        test_provider = available_providers[0] if available_providers else "openai"
        portkey_test = self.portkey_manager.test_connection(test_provider)
        
        return {
            "service": "portkey_integration",
            "status": "healthy" if portkey_test["connection_test"] else "degraded",
            "portkey_available": portkey_test["portkey_available"],
            "client_configured": portkey_test["client_initialized"],
            "available_providers": available_providers,
            "test_provider": test_provider,
            "connection_test": portkey_test["connection_test"],
            "fallback_enabled": self.fallback_enabled,
            "error": portkey_test.get("error"),
            "timestamp": portkey_test["timestamp"]
        }

# Global instance for easy import
portkey_integration = PortkeyIntegration()

def get_portkey_client():
    """Get configured Portkey client"""
    return portkey_integration.portkey_manager.portkey_client

def chat_completion_with_portkey(messages: List[Dict[str, str]], **kwargs):
    """Convenience function for chat completion through Portkey"""
    return portkey_integration.chat_completion(messages, **kwargs)

if __name__ == "__main__":
    # Test Portkey integration
    print("🧪 Testing Enhanced Portkey Integration...")
    
    manager = PortkeyManager()
    available_providers = manager.get_available_providers()
    
    print(f"\n📋 Available Providers: {available_providers}")
    
    if available_providers:
        test_provider = available_providers[0]
        print(f"\n🔍 Testing with provider: {test_provider}")
        
        test_result = manager.test_connection(test_provider)
        
        print("\n📊 Test Results:")
        for key, value in test_result.items():
            print(f"  {key}: {value}")
        
        if test_result["connection_test"]:
            print(f"\n✅ Portkey integration working with {test_provider}!")
        else:
            print(f"\n❌ Portkey integration failed: {test_result.get('error', 'Unknown error')}")
    else:
        print("\n❌ No providers available - check API key configuration")
    
    # Test integration layer
    print("\n🔄 Testing Integration Layer...")
    integration = PortkeyIntegration()
    health = integration.get_health_status()
    
    print(f"\n🏥 Health Status: {health['status']}")
    for key, value in health.items():
        if key != "status":
            print(f"  {key}: {value}")

