import requests
import json

# Updated Portkey API Configuration - trying different authentication methods
PORTKEY_API_KEY = "hPxFZGd8AN269n4bznDf2/Onbi8I"
PORTKEY_CONFIG = "pc-portke-b43e56"

def test_portkey_auth_methods():
    """Test different Portkey authentication methods"""
    
    # Method 1: Standard Bearer token
    headers_v1 = {
        "Authorization": f"Bearer {PORTKEY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Method 2: x-portkey-api-key header
    headers_v2 = {
        "x-portkey-api-key": PORTKEY_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Method 3: Portkey-Api-Key header
    headers_v3 = {
        "Portkey-Api-Key": PORTKEY_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Method 4: With config header
    headers_v4 = {
        "x-portkey-api-key": PORTKEY_API_KEY,
        "x-portkey-config": PORTKEY_CONFIG,
        "Content-Type": "application/json"
    }
    
    test_methods = [
        ("Bearer Token", headers_v1),
        ("x-portkey-api-key", headers_v2), 
        ("Portkey-Api-Key", headers_v3),
        ("With Config", headers_v4)
    ]
    
    base_urls = [
        "https://api.portkey.ai/v1",
        "https://api.portkey.ai",
        "https://portkey.ai/api/v1"
    ]
    
    endpoints = [
        "/configs",
        "/virtual-keys", 
        "/logs",
        "/chat/completions"
    ]
    
    print("🔧 Testing Portkey API Authentication Methods...")
    
    for base_url in base_urls:
        print(f"\n🌐 Testing base URL: {base_url}")
        
        for method_name, headers in test_methods:
            print(f"\n  📋 Method: {method_name}")
            
            for endpoint in endpoints:
                try:
                    url = f"{base_url}{endpoint}"
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    print(f"    {endpoint}: {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"    ✅ SUCCESS with {method_name} at {base_url}{endpoint}")
                        return True, headers, base_url
                    elif response.status_code == 401:
                        print(f"    ❌ Unauthorized")
                    elif response.status_code == 404:
                        print(f"    ❓ Endpoint not found")
                    else:
                        print(f"    ⚠️  Status: {response.status_code}")
                        
                except Exception as e:
                    print(f"    💥 Error: {str(e)}")
    
    return False, None, None

def test_portkey_chat_endpoint():
    """Test Portkey chat endpoint directly"""
    
    headers = {
        "x-portkey-api-key": PORTKEY_API_KEY,
        "x-portkey-config": PORTKEY_CONFIG,
        "Content-Type": "application/json"
    }
    
    # Test with a simple chat completion
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Hello, this is a test message"}
        ],
        "max_tokens": 50
    }
    
    try:
        response = requests.post(
            "https://api.portkey.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"\n🤖 Chat endpoint test: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Chat endpoint working!")
            print(f"Response: {result.get('choices', [{}])[0].get('message', {}).get('content', 'No content')}")
            return True
        else:
            print(f"❌ Chat failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Chat error: {str(e)}")
        return False

def create_virtual_keys():
    """Create virtual keys for different personas"""
    
    headers = {
        "x-portkey-api-key": PORTKEY_API_KEY,
        "Content-Type": "application/json"
    }
    
    virtual_keys = [
        {
            "name": "sophia-business-key",
            "note": "Virtual key for Sophia persona - business and apartment technology focus",
            "usage": "sophia-persona"
        },
        {
            "name": "karen-clinical-key", 
            "note": "Virtual key for Karen persona - clinical research and healthcare focus",
            "usage": "karen-persona"
        },
        {
            "name": "cherry-general-key",
            "note": "Virtual key for Cherry persona - balanced general assistant",
            "usage": "cherry-persona"
        }
    ]
    
    created_keys = []
    
    for vk_config in virtual_keys:
        try:
            response = requests.post(
                "https://api.portkey.ai/v1/virtual-keys",
                headers=headers,
                json=vk_config,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                created_keys.append(result)
                print(f"✅ Created virtual key: {vk_config['name']}")
            else:
                print(f"❌ Failed to create {vk_config['name']}: {response.text}")
                
        except Exception as e:
            print(f"💥 Error creating {vk_config['name']}: {str(e)}")
    
    return created_keys

if __name__ == "__main__":
    # Test authentication methods
    success, working_headers, working_url = test_portkey_auth_methods()
    
    if success:
        print(f"\n🎉 Found working authentication!")
        print(f"Headers: {working_headers}")
        print(f"Base URL: {working_url}")
    else:
        print("\n🔧 Testing chat endpoint directly...")
        chat_success = test_portkey_chat_endpoint()
        
        if chat_success:
            print("\n🎯 Chat endpoint works - proceeding with setup...")
            
            print("\n📋 Creating virtual keys...")
            virtual_keys = create_virtual_keys()
            
            if virtual_keys:
                print(f"\n✅ Created {len(virtual_keys)} virtual keys successfully!")
            else:
                print("\n⚠️  Virtual key creation may have failed - check manually")
        else:
            print("\n❌ Unable to establish working Portkey connection")
            print("Please verify:")
            print("1. API key is correct and active")
            print("2. Account has proper permissions") 
            print("3. Config ID is valid")

