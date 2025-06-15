#!/usr/bin/env python3
"""
Orchestra AI - Phase 1 Deployment Test
Tests all components are working correctly
"""

import requests
import json
import time
import subprocess
import os
from pathlib import Path

def test_flask_app():
    """Test if Flask app is running"""
    print("🔍 Testing Flask app...")
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        if response.status_code == 200:
            print("  ✅ Flask app is running")
            return True
        else:
            print(f"  ❌ Flask app returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Flask app not accessible: {e}")
        print("  💡 Start with: python src/main.py")
        return False

def test_chat_v2_endpoint():
    """Test the new chat v2 endpoint"""
    print("\n🔍 Testing chat v2 endpoint...")
    
    test_data = {
        "message": "What is Orchestra AI?",
        "persona": "sophia",
        "search_mode": "normal",
        "session_id": "test_session_123"
    }
    
    try:
        response = requests.post(
            "http://localhost:5000/api/chat/v2",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("  ✅ Chat v2 endpoint working")
            print(f"  Response preview: {data.get('response', '')[:100]}...")
            return True
        else:
            print(f"  ❌ Chat v2 returned status {response.status_code}")
            print(f"  Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Chat v2 test failed: {e}")
        return False

def test_search_modes():
    """Test search modes endpoint"""
    print("\n🔍 Testing search modes endpoint...")
    
    try:
        response = requests.get("http://localhost:5000/api/search/modes", timeout=5)
        if response.status_code == 200:
            modes = response.json()
            print("  ✅ Search modes endpoint working")
            print(f"  Available modes: {', '.join(modes.keys())}")
            return True
        else:
            print(f"  ❌ Search modes returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Search modes test failed: {e}")
        return False

def test_frontend():
    """Test if frontend is accessible"""
    print("\n🔍 Testing frontend...")
    
    try:
        # Test local dev server
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("  ✅ Frontend dev server is running")
            return True
    except:
        pass
    
    # Test Vercel deployment
    try:
        response = requests.get("https://modern-admin.vercel.app", timeout=10)
        if response.status_code == 200:
            print("  ✅ Frontend is live on Vercel")
            return True
        else:
            print(f"  ⚠️  Vercel returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Frontend test failed: {e}")
        return False

def check_api_keys():
    """Check which API keys are configured"""
    print("\n🔑 Checking API keys...")
    
    required_keys = [
        'OPENAI_API_KEY',
        'OPENROUTER_API_KEY',
        'PINECONE_API_KEY',
        'REDIS_URL',
        'DATABASE_URL'
    ]
    
    configured = 0
    missing = []
    
    for key in required_keys:
        if os.getenv(key):
            print(f"  ✅ {key}: Configured")
            configured += 1
        else:
            print(f"  ❌ {key}: Missing")
            missing.append(key)
    
    print(f"\n  Summary: {configured}/{len(required_keys)} keys configured")
    return configured, missing

def start_flask_app():
    """Attempt to start Flask app"""
    print("\n🚀 Starting Flask app...")
    
    try:
        # Check if already running
        response = requests.get("http://localhost:5000/api/health", timeout=2)
        if response.status_code == 200:
            print("  ✅ Flask app already running")
            return True
    except:
        pass
    
    # Start Flask app in background
    env = os.environ.copy()
    env['FLASK_ENV'] = 'development'
    
    proc = subprocess.Popen(
        ['python', 'src/main.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for startup
    print("  ⏳ Waiting for Flask app to start...")
    for i in range(30):
        time.sleep(1)
        try:
            response = requests.get("http://localhost:5000/api/health", timeout=1)
            if response.status_code == 200:
                print("  ✅ Flask app started successfully")
                return True
        except:
            pass
    
    print("  ❌ Flask app failed to start")
    return False

def main():
    """Run all tests"""
    print("🚀 Orchestra AI Phase 1 Deployment Test\n")
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check API keys
    configured_keys, missing_keys = check_api_keys()
    
    # Test Flask app
    flask_ok = test_flask_app()
    
    if not flask_ok:
        # Try to start it
        start_flask_app()
        flask_ok = test_flask_app()
    
    if flask_ok:
        # Test endpoints
        chat_ok = test_chat_v2_endpoint()
        modes_ok = test_search_modes()
    else:
        chat_ok = False
        modes_ok = False
    
    # Test frontend
    frontend_ok = test_frontend()
    
    # Summary
    print("\n" + "="*50)
    print("📊 Deployment Test Summary")
    print("="*50)
    print(f"{'✅' if configured_keys >= 3 else '❌'} API Keys: {configured_keys} configured")
    print(f"{'✅' if flask_ok else '❌'} Flask Backend: {'Running' if flask_ok else 'Not running'}")
    print(f"{'✅' if chat_ok else '❌'} Chat v2 API: {'Working' if chat_ok else 'Not working'}")
    print(f"{'✅' if modes_ok else '❌'} Search Modes: {'Available' if modes_ok else 'Not available'}")
    print(f"{'✅' if frontend_ok else '❌'} Frontend: {'Accessible' if frontend_ok else 'Not accessible'}")
    
    if missing_keys and len(missing_keys) <= 3:
        print(f"\n⚠️  Add these critical keys to .env:")
        for key in missing_keys:
            print(f"   - {key}")
    
    # Overall status
    all_ok = flask_ok and chat_ok and frontend_ok and configured_keys >= 3
    print(f"\n{'🎉 Deployment successful!' if all_ok else '⚠️  Deployment needs attention'}")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 