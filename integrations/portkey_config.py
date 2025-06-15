"""
Orchestra AI - Optimized Portkey Configuration
Central configuration for all Portkey settings and optimizations
"""

from typing import Dict, List, Any

class PortkeyConfig:
    """Centralized Portkey configuration with best practices"""
    
    # Provider hierarchy optimized for cost and performance
    PROVIDER_HIERARCHY = {
        "primary": "openrouter",  # Most versatile, best pricing
        "fallback_chain": [
            "deepseek",      # Very cost-effective for coding tasks
            "anthropic",     # Claude 3 Haiku for balanced performance
            "together",      # Open-source models, good pricing
            "openai",        # Reliable but more expensive
            "google",        # Gemini for specific use cases
            "perplexity"     # For real-time web search needs
        ]
    }
    
    # Model selection based on task type
    MODEL_SELECTION = {
        "coding_tasks": {
            "primary": "deepseek/deepseek-coder",
            "fallback": "openrouter/codellama/codellama-34b-instruct",
            "max_tokens": 4000,
            "temperature": 0.3
        },
        "general_chat": {
            "primary": "openrouter/openai/gpt-3.5-turbo",
            "fallback": "anthropic/claude-3-haiku-20240307",
            "max_tokens": 2000,
            "temperature": 0.7
        },
        "complex_reasoning": {
            "primary": "openrouter/anthropic/claude-3-sonnet",
            "fallback": "openrouter/openai/gpt-4",
            "max_tokens": 4000,
            "temperature": 0.5
        },
        "web_search": {
            "primary": "perplexity/llama-3.1-sonar-large-128k-online",
            "fallback": "perplexity/llama-3.1-sonar-small-128k-online",
            "max_tokens": 2000,
            "temperature": 0.5
        },
        "creative_writing": {
            "primary": "openrouter/anthropic/claude-3-opus",
            "fallback": "together/meta-llama/Llama-3-70b-chat-hf",
            "max_tokens": 4000,
            "temperature": 0.9
        },
        "summarization": {
            "primary": "anthropic/claude-3-haiku-20240307",
            "fallback": "openrouter/openai/gpt-3.5-turbo",
            "max_tokens": 1000,
            "temperature": 0.3
        }
    }
    
    # Portkey client configuration
    PORTKEY_CONFIG = {
        "cache": {
            "mode": "semantic",  # Enable semantic caching
            "ttl": 3600,        # 1 hour cache
            "similarity_threshold": 0.95
        },
        "retry": {
            "attempts": 3,
            "on_status_codes": [429, 500, 502, 503, 504],
            "delay": 1000,  # Initial delay in ms
            "multiplier": 2  # Exponential backoff multiplier
        },
        "request_timeout": 60,
        "loadbalance": {
            "strategy": "weighted_round_robin",
            "providers": [
                {"id": "openrouter", "weight": 40},
                {"id": "deepseek", "weight": 30},
                {"id": "anthropic", "weight": 20},
                {"id": "together", "weight": 10}
            ]
        }
    }
    
    # Cost tracking configuration
    COST_TRACKING = {
        "enabled": True,
        "track_token_usage": True,
        "track_provider_costs": True,
        "alert_threshold": 100,  # Alert when daily cost exceeds $100
        "budget_limits": {
            "daily": 150,
            "monthly": 3000
        },
        "cost_per_1k_tokens": {
            # Input costs per 1000 tokens
            "openrouter/openai/gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "openrouter/openai/gpt-4": {"input": 0.03, "output": 0.06},
            "openrouter/anthropic/claude-3-opus": {"input": 0.015, "output": 0.075},
            "openrouter/anthropic/claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "anthropic/claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            "deepseek/deepseek-chat": {"input": 0.0001, "output": 0.0002},
            "deepseek/deepseek-coder": {"input": 0.0001, "output": 0.0002},
            "google/gemini-1.5-flash": {"input": 0.00035, "output": 0.0007},
            "perplexity/llama-3.1-sonar-small-128k-online": {"input": 0.0002, "output": 0.0002},
            "together/meta-llama/Llama-3-8b-chat-hf": {"input": 0.0002, "output": 0.0002}
        }
    }
    
    # Content filtering configuration
    CONTENT_FILTER = {
        "enabled": True,
        "pii_detection": True,
        "pii_redaction": True,
        "profanity_filter": True,
        "custom_filters": [
            {"pattern": r"\b\d{3}-\d{2}-\d{4}\b", "type": "ssn", "action": "redact"},
            {"pattern": r"\b\d{16}\b", "type": "credit_card", "action": "redact"},
            {"pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "type": "email", "action": "log"}
        ]
    }
    
    # Observability configuration
    OBSERVABILITY = {
        "log_requests": True,
        "log_responses": True,
        "log_errors": True,
        "trace_id_header": "x-trace-id",
        "session_id_header": "x-session-id",
        "custom_metadata": {
            "app": "orchestra-ai",
            "environment": "production",
            "version": "1.0.0"
        },
        "metrics": {
            "latency": True,
            "token_usage": True,
            "error_rate": True,
            "cache_hit_rate": True
        }
    }
    
    # Semantic caching configuration
    CACHE_CONFIG = {
        "enabled": True,
        "mode": "semantic",
        "similarity_threshold": 0.95,
        "ttl": 3600,  # 1 hour
        "max_cache_size": 1000,  # Maximum number of cached responses
        "excluded_endpoints": [
            "/api/chat/streaming",
            "/api/generate/unique"
        ],
        "cache_headers": ["x-user-id", "x-session-id"],
        "cache_key_params": ["model", "temperature", "max_tokens"]
    }
    
    # Rate limiting configuration
    RATE_LIMITS = {
        "enabled": True,
        "global": {
            "requests_per_minute": 100,
            "requests_per_hour": 3000,
            "requests_per_day": 50000
        },
        "per_user": {
            "requests_per_minute": 20,
            "requests_per_hour": 500,
            "requests_per_day": 5000
        },
        "per_provider": {
            "openai": {"rpm": 50, "tpm": 150000},
            "anthropic": {"rpm": 40, "tpm": 100000},
            "deepseek": {"rpm": 60, "tpm": 200000},
            "openrouter": {"rpm": 100, "tpm": 500000}
        }
    }
    
    # Error handling configuration
    ERROR_HANDLING = {
        "max_retries": 3,
        "retry_delay": 1000,  # ms
        "exponential_backoff": True,
        "fallback_on_error": True,
        "error_response_format": "detailed",
        "log_errors": True,
        "alert_on_repeated_errors": True,
        "error_threshold": 10  # Alert after 10 errors in 5 minutes
    }
    
    @classmethod
    def get_model_for_task(cls, task_type: str) -> Dict[str, Any]:
        """Get optimal model configuration for a specific task type"""
        return cls.MODEL_SELECTION.get(task_type, cls.MODEL_SELECTION["general_chat"])
    
    @classmethod
    def get_provider_config(cls, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific provider"""
        provider_configs = {
            "openrouter": {
                "base_url": "https://openrouter.ai/api/v1",
                "timeout": 60,
                "max_retries": 3
            },
            "openai": {
                "base_url": "https://api.openai.com/v1",
                "timeout": 60,
                "max_retries": 3
            },
            "anthropic": {
                "base_url": "https://api.anthropic.com/v1",
                "timeout": 60,
                "max_retries": 3
            },
            "deepseek": {
                "base_url": "https://api.deepseek.com/v1",
                "timeout": 60,
                "max_retries": 3
            },
            "google": {
                "base_url": "https://generativelanguage.googleapis.com/v1",
                "timeout": 60,
                "max_retries": 3
            },
            "perplexity": {
                "base_url": "https://api.perplexity.ai",
                "timeout": 60,
                "max_retries": 3
            },
            "together": {
                "base_url": "https://api.together.xyz/v1",
                "timeout": 60,
                "max_retries": 3
            }
        }
        return provider_configs.get(provider, {})
    
    @classmethod
    def get_cost_for_usage(cls, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage"""
        model_key = f"{provider}/{model}" if "/" not in model else model
        costs = cls.COST_TRACKING["cost_per_1k_tokens"].get(model_key, {"input": 0.001, "output": 0.002})
        
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        
        return round(input_cost + output_cost, 4)
    
    @classmethod
    def should_use_cache(cls, endpoint: str) -> bool:
        """Check if caching should be used for an endpoint"""
        if not cls.CACHE_CONFIG["enabled"]:
            return False
        return endpoint not in cls.CACHE_CONFIG["excluded_endpoints"]
    
    @classmethod
    def get_fallback_chain(cls, primary_provider: str = None) -> List[str]:
        """Get the fallback chain starting from a specific provider"""
        if primary_provider:
            chain = [primary_provider]
            for provider in cls.PROVIDER_HIERARCHY["fallback_chain"]:
                if provider != primary_provider:
                    chain.append(provider)
            return chain
        return [cls.PROVIDER_HIERARCHY["primary"]] + cls.PROVIDER_HIERARCHY["fallback_chain"] 