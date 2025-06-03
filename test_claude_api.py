#!/usr/bin/env python3
import asyncio
import aiohttp
import os
from pathlib import Path

async def test_claude():
    # Load .env
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    print(f"API Key: {api_key[:20]}...")
    
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "Say hello"}
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        ) as response:
            print(f"Status: {response.status}")
            result = await response.text()
            print(f"Response: {result}")

asyncio.run(test_claude())