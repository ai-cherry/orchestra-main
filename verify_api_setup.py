#!/usr/bin/env python3
"""
🔧 Quick API Key and Configuration Verification
Test OpenAI and OpenRouter API keys plus all coding assistant configurations
"""

import os
import json
import requests
from pathlib import Path

def test_openai_api():
    """Test OpenAI API key"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"status": "❌", "message": "API key not set"}
    
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=10)
        
        if response.status_code == 200:
            models = response.json()
            available_models = [m["id"] for m in models["data"] if "gpt-4o" in m["id"]]
            return {
                "status": "✅", 
                "message": "OpenAI API key valid",
                "models": available_models[:3]  # Show first 3 GPT-4o models
            }
        else:
            return {"status": "❌", "message": f"API error: {response.status_code}"}
    except Exception as e:
        return {"status": "❌", "message": f"Test failed: {str(e)}"}

def test_openrouter_api():
    """Test OpenRouter API key"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return {"status": "❌", "message": "API key not set"}
    
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=10)
        
        if response.status_code == 200:
            models = response.json()
            deepseek_models = [m["id"] for m in models["data"] if "deepseek" in m["id"].lower()]
            claude_models = [m["id"] for m in models["data"] if "claude" in m["id"].lower()]
            return {
                "status": "✅", 
                "message": "OpenRouter API key valid",
                "deepseek_models": deepseek_models[:2],
                "claude_models": claude_models[:2]
            }
        else:
            return {"status": "❌", "message": f"API error: {response.status_code}"}
    except Exception as e:
        return {"status": "❌", "message": f"Test failed: {str(e)}"}

def check_configurations():
    """Check all configuration files"""
    configs = {
        "Cursor Rules": Path(".cursorrules").exists(),
        "Continue.dev Config": Path(".continue/config.json").exists(), 
        "Roo Main Config": Path(".roo/config.json").exists(),
        "Roo MCP Config": Path(".roo/mcp.json").exists(),
        "Roo Modes Directory": Path(".roo/modes").exists(),
        "Patrick Instructions": Path("PATRICK_INSTRUCTIONS.md").exists(),
        "AI Coding Instructions": Path("AI_CODING_INSTRUCTIONS.md").exists(),
        "Notion AI Notes": Path("NOTION_AI_NOTES.md").exists()
    }
    
    # Check Roo mode files have custom instructions
    mode_files = list(Path(".roo/modes").glob("*.json")) if Path(".roo/modes").exists() else []
    detailed_modes = 0
    for mode_file in mode_files:
        try:
            with open(mode_file) as f:
                mode_config = json.load(f)
            if "customInstructions" in mode_config:
                detailed_modes += 1
        except:
            pass
    
    return configs, detailed_modes, len(mode_files)

def main():
    """Run comprehensive verification"""
    print("🔧 Orchestra AI API Keys & Configuration Verification")
    print("=" * 60)
    
    # Test API keys
    print("\n🔑 API KEY TESTS:")
    
    openai_result = test_openai_api()
    print(f"   {openai_result['status']} OpenAI API: {openai_result['message']}")
    if "models" in openai_result:
        print(f"      Available models: {', '.join(openai_result['models'])}")
    
    openrouter_result = test_openrouter_api()
    print(f"   {openrouter_result['status']} OpenRouter API: {openrouter_result['message']}")
    if "deepseek_models" in openrouter_result:
        print(f"      DeepSeek models: {', '.join(openrouter_result['deepseek_models'])}")
        print(f"      Claude models: {', '.join(openrouter_result['claude_models'])}")
    
    # Check configurations
    print("\n📋 CONFIGURATION CHECK:")
    configs, detailed_modes, total_modes = check_configurations()
    
    for name, exists in configs.items():
        status = "✅" if exists else "❌"
        print(f"   {status} {name}")
    
    print(f"\n🤖 ROO MODES:")
    print(f"   ✅ Total modes: {total_modes}")
    print(f"   ✅ Detailed modes with custom instructions: {detailed_modes}")
    
    # Overall status
    print("\n" + "=" * 60)
    openai_ok = "✅" in openai_result["status"]
    openrouter_ok = "✅" in openrouter_result["status"]
    configs_ok = all(configs.values())
    
    if openai_ok and openrouter_ok and configs_ok and detailed_modes >= 5:
        print("🎉 ALL SYSTEMS READY!")
        print("🚀 Ready for AI-accelerated development with:")
        print("   - Continue.dev UI-GPT-4O (OpenAI)")
        print("   - Roo specialized modes (OpenRouter)")
        print("   - Cross-tool integration")
        print("   - Comprehensive documentation")
    else:
        print("⚠️ ISSUES FOUND - Check the results above")
    
    print("\n🎯 NEXT: Test the systems!")
    print("   Continue.dev: Try /ui command in VS Code")
    print("   Roo: Run 'roo code' or 'roo architect'")
    print("   MCP: Deploy servers with ./start_mcp_system_enhanced.sh")

if __name__ == "__main__":
    main() 