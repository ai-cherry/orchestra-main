#!/usr/bin/env python3
"""
ai_assist.py - Simplified multi-LLM assistant for Orchestra AI

Uses OpenRouter to access various LLMs for different tasks:
- GPT-4o-mini: Code reviews
- Claude Sonnet 4: Architecture & design
- Gemini 2.5 Flash: Performance optimization
"""

import sys
import os
import json
import requests
from pathlib import Path
from typing import Optional

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Model mappings - Using Claude Opus 4 for all tasks (world's best coding model)
MODELS = {
    "review": "anthropic/claude-opus-4",     # Code reviews & bug detection
    "design": "anthropic/claude-opus-4",     # Architecture design & planning
    "optimize": "anthropic/claude-opus-4"    # Performance optimization
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
    
    prompt = f"""Please review this Python code and provide:
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
    
    prompt = f"""Optimize this Python code for:
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
Orchestra AI Assistant - Multi-LLM Code Helper

Usage:
  python ai_assist.py review <filepath>    # Code review with GPT-4o-mini
  python ai_assist.py design <filepath>    # Architecture design with Claude
  python ai_assist.py optimize <filepath>  # Performance optimization with Gemini

Examples:
  python ai_assist.py review core/agents/base.py
  python ai_assist.py design services/memory/manager.py
  python ai_assist.py optimize shared/utils/performance.py

Environment:
  Set OPENROUTER_API_KEY before running
""")

def main():
    if len(sys.argv) < 3:
        usage()
        sys.exit(1)
    
    command = sys.argv[1]
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