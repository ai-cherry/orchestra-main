import os
#!/usr/bin/env python3
"""
ai_assist_v0.py - Enhanced Orchestra AI Assistant with v0.dev UI Generation

Features:
- Code review (GPT-4o-mini via OpenRouter)
- Architecture design (Claude 3.5 Sonnet via OpenRouter)
- Performance optimization (Gemini 2.5 Flash via OpenRouter)
- UI generation (v0.dev API) 🆕
"""

import sys
import os
import json
import requests
from pathlib import Path
from typing import Optional
import hashlib
import redis

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
V0_API_KEY = os.getenv("V0_API_KEY")
V0_API_URL = "https://api.v0.dev/v1/chat/completions"

# Redis connection for caching (optional)
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    REDIS_AVAILABLE = r.ping()
except:
    REDIS_AVAILABLE = False

# Model mappings
MODELS = {
    "review": "openai/gpt-4o-mini",
    "design": "anthropic/claude-3.5-sonnet",
    "optimize": "google/gemini-2.5-flash-preview-05-20"
}

def call_llm(model: str, prompt: str) -> str:
    """Send a prompt to OpenRouter for the specified model."""
    if not OPENROUTER_API_KEY:
        return "❌ Error: OPENROUTER_API_KEY not set in environment"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(OPENROUTER_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Error calling {model}: {str(e)}"

def generate_ui(description: str) -> str:
    """Generate UI components using v0.dev."""
    if not V0_API_KEY:
return "❌ Error: V0_API_KEY not set in environment\n\nTo use v0.dev:\n1. Sign up at https://v0.dev\n2. Get your API key\n3. Set: export V0_API_KEY = os.getenv('ORCHESTRA_APP_API_KEY')
    
    # Check cache first
    cache_key = None
    if REDIS_AVAILABLE:
        cache_key = f"ui:{hashlib.md5(description.encode()).hexdigest()}"
        cached = r.get(cache_key)
        if cached:
            return f"📦 (Cached)\n\n{cached}"
    
    headers = {
        "Authorization": f"Bearer {V0_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "v0-1.0-md",
        "messages": [
            {"role": "user", "content": description}
        ]
    }
    
    try:
        response = requests.post(V0_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        result = data["choices"][0]["message"]["content"]
        
        # Cache the result
        if REDIS_AVAILABLE and cache_key:
            r.setex(cache_key, 3600, result)  # Cache for 1 hour
        
        return result
    except Exception as e:
        return f"❌ Error generating UI: {str(e)}"

def read_file(filepath: str) -> Optional[str]:
    """Read file contents."""
    try:
        path = Path(filepath)
        if not path.exists():
            return None
        return path.read_text()
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        return None

def review_code(filepath: str) -> str:
    """Get code review from GPT-4o-mini."""
    content = read_file(filepath)
    if not content:
        return f"❌ Could not read {filepath}"
    
    prompt = f"""Please review this code and provide:
1. Bug detection
2. Style improvements  
3. Performance suggestions
4. Security considerations

File: {filepath}

{content}"""
    
    return call_llm(MODELS["review"], prompt)

def design_architecture(filepath: str) -> str:
    """Get architecture design from Claude Sonnet."""
    content = read_file(filepath)
    if not content:
        return f"❌ Could not read {filepath}"
    
    prompt = f"""Provide a high-level architecture design for this module:
1. Class/method structure
2. Design patterns to apply
3. Integration points
4. Scalability considerations

File: {filepath}

{content}"""
    
    return call_llm(MODELS["design"], prompt)

def optimize_code(filepath: str) -> str:
    """Get optimization suggestions from Gemini."""
    content = read_file(filepath)
    if not content:
        return f"❌ Could not read {filepath}"
    
    prompt = f"""Optimize this code for:
1. Performance (time & space complexity)
2. Modern Python 3.10 features
3. Readability
4. Maintainability

Provide the refactored code with explanations.

File: {filepath}

{content}"""
    
    return call_llm(MODELS["optimize"], prompt)

def usage():
    """Print usage information."""
    print("""
Orchestra AI Assistant - Enhanced with v0.dev UI Generation

Usage:
  python ai_assist_v0.py review <filepath>     # Code review with GPT-4o-mini
  python ai_assist_v0.py design <filepath>     # Architecture design with Claude
  python ai_assist_v0.py optimize <filepath>   # Performance optimization with Gemini
  python ai_assist_v0.py ui "<description>"    # UI generation with v0.dev 🆕

Examples:
  python ai_assist_v0.py review core/agents/base.py
  python ai_assist_v0.py design services/memory/manager.py
  python ai_assist_v0.py optimize shared/utils/performance.py
  python ai_assist_v0.py ui "modern dashboard with sidebar and charts"

UI Generation Examples:
  ai_assist ui "responsive pricing table with 3 tiers"
  ai_assist ui "login form with social auth buttons"
  ai_assist ui "data table with sorting and pagination"
  ai_assist ui "kanban board with drag and drop"

Environment Variables:
  OPENROUTER_API_KEY - For code review/design/optimize
  V0_API_KEY - For UI generation (get from https://v0.dev)
""")

def main():
    if len(sys.argv) < 3:
        usage()
        sys.exit(1)
    
    command = sys.argv[1]
    
    # For UI command, join all remaining args as description
    if command == "ui":
        description = " ".join(sys.argv[2:])
        print(f"\n🎨 Orchestra AI Assistant - UI Generation Mode\n")
        result = generate_ui(description)
        print(result)
        return
    
    # For other commands, second arg is filepath
    filepath = sys.argv[2]
    
    print(f"\n🤖 Orchestra AI Assistant - {command.title()} Mode\n")
    
    if command == "review":
        result = review_code(filepath)
    elif command == "design":
        result = design_architecture(filepath)
    elif command == "optimize":
        result = optimize_code(filepath)
    else:
        usage()
        sys.exit(1)
    
    print(result)

if __name__ == "__main__":
    main() 