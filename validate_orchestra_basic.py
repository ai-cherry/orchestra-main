#!/usr/bin/env python3
"""
Orchestra AI Basic System Validation Script
Validates the refactored architecture without external dependencies
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BasicValidator:
    """Basic system validator without external dependencies"""
    
    def __init__(self):
        self.results = []
        self.project_root = Path(".")
        
    def validate_system(self):
        """Run all validation checks"""
        logger.info("Starting Orchestra AI basic validation...")
        
        # Phase 1: Environment validation
        self._validate_environment()
        
        # Phase 2: File structure validation
        self._validate_file_structure()
        
        # Phase 3: Code quality validation
        self._validate_code_quality()
        
        # Phase 4: Docker validation
        self._validate_docker()
        
        # Phase 5: Python syntax validation
        self._validate_python_syntax()
        
        # Generate report
        self._generate_validation_report()
    
    def _validate_environment(self):
        """Validate environment configuration"""
        logger.info("Validating environment configuration...")
        
        # Check .env.production
        env_file = self.project_root / ".env.production"
        if env_file.exists():
            content = env_file.read_text()
            
            # Check for placeholder secrets
            if "your-secret-key-here" in content:
                self._add_result("Environment", "Secret placeholders", True, 
                               "Secrets are properly replaced with placeholders")
            else:
                self._add_result("Environment", "Secret placeholders", False,
                               "WARNING: Possible hardcoded secrets in .env.production")
            
            # Check required variables
            required_vars = [
                "DATABASE_URL", "REDIS_URL", "SECRET_KEY", 
                "JWT_SECRET", "OPENAI_API_KEY"
            ]
            
            missing_vars = []
            for var in required_vars:
                if f"{var}=" not in content:
                    missing_vars.append(var)
            
            if not missing_vars:
                self._add_result("Environment", "Required variables", True,
                               "All required environment variables present")
            else:
                self._add_result("Environment", "Required variables", False,
                               f"Missing environment variables: {', '.join(missing_vars)}")
        else:
            self._add_result("Environment", "Environment file", False,
                           ".env.production file not found")
    
    def _validate_file_structure(self):
        """Validate project file structure"""
        logger.info("Validating file structure...")
        
        # Check critical directories
        critical_dirs = [
            ("api", "API directory"),
            ("core", "Core business logic"),
            ("services", "Service layer"),
            ("repositories", "Repository pattern"),
            ("interfaces", "Interface definitions"),
            ("migrations", "Database migrations"),
            ("admin-interface", "Admin dashboard")
        ]
        
        for dir_name, description in critical_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                self._add_result("File Structure", description, True,
                               f"{dir_name} directory exists")
            else:
                self._add_result("File Structure", description, False,
                               f"{dir_name} directory missing")
        
        # Check critical files
        critical_files = [
            ("docker-compose.production.yml", "Docker Compose"),
            ("requirements.txt", "Python dependencies"),
            ("README.md", "Project documentation"),
            (".gitignore", "Git configuration")
        ]
        
        for file_name, description in critical_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                self._add_result("File Structure", description, True,
                               f"{file_name} exists")
            else:
                self._add_result("File Structure", description, False,
                               f"{file_name} missing")
        
        # Check for new architecture files
        new_files = [
            ("core/schema_manager.py", "Schema Manager"),
            ("services/authentication_service.py", "Authentication Service"),
            ("repositories/base_repository.py", "Repository Pattern"),
            ("interfaces/service_interfaces.py", "Service Interfaces"),
            ("core/error_handling.py", "Error Handling"),
            ("core/connection_pool_manager.py", "Connection Pool Manager"),
            ("core/cache_manager.py", "Cache Manager"),
            ("core/monitoring.py", "Monitoring System"),
            ("migrations/001_initial_schema.sql", "Initial Schema Migration")
        ]
        
        for file_path, description in new_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self._add_result("Architecture", description, True,
                               f"{description} implemented")
            else:
                self._add_result("Architecture", description, False,
                               f"{description} not found at {file_path}")
    
    def _validate_code_quality(self):
        """Validate code quality and patterns"""
        logger.info("Validating code quality...")
        
        # Check for deleted file references
        patterns_to_check = [
            "audit_results_",
            "fix_",
            "cleanup_",
            "debug_",
            "test_output_"
        ]
        
        python_files = list(self.project_root.rglob("*.py"))
        files_with_issues = []
        
        for py_file in python_files:
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                for pattern in patterns_to_check:
                    if pattern in content and "cleaned_reference" not in content:
                        files_with_issues.append((py_file, pattern))
                        break
            except Exception:
                pass
        
        if not files_with_issues:
            self._add_result("Code Quality", "Deleted file references", True,
                           "No references to deleted files found")
        else:
            self._add_result("Code Quality", "Deleted file references", False,
                           f"Found {len(files_with_issues)} files with references to deleted patterns")
        
        # Check README content
        readme = self.project_root / "README.md"
        if readme.exists():
            content = readme.read_text()
            if "Orchestra AI" in content:
                self._add_result("Documentation", "README content", True,
                               "README contains Orchestra AI documentation")
            else:
                self._add_result("Documentation", "README content", False,
                               "README does not contain Orchestra AI documentation")
    
    def _validate_docker(self):
        """Validate Docker configuration"""
        logger.info("Validating Docker configuration...")
        
        docker_compose = self.project_root / "docker-compose.production.yml"
        if docker_compose.exists():
            # Check for syntax using docker-compose config
            result = subprocess.run(
                ["docker-compose", "-f", str(docker_compose), "config"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self._add_result("Docker", "Docker Compose syntax", True,
                               "Docker Compose file is valid")
                
                # Check for ai_bridge service
                content = docker_compose.read_text()
                if "ai_bridge:" in content:
                    self._add_result("Docker", "AI Bridge service", True,
                                   "AI Bridge service properly defined")
                else:
                    self._add_result("Docker", "AI Bridge service", False,
                                   "AI Bridge service missing")
            else:
                self._add_result("Docker", "Docker Compose syntax", False,
                               "Docker Compose file has syntax errors")
    
    def _validate_python_syntax(self):
        """Validate Python syntax in key files"""
        logger.info("Validating Python syntax...")
        
        key_files = [
            "api/main.py",
            "api/conversation_engine.py",
            "core/schema_manager.py",
            "services/authentication_service.py"
        ]
        
        for file_path in key_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                result = subprocess.run(
                    ["python3", "-m", "py_compile", str(full_path)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self._add_result("Python Syntax", file_path, True,
                                   f"{file_path} has valid syntax")
                else:
                    self._add_result("Python Syntax", file_path, False,
                                   f"{file_path} has syntax errors: {result.stderr}")
    
    def _add_result(self, component: str, check: str, passed: bool, message: str):
        """Add a validation result"""
        self.results.append({
            "component": component,
            "check": check,
            "passed": passed,
            "message": message
        })
        
        # Log result
        status = "✅" if passed else "❌"
        logger.info(f"{status} [{component}] {check}: {message}")
    
    def _generate_validation_report(self):
        """Generate validation report"""
        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results if r["passed"])
        failed_checks = total_checks - passed_checks
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_checks": total_checks,
                "passed": passed_checks,
                "failed": failed_checks,
                "success_rate": f"{(passed_checks/total_checks)*100:.1f}%" if total_checks > 0 else "0%"
            },
            "results": self.results,
            "critical_issues": [
                r for r in self.results 
                if not r["passed"] and r["component"] in ["Environment", "Docker", "Architecture"]
            ],
            "recommendations": self._generate_recommendations()
        }
        
        # Save report
        report_path = self.project_root / "validation_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("ORCHESTRA AI VALIDATION REPORT")
        print("="*60)
        print(f"Total Checks: {total_checks}")
        print(f"Passed: {passed_checks} ✅")
        print(f"Failed: {failed_checks} ❌")
        print(f"Success Rate: {(passed_checks/total_checks)*100:.1f}%" if total_checks > 0 else "0%")
        
        if failed_checks > 0:
            print("\n⚠️  CRITICAL ISSUES:")
            for r in report["critical_issues"]:
                print(f"  - [{r['component']}] {r['check']}: {r['message']}")
            
            print("\n❌ ALL FAILED CHECKS:")
            for r in self.results:
                if not r["passed"]:
                    print(f"  - [{r['component']}] {r['check']}: {r['message']}")
        
        print(f"\nDetailed report saved to: {report_path}")
        
        # Return summary for CI/CD integration
        return failed_checks == 0
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Check for specific issues
        for result in self.results:
            if not result["passed"]:
                if "docker" in result["component"].lower():
                    recommendations.append("Fix Docker Compose configuration before deployment")
                elif "environment" in result["component"].lower():
                    recommendations.append("Configure all required environment variables")
                elif "architecture" in result["component"].lower():
                    recommendations.append("Complete architecture refactoring implementation")
        
        # General recommendations
        recommendations.extend([
            "Run 'pip install -r requirements.txt' to install dependencies",
            "Set up continuous integration/continuous deployment (CI/CD)",
            "Implement comprehensive logging and monitoring",
            "Add integration and end-to-end tests",
            "Configure automated backups for databases",
            "Set up SSL/TLS certificates for production"
        ])
        
        return list(set(recommendations))  # Remove duplicates

def main():
    """Run validation"""
    validator = BasicValidator()
    success = validator.validate_system()
    
    # Exit with appropriate code for CI/CD
    exit(0 if success else 1)

if __name__ == "__main__":
    main()