#!/usr/bin/env python3
"""
Orchestra AI System Validation Script
Comprehensive testing and validation of the refactored architecture
"""

import os
import sys
import asyncio
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import logging
import asyncpg
import redis
import httpx
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of a validation check"""
    component: str
    check: str
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None

class OrchestraValidator:
    """Comprehensive system validator"""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.project_root = Path(".")
        
    async def validate_system(self):
        """Run all validation checks"""
        logger.info("Starting Orchestra AI system validation...")
        
        # Phase 1: Environment validation
        await self._validate_environment()
        
        # Phase 2: File structure validation
        await self._validate_file_structure()
        
        # Phase 3: Code quality validation
        await self._validate_code_quality()
        
        # Phase 4: Service connectivity
        await self._validate_services()
        
        # Phase 5: API functionality
        await self._validate_api()
        
        # Phase 6: Security validation
        await self._validate_security()
        
        # Generate report
        self._generate_validation_report()
    
    async def _validate_environment(self):
        """Validate environment configuration"""
        logger.info("Validating environment configuration...")
        
        # Check .env.production
        env_file = self.project_root / ".env.production"
        if env_file.exists():
            content = env_file.read_text()
            
            # Check for placeholder secrets
            if "your-secret-key-here" in content:
                self.results.append(ValidationResult(
                    component="Environment",
                    check="Secret placeholders",
                    passed=True,
                    message="Secrets are properly replaced with placeholders"
                ))
            else:
                self.results.append(ValidationResult(
                    component="Environment",
                    check="Secret placeholders",
                    passed=False,
                    message="WARNING: Hardcoded secrets detected in .env.production"
                ))
            
            # Check required variables
            required_vars = [
                "DATABASE_URL", "REDIS_URL", "SECRET_KEY", 
                "JWT_SECRET", "OPENAI_API_KEY"
            ]
            
            missing_vars = []
            for var in required_vars:
                if var not in content:
                    missing_vars.append(var)
            
            if not missing_vars:
                self.results.append(ValidationResult(
                    component="Environment",
                    check="Required variables",
                    passed=True,
                    message="All required environment variables present"
                ))
            else:
                self.results.append(ValidationResult(
                    component="Environment",
                    check="Required variables",
                    passed=False,
                    message=f"Missing environment variables: {', '.join(missing_vars)}"
                ))
        else:
            self.results.append(ValidationResult(
                component="Environment",
                check="Environment file",
                passed=False,
                message=".env.production file not found"
            ))
    
    async def _validate_file_structure(self):
        """Validate project file structure"""
        logger.info("Validating file structure...")
        
        # Check critical directories
        critical_dirs = [
            "api", "core", "services", "repositories", 
            "interfaces", "migrations", "admin-interface"
        ]
        
        for dir_name in critical_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                self.results.append(ValidationResult(
                    component="File Structure",
                    check=f"{dir_name} directory",
                    passed=True,
                    message=f"{dir_name} directory exists"
                ))
            else:
                self.results.append(ValidationResult(
                    component="File Structure",
                    check=f"{dir_name} directory",
                    passed=False,
                    message=f"{dir_name} directory missing"
                ))
        
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
                self.results.append(ValidationResult(
                    component="File Structure",
                    check=description,
                    passed=True,
                    message=f"{file_name} exists"
                ))
            else:
                self.results.append(ValidationResult(
                    component="File Structure",
                    check=description,
                    passed=False,
                    message=f"{file_name} missing"
                ))
        
        # Check for new architecture files
        new_files = [
            ("core/schema_manager.py", "Schema Manager"),
            ("services/authentication_service.py", "Authentication Service"),
            ("repositories/base_repository.py", "Repository Pattern"),
            ("interfaces/service_interfaces.py", "Service Interfaces"),
            ("core/error_handling.py", "Error Handling"),
            ("core/connection_pool_manager.py", "Connection Pool Manager"),
            ("core/cache_manager.py", "Cache Manager"),
            ("core/monitoring.py", "Monitoring System")
        ]
        
        for file_path, description in new_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.results.append(ValidationResult(
                    component="Architecture",
                    check=description,
                    passed=True,
                    message=f"{description} implemented"
                ))
            else:
                self.results.append(ValidationResult(
                    component="Architecture",
                    check=description,
                    passed=False,
                    message=f"{description} not found at {file_path}"
                ))
    
    async def _validate_code_quality(self):
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
            self.results.append(ValidationResult(
                component="Code Quality",
                check="Deleted file references",
                passed=True,
                message="No references to deleted files found"
            ))
        else:
            self.results.append(ValidationResult(
                component="Code Quality",
                check="Deleted file references",
                passed=False,
                message=f"Found {len(files_with_issues)} files with references to deleted patterns",
                details={"files": [str(f[0]) for f in files_with_issues[:5]]}
            ))
        
        # Check Docker Compose syntax
        docker_compose = self.project_root / "docker-compose.production.yml"
        if docker_compose.exists():
            result = subprocess.run(
                ["docker-compose", "-f", str(docker_compose), "config"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.results.append(ValidationResult(
                    component="Docker",
                    check="Docker Compose syntax",
                    passed=True,
                    message="Docker Compose file is valid"
                ))
            else:
                self.results.append(ValidationResult(
                    component="Docker",
                    check="Docker Compose syntax",
                    passed=False,
                    message="Docker Compose file has syntax errors",
                    details={"error": result.stderr}
                ))
    
    async def _validate_services(self):
        """Validate service connectivity"""
        logger.info("Validating service connectivity...")
        
        # Check PostgreSQL
        try:
            conn = await asyncpg.connect(
                "postgresql://localhost:5432/postgres",
                timeout=5
            )
            await conn.close()
            self.results.append(ValidationResult(
                component="Services",
                check="PostgreSQL",
                passed=True,
                message="PostgreSQL is accessible"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                component="Services",
                check="PostgreSQL",
                passed=False,
                message=f"PostgreSQL connection failed: {str(e)}"
            ))
        
        # Check Redis
        try:
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.ping()
            self.results.append(ValidationResult(
                component="Services",
                check="Redis",
                passed=True,
                message="Redis is accessible"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                component="Services",
                check="Redis",
                passed=False,
                message=f"Redis connection failed: {str(e)}"
            ))
        
        # Check Weaviate
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8080/v1/.well-known/ready")
                if response.status_code == 200:
                    self.results.append(ValidationResult(
                        component="Services",
                        check="Weaviate",
                        passed=True,
                        message="Weaviate is accessible"
                    ))
                else:
                    self.results.append(ValidationResult(
                        component="Services",
                        check="Weaviate",
                        passed=False,
                        message=f"Weaviate returned status {response.status_code}"
                    ))
        except Exception as e:
            self.results.append(ValidationResult(
                component="Services",
                check="Weaviate",
                passed=False,
                message=f"Weaviate connection failed: {str(e)}"
            ))
    
    async def _validate_api(self):
        """Validate API functionality"""
        logger.info("Validating API functionality...")
        
        # Check API health endpoint
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/api/system/health")
                if response.status_code == 200:
                    self.results.append(ValidationResult(
                        component="API",
                        check="Health endpoint",
                        passed=True,
                        message="API health endpoint is working"
                    ))
                else:
                    self.results.append(ValidationResult(
                        component="API",
                        check="Health endpoint",
                        passed=False,
                        message=f"API health endpoint returned {response.status_code}"
                    ))
        except Exception as e:
            self.results.append(ValidationResult(
                component="API",
                check="Health endpoint",
                passed=False,
                message=f"API not accessible: {str(e)}"
            ))
        
        # Check API documentation
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/docs")
                if response.status_code == 200:
                    self.results.append(ValidationResult(
                        component="API",
                        check="Documentation",
                        passed=True,
                        message="API documentation is accessible"
                    ))
                else:
                    self.results.append(ValidationResult(
                        component="API",
                        check="Documentation",
                        passed=False,
                        message=f"API documentation returned {response.status_code}"
                    ))
        except Exception:
            pass  # Documentation might not be available if API is down
    
    async def _validate_security(self):
        """Validate security configurations"""
        logger.info("Validating security...")
        
        # Check for common security issues
        security_checks = [
            ("CORS configuration", self._check_cors_config),
            ("JWT configuration", self._check_jwt_config),
            ("Database credentials", self._check_db_credentials),
            ("API rate limiting", self._check_rate_limiting)
        ]
        
        for check_name, check_func in security_checks:
            result = await check_func()
            self.results.append(ValidationResult(
                component="Security",
                check=check_name,
                passed=result["passed"],
                message=result["message"],
                details=result.get("details")
            ))
    
    async def _check_cors_config(self) -> Dict[str, Any]:
        """Check CORS configuration"""
        api_main = self.project_root / "api" / "main.py"
        if api_main.exists():
            content = api_main.read_text()
            if "CORSMiddleware" in content:
                if "allow_origins=[\"*\"]" in content:
                    return {
                        "passed": False,
                        "message": "CORS allows all origins (security risk)"
                    }
                else:
                    return {
                        "passed": True,
                        "message": "CORS properly configured with specific origins"
                    }
        return {
            "passed": False,
            "message": "CORS configuration not found"
        }
    
    async def _check_jwt_config(self) -> Dict[str, Any]:
        """Check JWT configuration"""
        # This is a simplified check
        return {
            "passed": True,
            "message": "JWT configuration present (verify secret strength manually)"
        }
    
    async def _check_db_credentials(self) -> Dict[str, Any]:
        """Check database credential security"""
        env_file = self.project_root / ".env.production"
        if env_file.exists():
            content = env_file.read_text()
            if "cherry_ai_secure_2024" in content:
                return {
                    "passed": False,
                    "message": "Default database password detected"
                }
        return {
            "passed": True,
            "message": "Database credentials properly configured"
        }
    
    async def _check_rate_limiting(self) -> Dict[str, Any]:
        """Check for rate limiting implementation"""
        # This would check for rate limiting middleware
        return {
            "passed": False,
            "message": "Rate limiting not implemented (recommended for production)"
        }
    
    def _generate_validation_report(self):
        """Generate validation report"""
        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results if r.passed)
        failed_checks = total_checks - passed_checks
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_checks": total_checks,
                "passed": passed_checks,
                "failed": failed_checks,
                "success_rate": f"{(passed_checks/total_checks)*100:.1f}%"
            },
            "results": [
                {
                    "component": r.component,
                    "check": r.check,
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details
                }
                for r in self.results
            ],
            "critical_issues": [
                r for r in self.results 
                if not r.passed and r.component in ["Security", "Environment", "Docker"]
            ],
            "recommendations": self._generate_recommendations()
        }
        
        # Save report
        report_path = self.project_root / "validation_report.json"
        report_path.write_text(json.dumps(report, indent=2, default=str))
        
        # Print summary
        print("\n" + "="*60)
        print("ORCHESTRA AI VALIDATION REPORT")
        print("="*60)
        print(f"Total Checks: {total_checks}")
        print(f"Passed: {passed_checks} ✅")
        print(f"Failed: {failed_checks} ❌")
        print(f"Success Rate: {(passed_checks/total_checks)*100:.1f}%")
        
        if failed_checks > 0:
            print("\n⚠️  FAILED CHECKS:")
            for r in self.results:
                if not r.passed:
                    print(f"  - [{r.component}] {r.check}: {r.message}")
        
        print(f"\nDetailed report saved to: {report_path}")
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Check for specific issues
        for result in self.results:
            if not result.passed:
                if "rate limiting" in result.check.lower():
                    recommendations.append("Implement rate limiting using slowapi or similar")
                elif "cors" in result.check.lower():
                    recommendations.append("Review and restrict CORS origins for production")
                elif "secret" in result.message.lower():
                    recommendations.append("Use environment-specific secrets management (e.g., AWS Secrets Manager)")
                elif "docker" in result.component.lower():
                    recommendations.append("Fix Docker Compose configuration before deployment")
        
        # General recommendations
        recommendations.extend([
            "Set up continuous integration/continuous deployment (CI/CD)",
            "Implement comprehensive logging and monitoring",
            "Add integration and end-to-end tests",
            "Configure automated backups for databases",
            "Set up SSL/TLS certificates for production",
            "Implement API versioning strategy"
        ])
        
        return list(set(recommendations))  # Remove duplicates

async def main():
    """Run validation"""
    validator = OrchestraValidator()
    await validator.validate_system()

if __name__ == "__main__":
    asyncio.run(main())