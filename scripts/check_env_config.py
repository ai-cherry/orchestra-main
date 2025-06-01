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
    'Core': [
        'NODE_ENV',
        'ENVIRONMENT',
        'API_PORT',
        'SERVER_HOST'
    ],
    'Database': [
        'DATABASE_URL',
        'POSTGRES_HOST',
        'POSTGRES_PORT',
        'POSTGRES_DB',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'WEAVIATE_URL'
    ],
    'Authentication': [
        'JWT_SECRET',
        'ADMIN_API_KEY'
    ],
    'Portkey': [
        'PORTKEY_API_KEY'
    ]
}

OPTIONAL_VARS = {
    'Portkey Virtual Keys': [
        'PORTKEY_OPENAI_VIRTUAL_KEY',
        'PORTKEY_ANTHROPIC_VIRTUAL_KEY',
        'PORTKEY_GEMINI_VIRTUAL_KEY',
        'PORTKEY_PERPLEXITY_VIRTUAL_KEY'
    ],
    'Feature Flags': [
        'ENABLE_IMAGE_GEN',
        'ENABLE_VIDEO_SYNTH',
        'ENABLE_ADVANCED_SEARCH',
        'ENABLE_MULTIMODAL'
    ],
    'Media Services': [
        'PEXELS_API_KEY',
        'RESEMBLE_API_KEY'
    ],
    'Monitoring': [
        'SENTRY_DSN',
        'LOG_LEVEL'
    ],
    'Cost Management': [
        'DAILY_COST_LIMIT_USD',
        'COST_ALERT_THRESHOLD',
        'MAX_DALLE_REQUESTS_PER_DAY',
        'MAX_GPT4_TOKENS_PER_DAY'
    ]
}

# Virtual keys available in Portkey
PORTKEY_VIRTUAL_KEYS = {
    'gemini-api-key-1ea5a2': 'Google Gemini',
    'perplexity-api-015025': 'Perplexity',
    'deepseek-api-ke-e7859b': 'DeepSeek',
    'xai-api-key-a760a5': 'X.AI Grok',
    'openai-api-key-345cc9': 'OpenAI (GPT-4, DALL-E)',
    'anthropic-api-k-6feca8': 'Anthropic Claude',
    'together-ai-670469': 'Together AI',
    'openrouter-api-15df95': 'OpenRouter'
}


def check_env_var(var_name: str) -> Tuple[bool, str]:
    """Check if an environment variable is set and return its value (masked)"""
    value = os.environ.get(var_name)
    if value:
        # Mask sensitive values
        if 'KEY' in var_name or 'SECRET' in var_name or 'PASSWORD' in var_name:
            masked = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '*' * len(value)
            return True, masked
        else:
            return True, value
    return False, 'NOT SET'


def validate_portkey_virtual_key(key_value: str) -> bool:
    """Validate if a virtual key matches known Portkey virtual keys"""
    return key_value in PORTKEY_VIRTUAL_KEYS


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'=' * 60}")
    print(f"{title:^60}")
    print('=' * 60)


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
            if not exists:
                missing_required.append(var)
    
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
        'PORTKEY_OPENAI_VIRTUAL_KEY',
        'PORTKEY_ANTHROPIC_VIRTUAL_KEY',
        'PORTKEY_GEMINI_VIRTUAL_KEY',
        'PORTKEY_PERPLEXITY_VIRTUAL_KEY'
    ]
    
    for var in portkey_vars:
        value = os.environ.get(var)
        if value:
            if validate_portkey_virtual_key(value):
                provider = PORTKEY_VIRTUAL_KEYS.get(value, 'Unknown')
                print(f"  ✅ {var}: {value} ({provider})")
            else:
                print(f"  ⚠️  {var}: {value} (NOT a valid Portkey virtual key)")
    
    print_section("Available Portkey Virtual Keys")
    
    print("\nYour Portkey account has these virtual keys available:")
    for key, provider in PORTKEY_VIRTUAL_KEYS.items():
        print(f"  • {key} - {provider}")
    
    print_section("Summary")
    
    if missing_required:
        print(f"\n❌ Missing {len(missing_required)} required variables:")
        for var in missing_required:
            print(f"   - {var}")
        print("\n⚠️  Please set these variables in your .env file or environment")
        return 1
    else:
        print("\n✅ All required environment variables are set!")
        print("\n💡 Tip: Check optional variables for enhanced functionality")
        return 0


if __name__ == "__main__":
    # Load .env file if it exists
    if os.path.exists('.env'):
        print("Loading variables from .env file...")
        from dotenv import load_dotenv
        load_dotenv()
    
    sys.exit(main()) 