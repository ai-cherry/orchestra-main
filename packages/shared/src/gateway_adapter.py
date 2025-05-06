"""
Gateway Adapter for AI Orchestra Agent Orchestration System.

This module implements adapters for connecting various LLM gateways (Portkey, Kong, OpenRouter, etc.)
to the AI Orchestra agent orchestration system. It provides a unified interface for agent-to-LLM 
communication while abstracting away the specifics of each gateway implementation.
"""

import logging
import os
import yaml
import asyncio
import time
from typing import Dict, List, Any, Optional, Union, Callable, Set
from abc import ABC, abstractmethod
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class GatewayAdapter(ABC):
    """Abstract base class for LLM gateway adapters."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the gateway connection."""
        pass
    
    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        agent_type: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate text completion using the gateway."""
        pass
    
    @abstractmethod
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        agent_type: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate chat completion using the gateway."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close gateway connections and release resources."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the provider name."""
        pass
    
    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if gateway is initialized."""
        pass
    
    @abstractmethod
    async def monitor_credits(self) -> Dict[str, Any]:
        """Monitor credit usage."""
        pass


class PortkeyGatewayAdapter(GatewayAdapter):
    """Adapter for Portkey API Gateway."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration."""
        self.config = config
        self._client = None
        self._initialized = False
        self._virtual_keys = config.get("virtual_keys", {})
        self._default_models = config.get("default_models", {})
        self._route_cache = {}
        self._last_errors = {}
        
    async def initialize(self) -> bool:
        """Initialize the Portkey client."""
        try:
            # Dynamically import to avoid hard dependency
            import portkey_ai
            
            # Initialize Portkey client with API key
            self._client = portkey_ai.Portkey(
                api_key=self.config.get("api_key"),
                # Include other options like retries
                max_retries=3,
                timeout=self.config.get("timeout_seconds", 15),
            )
            
            logger.info("Portkey gateway adapter initialized successfully")
            self._initialized = True
            return True
        except ImportError:
            logger.error("Failed to import portkey_ai - please install with: pip install portkey-ai")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Portkey gateway: {str(e)}")
            return False
    
    async def generate_completion(
        self,
        prompt: str,
        agent_type: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate text completion using Portkey."""
        if not self._initialized:
            raise RuntimeError("Portkey gateway not initialized")
        
        # Select appropriate model based on agent type
        selected_model = self._select_model(agent_type, model)
        
        # Determine the right virtual key based on the model
        provider, model_name = self._parse_model_string(selected_model)
        virtual_key = self._get_virtual_key_for_provider(provider)
        
        try:
            # Use the Portkey client with specific virtual key
            with self._client.use_virtual_key(virtual_key):
                response = await self._client.completions.create(
                    model=model_name,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens or 1024,
                )
            
            # Format the response
            return {
                "text": response.choices[0].text,
                "model": selected_model,
                "provider": self.provider_name,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "finish_reason": response.choices[0].finish_reason,
            }
        except Exception as e:
            logger.error(f"Portkey completion error: {str(e)}")
            self._record_error(provider)
            raise
    
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        agent_type: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate chat completion using Portkey."""
        if not self._initialized:
            raise RuntimeError("Portkey gateway not initialized")
        
        # Select appropriate model based on agent type
        selected_model = self._select_model(agent_type, model)
        
        # Determine the right virtual key based on the model
        provider, model_name = self._parse_model_string(selected_model)
        virtual_key = self._get_virtual_key_for_provider(provider)
        
        try:
            # Use the Portkey client with specific virtual key
            with self._client.use_virtual_key(virtual_key):
                response = await self._client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens or 1024,
                )
            
            # Format the response
            return {
                "message": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "model": selected_model,
                "provider": self.provider_name,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "finish_reason": response.choices[0].finish_reason,
            }
        except Exception as e:
            logger.error(f"Portkey chat completion error: {str(e)}")
            self._record_error(provider)
            raise
    
    async def close(self) -> None:
        """Close Portkey client connections."""
        self._initialized = False
        # Portkey client doesn't need explicit cleanup
        logger.info("Portkey adapter connections closed")
    
    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return "portkey"
    
    @property
    def is_initialized(self) -> bool:
        """Check if gateway is initialized."""
        return self._initialized
    
    async def monitor_credits(self) -> Dict[str, Any]:
        """Monitor credit usage for Portkey."""
        if not self._initialized:
            raise RuntimeError("Portkey gateway not initialized")
        
        try:
            # This is a placeholder - implement actual credit monitoring 
            # when Portkey provides this API
            return {
                "credits_used": 0,
                "credits_remaining": 0,
                "credits_limit": 0,
            }
        except Exception as e:
            logger.error(f"Failed to monitor Portkey credits: {str(e)}")
            return {
                "credits_used": 0,
                "credits_remaining": 0,
                "credits_limit": 0,
                "error": str(e)
            }
    
    def _select_model(self, agent_type: Optional[str], model: Optional[str]) -> str:
        """Select appropriate model based on agent type or explicit model."""
        # If model is explicitly provided, use it
        if model:
            return model
        
        # If agent type is provided, check agent-model mapping
        if agent_type:
            # Get agent model mapping from config
            agent_mapping = self.config.get("agent_model_mapping", {})
            if agent_type in agent_mapping:
                return agent_mapping[agent_type]
        
        # Default to primary model
        return self._default_models.get("primary", "openai/gpt-4o")
    
    def _parse_model_string(self, model_string: str) -> tuple:
        """Parse model string into provider and model name."""
        if "/" in model_string:
            provider, model_name = model_string.split("/", 1)
            return provider, model_name
        
        # Default to openai if no provider is specified
        return "openai", model_string
    
    def _get_virtual_key_for_provider(self, provider: str) -> str:
        """Get virtual key for specified provider."""
        provider_lower = provider.lower()
        
        # Check if we have a virtual key for this provider
        if provider_lower in self._virtual_keys:
            return self._virtual_keys[provider_lower]
        
        # Default to using the openai virtual key
        return self._virtual_keys.get("openai", "")
    
    def _record_error(self, provider: str) -> None:
        """Record error for provider to support circuit breaker logic."""
        now = time.time()
        provider_lower = provider.lower()
        
        if provider_lower not in self._last_errors:
            self._last_errors[provider_lower] = []
            
        # Add current error timestamp
        self._last_errors[provider_lower].append(now)
        
        # Keep only errors from the last 5 minutes
        self._last_errors[provider_lower] = [
            t for t in self._last_errors[provider_lower] 
            if now - t < 300  # 5 minutes
        ]


