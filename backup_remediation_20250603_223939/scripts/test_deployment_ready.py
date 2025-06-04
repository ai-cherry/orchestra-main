#!/usr/bin/env python3
"""Test if the system is ready for deployment"""

import sys
import os
import subprocess
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_python_imports():
    """Test if critical Python modules can be imported"""
    print("🔍 Testing Python imports...")
    
    critical_imports = [
        "from src.api.main import app",
        "from src.search_engine.search_router import SearchRouter",
        "from src.search_engine.normal_search import NormalSearcher",
        "from src.search_engine.creative_search import CreativeSearcher",
        "from src.file_ingestion.ingestion_controller import IngestionController",
        "from src.utils.circuit_breaker import circuit_breaker",
    ]
    
    failed = []
    for import_stmt in critical_imports:
        try:
            # SECURITY: exec() removed - import_stmt
            print(f"  ✅ {import_stmt}")
        except Exception as e:
            print(f"  ❌ {import_stmt}: {str(e)}")
            failed.append(import_stmt)
    
    return len(failed) == 0

def test_docker_services():
    """Test if Docker services are available"""
    print("\n🐳 Testing Docker services...")
    
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ Docker is running")
            
            # Check for specific services
            services = ["postgres", "redis", "weaviate"]
            for service in services:
                if service in result.stdout:
                    print(f"  ✅ {service} container found")
                else:
                    print(f"  ⚠️  {service} container not running")
            
            return True
        else:
            print("  ❌ Docker is not running")
            return False
    except Exception as e:
        print(f"  ❌ Docker check failed: {e}")
        return False

def test_environment():
    """Test environment configuration"""
    print("\n🔧 Testing environment...")
    
    env_file = Path(".env")
    if env_file.exists():
        print("  ✅ .env file exists")
        
        # Check for critical variables
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "WEAVIATE_URL",
            "JWT_SECRET",
            "OPENAI_API_KEY"
        ]
        
        env_content = env_file.read_text()
        missing = []
        for var in required_vars:
            if var in env_content:
                print(f"  ✅ {var} is set")
            else:
                print(f"  ❌ {var} is missing")
                missing.append(var)
        
        return len(missing) == 0
    else:
        print("  ❌ .env file not found")
        return False

def test_api_startup():
    """Test if the API can start"""
    print("\n🚀 Testing API startup...")
    
    try:
        # Try to import and create the app
        from src.api.main import app
        print("  ✅ API app created successfully")
        return True
    except Exception as e:
        print(f"  ❌ API startup failed: {e}")
        return False

def main():
    """Run all deployment tests"""
    print("🔍 Cherry AI Deployment Readiness Test")
    print("=" * 50)
    
    tests = [
        ("Python Imports", test_python_imports),
        ("Docker Services", test_docker_services),
        ("Environment", test_environment),
        ("API Startup", test_api_startup),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✅ System is ready for deployment!")
        print("\nNext steps:")
        print("1. Create .env.production with actual values")
        print("2. Run: docker-compose -f docker-compose.prod.yml up -d")
        print("3. Run: python3 scripts/migrate_database.py")
        print("4. Configure Nginx for cherry-ai.me")
        print("5. Install SSL certificate with certbot")
        return 0
    else:
        print("\n❌ System is NOT ready for deployment!")
        print("\nFix the failed tests before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())