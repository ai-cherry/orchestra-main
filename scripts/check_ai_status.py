#!/usr/bin/env python3
"""
Check the status of all AI optimizations for Orchestra AI
"""

import os
import sys
import subprocess
import json
import requests
from pathlib import Path
from typing import Dict, List, Tuple
import psutil

class AIStatusChecker:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.checks = []
        
    def add_check(self, name: str, status: bool, message: str):
        """Add a check result"""
        icon = "✅" if status else "❌"
        self.checks.append(f"{icon} {name}: {message}")
        
    def check_file_exists(self, path: str, name: str) -> bool:
        """Check if a file exists"""
        file_path = self.project_root / path
        exists = file_path.exists()
        self.add_check(name, exists, f"{'Found' if exists else 'Missing'} at {path}")
        return exists
        
    def check_service_running(self, port: int, name: str) -> bool:
        """Check if a service is running on a port"""
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            running = response.status_code == 200
            self.add_check(name, running, f"Running on port {port}")
            return running
        except:
            self.add_check(name, False, f"Not running on port {port}")
            return False
            
    def check_process_running(self, process_name: str, display_name: str) -> bool:
        """Check if a process is running"""
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if process_name in cmdline:
                    self.add_check(display_name, True, f"Process running (PID: {proc.pid})")
                    return True
            except:
                continue
        self.add_check(display_name, False, "Process not found")
        return False
        
    def run_checks(self):
        """Run all status checks"""
        print("🤖 Orchestra AI - AI Optimization Status Check")
        print("=" * 50)
        
        # Check AI Context Files
        print("\n📁 AI Context Files:")
        self.check_file_exists(".ai-context/context_loader.py", "AI Context Loader")
        self.check_file_exists("src/utils/ai_directives.py", "AI Directives")
        self.check_file_exists(".cursor/rules/orchestra_ai_rules.yaml", "Cursor AI Rules")
        self.check_file_exists("api/vercel_gateway.py", "Vercel AI Gateway")
        self.check_file_exists("scripts/setup_ai_agents.py", "AI Setup Script")
        
        # Check MCP Server Files
        print("\n📦 MCP Server Files:")
        self.check_file_exists("mcp_servers/base_mcp_server.py", "Base MCP Server")
        self.check_file_exists("mcp_servers/example_mcp_server.py", "Example MCP Server")
        
        # Check CI/CD Files
        print("\n🔧 CI/CD Configuration:")
        self.check_file_exists(".pre-commit-config.yaml", "Pre-commit Hooks")
        self.check_file_exists(".github/workflows/deploy-infrastructure.yml", "GitHub Actions")
        self.check_file_exists("scripts/setup-ci-cd.sh", "CI/CD Setup Script")
        
        # Check Documentation
        print("\n📚 Documentation:")
        self.check_file_exists("AI_AGENT_OPTIMIZATION_SUMMARY.md", "AI Optimization Summary")
        self.check_file_exists("AI_OPTIMIZATION_README.md", "AI Optimization Guide")
        self.check_file_exists("AUTOSTART_GUIDE.md", "Autostart Guide")
        self.check_file_exists("OPTIMAL_AI_CODING_SETUP.md", "Optimal Setup Guide")
        
        # Check Running Services
        print("\n🚀 Running Services:")
        self.check_service_running(8000, "API Server")
        self.check_service_running(3000, "Frontend")
        self.check_service_running(8003, "MCP Memory Server")
        
        # Check Processes
        print("\n⚙️ Background Processes:")
        self.check_process_running("orchestra_autostart.py", "Orchestra Autostart")
        self.check_process_running("context_loader.py", "AI Context Loader")
        
        # Check Environment
        print("\n🌍 Environment:")
        venv_active = os.environ.get('VIRTUAL_ENV') is not None
        self.add_check("Virtual Environment", venv_active, 
                      f"{'Active' if venv_active else 'Not active - run: source venv/bin/activate'}")
        
        # Check Dependencies
        print("\n📦 Key Dependencies:")
        try:
            import greenlet
            self.add_check("Greenlet", True, "Installed")
        except ImportError:
            self.add_check("Greenlet", False, "Not installed - run: pip install greenlet")
            
        try:
            import magic
            self.add_check("Python-Magic", True, "Installed")
        except ImportError:
            self.add_check("Python-Magic", False, "Not installed - run: pip install python-magic")
            
        # Summary
        print("\n" + "=" * 50)
        total = len(self.checks)
        passed = sum(1 for check in self.checks if check.startswith("✅"))
        print(f"📊 Summary: {passed}/{total} checks passed")
        
        if passed < total:
            print("\n💡 To fix issues:")
            print("1. Run: ./scripts/fix_dependencies.sh")
            print("2. Run: ./scripts/orchestra_autostart.py")
            print("3. Run: python scripts/setup_ai_agents.py")
            
        return passed == total

if __name__ == "__main__":
    checker = AIStatusChecker()
    success = checker.run_checks()
    sys.exit(0 if success else 1) 