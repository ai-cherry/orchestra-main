#!/usr/bin/env python3
"""
Quick test script to verify Orchestra AI setup is working
"""

import requests
import sys
import os

def test_api_health():
    """Test if the API is responding"""
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running and healthy")
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API is not responding (not running?)")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_frontend():
    """Test if the frontend is accessible"""
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running and accessible")
            return True
        else:
            print(f"❌ Frontend returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Frontend is not responding (not running?)")
        return False
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False

def test_imports():
    """Test if critical imports are working"""
    try:
        sys.path.insert(0, 'api')
        from database.connection import init_database
        from services.file_service import enhanced_file_service
        print("✅ All critical imports working")
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def main():
    print("🎼 Orchestra AI Setup Test")
    print("=" * 30)
    
    # Check if we're in the right directory
    if not os.path.exists('api') or not os.path.exists('web'):
        print("❌ Please run this from the orchestra-dev root directory")
        sys.exit(1)
    
    tests = [
        ("Import Test", test_imports),
        ("API Health Check", test_api_health), 
        ("Frontend Check", test_frontend)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        result = test_func()
        results.append(result)
    
    print(f"\n🎯 Test Results:")
    print(f"Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! Orchestra AI is ready to use!")
        print("\n📚 Access points:")
        print("  Frontend:  http://localhost:3000")
        print("  API:       http://localhost:8000") 
        print("  API Docs:  http://localhost:8000/docs")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        if not results[0]:  # Import test failed
            print("💡 Try running: ./setup_dev_environment.sh")
        if not results[1]:  # API test failed
            print("💡 Try running: ./start_api.sh")
        if not results[2]:  # Frontend test failed
            print("💡 Try running: ./start_frontend.sh")

if __name__ == "__main__":
    main() 