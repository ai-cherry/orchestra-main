#!/usr/bin/env python3
"""
🪃 Roo Code Integration Test
Tests all Roo configurations, MCP server connections, and custom modes
"""

import json
import os
import sys
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional

# Color codes for output
class Colors:
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def log(message: str, color: str = Colors.GREEN) -> None:
    """Log a message with color"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"{color}[{timestamp}] {message}{Colors.NC}")

def test_roo_configurations() -> Dict[str, bool]:
    """Test all Roo configuration files"""
    results = {}
    
    # Test main config
    config_file = Path(".roo/config.json")
    if config_file.exists():
        try:
            with open(config_file) as f:
                config = json.load(f)
            
            results["main_config"] = True
            results["boomerang_enabled"] = config.get("boomerang", {}).get("enabled", False)
            results["custom_modes_enabled"] = config.get("enableCustomModes", False)
            results["mode_count"] = len(config.get("modes", []))
            
            log(f"✅ Main config: {results['mode_count']} modes, boomerang: {results['boomerang_enabled']}")
        except Exception as e:
            log(f"❌ Main config error: {e}", Colors.RED)
            results["main_config"] = False
    else:
        log("❌ Main config file not found", Colors.RED)
        results["main_config"] = False
    
    # Test MCP config
    mcp_file = Path(".roo/mcp.json")
    if mcp_file.exists():
        try:
            with open(mcp_file) as f:
                mcp_config = json.load(f)
            
            results["mcp_config"] = True
            results["mcp_server_count"] = len(mcp_config.get("mcpServers", {}))
            results["single_dev_mode"] = mcp_config.get("optimization", {}).get("single_developer_mode", False)
            
            log(f"✅ MCP config: {results['mcp_server_count']} servers configured")
        except Exception as e:
            log(f"❌ MCP config error: {e}", Colors.RED)
            results["mcp_config"] = False
    else:
        log("❌ MCP config file not found", Colors.RED)
        results["mcp_config"] = False
    
    return results

def test_mode_configurations() -> Dict[str, bool]:
    """Test individual mode configurations"""
    results = {}
    modes_dir = Path(".roo/modes")
    
    if not modes_dir.exists():
        log("❌ Modes directory not found", Colors.RED)
        return {"modes_dir": False}
    
    mode_files = list(modes_dir.glob("*.json"))
    results["mode_file_count"] = len(mode_files)
    
    detailed_modes = 0
    basic_modes = 0
    
    for mode_file in mode_files:
        try:
            with open(mode_file) as f:
                mode_config = json.load(f)
            
            mode_name = mode_file.stem
            has_custom_instructions = "customInstructions" in mode_config
            has_api_config = "apiConfiguration" in mode_config
            has_openrouter = mode_config.get("apiConfiguration", {}).get("provider") == "openrouter"
            
            if has_custom_instructions and has_api_config:
                detailed_modes += 1
                status = "detailed" if has_openrouter else "configured"
                log(f"✅ {mode_name}: {status} configuration")
            else:
                basic_modes += 1
                log(f"⚠️ {mode_name}: basic configuration", Colors.YELLOW)
                
        except Exception as e:
            log(f"❌ {mode_file.name}: invalid JSON - {e}", Colors.RED)
    
    results["detailed_modes"] = detailed_modes
    results["basic_modes"] = basic_modes
    
    return results

def test_mcp_servers() -> Dict[str, bool]:
    """Test MCP server connections"""
    results = {}
    
    # Essential servers for single developer mode
    essential_servers = [
        ("orchestra-unified", 8000),
        ("infrastructure", 8009),
        ("weaviate-direct", 8011)
    ]
    
    for server_name, port in essential_servers:
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code == 200:
                log(f"✅ {server_name} server: Connected")
                results[server_name] = True
            else:
                log(f"⚠️ {server_name} server: Responding but unhealthy", Colors.YELLOW)
                results[server_name] = False
        except requests.exceptions.RequestException:
            log(f"❌ {server_name} server: Not accessible", Colors.RED)
            results[server_name] = False
    
    return results

def test_environment_variables() -> Dict[str, bool]:
    """Test required environment variables"""
    results = {}
    
    # Load .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    # Check required variables
    required_vars = {
        "OPENROUTER_API_KEY": "OpenRouter API integration",
        "OPENAI_API_KEY": "OpenAI API fallback", 
        "POSTGRES_HOST": "Database connection",
        "REDIS_HOST": "Cache connection",
        "WEAVIATE_URL": "Vector database"
    }
    
    for var, description in required_vars.items():
        if os.getenv(var):
            log(f"✅ {var}: Configured")
            results[var] = True
        else:
            log(f"❌ {var}: Not set ({description})", Colors.RED)
            results[var] = False
    
    return results

def test_api_connections() -> Dict[str, bool]:
    """Test API connections"""
    results = {}
    
    # Test OpenRouter
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        try:
            headers = {"Authorization": f"Bearer {openrouter_key}"}
            response = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=10)
            if response.status_code == 200:
                models = response.json()
                model_count = len(models.get("data", []))
                log(f"✅ OpenRouter API: {model_count} models available")
                results["openrouter"] = True
            else:
                log(f"❌ OpenRouter API: HTTP {response.status_code}", Colors.RED)
                results["openrouter"] = False
        except Exception as e:
            log(f"❌ OpenRouter API: Connection failed - {e}", Colors.RED)
            results["openrouter"] = False
    else:
        log("⚠️ OpenRouter API: No key configured", Colors.YELLOW)
        results["openrouter"] = False
    
    # Test OpenAI (optional)
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            headers = {"Authorization": f"Bearer {openai_key}"}
            response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=10)
            if response.status_code == 200:
                log("✅ OpenAI API: Connected")
                results["openai"] = True
            else:
                log(f"❌ OpenAI API: HTTP {response.status_code}", Colors.RED)
                results["openai"] = False
        except Exception as e:
            log(f"❌ OpenAI API: Connection failed - {e}", Colors.RED)
            results["openai"] = False
    else:
        log("⚠️ OpenAI API: No key configured (optional)", Colors.YELLOW)
        results["openai"] = None
    
    return results

def test_vscode_integration() -> Dict[str, bool]:
    """Test VS Code integration files"""
    results = {}
    
    vscode_files = {
        ".vscode/settings.json": "VS Code settings",
        ".vscode/launch.json": "Debug configurations",
        ".vscode/tasks.json": "Build tasks"
    }
    
    for file_path, description in vscode_files.items():
        if Path(file_path).exists():
            try:
                with open(file_path) as f:
                    json.load(f)
                log(f"✅ {description}: Valid JSON")
                results[Path(file_path).stem] = True
            except json.JSONDecodeError:
                log(f"❌ {description}: Invalid JSON", Colors.RED)
                results[Path(file_path).stem] = False
        else:
            log(f"❌ {description}: File not found", Colors.RED)
            results[Path(file_path).stem] = False
    
    return results

def main():
    """Run comprehensive Roo integration test"""
    print(f"{Colors.CYAN}")
    print("🪃 Roo Code Integration Test")
    print("============================")
    print("Testing all configurations, MCP servers, and integrations")
    print(f"{Colors.NC}\n")
    
    # Track overall results
    all_results = {}
    
    # Run tests
    log("📋 Testing Roo configurations...", Colors.BLUE)
    all_results["config"] = test_roo_configurations()
    
    log("\n🎭 Testing mode configurations...", Colors.BLUE)
    all_results["modes"] = test_mode_configurations()
    
    log("\n🌐 Testing environment variables...", Colors.BLUE)
    all_results["env"] = test_environment_variables()
    
    log("\n🔌 Testing API connections...", Colors.BLUE)
    all_results["api"] = test_api_connections()
    
    log("\n🖥️ Testing VS Code integration...", Colors.BLUE)
    all_results["vscode"] = test_vscode_integration()
    
    log("\n🔧 Testing MCP servers...", Colors.BLUE)
    all_results["mcp"] = test_mcp_servers()
    
    # Calculate scores
    total_tests = 0
    passed_tests = 0
    
    for category, results in all_results.items():
        for test, result in results.items():
            if isinstance(result, bool):
                total_tests += 1
                if result:
                    passed_tests += 1
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    # Summary
    print(f"\n{Colors.CYAN}🎯 ROO INTEGRATION TEST SUMMARY{Colors.NC}")
    print("=" * 40)
    
    # Configuration status
    config_ok = all_results["config"].get("main_config", False)
    mcp_ok = all_results["config"].get("mcp_config", False)
    mode_count = all_results["modes"].get("detailed_modes", 0)
    
    print(f"📋 Configuration: {'✅' if config_ok and mcp_ok else '❌'}")
    print(f"🎭 Modes: {mode_count}/10 detailed configurations")
    print(f"🔌 API Integration: {'✅' if all_results['api'].get('openrouter') else '❌'}")
    print(f"🖥️ VS Code Setup: {'✅' if all_results['vscode'].get('settings') else '❌'}")
    
    # MCP server status
    mcp_servers_up = sum(1 for result in all_results["mcp"].values() if result)
    print(f"🔧 MCP Servers: {mcp_servers_up}/3 essential servers running")
    
    # Overall status
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    
    if success_rate >= 85:
        print(f"{Colors.GREEN}🎉 ROO INTEGRATION: EXCELLENT!{Colors.NC}")
        print("Ready for production use with full feature set")
    elif success_rate >= 70:
        print(f"{Colors.YELLOW}⚠️ ROO INTEGRATION: GOOD{Colors.NC}")
        print("Most features working, minor issues to resolve")
    else:
        print(f"{Colors.RED}❌ ROO INTEGRATION: NEEDS WORK{Colors.NC}")
        print("Significant issues found, run setup script again")
    
    # Next steps
    print(f"\n{Colors.BLUE}📋 NEXT STEPS:{Colors.NC}")
    
    if not all_results["vscode"].get("settings"):
        print("1. Run: ./setup_roo_complete.sh")
    
    if not all_results["api"].get("openrouter"):
        print("2. Check OpenRouter API key in .env file")
    
    if mcp_servers_up < 2:
        print("3. Start MCP servers: ./start_mcp_minimal.sh")
    
    if mode_count < 8:
        print("4. Verify mode configurations in .roo/modes/")
    
    print("5. Install Roo Code VS Code extension")
    print("6. Test with: 'Create a simple feature using orchestrator mode'")
    
    return success_rate >= 70

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Test failed with error: {e}{Colors.NC}")
        sys.exit(1) 