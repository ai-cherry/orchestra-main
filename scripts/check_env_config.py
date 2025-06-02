#!/usr/bin/env python3
"""
Environment Configuration Checker
Validates that all required environment variables are properly set
"""

import os
import sys
from typing import Dict, List, Tuple

# Define required and optional environment variables
REQUIRED_VARS = {
    "Core": ["NODE_ENV", "ENVIRONMENT", "API_PORT", "SERVER_HOST"],
    "Database": [
        "DATABASE_URL",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "WEAVIATE_URL",
    ],
    "Authentication": ["JWT_SECRET", "ADMIN_API_KEY"],
    "AI Services (at least one)": ["PORTKEY_API_KEY"],  # Preferred
}

OPTIONAL_VARS = {
    "Portkey Virtual Keys": [
        "PORTKEY_OPENAI_VIRTUAL_KEY",
        "PORTKEY_ANTHROPIC_VIRTUAL_KEY",
        "PORTKEY_GEMINI_VIRTUAL_KEY",
        "PORTKEY_PERPLEXITY_VIRTUAL_KEY",
    ],
    "Direct AI Keys (Alternative to Portkey)": [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "DEEPSEEK_API_KEY",
        "PERPLEXITY_API_KEY",
        "MISTRAL_API_KEY",
        "OPENROUTER_API_KEY",
        "HUGGINGFACE_API_TOKEN",
    ],
    "Feature Flags": ["ENABLE_IMAGE_GEN", "ENABLE_VIDEO_SYNTH", "ENABLE_ADVANCED_SEARCH", "ENABLE_MULTIMODAL"],
    "Media Services": [
        "PEXELS_API_KEY",
        "ELEVENLABS_API_KEY",
        "RECRAFT_API_KEY",
    ],
    "Monitoring": ["SENTRY_DSN", "LOG_LEVEL", "LANGSMITH_API_KEY"],
    "Cost Management": [
        "DAILY_COST_LIMIT_USD",
        "COST_ALERT_THRESHOLD",
        "MAX_DALLE_REQUESTS_PER_DAY",
        "MAX_GPT4_TOKENS_PER_DAY",
    ],
    "Infrastructure": ["VULTR_PROJECT_ID", "PULUMI_ACCESS_TOKEN", "DIGITALOCEAN_TOKEN"],
    "Integration Services": ["SLACK_BOT_TOKEN", "NOTION_API_KEY", "GONG_ACCESS_KEY", "APOLLO_API_KEY"],
}

# Virtual keys available in Portkey
PORTKEY_VIRTUAL_KEYS = {
    "gemini-api-key-1ea5a2": "Google Gemini",
    "perplexity-api-015025": "Perplexity",
    "deepseek-api-ke-e7859b": "DeepSeek",
    "xai-api-key-a760a5": "X.AI Grok",
    "openai-api-key-345cc9": "OpenAI (GPT-4, DALL-E)",
    "anthropic-api-k-6feca8": "Anthropic Claude",
    "together-ai-670469": "Together AI",
    "openrouter-api-15df95": "OpenRouter",
}

def check_env_var(var_name: str) -> Tuple[bool, str]:
    """Check if an environment variable is set and return its value (masked)"""
    value = os.environ.get(var_name)
    if value:
        # Mask sensitive values
        if "KEY" in var_name or "SECRET" in var_name or "PASSWORD" in var_name or "TOKEN" in var_name:
            masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "*" * len(value)
            return True, masked
        else:
            return True, value
    return False, "NOT SET"

def validate_portkey_virtual_key(key_value: str) -> bool:
    """Validate if a virtual key matches known Portkey virtual keys"""
    return key_value in PORTKEY_VIRTUAL_KEYS

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'=' * 60}")
    print(f"{title:^60}")
    print("=" * 60)

