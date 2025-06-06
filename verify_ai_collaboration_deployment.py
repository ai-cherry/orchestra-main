#!/usr/bin/env python3
"""
Deployment verification script for AI Collaboration Dashboard
Checks all components are ready for production deployment
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime


class DeploymentVerifier:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.issues = []
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def check_file_exists(self, filepath: str, description: str) -> bool:
        """Check if a required file exists"""
        if Path(filepath).exists():
            self.log(f"✅ {description}: {filepath}")
            self.checks_passed += 1
            return True
        else:
            self.log(f"❌ {description}: {filepath} NOT FOUND", "ERROR")
            self.checks_failed += 1
            self.issues.append(f"Missing {description}: {filepath}")
            return False
            
    def check_python_syntax(self, filepath: str) -> bool:
        """Check Python file syntax"""
        try:
            result = subprocess.run(
                ["python3", "-m", "py_compile", filepath],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.log(f"✅ Valid Python syntax: {filepath}")
                self.checks_passed += 1
                return True
            else:
                self.log(f"❌ Python syntax error in {filepath}", "ERROR")
                self.log(result.stderr, "ERROR")
                self.checks_failed += 1
                self.issues.append(f"Syntax error in {filepath}")
                return False
        except Exception as e:
            self.log(f"❌ Failed to check {filepath}: {e}", "ERROR")
            self.checks_failed += 1
            return False
            
    def check_imports(self, module_path: str) -> bool:
        """Check if a Python module can be imported"""
        try:
            result = subprocess.run(
                ["python3", "-c", f"import {module_path}"],
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONPATH": "."}
            )
            if result.returncode == 0:
                self.log(f"✅ Can import: {module_path}")
                self.checks_passed += 1
                return True
            else:
                self.log(f"❌ Cannot import {module_path}", "ERROR")
                self.log(result.stderr, "ERROR")
                self.checks_failed += 1
                self.issues.append(f"Import error: {module_path}")
                return False
        except Exception as e:
            self.log(f"❌ Failed to check import {module_path}: {e}", "ERROR")
            self.checks_failed += 1
            return False
            
    def check_environment_variables(self) -> bool:
        """Check required environment variables"""
        required_vars = [
            "POSTGRES_HOST",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "REDIS_HOST",
            "WEAVIATE_URL",
            "VULTR_API_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if os.getenv(var):
                self.log(f"✅ Environment variable set: {var}")
                self.checks_passed += 1
            else:
                self.log(f"⚠️  Environment variable not set: {var}", "WARNING")
                missing_vars.append(var)
                
        if missing_vars:
            self.issues.append(f"Missing environment variables: {', '.join(missing_vars)}")
            
        return len(missing_vars) == 0
        
    def run_verification(self):
        """Run all verification checks"""
        self.log("=" * 60)
        self.log("AI Collaboration Dashboard Deployment Verification")
        self.log("=" * 60)
        
        # Check core files exist
        self.log("\n📁 Checking core files...")
        core_files = [
            ("services/ai_collaboration/__init__.py", "Package init"),
            ("services/ai_collaboration/service.py", "Main service"),
            ("services/ai_collaboration/interfaces.py", "Interfaces"),
            ("services/ai_collaboration/exceptions.py", "Exceptions"),
            ("services/ai_collaboration/models/entities.py", "Domain entities"),
            ("services/ai_collaboration/models/value_objects.py", "Value objects"),
            ("services/ai_collaboration/models/dto.py", "DTOs"),
            ("services/ai_collaboration/adapters/websocket_adapter.py", "WebSocket adapter"),
            ("services/ai_collaboration/metrics/collector.py", "Metrics collector"),
            ("services/ai_collaboration/routing/task_router.py", "Task router"),
            ("services/ai_collaboration/api/endpoints.py", "API endpoints"),
        ]
        
        for filepath, description in core_files:
            self.check_file_exists(filepath, description)
            
        # Check infrastructure files
        self.log("\n🏗️  Checking infrastructure files...")
        infra_files = [
            ("infrastructure/ai_collaboration/vultr_stack.py", "Vultr Pulumi stack"),
            ("deploy_ai_collaboration.py", "Deployment script"),
        ]
        
        for filepath, description in infra_files:
            self.check_file_exists(filepath, description)
            
        # Check Python syntax
        self.log("\n🐍 Checking Python syntax...")
        python_files = [
            "services/ai_collaboration/service.py",
            "services/ai_collaboration/interfaces.py",
            "services/ai_collaboration/exceptions.py",
            "services/ai_collaboration/models/entities.py",
            "services/ai_collaboration/adapters/websocket_adapter.py",
            "services/ai_collaboration/api/endpoints.py",
        ]
        
        for filepath in python_files:
            if Path(filepath).exists():
                self.check_python_syntax(filepath)
                
        # Check imports
        self.log("\n📦 Checking module imports...")
        modules = [
            "services.ai_collaboration",
            "services.ai_collaboration.models.enums",
            "services.ai_collaboration.models.entities",
            "services.ai_collaboration.service",
        ]
        
        for module in modules:
            self.check_imports(module)
            
        # Check environment variables
        self.log("\n🔐 Checking environment variables...")
        self.check_environment_variables()
        
        # Check test results
        self.log("\n🧪 Running component tests...")
        try:
            result = subprocess.run(
                ["python3", "test_ai_collaboration.py"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.log("✅ All component tests passed")
                self.checks_passed += 1
            else:
                self.log("❌ Component tests failed", "ERROR")
                self.checks_failed += 1
                self.issues.append("Component tests failed")
        except Exception as e:
            self.log(f"❌ Failed to run tests: {e}", "ERROR")
            self.checks_failed += 1
            
        # Summary
        self.log("\n" + "=" * 60)
        self.log("VERIFICATION SUMMARY")
        self.log("=" * 60)
        self.log(f"✅ Checks passed: {self.checks_passed}")
        self.log(f"❌ Checks failed: {self.checks_failed}")
        
        if self.issues:
            self.log("\n⚠️  Issues found:", "WARNING")
            for issue in self.issues:
                self.log(f"  - {issue}", "WARNING")
                
        if self.checks_failed == 0:
            self.log("\n🎉 All checks passed! Ready for deployment.", "SUCCESS")
            self.log("\nNext steps:")
            self.log("1. Set required environment variables")
            self.log("2. Run: python deploy_ai_collaboration.py --environment staging")
            self.log("3. Verify staging deployment")
            self.log("4. Run: python deploy_ai_collaboration.py --environment production")
            return True
        else:
            self.log("\n❌ Deployment verification failed. Please fix the issues above.", "ERROR")
            return False
            
        
def main():
    verifier = DeploymentVerifier()
    success = verifier.run_verification()
    
    # Save verification report
    report = {
        "timestamp": datetime.now().isoformat(),
        "checks_passed": verifier.checks_passed,
        "checks_failed": verifier.checks_failed,
        "issues": verifier.issues,
        "ready_for_deployment": success
    }
    
    with open("ai_collaboration_verification_report.json", "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"\nVerification report saved to: ai_collaboration_verification_report.json")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())