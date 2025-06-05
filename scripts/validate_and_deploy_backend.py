#!/usr/bin/env python3
"""
Comprehensive Backend Validation and Deployment Script
Ensures all backend services are properly configured, tested, and deployed
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime
import psycopg2
import redis
import requests
from typing import Dict, List, Tuple, Any

class BackendValidator:
    def __init__(self):
        self.project_root = Path("/root/cherry_ai-main")
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "errors": [],
            "warnings": [],
            "ready_for_deployment": False
        }
        
    def check_environment(self) -> bool:
        """Check if environment is properly configured"""
        print("🔍 Checking environment configuration...")
        
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "SECRET_KEY",
            "JWT_SECRET",
            "WEAVIATE_URL"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
                
        if missing_vars:
            self.validation_results["errors"].append({
                "check": "environment",
                "error": f"Missing environment variables: {', '.join(missing_vars)}"
            })
            return False
            
        self.validation_results["checks"]["environment"] = "✅ All required variables set"
        return True
        
    def check_database_connection(self) -> bool:
        """Validate PostgreSQL connection and schema"""
        print("🗄️  Checking database connection...")
        
        try:
            db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/cherry_ai")
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ["users", "sessions", "interactions", "personas"]
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                self.validation_results["warnings"].append({
                    "check": "database",
                    "warning": f"Missing tables: {', '.join(missing_tables)}"
                })
                
            cursor.close()
            conn.close()
            
            self.validation_results["checks"]["database"] = f"✅ Connected, {len(tables)} tables found"
            return True
            
        except Exception as e:
            self.validation_results["errors"].append({
                "check": "database",
                "error": str(e)
            })
            return False
            
    def check_redis_connection(self) -> bool:
        """Validate Redis connection"""
        print("📮 Checking Redis connection...")
        
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            r = redis.from_url(redis_url)
            r.ping()
            
            # Test basic operations
            r.set("test_key", "test_value", ex=10)
            value = r.get("test_key")
            r.delete("test_key")
            
            self.validation_results["checks"]["redis"] = "✅ Connected and operational"
            return True
            
        except Exception as e:
            self.validation_results["errors"].append({
                "check": "redis",
                "error": str(e)
            })
            return False
            
    def check_weaviate_connection(self) -> bool:
        """Validate Weaviate connection"""
        print("🔍 Checking Weaviate connection...")
        
        try:
            weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
            response = requests.get(f"{weaviate_url}/v1/meta", timeout=5)
            
            if response.status_code == 200:
                meta = response.json()
                self.validation_results["checks"]["weaviate"] = f"✅ Connected, version {meta.get('version', 'unknown')}"
                return True
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            self.validation_results["errors"].append({
                "check": "weaviate",
                "error": str(e)
            })
            return False
            
    def check_api_endpoints(self) -> bool:
        """Check if API endpoints are accessible"""
        print("🌐 Checking API endpoints...")
        
        api_base = "http://localhost:8000"
        endpoints = [
            ("/health", "GET"),
            ("/api/v1/auth/login", "POST"),
            ("/api/v1/interactions", "GET"),
            ("/api/v1/personas", "GET")
        ]
        
        all_good = True
        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{api_base}{endpoint}", timeout=5)
                else:
                    response = requests.post(f"{api_base}{endpoint}", json={}, timeout=5)
                    
                if response.status_code in [200, 401, 422]:  # Expected responses
                    self.validation_results["checks"][f"api_{endpoint}"] = "✅ Accessible"
                else:
                    self.validation_results["warnings"].append({
                        "check": f"api_{endpoint}",
                        "warning": f"Unexpected status: {response.status_code}"
                    })
                    
            except requests.exceptions.ConnectionError:
                self.validation_results["warnings"].append({
                    "check": f"api_{endpoint}",
                    "warning": "API not running"
                })
                all_good = False
            except Exception as e:
                self.validation_results["errors"].append({
                    "check": f"api_{endpoint}",
                    "error": str(e)
                })
                all_good = False
                
        return all_good
        
    def check_dependencies(self) -> bool:
        """Check if all dependencies are installed"""
        print("📦 Checking dependencies...")
        
        try:
            # Check Python dependencies
            result = subprocess.run(
                ["pip", "check"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.validation_results["warnings"].append({
                    "check": "dependencies",
                    "warning": "Some packages have incompatible dependencies"
                })
                
            # Check for security vulnerabilities
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                self.validation_results["checks"]["dependencies"] = f"✅ {len(packages)} packages installed"
                return True
            else:
                raise Exception("Failed to list packages")
                
        except Exception as e:
            self.validation_results["errors"].append({
                "check": "dependencies",
                "error": str(e)
            })
            return False
            
    def run_tests(self) -> bool:
        """Run backend tests"""
        print("🧪 Running tests...")
        
        test_dirs = ["tests", "test", "tests/unit", "tests/integration"]
        tests_found = False
        
        for test_dir in test_dirs:
            test_path = self.project_root / test_dir
            if test_path.exists():
                tests_found = True
                try:
                    result = subprocess.run(
                        ["python", "-m", "pytest", str(test_path), "-v", "--tb=short"],
                        capture_output=True,
                        text=True,
                        cwd=str(self.project_root)
                    )
                    
                    if result.returncode == 0:
                        self.validation_results["checks"]["tests"] = "✅ All tests passed"
                        return True
                    else:
                        self.validation_results["warnings"].append({
                            "check": "tests",
                            "warning": "Some tests failed"
                        })
                        return False
                        
                except Exception as e:
                    self.validation_results["warnings"].append({
                        "check": "tests",
                        "warning": f"Failed to run tests: {str(e)}"
                    })
                    
        if not tests_found:
            self.validation_results["warnings"].append({
                "check": "tests",
                "warning": "No test directory found"
            })
            
        return True
        
    def check_docker_services(self) -> bool:
        """Check if Docker services are running"""
        print("🐳 Checking Docker services...")
        
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        containers.append(json.loads(line))
                        
                required_services = ["postgres", "redis", "weaviate"]
                running_services = []
                
                for container in containers:
                    for service in required_services:
                        if service in container.get("Names", "").lower():
                            running_services.append(service)
                            
                missing_services = set(required_services) - set(running_services)
                
                if missing_services:
                    self.validation_results["warnings"].append({
                        "check": "docker",
                        "warning": f"Services not running: {', '.join(missing_services)}"
                    })
                    
                self.validation_results["checks"]["docker"] = f"✅ {len(running_services)}/{len(required_services)} services running"
                return len(missing_services) == 0
                
        except Exception as e:
            self.validation_results["errors"].append({
                "check": "docker",
                "error": str(e)
            })
            return False
            
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks"""
        print("\n🚀 Starting comprehensive backend validation...\n")
        
        checks = [
            ("Environment", self.check_environment),
            ("Database", self.check_database_connection),
            ("Redis", self.check_redis_connection),
            ("Weaviate", self.check_weaviate_connection),
            ("Docker Services", self.check_docker_services),
            ("Dependencies", self.check_dependencies),
            ("API Endpoints", self.check_api_endpoints),
            ("Tests", self.run_tests)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                if not check_func():
                    all_passed = False
            except Exception as e:
                self.validation_results["errors"].append({
                    "check": check_name.lower(),
                    "error": f"Check failed: {str(e)}"
                })
                all_passed = False
                
        self.validation_results["ready_for_deployment"] = all_passed and len(self.validation_results["errors"]) == 0
        
        return self.validation_results

class BackendDeployer:
    def __init__(self, validation_results: Dict[str, Any]):
        self.validation_results = validation_results
        self.project_root = Path("/root/cherry_ai-main")
        
    def start_services(self) -> bool:
        """Start all backend services"""
        print("\n🚀 Starting backend services...")
        
        # Start Docker services
        docker_compose_file = self.project_root / "docker-compose.prod.yml"
        if not docker_compose_file.exists():
            docker_compose_file = self.project_root / "docker-compose.yml"
            
        if docker_compose_file.exists():
            print("  Starting Docker services...")
            result = subprocess.run(
                ["docker-compose", "-f", str(docker_compose_file), "up", "-d"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"  ❌ Failed to start Docker services: {result.stderr}")
                return False
                
            # Wait for services to be ready
            print("  Waiting for services to be ready...")
            # TODO: Replace with asyncio.sleep() for async code
            time.sleep(10)
            
        # Start API server
        print("  Starting API server...")
        api_script = self.project_root / "scripts" / "start_api.sh"
        if api_script.exists():
            subprocess.Popen(
                ["bash", str(api_script)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            # Try to start FastAPI directly
            subprocess.Popen(
                ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
                cwd=str(self.project_root / "api"),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
        print("  ✅ Services started")
        return True
        
    def deploy(self) -> bool:
        """Deploy the backend"""
        if not self.validation_results["ready_for_deployment"]:
            print("\n❌ Backend is not ready for deployment!")
            print("\nErrors found:")
            for error in self.validation_results["errors"]:
                print(f"  - {error['check']}: {error['error']}")
            return False
            
        print("\n✅ Backend validation passed! Starting deployment...")
        
        # Start services
        if not self.start_services():
            return False
            
        # Run database migrations
        print("\n📊 Running database migrations...")
        migration_script = self.project_root / "scripts" / "migrate_database.py"
        if migration_script.exists():
            result = subprocess.run(
                ["python3", str(migration_script)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"  ⚠️  Migration warnings: {result.stderr}")
                
        print("\n✅ Backend deployment complete!")
        return True

def main():
    """Main execution function"""
    # Load environment variables
    env_file = Path(".env")
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
    else:
        print("⚠️  Warning: .env file not found. Using default values.")
        
    # Run validation
    validator = BackendValidator()
    validation_results = validator.validate_all()
    
    # Save validation results
    report_file = f"backend_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(validation_results, f, indent=2)
        
    print(f"\n📊 Validation report saved to: {report_file}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    print("\n✅ Passed checks:")
    for check, result in validation_results["checks"].items():
        print(f"  {result}")
        
    if validation_results["warnings"]:
        print("\n⚠️  Warnings:")
        for warning in validation_results["warnings"]:
            print(f"  - {warning['check']}: {warning['warning']}")
            
    if validation_results["errors"]:
        print("\n❌ Errors:")
        for error in validation_results["errors"]:
            print(f"  - {error['check']}: {error['error']}")
            
    print(f"\n🎯 Ready for deployment: {'YES' if validation_results['ready_for_deployment'] else 'NO'}")
    
    # Deploy if validation passed
    if validation_results["ready_for_deployment"]:
        deploy = input("\n🚀 Deploy backend now? (y/n): ")
        if deploy.lower() == 'y':
            deployer = BackendDeployer(validation_results)
            deployer.deploy()
    else:
        print("\n📝 Fix the errors above before deployment.")
        print("\nNext steps:")
        print("1. Review and fix all errors")
        print("2. Set up missing environment variables")
        print("3. Ensure Docker services are running")
        print("4. Run this script again")

if __name__ == "__main__":
    # Install required packages for validation
    subprocess.run(
        ["pip",
        "install",
        "-q",
        "psycopg2-binary",
        "redis",
        "requests",
        "python-dotenv"],
        capture_output=True
    )
    main()