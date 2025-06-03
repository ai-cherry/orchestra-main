#!/usr/bin/env python3
"""
"""
    "OPENAI_API_KEY": {
        "virtual_key": "openai-api-key-345cc9",
        "env_var": "PORTKEY_OPENAI_VIRTUAL_KEY",
        "provider": "OpenAI",
    },
    "ANTHROPIC_API_KEY": {
        "virtual_key": "anthropic-api-k-6feca8",
        "env_var": "PORTKEY_ANTHROPIC_VIRTUAL_KEY",
        "provider": "Anthropic",
    },
    "DEEPSEEK_API_KEY": {
        "virtual_key": "deepseek-api-ke-e7859b",
        "env_var": "PORTKEY_DEEPSEEK_VIRTUAL_KEY",
        "provider": "DeepSeek",
    },
    "PERPLEXITY_API_KEY": {
        "virtual_key": "perplexity-api-015025",
        "env_var": "PORTKEY_PERPLEXITY_VIRTUAL_KEY",
        "provider": "Perplexity",
    },
    "OPENROUTER_API_KEY": {
        "virtual_key": "openrouter-api-15df95",
        "env_var": "PORTKEY_OPENROUTER_VIRTUAL_KEY",
        "provider": "OpenRouter",
    },
}

def check_existing_keys() -> Dict[str, bool]:
    """Check which direct API keys are currently set"""
    """Generate Portkey configuration based on existing keys"""
    config_lines.append("# Portkey Configuration")
    config_lines.append("PORTKEY_API_KEY=your-portkey-api-key  # Get from https://app.portkey.ai")
    config_lines.append("PORTKEY_BASE_URL=https://api.portkey.ai/v1")
    config_lines.append("")
    config_lines.append("# Virtual Key Mappings")

    existing_keys = check_existing_keys()
    for direct_key, mapping in KEY_MAPPINGS.items():
        if existing_keys.get(direct_key):
            config_lines.append(f"{mapping['env_var']}={mapping['virtual_key']}  # {mapping['provider']}")

    return config_lines

def update_code_references():
    """Generate code update suggestions"""
    print("\n📝 Code Update Suggestions:")
    print("\n1. Replace direct API client initialization:")
    print("   Before:")
    print("   ```python")
    print("   import openai")
    print("   openai.api_key = os.getenv('OPENAI_API_KEY')")
    print("   ```")
    print("\n   After:")
    print("   ```python")
    print("   from portkey_ai import Portkey")
    print("   portkey = Portkey(")
    print("       api_key=os.getenv('PORTKEY_API_KEY'),")
    print("       virtual_key=os.getenv('PORTKEY_OPENAI_VIRTUAL_KEY')")
    print("   )")
    print("   ```")

    print("\n2. Update service initialization:")
    print("   ```typescript")
    print("   import { getPortkeyService } from '@/services/portkey/PortkeyService';")
    print("   const portkey = getPortkeyService();")
    print("   ")
    print("   // Generate text")
    print("   const result = await portkey.generateText(prompt);")
    print("   ")
    print("   // Generate images")
    print("   const image = await portkey.generateImage(prompt);")
    print("   ```")

def main():
    """Main migration function"""
    print("🚀 Portkey Migration Assistant")
    print("=" * 50)

    # Check for existing .env file
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ No .env file found. Please create one first.")
        return 1

    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    # Check existing configuration
    print("\n🔍 Checking current configuration...")
    existing_keys = check_existing_keys()

    has_portkey = bool(os.environ.get("PORTKEY_API_KEY"))
    has_direct_keys = any(existing_keys.values())

    if has_portkey:
        print("✅ Portkey is already configured!")
        if has_direct_keys:
            print("⚠️  You also have direct API keys set. Consider removing them.")
    elif has_direct_keys:
        print("📋 Found direct API keys:")
        for key, exists in existing_keys.items():
            if exists:
                provider = KEY_MAPPINGS[key]["provider"]
                print(f"   • {key} ({provider})")

        print("\n🔄 Migration Steps:")
        print("\n1. Sign up for Portkey at https://app.portkey.ai")
        print("2. Add the following to your .env file:")
        print("   " + "-" * 40)
        for line in generate_portkey_config():
            print(f"   {line}")
        print("   " + "-" * 40)

        print("\n3. Update your code to use Portkey:")
        update_code_references()

        print("\n4. Test your configuration:")
        print("   ```bash")
        print("   npm run check:env  # or python scripts/check_env_config.py")
        print("   ```")

        print("\n5. Once verified, remove direct API keys from .env")

        print("\n💡 Benefits of using Portkey:")
        print("   • Unified billing and cost tracking")
        print("   • Automatic fallback handling")
        print("   • Request caching and optimization")
        print("   • Single dashboard for all AI services")
        print("   • Built-in rate limiting and retries")
    else:
        print("❌ No AI service keys found. Please configure either:")
        print("   • Portkey (recommended)")
        print("   • Direct API keys")

    print("\n📚 Resources:")
    print("   • Portkey Docs: https://docs.portkey.ai")
    print("   • Virtual Keys: https://app.portkey.ai/virtual-keys")
    print("   • Orchestra Docs: docs/SECRETS_CONFIGURATION.md")

    return 0

if __name__ == "__main__":
    sys.exit(main())
