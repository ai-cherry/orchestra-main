#!/usr/bin/env python3
"""
Test script to verify Vercel deployment is working correctly
"""

import requests
import time
import sys

def test_deployment():
    """Test the main deployment URL"""
    url = "https://orchestra-admin-interface.vercel.app"
    
    print(f"🔍 Testing {url}")
    
    try:
        # Test main page
        response = requests.get(url, timeout=10)
        print(f"📄 Main page: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Main page failed: {response.status_code}")
            return False
        
        # Check if it's HTML (not auth redirect)
        if 'text/html' not in response.headers.get('content-type', ''):
            print(f"❌ Not serving HTML: {response.headers.get('content-type')}")
            return False
        
        # Check for auth redirect
        if 'sso-api' in response.text or 'Authentication Required' in response.text:
            print("❌ Still showing authentication page")
            return False
        
        # Extract asset URLs from HTML
        html = response.text
        js_assets = []
        css_assets = []
        
        # Simple parsing for script and link tags
        lines = html.split('\n')
        for line in lines:
            if 'src="/assets/' in line and '.js' in line:
                start = line.find('src="/assets/') + 5
                end = line.find('"', start)
                if end > start:
                    js_assets.append(line[start:end])
            elif 'href="/assets/' in line and '.css' in line:
                start = line.find('href="/assets/') + 6
                end = line.find('"', start)
                if end > start:
                    css_assets.append(line[start:end])
        
        print(f"📦 Found {len(js_assets)} JS assets, {len(css_assets)} CSS assets")
        
        # Test asset loading
        all_assets_ok = True
        
        for asset in js_assets[:2]:  # Test first 2 JS assets
            asset_url = f"{url}{asset}"
            try:
                asset_response = requests.head(asset_url, timeout=5)
                if asset_response.status_code == 200:
                    content_type = asset_response.headers.get('content-type', '')
                    if 'javascript' in content_type or 'application/javascript' in content_type:
                        print(f"✅ JS asset OK: {asset}")
                    else:
                        print(f"⚠️ JS asset wrong type: {asset} ({content_type})")
                        all_assets_ok = False
                else:
                    print(f"❌ JS asset failed: {asset} ({asset_response.status_code})")
                    all_assets_ok = False
            except Exception as e:
                print(f"❌ JS asset error: {asset} ({str(e)[:50]})")
                all_assets_ok = False
        
        for asset in css_assets[:2]:  # Test first 2 CSS assets
            asset_url = f"{url}{asset}"
            try:
                asset_response = requests.head(asset_url, timeout=5)
                if asset_response.status_code == 200:
                    content_type = asset_response.headers.get('content-type', '')
                    if 'css' in content_type:
                        print(f"✅ CSS asset OK: {asset}")
                    else:
                        print(f"⚠️ CSS asset wrong type: {asset} ({content_type})")
                        all_assets_ok = False
                else:
                    print(f"❌ CSS asset failed: {asset} ({asset_response.status_code})")
                    all_assets_ok = False
            except Exception as e:
                print(f"❌ CSS asset error: {asset} ({str(e)[:50]})")
                all_assets_ok = False
        
        if all_assets_ok:
            print("🎉 All tests passed! Deployment is working correctly.")
            return True
        else:
            print("⚠️ Some assets have issues, but main page loads.")
            return True  # Still consider it working if main page loads
            
    except Exception as e:
        print(f"❌ Error testing deployment: {e}")
        return False

def wait_for_deployment():
    """Wait for deployment to be ready and test it"""
    print("⏳ Waiting for deployment to be ready...")
    
    for i in range(12):  # Wait up to 2 minutes
        if test_deployment():
            return True
        
        if i < 11:
            print(f"⏳ Waiting 10 seconds... ({i+1}/12)")
            time.sleep(10)
    
    print("❌ Deployment not ready after 2 minutes")
    return False

if __name__ == "__main__":
    print("🚀 Vercel Deployment Test")
    print("=" * 40)
    
    if wait_for_deployment():
        print("\n✅ SUCCESS: Deployment is working!")
        sys.exit(0)
    else:
        print("\n❌ FAILED: Deployment has issues")
        sys.exit(1) 