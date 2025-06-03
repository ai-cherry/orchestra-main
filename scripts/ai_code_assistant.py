#!/usr/bin/env python3
"""
AI Code Assistant - Direct interface for coding with AI assistance
Works with Claude, OpenAI, and local orchestrator
"""

import os
import sys
import asyncio
import logging
from typing import Optional, Dict, Any
import aiohttp
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.setup_secrets_manager import SecretsManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class AICodeAssistant:
    """Direct AI coding assistant interface"""
    
    def __init__(self):
        # Load .env file if it exists
        env_path = Path('.env')
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        self.secrets = SecretsManager()
        self.anthropic_key = self.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        self.openai_key = self.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.current_model = "claude"  # Default to Claude
        self.context = []
        
    async def ask_claude(self, prompt: str) -> str:
        """Ask Claude directly"""
        try:
            if not self.anthropic_key:
                return "Error: ANTHROPIC_API_KEY not found in environment"
                
            headers = {
                "x-api-key": self.anthropic_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            data = {
                "model": "claude-3-opus-20240229",
                "max_tokens": 4096,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["content"][0]["text"]
                    else:
                        error = await response.text()
                        return f"Claude API error: {error}"
        except Exception as e:
            return f"Error calling Claude API: {str(e)}"
    
    async def ask_openai(self, prompt: str) -> str:
        """Ask OpenAI directly"""
        try:
            if not self.openai_key:
                return "Error: OPENAI_API_KEY not found in environment"
                
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 4096
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error = await response.text()
                        return f"OpenAI API error: {error}"
        except Exception as e:
            return f"Error calling OpenAI API: {str(e)}"
    
    async def code_review(self, file_path: str) -> str:
        """Review code in a file"""
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            
            prompt = f"""Please review this code and provide suggestions for improvement:

File: {file_path}

```python
{code}
```

Provide:
1. Code quality assessment
2. Potential bugs or issues
3. Performance improvements
4. Best practices recommendations
"""
            
            if self.current_model == "claude":
                return await self.ask_claude(prompt)
            else:
                return await self.ask_openai(prompt)
                
        except Exception as e:
            return f"Error reading file: {e}"
    
    async def generate_code(self, description: str) -> str:
        """Generate code based on description"""
        prompt = f"""Generate Python code for the following requirement:

{description}

Provide:
1. Complete, working code
2. Comments explaining key parts
3. Example usage if applicable
"""
        
        if self.current_model == "claude":
            return await self.ask_claude(prompt)
        else:
            return await self.ask_openai(prompt)
    
    async def explain_code(self, code_snippet: str) -> str:
        """Explain what code does"""
        prompt = f"""Explain what this code does in detail:

```python
{code_snippet}
```

Provide:
1. Overall purpose
2. Step-by-step explanation
3. Any potential issues or improvements
"""
        
        if self.current_model == "claude":
            return await self.ask_claude(prompt)
        else:
            return await self.ask_openai(prompt)
    
    async def interactive_session(self):
        """Run interactive coding session"""
        print("🤖 AI Code Assistant")
        print("===================")
        print(f"Using: {self.current_model.upper()}")
        print("\nCommands:")
        print("  /review <file>  - Review code in file")
        print("  /generate      - Generate code from description")
        print("  /explain       - Explain code snippet")
        print("  /model <name>  - Switch model (claude/openai)")
        print("  /help          - Show this help")
        print("  /exit          - Exit assistant")
        print("\nOr just type your coding question!\n")
        
        while True:
            try:
                user_input = input(f"[{self.current_model}]> ").strip()
                
                if not user_input:
                    continue
                
                if user_input == "/exit":
                    print("Goodbye!")
                    break
                
                elif user_input == "/help":
                    print("\nCommands:")
                    print("  /review <file>  - Review code in file")
                    print("  /generate      - Generate code from description")
                    print("  /explain       - Explain code snippet")
                    print("  /model <name>  - Switch model (claude/openai)")
                    print("  /help          - Show this help")
                    print("  /exit          - Exit assistant\n")
                
                elif user_input.startswith("/model "):
                    model = user_input.split()[1].lower()
                    if model in ["claude", "openai"]:
                        self.current_model = model
                        print(f"Switched to {model.upper()}")
                    else:
                        print("Invalid model. Use 'claude' or 'openai'")
                
                elif user_input.startswith("/review "):
                    file_path = user_input[8:].strip()
                    print("\nReviewing code...")
                    response = await self.code_review(file_path)
                    print(f"\n{response}\n")
                
                elif user_input == "/generate":
                    print("Describe what you want to generate:")
                    description = input("> ").strip()
                    print("\nGenerating code...")
                    response = await self.generate_code(description)
                    print(f"\n{response}\n")
                
                elif user_input == "/explain":
                    print("Paste code to explain (end with '###' on new line):")
                    lines = []
                    while True:
                        line = input()
                        if line == "###":
                            break
                        lines.append(line)
                    code = "\n".join(lines)
                    print("\nExplaining code...")
                    response = await self.explain_code(code)
                    print(f"\n{response}\n")
                
                else:
                    # Direct question
                    print("\nThinking...")
                    if self.current_model == "claude":
                        response = await self.ask_claude(user_input)
                    else:
                        response = await self.ask_openai(user_input)
                    print(f"\n{response}\n")
                    
            except KeyboardInterrupt:
                print("\n\nUse /exit to quit")
            except Exception as e:
                print(f"\nError: {e}\n")

async def main():
    """Main entry point"""
    assistant = AICodeAssistant()
    await assistant.interactive_session()

if __name__ == "__main__":
    asyncio.run(main())