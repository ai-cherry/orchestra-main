#!/usr/bin/env python

import os
import requests

portkey_api_key = os.environ.get("PORTKEY_API_KEY", "pk-AdZZMDIwNWU2ZGMxNmRjZWIzMmY2NTJjYzg0NDBhODJlN2Q=")

print(f"Testing Portkey API key: {portkey_api_key[:5]}...{portkey_api_key[-5:]}")

# Test a simple API call to Portkey
headers = {
    "Authorization": f"Bearer {portkey_api_key}",
    "Content-Type": "application/json"
}

# Try a simple call to OpenAI via Portkey
try:
    response = requests.post(
        "https://api.portkey.ai/v1/completions",
        headers=headers,
        json={
            "model": "gpt-3.5-turbo-instruct",
            "prompt": "Hello, world!",
            "max_tokens": 10
        }
    )
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text[:100]}...")
    
    if response.status_code == 200:
        print("API key works for basic operations!")
    else:
        print(f"API key does not work. Status code: {response.status_code}")
        
except Exception as e:
    print(f"Error testing API key: {e}")
