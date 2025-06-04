#!/usr/bin/env python3
"""
Cherry AI Tools Integration Test Suite
Tests all AI integrations including Codex, MCP servers, and Cherry AI tools
"""

import json
import os
import sys
import subprocess
import requests
from pathlib import Path

def test_cursor_settings():
    """Test if Cursor settings are properly configured"""
    print("🔧 Testing Cursor AI Settings...")
    
    settings_path = Path(".cursor/settings.json")
    if settings_path.exists():
        try:
            with open(settings_path) as f:
                settings = json.load(f)
            
            # Check for required settings
            required_keys = [
                "cursor.ai.models",
                "cursor.ai.codex", 
                "cursor.ai.features",
                "cursor.ai.cherryAI"
            ]
            
            missing_keys = [key for key in required_keys if key not in settings]
            if missing_keys:
                print(f"❌ Missing settings: {missing_keys}")
                return False
            
            print("✅ Cursor settings properly configured")
            return True
            
        except json.JSONDecodeError:
            print("❌ Invalid JSON in Cursor settings")
            return False
    else:
        print("❌ Cursor settings file not found")
        return False

def test_mcp_configuration():
    """Test MCP server configuration"""
    print("\n🔗 Testing MCP Configuration...")
    
    mcp_configs = [
        ".cursor/mcp.json",
        ".roo/mcp.json"
    ]
    
    for config_path in mcp_configs:
        if Path(config_path).exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                
                if "mcpServers" in config:
                    servers = config["mcpServers"]
                    print(f"✅ Found {len(servers)} MCP servers in {config_path}")
                    for server_name in servers:
                        print(f"   - {server_name}")
                else:
                    print(f"❌ No mcpServers found in {config_path}")
                    
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON in {config_path}")
        else:
            print(f"⚠️ MCP config not found: {config_path}")

def test_mcp_servers():
    """Test if MCP server files exist and are executable"""
    print("\n🖥️ Testing MCP Server Files...")
    
    server_files = [
        "mcp_server/servers/enhanced_codebase_server.py",
        "mcp_server/servers/infrastructure_manager.py"
    ]
    
    for server_file in server_files:
        path = Path(server_file)
        if path.exists():
            if os.access(path, os.X_OK):
                print(f"✅ {server_file} exists and is executable")
            else:
                print(f"⚠️ {server_file} exists but not executable")
        else:
            print(f"❌ {server_file} not found")

def test_python_dependencies():
    """Test required Python packages"""
    print("\n📦 Testing Python Dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn", 
        "python-dotenv",
        "aiofiles",
        "watchdog",
        "git",  # GitPython
        "psutil",
        "requests",
        "anthropic",
        "openai"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == "git":
                import git
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} not installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Install missing packages: pip3 install {' '.join(missing_packages)}")
        return False
    
    return True

def test_openai_codex_setup():
    """Test OpenAI Codex configuration"""
    print("\n🤖 Testing OpenAI Codex Setup...")
    
    # Check if API key is configured
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ OPENAI_API_KEY environment variable not set")
        print("   Add it to your shell profile or Cursor settings")
        return False
    
    # Test API connectivity (without making actual API calls)
    if api_key.startswith("sk-"):
        print("✅ OpenAI API key format is correct")
        return True
    else:
        print("❌ OpenAI API key format is incorrect")
        return False

def test_cherry_ai_tools():
    """Test Cherry AI tools configuration"""
    print("\n🍒 Testing Cherry AI Tools...")
    
    # Check for Cherry AI extension files
    extension_files = [
        ".vscode/extensions/cherry-ai-tools/package.json",
        ".vscode/extensions/cherry-ai-tools/extension.js"
    ]
    
    found_files = 0
    for file_path in extension_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
            found_files += 1
        else:
            print(f"⚠️ {file_path} not found")
    
    if found_files > 0:
        print("✅ Cherry AI Tools files found")
        return True
    else:
        print("⚠️ Cherry AI Tools extension files not found")
        return False

def test_roo_code_setup():
    """Test Roo Code configuration"""
    print("\n🦘 Testing Roo Code Setup...")
    
    roo_config = Path(".roo/config.json")
    if roo_config.exists():
        try:
            with open(roo_config) as f:
                config = json.load(f)
            
            required_keys = ["ai_provider", "model", "api_key"]
            missing_keys = [key for key in required_keys if key not in config]
            
            if missing_keys:
                print(f"❌ Missing Roo config keys: {missing_keys}")
                return False
            
            print("✅ Roo Code configuration found and valid")
            return True
            
        except json.JSONDecodeError:
            print("❌ Invalid JSON in Roo config")
            return False
    else:
        print("⚠️ Roo Code config not found")
        return False

def generate_test_report():
    """Generate a comprehensive test report"""
    print("\n" + "="*60)
    print("🎯 CHERRY AI TOOLS INTEGRATION TEST REPORT")
    print("="*60)
    
    tests = [
        ("Cursor AI Settings", test_cursor_settings),
        ("MCP Configuration", test_mcp_configuration),
        ("MCP Server Files", test_mcp_servers), 
        ("Python Dependencies", test_python_dependencies),
        ("OpenAI Codex Setup", test_openai_codex_setup),
        ("Cherry AI Tools", test_cherry_ai_tools),
        ("Roo Code Setup", test_roo_code_setup)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Your Cherry AI development environment is ready!")
        print("\n🚀 Next Steps:")
        print("1. Test AI chat with: 'Hello! Can you see my project structure?'")
        print("2. Try code completion by typing comments and pressing Tab")
        print("3. Use Quick Actions on selected code")
        print("4. Test MCP integration with @cherry-ai-codebase commands")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please fix the issues above.")
        print("\n🔧 Common Fixes:")
        print("- Install missing Python packages: pip3 install [package_name]")
        print("- Add API keys to Cursor Settings > Models")
        print("- Restart Cursor after configuration changes")
    
    return passed == total

if __name__ == "__main__":
    # Change to project directory if not already there
    if not Path("mcp_server").exists():
        print("❌ Please run this script from the orchestra-main project directory")
        sys.exit(1)
    
    success = generate_test_report()
    sys.exit(0 if success else 1)

