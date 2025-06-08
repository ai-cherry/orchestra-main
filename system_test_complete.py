#!/usr/bin/env python3
"""
🧪 Complete Orchestra AI System Test
Comprehensive verification of all coding assistant components and configurations
"""

import os
import json
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Any, Tuple

class OrchestralSystemTest:
    """Comprehensive test suite for Orchestra AI ecosystem"""
    
    def __init__(self):
        self.results = {
            "api_keys": {},
            "configurations": {},
            "integrations": {},
            "tools": {},
            "overall_status": "unknown"
        }
    
    def test_api_keys(self) -> Dict[str, Any]:
        """Test all API key configurations"""
        print("🔑 Testing API Keys...")
        
        # Test OpenAI API
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                headers = {"Authorization": f"Bearer {openai_key}"}
                response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=10)
                if response.status_code == 200:
                    models = response.json()
                    gpt4o_models = [m["id"] for m in models["data"] if "gpt-4o" in m["id"]]
                    self.results["api_keys"]["openai"] = {
                        "status": "✅ Valid",
                        "models_available": len(gpt4o_models),
                        "key_prefix": openai_key[:20] + "...",
                        "gpt4o_models": gpt4o_models[:3]
                    }
                else:
                    self.results["api_keys"]["openai"] = {"status": "❌ Invalid", "error": f"HTTP {response.status_code}"}
            except Exception as e:
                self.results["api_keys"]["openai"] = {"status": "❌ Error", "error": str(e)}
        else:
            self.results["api_keys"]["openai"] = {"status": "❌ Not Set"}
        
        # Test OpenRouter API
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            try:
                headers = {"Authorization": f"Bearer {openrouter_key}"}
                response = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=10)
                if response.status_code == 200:
                    models = response.json()
                    deepseek_models = [m["id"] for m in models["data"] if "deepseek" in m["id"].lower()]
                    claude_models = [m["id"] for m in models["data"] if "claude" in m["id"].lower()]
                    self.results["api_keys"]["openrouter"] = {
                        "status": "✅ Valid", 
                        "key_prefix": openrouter_key[:20] + "...",
                        "deepseek_available": len(deepseek_models),
                        "claude_available": len(claude_models),
                        "deepseek_models": deepseek_models[:2],
                        "claude_models": claude_models[:2]
                    }
                else:
                    self.results["api_keys"]["openrouter"] = {"status": "❌ Invalid", "error": f"HTTP {response.status_code}"}
            except Exception as e:
                self.results["api_keys"]["openrouter"] = {"status": "❌ Error", "error": str(e)}
        else:
            self.results["api_keys"]["openrouter"] = {"status": "❌ Not Set"}
        
        return self.results["api_keys"]
    
    def test_configurations(self) -> Dict[str, Any]:
        """Test all configuration files"""
        print("📋 Testing Configurations...")
        
        config_files = {
            "cursor_rules": ".cursorrules",
            "continue_config": ".continue/config.json",
            "roo_main_config": ".roo/config.json",
            "roo_mcp_config": ".roo/mcp.json",
            "patrick_instructions": "PATRICK_INSTRUCTIONS.md",
            "ai_coding_instructions": "AI_CODING_INSTRUCTIONS.md",
            "notion_ai_notes": "NOTION_AI_NOTES.md"
        }
        
        for name, file_path in config_files.items():
            path = Path(file_path)
            if path.exists():
                size_kb = round(path.stat().st_size / 1024, 1)
                self.results["configurations"][name] = {
                    "status": "✅ Exists",
                    "size_kb": size_kb,
                    "path": str(path)
                }
            else:
                self.results["configurations"][name] = {"status": "❌ Missing", "path": str(path)}
        
        # Check Roo modes
        modes_dir = Path(".roo/modes")
        if modes_dir.exists():
            mode_files = list(modes_dir.glob("*.json"))
            detailed_modes = 0
            for mode_file in mode_files:
                try:
                    with open(mode_file) as f:
                        mode_config = json.load(f)
                    if "customInstructions" in mode_config:
                        detailed_modes += 1
                except:
                    pass
            
            self.results["configurations"]["roo_modes"] = {
                "status": "✅ Configured",
                "total_modes": len(mode_files),
                "detailed_modes": detailed_modes,
                "modes": [f.stem for f in mode_files]
            }
        else:
            self.results["configurations"]["roo_modes"] = {"status": "❌ Missing"}
        
        return self.results["configurations"]
    
    def test_continue_integration(self) -> Dict[str, Any]:
        """Test Continue.dev integration"""
        print("🔄 Testing Continue.dev Integration...")
        
        continue_config_path = Path(".continue/config.json")
        if continue_config_path.exists():
            try:
                with open(continue_config_path) as f:
                    config = json.load(f)
                
                # Check models
                models = config.get("models", [])
                ui_models = [m for m in models if "UI-GPT-4O" in m.get("title", "")]
                
                # Check custom commands
                commands = config.get("customCommands", [])
                command_names = [c.get("name") for c in commands]
                
                # Check context providers
                providers = config.get("contextProviders", [])
                provider_names = [p.get("name") for p in providers]
                
                self.results["integrations"]["continue"] = {
                    "status": "✅ Configured",
                    "total_models": len(models),
                    "ui_models": len(ui_models),
                    "custom_commands": command_names,
                    "context_providers": provider_names,
                    "ui_gpt4o_ready": len(ui_models) > 0
                }
            except Exception as e:
                self.results["integrations"]["continue"] = {"status": "❌ Config Error", "error": str(e)}
        else:
            self.results["integrations"]["continue"] = {"status": "❌ Not Configured"}
        
        return self.results["integrations"]["continue"]
    
    def test_roo_installation(self) -> Dict[str, Any]:
        """Test Roo installation and availability"""
        print("🤖 Testing Roo Installation...")
        
        # Check if roo command exists
        try:
            result = subprocess.run(["which", "roo"], capture_output=True, text=True)
            if result.returncode == 0:
                self.results["tools"]["roo"] = {
                    "status": "✅ Installed",
                    "path": result.stdout.strip()
                }
            else:
                self.results["tools"]["roo"] = {"status": "❌ Not Installed", "note": "Roo binary not found in PATH"}
        except Exception as e:
            self.results["tools"]["roo"] = {"status": "❌ Error", "error": str(e)}
        
        # Check if it's a VS Code extension or different installation method
        if self.results["tools"]["roo"]["status"].startswith("❌"):
            # Check for VS Code extensions directory
            vscode_extensions = Path.home() / ".vscode" / "extensions"
            if vscode_extensions.exists():
                roo_extensions = list(vscode_extensions.glob("*roo*"))
                if roo_extensions:
                    self.results["tools"]["roo"]["vscode_extension"] = [str(ext.name) for ext in roo_extensions]
                    self.results["tools"]["roo"]["note"] = "Might be VS Code extension"
        
        return self.results["tools"]["roo"]
    
    def test_mcp_servers(self) -> Dict[str, Any]:
        """Test MCP server availability"""
        print("🔧 Testing MCP Servers...")
        
        mcp_scripts = [
            "start_mcp_minimal.sh",
            "start_mcp_servers_working.sh", 
            "check_mcp_status.sh",
            "stop_mcp_servers.sh"
        ]
        
        for script in mcp_scripts:
            path = Path(script)
            if path.exists() and path.stat().st_mode & 0o111:  # Check if executable
                self.results["tools"][f"mcp_{script.replace('.sh', '')}"] = {"status": "✅ Ready", "executable": True}
            elif path.exists():
                self.results["tools"][f"mcp_{script.replace('.sh', '')}"] = {"status": "⚠️ Not Executable", "executable": False}
            else:
                self.results["tools"][f"mcp_{script.replace('.sh', '')}"] = {"status": "❌ Missing"}
        
        # Check for MCP server files
        mcp_servers = [
            "mcp_unified_server.py",
            "mcp_simple_server.py"
        ]
        
        for server in mcp_servers:
            path = Path(server)
            if path.exists():
                size_kb = round(path.stat().st_size / 1024, 1)
                self.results["tools"][f"server_{server.replace('.py', '')}"] = {
                    "status": "✅ Available",
                    "size_kb": size_kb
                }
            else:
                self.results["tools"][f"server_{server.replace('.py', '')}"] = {"status": "❌ Missing"}
        
        return {k: v for k, v in self.results["tools"].items() if "mcp" in k or "server" in k}
    
    def determine_overall_status(self) -> str:
        """Determine overall system status"""
        
        # Count successes
        api_success = sum(1 for v in self.results["api_keys"].values() if v["status"].startswith("✅"))
        config_success = sum(1 for v in self.results["configurations"].values() if v["status"].startswith("✅"))
        integration_success = sum(1 for v in self.results["integrations"].values() if v["status"].startswith("✅"))
        
        total_critical = len(self.results["api_keys"]) + len(self.results["configurations"]) + len(self.results["integrations"])
        total_success = api_success + config_success + integration_success
        
        success_rate = (total_success / total_critical) * 100 if total_critical > 0 else 0
        
        if success_rate >= 90:
            return "🟢 FULLY OPERATIONAL"
        elif success_rate >= 70:
            return "🟡 MOSTLY OPERATIONAL"
        elif success_rate >= 50:
            return "🟠 PARTIALLY OPERATIONAL"
        else:
            return "🔴 NEEDS ATTENTION"
    
    def run_complete_test(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        print("🧪 Orchestra AI Complete System Test")
        print("=" * 50)
        
        # Run all tests
        self.test_api_keys()
        self.test_configurations()
        self.test_continue_integration()
        self.test_roo_installation()
        self.test_mcp_servers()
        
        # Determine overall status
        self.results["overall_status"] = self.determine_overall_status()
        
        return self.results
    
    def print_summary(self):
        """Print a formatted summary of results"""
        print("\n" + "=" * 60)
        print(f"🎯 OVERALL STATUS: {self.results['overall_status']}")
        print("=" * 60)
        
        print("\n🔑 API KEYS:")
        for name, result in self.results["api_keys"].items():
            print(f"   {result['status']} {name.upper()}")
            if "models_available" in result:
                print(f"      Models: {result['models_available']} available")
        
        print("\n📋 CONFIGURATIONS:")
        for name, result in self.results["configurations"].items():
            print(f"   {result['status']} {name.replace('_', ' ').title()}")
            if "size_kb" in result:
                print(f"      Size: {result['size_kb']} KB")
        
        print("\n🔄 INTEGRATIONS:")
        for name, result in self.results["integrations"].items():
            print(f"   {result['status']} {name.upper()}")
            if "custom_commands" in result:
                print(f"      Commands: {', '.join(result['custom_commands'])}")
        
        print("\n🛠 TOOLS & SERVERS:")
        for name, result in self.results["tools"].items():
            print(f"   {result['status']} {name.replace('_', ' ').title()}")
        
        # Provide next steps
        print("\n🎯 IMMEDIATE NEXT STEPS:")
        
        if any("❌" in r["status"] for r in self.results["api_keys"].values()):
            print("   1. ⚠️ Fix API key configuration")
        else:
            print("   1. ✅ API keys configured")
            
        if self.results["integrations"]["continue"]["status"].startswith("✅"):
            print("   2. ✅ Continue.dev ready - Test /ui command in VS Code")
        else:
            print("   2. ⚠️ Configure Continue.dev")
            
        if self.results["tools"]["roo"]["status"].startswith("❌"):
            print("   3. ⚠️ Install Roo (may be VS Code extension)")
        else:
            print("   3. ✅ Test Roo modes")
            
        mcp_ready = any("✅" in r["status"] for k, r in self.results["tools"].items() if "server" in k)
        if mcp_ready:
            print("   4. ✅ Deploy MCP servers for context sharing")
        else:
            print("   4. ⚠️ Fix MCP server configuration")

def main():
    """Run the complete system test"""
    tester = OrchestralSystemTest()
    results = tester.run_complete_test()
    tester.print_summary()
    
    # Save results to file
    with open("system_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: system_test_results.json")
    return results

if __name__ == "__main__":
    main() 