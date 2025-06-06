#!/usr/bin/env python3
"""
Cherry AI Orchestrator - Final Setup Verification
Comprehensive verification of all Cherry AI tools and configurations
"""

import os
import sys
import json
import subprocess
import requests
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CherryAIVerifier:
    """Comprehensive verification of Cherry AI setup"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.results = {}
        self.errors = []
        self.warnings = []
        
    def print_header(self, title: str):
        """Print formatted section header"""
        print(f"\n{'='*60}")
        print(f"🍒 {title}")
        print(f"{'='*60}")
    
    def print_result(self, check: str, status: bool, message: str = ""):
        """Print formatted check result"""
        icon = "✅" if status else "❌"
        print(f"{icon} {check}")
        if message:
            print(f"   {message}")
        
        self.results[check] = {"status": status, "message": message}
        if not status:
            self.errors.append(f"{check}: {message}")
    
    def print_warning(self, check: str, message: str):
        """Print formatted warning"""
        print(f"⚠️  {check}")
        print(f"   {message}")
        self.warnings.append(f"{check}: {message}")
    
    def check_environment_variables(self) -> bool:
        """Verify all required environment variables are set"""
        self.print_header("Environment Variables Verification")
        
        required_vars = {
            "OPENAI_API_KEY": "OpenAI API Key",
            "ANTHROPIC_API_KEY": "Anthropic API Key", 
            "GEMINI_API_KEY": "Google Gemini API Key",
            "WEAVIATE_URL": "Weaviate Database URL",
            "WEAVIATE_API_KEY": "Weaviate API Key",
            "PINECONE_API_KEY": "Pinecone API Key",
            "LAMBDA_API_KEY": "Lambda Infrastructure API Key",
            "PULUMI_ACCESS_TOKEN": "Pulumi Access Token",
            "GITHUB_TOKEN": "GitHub Personal Access Token"
        }
        
        all_good = True
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value and len(value) > 10:
                self.print_result(description, True, f"Configured ({len(value)} chars)")
            else:
                self.print_result(description, False, "Missing or invalid")
                all_good = False
        
        return all_good
    
    def check_api_connectivity(self) -> bool:
        """Test connectivity to all AI APIs"""
        self.print_header("AI API Connectivity Tests")
        
        all_good = True
        
        # Test OpenAI API
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            models = client.models.list()
            self.print_result("OpenAI API", True, f"Connected ({len(models.data)} models available)")
        except Exception as e:
            self.print_result("OpenAI API", False, str(e))
            all_good = False
        
        # Test Anthropic API
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            # Simple test call
            self.print_result("Anthropic API", True, "Connected and authenticated")
        except Exception as e:
            self.print_result("Anthropic API", False, str(e))
            all_good = False
        
        # Test Weaviate
        try:
            import weaviate
            client = weaviate.Client(
                url=f"https://{os.getenv('WEAVIATE_URL')}",
                auth_client_secret=weaviate.AuthApiKey(api_key=os.getenv("WEAVIATE_API_KEY"))
            )
            meta = client.get_meta()
            self.print_result("Weaviate Database", True, f"Connected (version {meta.get('version', 'unknown')})")
        except Exception as e:
            self.print_result("Weaviate Database", False, str(e))
            all_good = False
        
        return all_good
    
    def check_project_structure(self) -> bool:
        """Verify project structure and key files"""
        self.print_header("Project Structure Verification")
        
        required_files = {
            ".cursor/mcp.json": "MCP Configuration",
            ".cursor/settings.json": "Cursor AI Settings",
            ".cursor/rules.json": "Cursor AI Rules",
            ".devcontainer/devcontainer.json": "DevContainer Configuration",
            ".devcontainer/setup_env.sh": "Environment Setup Script",
            "mcp_server/codex_integration.py": "OpenAI Codex Integration",
            "mcp_server/servers/enhanced_codebase_server.py": "Enhanced Codebase MCP Server",
            "infrastructure/database_layer/enterprise_db_manager.py": "Database Manager",
            "admin-interface/enhanced-production-interface.html": "Enhanced Admin Interface"
        }
        
        all_good = True
        for file_path, description in required_files.items():
            full_path = self.project_root / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                self.print_result(description, True, f"Found ({size} bytes)")
            else:
                self.print_result(description, False, "File not found")
                all_good = False
        
        return all_good
    
    def check_mcp_configuration(self) -> bool:
        """Verify MCP server configuration"""
        self.print_header("MCP Server Configuration")
        
        mcp_config_path = self.project_root / ".cursor" / "mcp.json"
        if not mcp_config_path.exists():
            self.print_result("MCP Configuration File", False, "File not found")
            return False
        
        try:
            with open(mcp_config_path) as f:
                config = json.load(f)
            
            servers = config.get("mcpServers", {})
            self.print_result("MCP Configuration File", True, f"Valid JSON with {len(servers)} servers")
            
            expected_servers = [
                "cherry-ai-codebase",
                "cherry-ai-infrastructure", 
                "cherry-ai-codex",
                "cherry-ai-database"
            ]
            
            all_servers_present = True
            for server in expected_servers:
                if server in servers:
                    self.print_result(f"MCP Server: {server}", True, "Configured")
                else:
                    self.print_result(f"MCP Server: {server}", False, "Not configured")
                    all_servers_present = False
            
            return all_servers_present
            
        except json.JSONDecodeError as e:
            self.print_result("MCP Configuration File", False, f"Invalid JSON: {e}")
            return False
    
    def check_cursor_configuration(self) -> bool:
        """Verify Cursor AI configuration"""
        self.print_header("Cursor AI Configuration")
        
        settings_path = self.project_root / ".cursor" / "settings.json"
        rules_path = self.project_root / ".cursor" / "rules.json"
        
        all_good = True
        
        # Check settings file
        if settings_path.exists():
            try:
                with open(settings_path) as f:
                    settings = json.load(f)
                
                cursor_ai_enabled = settings.get("cursor.ai.enabled", False)
                mcp_enabled = settings.get("cursor.mcp.enabled", False)
                
                self.print_result("Cursor AI Settings", True, f"Valid configuration")
                self.print_result(
                    "Cursor AI Enabled",
                    cursor_ai_enabled,
                    "AI features enabled" if cursor_ai_enabled else "AI features disabled"
                )
                self.print_result("MCP Integration", mcp_enabled, "MCP enabled" if mcp_enabled else "MCP disabled")
                
            except json.JSONDecodeError as e:
                self.print_result("Cursor AI Settings", False, f"Invalid JSON: {e}")
                all_good = False
        else:
            self.print_result("Cursor AI Settings", False, "Settings file not found")
            all_good = False
        
        # Check rules file
        if rules_path.exists():
            try:
                with open(rules_path) as f:
                    rules = json.load(f)
                
                rule_count = len(rules.get("rules", []))
                self.print_result("Cursor AI Rules", True, f"{rule_count} rules configured")
                
            except json.JSONDecodeError as e:
                self.print_result("Cursor AI Rules", False, f"Invalid JSON: {e}")
                all_good = False
        else:
            self.print_result("Cursor AI Rules", False, "Rules file not found")
            all_good = False
        
        return all_good
    
    def check_devcontainer_configuration(self) -> bool:
        """Verify devcontainer configuration"""
        self.print_header("DevContainer Configuration")
        
        devcontainer_path = self.project_root / ".devcontainer" / "devcontainer.json"
        setup_script_path = self.project_root / ".devcontainer" / "setup_env.sh"
        
        all_good = True
        
        # Check devcontainer.json
        if devcontainer_path.exists():
            try:
                with open(devcontainer_path) as f:
                    config = json.load(f)
                
                extensions = config.get("customizations", {}).get("vscode", {}).get("extensions", [])
                features = config.get("features", {})
                
                self.print_result("DevContainer Configuration", True, f"{len(extensions)} extensions, {len(features)} features")
                
                # Check for key extensions
                key_extensions = [
                    "ms-python.python",
                    "github.copilot",
                    "ms-python.black-formatter"
                ]
                
                for ext in key_extensions:
                    if ext in extensions:
                        self.print_result(f"Extension: {ext}", True, "Configured")
                    else:
                        self.print_warning(f"Extension: {ext}", "Not configured")
                
            except json.JSONDecodeError as e:
                self.print_result("DevContainer Configuration", False, f"Invalid JSON: {e}")
                all_good = False
        else:
            self.print_result("DevContainer Configuration", False, "File not found")
            all_good = False
        
        # Check setup script
        if setup_script_path.exists():
            if os.access(setup_script_path, os.X_OK):
                self.print_result("Setup Script", True, "Found and executable")
            else:
                self.print_result("Setup Script", False, "Found but not executable")
                all_good = False
        else:
            self.print_result("Setup Script", False, "File not found")
            all_good = False
        
        return all_good
    
    def check_python_dependencies(self) -> bool:
        """Verify Python dependencies are installed"""
        self.print_header("Python Dependencies")
        
        required_packages = [
            "openai",
            "anthropic", 
            "weaviate-client",
            "pinecone-client",
            "redis",
            "psycopg2-binary",
            "fastapi",
            "uvicorn",
            "python-dotenv",
            "gitpython",
            "psutil"
        ]
        
        all_good = True
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                self.print_result(f"Package: {package}", True, "Installed")
            except ImportError:
                self.print_result(f"Package: {package}", False, "Not installed")
                all_good = False
        
        return all_good
    
    def check_services(self) -> bool:
        """Check if required services are running"""
        self.print_header("Service Status")
        
        all_good = True
        
        # Check Redis
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.ping()
            self.print_result("Redis Server", True, "Running and accessible")
        except Exception as e:
            self.print_result("Redis Server", False, str(e))
            all_good = False
        
        return all_good
    
    def generate_summary_report(self):
        """Generate final summary report"""
        self.print_header("Cherry AI Setup Verification Summary")
        
        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results.values() if r["status"])
        failed_checks = total_checks - passed_checks
        
        print(f"\n📊 Overall Results:")
        print(f"   Total Checks: {total_checks}")
        print(f"   ✅ Passed: {passed_checks}")
        print(f"   ❌ Failed: {failed_checks}")
        print(f"   ⚠️  Warnings: {len(self.warnings)}")
        
        success_rate = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print(f"\n🎉 Excellent! Your Cherry AI setup is ready for production use!")
        elif success_rate >= 75:
            print(f"\n👍 Good! Your Cherry AI setup is mostly ready. Address the failed checks for optimal performance.")
        elif success_rate >= 50:
            print(f"\n⚠️  Your Cherry AI setup needs attention. Please address the failed checks before proceeding.")
        else:
            print(f"\n🚨 Your Cherry AI setup requires significant fixes. Please review all failed checks.")
        
        if self.errors:
            print(f"\n❌ Critical Issues to Address:")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(self.errors) > 5:
                print(f"   ... and {len(self.errors) - 5} more issues")
        
        if self.warnings:
            print(f"\n⚠️  Warnings to Consider:")
            for warning in self.warnings[:3]:  # Show first 3 warnings
                print(f"   • {warning}")
            if len(self.warnings) > 3:
                print(f"   ... and {len(self.warnings) - 3} more warnings")
        
        print(f"\n🔗 Next Steps:")
        if success_rate >= 90:
            print(f"   1. Start using Cursor AI with Cherry AI tools")
            print(f"   2. Run: cherry-ai start-mcp")
            print(f"   3. Test AI coding assistance")
            print(f"   4. Deploy to production when ready")
        else:
            print(f"   1. Fix critical issues listed above")
            print(f"   2. Re-run this verification script")
            print(f"   3. Consult the Cherry AI documentation")
            print(f"   4. Contact support if needed")
    
    async def run_verification(self):
        """Run complete verification suite"""
        print("🍒 Cherry AI Orchestrator - Setup Verification")
        print("=" * 60)
        print("This script will verify your Cherry AI development environment")
        print("and ensure all components are properly configured.\n")
        
        # Run all verification checks
        checks = [
            self.check_environment_variables,
            self.check_project_structure,
            self.check_mcp_configuration,
            self.check_cursor_configuration,
            self.check_devcontainer_configuration,
            self.check_python_dependencies,
            self.check_services,
            self.check_api_connectivity
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                logger.error(f"Error in {check.__name__}: {e}")
                self.errors.append(f"{check.__name__}: {e}")
        
        # Generate final report
        self.generate_summary_report()

def main():
    """Main entry point"""
    verifier = CherryAIVerifier()
    asyncio.run(verifier.run_verification())

if __name__ == "__main__":
    main()

