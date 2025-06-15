#!/usr/bin/env python3

# 🎼 Orchestra AI Environment Validation & Health Check
# Comprehensive validation of development environment

import sys
import os
import subprocess
import json
import time
import requests
from pathlib import Path

class EnvironmentValidator:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0
        
    def log_success(self, message):
        print(f"✅ {message}")
        self.success_count += 1
        
    def log_warning(self, message):
        print(f"⚠️  {message}")
        self.warnings.append(message)
        
    def log_error(self, message):
        print(f"❌ {message}")
        self.issues.append(message)
        
    def run_command(self, command, description=""):
        """Run shell command and return output"""
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            self.log_error(f"Command timed out: {command}")
            return False, "", "Timeout"
        except Exception as e:
            self.log_error(f"Command failed: {command} - {str(e)}")
            return False, "", str(e)
    
    def check_python_environment(self):
        """Validate Python environment and dependencies"""
        print("\n🐍 Python Environment Check")
        print("=" * 30)
        
        # Check Python version
        self.total_checks += 1
        success, output, _ = self.run_command("python3 --version")
        if success and "3.11" in output:
            self.log_success(f"Python version: {output.strip()}")
        else:
            self.log_error("Python 3.11 not found or not accessible")
        
        # Check virtual environment
        self.total_checks += 1
        if os.environ.get('VIRTUAL_ENV'):
            self.log_success(f"Virtual environment active: {os.environ['VIRTUAL_ENV']}")
        else:
            self.log_warning("No virtual environment detected")
        
        # Check critical Python packages
        critical_packages = [
            'fastapi', 'uvicorn', 'sqlalchemy', 'pydantic', 
            'aiosqlite', 'python-magic', 'structlog', 'greenlet'
        ]
        
        for package in critical_packages:
            self.total_checks += 1
            success, _, _ = self.run_command(f"pip show {package}")
            if success:
                self.log_success(f"Package installed: {package}")
            else:
                self.log_error(f"Missing package: {package}")
    
    def check_file_structure(self):
        """Validate project file structure"""
        print("\n📁 File Structure Check")
        print("=" * 25)
        
        critical_files = [
            'api/main.py',
            'api/__init__.py',
            'api/database/connection.py',
            'api/services/__init__.py',
            'web/package.json',
            'web/src/App.tsx',
            'web/vite.config.ts',
            'web/tsconfig.json',
            'start_orchestra.sh',
            'setup_dev_environment.sh'
        ]
        
        for file_path in critical_files:
            self.total_checks += 1
            if Path(file_path).exists():
                self.log_success(f"File exists: {file_path}")
            else:
                self.log_error(f"Missing file: {file_path}")
    
    def check_git_status(self):
        """Check Git repository status"""
        print("\n🌿 Git Repository Check")
        print("=" * 23)
        
        # Check if we're in a git repo
        self.total_checks += 1
        success, _, _ = self.run_command("git status")
        if success:
            self.log_success("Git repository detected")
        else:
            self.log_error("Not in a Git repository")
            return
        
        # Check current branch
        self.total_checks += 1
        success, output, _ = self.run_command("git branch --show-current")
        if success:
            branch = output.strip()
            self.log_success(f"Current branch: {branch}")
            
            if branch == "main":
                self.log_warning("Working directly on main branch - consider using feature branches")
        
        # Check for uncommitted changes
        self.total_checks += 1
        success, output, _ = self.run_command("git status --porcelain")
        if success:
            if output.strip():
                # Filter out node_modules changes
                filtered_changes = [line for line in output.split('\n') if line and 'node_modules' not in line]
                if filtered_changes:
                    self.log_warning(f"Important uncommitted changes detected:\n" + '\n'.join(filtered_changes))
                else:
                    self.log_success("Working directory clean (ignoring node_modules)")
            else:
                self.log_success("Working directory clean")
    
    def check_services(self):
        """Check if services are running"""
        print("\n🚀 Service Status Check")
        print("=" * 24)
        
        # Check API server
        self.total_checks += 1
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=5)
            if response.status_code == 200:
                self.log_success("API server responding (port 8000)")
            else:
                self.log_error(f"API server error: HTTP {response.status_code}")
        except requests.exceptions.RequestException:
            self.log_warning("API server not responding (port 8000)")
        
        # Check frontend server
        self.total_checks += 1
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code == 200:
                self.log_success("Frontend server responding (port 3000)")
            else:
                self.log_error(f"Frontend server error: HTTP {response.status_code}")
        except requests.exceptions.RequestException:
            self.log_warning("Frontend server not responding (port 3000)")
    
    def check_ports(self):
        """Check port availability and conflicts"""
        print("\n🔌 Port Status Check")
        print("=" * 19)
        
        critical_ports = [3000, 8000, 8003, 8006, 8007, 8008, 8009]
        
        for port in critical_ports:
            self.total_checks += 1
            success, output, _ = self.run_command(f"lsof -ti :{port}")
            if success and output.strip():
                pid = output.strip()
                # Get process info
                success2, proc_info, _ = self.run_command(f"ps -p {pid} -o comm=")
                if success2:
                    process = proc_info.strip()
                    self.log_success(f"Port {port}: Used by {process} (PID: {pid})")
                else:
                    self.log_success(f"Port {port}: In use (PID: {pid})")
            else:
                self.log_warning(f"Port {port}: Available")
    
    def check_dependencies(self):
        """Check system dependencies"""
        print("\n🔧 System Dependencies Check")
        print("=" * 30)
        
        # Check Node.js
        self.total_checks += 1
        success, output, _ = self.run_command("node --version")
        if success:
            self.log_success(f"Node.js version: {output.strip()}")
        else:
            self.log_error("Node.js not found")
        
        # Check npm/yarn
        self.total_checks += 1
        success, output, _ = self.run_command("npm --version")
        if success:
            self.log_success(f"npm version: {output.strip()}")
        else:
            self.log_error("npm not found")
        
        # Check libmagic (for file processing)
        self.total_checks += 1
        libmagic_paths = [
            "/opt/homebrew/lib/libmagic.dylib",
            "/usr/local/lib/libmagic.dylib",
            "/usr/lib/libmagic.so"
        ]
        
        libmagic_found = False
        for path in libmagic_paths:
            if Path(path).exists():
                self.log_success(f"libmagic found: {path}")
                libmagic_found = True
                break
        
        if not libmagic_found:
            self.log_warning("libmagic not found - file processing may not work")
    
    def check_database(self):
        """Check database connectivity"""
        print("\n🗄️  Database Check")
        print("=" * 16)
        
        # Check SQLite file
        self.total_checks += 1
        sqlite_path = "api/orchestra.db"
        if Path(sqlite_path).exists():
            self.log_success(f"SQLite database exists: {sqlite_path}")
        else:
            self.log_warning("SQLite database not found - will be created on first run")
        
        # Test database connection (if API is running)
        self.total_checks += 1
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=5)
            if response.status_code == 200:
                self.log_success("Database connection working (via API health check)")
            else:
                self.log_warning("Database connection status unknown")
        except requests.exceptions.RequestException:
            self.log_warning("Cannot test database connection (API not running)")
    
    def check_mcp_infrastructure(self):
        """Check MCP server infrastructure"""
        print("\n🔗 MCP Infrastructure Check")
        print("=" * 28)
        
        # Check for MCP configuration
        self.total_checks += 1
        mcp_config = "claude_mcp_config.json"
        if Path(mcp_config).exists():
            self.log_success(f"MCP configuration found: {mcp_config}")
            
            # Try to parse the config
            try:
                with open(mcp_config, 'r') as f:
                    config = json.load(f)
                    if 'mcp_servers' in config:
                        server_count = len(config['mcp_servers'])
                        self.log_success(f"MCP servers configured: {server_count}")
                        
                        # List the configured servers
                        servers = list(config['mcp_servers'].keys())
                        self.log_success(f"Available MCP servers: {', '.join(servers)}")
                    elif 'mcpServers' in config:
                        server_count = len(config['mcpServers'])
                        self.log_success(f"MCP servers configured: {server_count}")
                    else:
                        self.log_warning("MCP config exists but no servers defined")
            except json.JSONDecodeError:
                self.log_error("MCP config file is not valid JSON")
            except Exception as e:
                self.log_error(f"Error reading MCP config: {str(e)}")
        else:
            self.log_warning("MCP configuration not found - available in IaC branch")
        
        # Check for MCP server scripts
        self.total_checks += 1
        mcp_script = "start_mcp_servers_working.sh"
        if Path(mcp_script).exists():
            self.log_success(f"MCP startup script found: {mcp_script}")
        else:
            self.log_warning("MCP startup script not found - available in IaC branch")
    
    def check_frontend_configuration(self):
        """Check frontend configuration and dependencies"""
        print("\n🌐 Frontend Configuration Check")
        print("=" * 33)
        
        # Check TypeScript configuration
        self.total_checks += 1
        ts_config = "web/tsconfig.json"
        if Path(ts_config).exists():
            try:
                with open(ts_config, 'r') as f:
                    config = json.load(f)
                    if 'compilerOptions' in config and 'paths' in config['compilerOptions']:
                        self.log_success("TypeScript path mapping configured")
                    else:
                        self.log_warning("TypeScript path mapping not configured")
            except Exception as e:
                self.log_error(f"Error reading TypeScript config: {str(e)}")
        else:
            self.log_error("TypeScript configuration not found")
        
        # Check Vite configuration
        self.total_checks += 1
        vite_config = "web/vite.config.ts"
        if Path(vite_config).exists():
            self.log_success("Vite configuration found")
        else:
            self.log_error("Vite configuration not found")
        
        # Check package.json
        self.total_checks += 1
        package_json = "web/package.json"
        if Path(package_json).exists():
            try:
                with open(package_json, 'r') as f:
                    config = json.load(f)
                    if 'dependencies' in config:
                        self.log_success(f"Frontend dependencies: {len(config['dependencies'])} packages")
                    if 'scripts' in config:
                        self.log_success(f"NPM scripts: {len(config['scripts'])} scripts")
            except Exception as e:
                self.log_error(f"Error reading package.json: {str(e)}")
        else:
            self.log_error("package.json not found")
    
    def run_comprehensive_check(self):
        """Run all validation checks"""
        print("🎼 Orchestra AI Environment Validation")
        print("=" * 40)
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
        
        # Run all checks
        self.check_python_environment()
        self.check_file_structure()
        self.check_git_status()
        self.check_services()
        self.check_ports()
        self.check_dependencies()
        self.check_database()
        self.check_mcp_infrastructure()
        self.check_frontend_configuration()
        
        # Summary
        print("\n" + "=" * 40)
        print("📊 VALIDATION SUMMARY")
        print("=" * 40)
        
        success_rate = (self.success_count / self.total_checks) * 100 if self.total_checks > 0 else 0
        
        print(f"✅ Successful checks: {self.success_count}/{self.total_checks} ({success_rate:.1f}%)")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Critical issues: {len(self.issues)}")
        
        if self.issues:
            print("\n🚨 CRITICAL ISSUES:")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
        
        print("\n" + "=" * 40)
        
        if not self.issues:
            if not self.warnings:
                print("🎉 ENVIRONMENT STATUS: EXCELLENT")
                print("   All checks passed! Your environment is ready for development.")
            else:
                print("✅ ENVIRONMENT STATUS: GOOD")
                print("   Minor warnings detected, but environment is functional.")
        else:
            print("🚨 ENVIRONMENT STATUS: NEEDS ATTENTION")
            print("   Critical issues detected. Please resolve before continuing.")
        
        print("\n🔗 Next Steps:")
        if self.issues:
            print("   1. Resolve critical issues listed above")
            print("   2. Run './setup_dev_environment.sh' to fix common issues")
            print("   3. Re-run this validation script")
        else:
            print("   1. Start services: './start_orchestra.sh'")
            print("   2. Begin development work")
            print("   3. Consider integrating MCP infrastructure")
        
        print("")
        return len(self.issues) == 0

def main():
    """Main execution"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("🎼 Orchestra AI Environment Validator")
        print("")
        print("Usage:")
        print("  python3 validate_environment.py           # Run all checks")
        print("  python3 validate_environment.py --help    # Show this help")
        print("")
        print("This script validates your Orchestra AI development environment")
        print("and identifies any issues that need to be resolved.")
        return
    
    validator = EnvironmentValidator()
    success = validator.run_comprehensive_check()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 