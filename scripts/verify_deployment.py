#!/usr/bin/env python3
"""
Verify Cherry AI deployment is working correctly
"""

import requests
import sys
from datetime import datetime

def verify_deployment():
    """Verify the deployment is successful"""
    
    print("🔍 Verifying Cherry AI deployment...")
    print("=" * 50)
    
    url = "https://cherry-ai.me"
    
    try:
        # Check if site is accessible
        response = requests.get(url, timeout=10)
        print(f"✅ Site accessible: {response.status_code}")
        
        # Check for correct branding
        content = response.text
        
        if "Cherry AI" in content:
            print("✅ Correct title found: Cherry AI")
        else:
            print("❌ Title not found in HTML")
            
        if "Cherry Admin UI" in content:
            print("❌ Old branding still present in HTML")
        else:
            print("✅ No old branding in HTML")
            
        # Check for new assets
        if "index-1748981508195" in content:
            print("✅ Latest assets being served (timestamp: 1748981508195)")
        else:
            print("⚠️  Assets may not be the latest version")
            
        # Check cache headers
        asset_url = f"{url}/assets/index-1748981508195.js"
        asset_response = requests.head(asset_url, timeout=10)
        cache_control = asset_response.headers.get('Cache-Control', '')
        
        if 'no-cache' not in cache_control:
            print(f"✅ Asset caching enabled: {cache_control}")
        else:
            print(f"⚠️  Asset caching may be disabled: {cache_control}")
            
        # Test login endpoint
        login_url = f"{url}/api/auth/login"
        login_data = {
            "username": "scoobyjava",
            "password": "Huskers1983$"
        }
        
        login_response = requests.post(login_url, json=login_data, timeout=10)
        
        if login_response.status_code == 200:
            print("✅ Login endpoint working")
            data = login_response.json()
            if 'token' in data:
                print("✅ Authentication successful - token received")
            else:
                print("⚠️  Login successful but no token in response")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error accessing site: {e}")
        return False
        
    print("=" * 50)
    print(f"✅ Deployment verification complete at {datetime.now()}")
    
    # Instructions for user
    print("\n📝 Next steps:")
    print("1. Open https://cherry-ai.me in a new incognito/private browser window")
    print("2. You should see 'Cherry AI' as the page title")
    print("3. Login with username: scoobyjava, password: Huskers1983$")
    print("4. If you still see old content, try:")
    print("   - Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)")
    print("   - Clear browser cache for cherry-ai.me")
    print("   - Use a different browser or device")
    
    return True

if __name__ == "__main__":
    success = verify_deployment()
    sys.exit(0 if success else 1)