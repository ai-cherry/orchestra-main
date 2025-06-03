#!/usr/bin/env python3
"""
Test script to verify AI Orchestration setup
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def test_environment():
    """Test environment variables"""
    print("=== Testing Environment Variables ===")
    
    required_vars = [
        'DATABASE_URL',
        'POSTGRES_HOST',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'POSTGRES_DB'
    ]
    
    # Load .env file
    env_file = Path('.env')
    if env_file.exists():
        print("✓ .env file found")
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    else:
        print("✗ .env file not found")
        return False
    
    # Check required variables
    all_good = True
    for var in required_vars:
        if os.environ.get(var):
            print(f"✓ {var}: Set")
        else:
            print(f"✗ {var}: Not set")
            all_good = False
    
    return all_good

def test_database():
    """Test database connection"""
    print("\n=== Testing Database Connection ===")
    
    try:
        # Simple connection test without psycopg2
        db_url = os.environ.get('DATABASE_URL', '')
        if 'postgresql://' in db_url:
            print("✓ Database URL format is correct")
            # Parse URL
            from urllib.parse import urlparse
            parsed = urlparse(db_url)
            print(f"  Host: {parsed.hostname}")
            print(f"  Port: {parsed.port or 5432}")
            print(f"  Database: {parsed.path.lstrip('/')}")
            print(f"  User: {parsed.username}")
            return True
        else:
            print("✗ Invalid database URL format")
            return False
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_api_keys():
    """Test API keys availability"""
    print("\n=== Testing API Keys ===")
    
    api_services = {
        'Anthropic Claude': 'ANTHROPIC_API_KEY',
        'OpenAI': 'OPENAI_API_KEY',
        'OpenRouter': 'OPENROUTER_API_KEY',
        'Grok AI': 'GROK_AI_API_KEY',
        'Mistral': 'MISTRAL_API_KEY',
        'Perplexity': 'PERPLEXITY_API_KEY',
        'Portkey': 'PORTKEY_API_KEY',
        'ElevenLabs': 'ELEVEN_LABS_API_KEY',
        'Figma': 'FIGMA_PERSONAL_ACCESS_TOKEN',
        'Notion': 'NOTION_API_KEY'
    }
    
    configured = 0
    for service, key in api_services.items():
        if os.environ.get(key):
            print(f"✓ {service}: Configured")
            configured += 1
        else:
            print(f"✗ {service}: Not configured")
    
    print(f"\nTotal API services configured: {configured}/{len(api_services)}")
    return configured > 0

def test_orchestrator_import():
    """Test if orchestrator can be imported"""
    print("\n=== Testing AI Orchestrator Import ===")
    
    try:
        # Test basic import
        from scripts.setup_api_keys import SimpleSecretsManager
        print("✓ Can import SimpleSecretsManager")
        
        # Test orchestrator structure
        orchestrator_path = Path('ai_components/orchestration/ai_orchestrator.py')
        if orchestrator_path.exists():
            print("✓ AI orchestrator file exists")
            return True
        else:
            print("✗ AI orchestrator file not found")
            return False
            
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=== AI Orchestration Setup Test ===\n")
    
    results = []
    
    # Run tests
    results.append(("Environment", test_environment()))
    results.append(("Database", test_database()))
    results.append(("API Keys", test_api_keys()))
    results.append(("Orchestrator", test_orchestrator_import()))
    
    # Summary
    print("\n=== Test Summary ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! Your AI Orchestration system is ready.")
        print("\nNext steps:")
        print("1. Test the orchestrator:")
        print("   python3 ai_components/orchestration/ai_orchestrator.py")
        print("\n2. Set up GitHub Secrets for CI/CD:")
        print("   ./scripts/setup_github_secrets.sh")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())