class KongGatewayAdapter(GatewayAdapter):
    """Adapter for Kong AI Gateway."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration."""
        self.config = config
        self._initialized = False
        # Additional Kong-specific initialization here
    
    async def initialize(self) -> bool:
        """Initialize Kong client connection."""
        # Kong integration would be implemented here
        # For now, return a placeholder
        logger.info("Kong gateway adapter initialization not implemented yet")
        return False
    
    async def generate_completion(
        self,
        prompt: str,
        agent_type: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate text completion using Kong."""
        # Kong integration would be implemented here
        raise NotImplementedError("Kong gateway adapter is not implemented yet")
    
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        agent_type: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate chat completion using Kong."""
        raise NotImplementedError("Kong gateway adapter is not implemented yet")
    
    async def close(self) -> None:
        """Close Kong client connections."""
        self._initialized = False
        logger.info("Kong adapter connections closed")
    
    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return "kong"
    
    @property
    def is_initialized(self) -> bool:
        """Check if gateway is initialized."""
        return self._initialized
    
    async def monitor_credits(self) -> Dict[str, Any]:
        """Monitor credit usage for Kong."""
        # Kong integration would be implemented here
        raise NotImplementedError("Kong gateway adapter is not implemented yet")


class GatewayAdapterFactory:
    """Factory for creating gateway adapters."""
    
    @staticmethod
    async def create_adapter(config_path: str = None) -> GatewayAdapter:
        """Create appropriate adapter based on configuration."""
        # Load configuration
        gateway_config = GatewayAdapterFactory._load_config(config_path)
        
        # Get primary provider from config
        primary_provider = gateway_config.get("llm_gateway", {}).get("primary_provider", "portkey")
        
        # Create adapter based on primary provider
        if primary_provider == "portkey":
            portkey_config = gateway_config.get("portkey", {})
            adapter = PortkeyGatewayAdapter(portkey_config)
        elif primary_provider == "kong":
            kong_config = gateway_config.get("kong", {})
            adapter = KongGatewayAdapter(kong_config)
        else:
            raise ValueError(f"Unsupported gateway provider: {primary_provider}")
        
        # Initialize adapter
        success = await adapter.initialize()
        if not success:
            # Try fallback provider if initialization fails
            fallback_provider = gateway_config.get("llm_gateway", {}).get("fallback_provider")
            if fallback_provider and fallback_provider != primary_provider:
                logger.warning(f"Primary provider {primary_provider} failed, trying fallback: {fallback_provider}")
                if fallback_provider == "portkey":
                    adapter = PortkeyGatewayAdapter(gateway_config.get("portkey", {}))
                elif fallback_provider == "kong":
                    adapter = KongGatewayAdapter(gateway_config.get("kong", {}))
                
                success = await adapter.initialize()
                if not success:
                    raise RuntimeError(f"Failed to initialize both primary and fallback gateways")
            else:
                raise RuntimeError(f"Failed to initialize gateway {primary_provider} and no fallback specified")
        
        return adapter
    
    @staticmethod
    def _load_config(config_path: str = None) -> Dict[str, Any]:
        """Load gateway configuration from yaml file."""
        if not config_path:
            # Default config path
            config_path = os.environ.get(
                "LLM_GATEWAY_CONFIG_PATH", 
                str(Path(__file__).parent.parent / "config" / "llm_gateway_config.yaml")
            )
        
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                
            # Process environment variables in config
            config = GatewayAdapterFactory._process_env_vars(config)
            
            return config
        except Exception as e:
            logger.error(f"Failed to load gateway configuration: {str(e)}")
            # Return default configuration
            return {
                "llm_gateway": {
                    "primary_provider": "portkey",
                    "timeout_seconds": 15
                },
                "portkey": {
                    "api_key": os.environ.get("PORTKEY_API_KEY", ""),
                    "virtual_keys": {
                        "openai": os.environ.get("PORTKEY_VIRTUAL_KEY_OPENAI", ""),
                        "anthropic": os.environ.get("PORTKEY_VIRTUAL_KEY_ANTHROPIC", "")
                    },
                    "default_models": {
                        "primary": "openai/gpt-4o"
                    }
                }
            }
    
    @staticmethod
    def _process_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
        """Process environment variables in configuration."""
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    # Extract environment variable name
                    env_var = value[2:-1]
                    # Replace with environment variable value or empty string
                    config[key] = os.environ.get(env_var, "")
                elif isinstance(value, (dict, list)):
                    # Recursively process nested dictionaries and lists
                    config[key] = GatewayAdapterFactory._process_env_vars(value)
        elif isinstance(config, list):
            for i, item in enumerate(config):
                if isinstance(item, (dict, list)):
                    config[i] = GatewayAdapterFactory._process_env_vars(item)
        
        return config


async def get_gateway_adapter() -> GatewayAdapter:
    """Get gateway adapter singleton."""
    if not hasattr(get_gateway_adapter, "_instance") or get_gateway_adapter._instance is None:
        get_gateway_adapter._instance = await GatewayAdapterFactory.create_adapter()
    
    return get_gateway_adapter._instance