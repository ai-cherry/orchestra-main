#!/usr/bin/env python3
import os
from pathlib import Path

# Load .env file
env_path = Path('.env')
if env_path.exists():
    print(f"Loading .env from: {env_path.absolute()}")
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                if key == 'ANTHROPIC_API_KEY':
                    print(f"Found ANTHROPIC_API_KEY: {value[:10]}...")
                    os.environ[key] = value

# Check environment
api_key = os.environ.get('ANTHROPIC_API_KEY')
if api_key:
    print(f"\nAPI Key loaded successfully: {api_key[:10]}...")
else:
    print("\nERROR: ANTHROPIC_API_KEY not found!")
    print("\nChecking .env file contents:")
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if 'ANTHROPIC' in line:
                    print(f"  {line.strip()}")