def check_ai_service_config() -> bool:
    """Check if at least one AI service is configured"""
    has_portkey = os.environ.get("PORTKEY_API_KEY")
    direct_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY", "PERPLEXITY_API_KEY", "MISTRAL_API_KEY"]
    has_direct = any(os.environ.get(key) for key in direct_keys)

    return bool(has_portkey or has_direct)

def main():
    """Main function to check environment configuration"""
    print("Orchestra AI Environment Configuration Checker")
    print_section("Checking Required Variables")

    missing_required = []

    # Check required variables
    for category, vars_list in REQUIRED_VARS.items():
        print(f"\n{category}:")
        for var in vars_list:
            exists, value = check_env_var(var)
            status = "✅" if exists else "❌"
            print(f"  {status} {var}: {value}")
            if not exists and var != "PORTKEY_API_KEY":  # Special handling for AI services
                missing_required.append(var)

    # Special check for AI services
    print("\n🤖 AI Service Configuration:")
    if check_ai_service_config():
        print("  ✅ At least one AI service is configured")
        if os.environ.get("PORTKEY_API_KEY"):
            print("  ✅ Using Portkey (recommended)")
        else:
            print("  ⚠️  Using direct API keys (consider Portkey for better management)")
    else:
        print("  ❌ No AI service configured!")
        missing_required.append("AI_SERVICE")

    print_section("Checking Optional Variables")

    # Check optional variables
    for category, vars_list in OPTIONAL_VARS.items():
        print(f"\n{category}:")
        for var in vars_list:
            exists, value = check_env_var(var)
            status = "✅" if exists else "⚠️"
            print(f"  {status} {var}: {value}")

    print_section("Portkey Virtual Keys Validation")

    # Validate Portkey virtual keys
    portkey_vars = [
        "PORTKEY_OPENAI_VIRTUAL_KEY",
        "PORTKEY_ANTHROPIC_VIRTUAL_KEY",
        "PORTKEY_GEMINI_VIRTUAL_KEY",
        "PORTKEY_PERPLEXITY_VIRTUAL_KEY",
    ]

    if os.environ.get("PORTKEY_API_KEY"):
        print("\n✅ Portkey API Key is set")
        for var in portkey_vars:
            value = os.environ.get(var)
            if value:
                if validate_portkey_virtual_key(value):
                    provider = PORTKEY_VIRTUAL_KEYS.get(value, "Unknown")
                    print(f"  ✅ {var}: {value} ({provider})")
                else:
                    print(f"  ⚠️  {var}: {value} (NOT a valid Portkey virtual key)")

        print("\nAvailable Portkey Virtual Keys:")
        for key, provider in PORTKEY_VIRTUAL_KEYS.items():
            print(f"  • {key} - {provider}")
    else:
        print("\n⚠️  Portkey not configured - using direct API keys")

    print_section("Configuration Recommendations")

    print("\n🎯 Best Practices:")
    print("1. Use Portkey for unified AI service management")
    print("2. Set up monitoring with Sentry or similar")
    print("3. Configure cost limits for AI services")
    print("4. Enable feature flags based on your needs")
    print("5. Use environment-specific configurations")

    print_section("Summary")

    if missing_required:
        print(f"\n❌ Missing {len(missing_required)} required variables:")
        for var in missing_required:
            print(f"   - {var}")
        print("\n⚠️  Please set these variables in your .env file or environment")
        return 1
    else:
        print("\n✅ All required environment variables are set!")

        # Additional recommendations
        if not os.environ.get("PORTKEY_API_KEY"):
            print("\n💡 Consider using Portkey for better AI service management")

        if not os.environ.get("SENTRY_DSN"):
            print("\n💡 Consider setting up error monitoring with Sentry")

        if not os.environ.get("SLACK_BOT_TOKEN"):
            print("\n💡 Consider setting up Slack notifications")

        return 0

if __name__ == "__main__":
    # Load .env file if it exists
    if os.path.exists(".env"):
        print("Loading variables from .env file...")
        from dotenv import load_dotenv

        load_dotenv()

    sys.exit(main())
