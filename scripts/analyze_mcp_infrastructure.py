#!/usr/bin/env python3
"""
Comprehensive MCP Infrastructure Audit and Analysis
Performs deep technical audit of Model Context Protocol server infrastructure
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from typing_extensions import Optional, Tuple
import subprocess
import re
import yaml
import importlib.util
import ast

class MCPInfrastructureAuditor:
    """Comprehensive auditor for MCP server infrastructure"""
    
    def __init__(self):
        self.base_dir = Path("/root/cherry_ai-main")
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "configuration": {},
            "security": {},
            "performance": {},
            "compatibility": {},
            "deployment": {},
            "recommendations": [],
            "critical_issues": [],
            "warnings": [],
            "optimizations": []
        }
        
    def run_comprehensive_audit(self) -> Dict[str, Any]:
        """Execute full infrastructure audit"""
        print("🔍 Starting Comprehensive MCP Infrastructure Audit...")
        print("=" * 60)
        
        # Phase 1: Configuration Analysis
        print("\n📋 Phase 1: Configuration Analysis")
        self.audit_configuration()
        
        # Phase 2: Security Assessment
        print("\n🔒 Phase 2: Security Assessment")
        self.audit_security()
        
        # Phase 3: Performance Analysis
        print("\n⚡ Phase 3: Performance Analysis")
        self.audit_performance()
        
        # Phase 4: Compatibility Check
        print("\n🔧 Phase 4: Compatibility Check")
        self.audit_compatibility()
        
        # Phase 5: Deployment Pipeline
        print("\n🚀 Phase 5: Deployment Pipeline Analysis")
        self.audit_deployment()
        
        # Phase 6: Generate Recommendations
        print("\n💡 Phase 6: Generating Recommendations")
        self.generate_recommendations()
        
        # Save audit report
        self.save_audit_report()
        
        return self.audit_results
    
    def audit_configuration(self):
        """Audit all configuration files and settings"""
        config_issues = []
        config_stats = {
            "total_configs": 0,
            "valid_configs": 0,
            "missing_configs": [],
            "invalid_configs": [],
            "deprecated_settings": []
        }
        
        # Check MCP configuration
        mcp_config_path = self.base_dir / ".mcp.json"
        if mcp_config_path.exists():
            try:
                with open(mcp_config_path) as f:
                    mcp_config = json.load(f)
                
                config_stats["total_configs"] += 1
                config_stats["valid_configs"] += 1
                
                # Analyze server configurations
                servers = mcp_config.get("servers", {})
                for server_name, server_config in servers.items():
                    # Check for required fields
                    if "command" not in server_config:
                        config_issues.append({
                            "severity": "HIGH",
                            "component": f"MCP Server: {server_name}",
                            "issue": "Missing command configuration",
                            "impact": "Server cannot be started"
                        })
                    
                    # Check for deprecated settings
                    if "legacy_mode" in server_config:
                        config_stats["deprecated_settings"].append({
                            "server": server_name,
                            "setting": "legacy_mode",
                            "recommendation": "Remove legacy_mode and use modern configuration"
                        })
                        
            except json.JSONDecodeError as e:
                config_stats["invalid_configs"].append({
                    "file": ".mcp.json",
                    "error": str(e)
                })
                self.audit_results["critical_issues"].append({
                    "component": "MCP Configuration",
                    "issue": "Invalid JSON in .mcp.json",
                    "severity": "CRITICAL"
                })
        else:
            config_stats["missing_configs"].append(".mcp.json")
            self.audit_results["critical_issues"].append({
                "component": "MCP Configuration",
                "issue": "Missing .mcp.json configuration file",
                "severity": "CRITICAL"
            })
        
        # Check environment configuration
        env_path = self.base_dir / ".env"
        env_example_path = self.base_dir / ".env.example"
        
        if env_example_path.exists():
            with open(env_example_path) as f:
                env_example = f.read()
            
            required_vars = re.findall(r'^([A-Z_]+)=', env_example, re.MULTILINE)
            
            if env_path.exists():
                with open(env_path) as f:
                    env_content = f.read()
                
                configured_vars = re.findall(r'^([A-Z_]+)=', env_content, re.MULTILINE)
                missing_vars = set(required_vars) - set(configured_vars)
                
                if missing_vars:
                    self.audit_results["warnings"].append({
                        "component": "Environment Configuration",
                        "issue": f"Missing environment variables: {', '.join(missing_vars)}",
                        "severity": "MEDIUM"
                    })
            else:
                self.audit_results["critical_issues"].append({
                    "component": "Environment Configuration",
                    "issue": "Missing .env file",
                    "severity": "HIGH"
                })
        
        # Check model configurations
        models_config_path = self.base_dir / "mcp_server" / "config" / "models.py"
        if models_config_path.exists():
            try:
                with open(models_config_path) as f:
                    content = f.read()
                
                # Parse Python AST to analyze configuration
                tree = ast.parse(content)
                
                # Look for configuration classes
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if "Config" in node.name:
                            config_stats["total_configs"] += 1
                            config_stats["valid_configs"] += 1
                            
            except SyntaxError as e:
                config_stats["invalid_configs"].append({
                    "file": "models.py",
                    "error": str(e)
                })
        
        self.audit_results["configuration"] = {
            "statistics": config_stats,
            "issues": config_issues
        }
        
        print(f"  ✓ Analyzed {config_stats['total_configs']} configurations")
        print(f"  ✓ Valid: {config_stats['valid_configs']}")
        print(f"  ⚠️  Issues found: {len(config_issues)}")
    
    def audit_security(self):
        """Perform security assessment"""
        security_issues = []
        security_score = 100
        
        # Check for hardcoded credentials
        print("  🔍 Scanning for hardcoded credentials...")
        sensitive_patterns = [
            (r'password\s*=\s*["\'](?!your-|placeholder|example)[^"\']+["\']', "Hardcoded password"),
            (r'api_key\s*=\s*["\'](?!your-|placeholder|example)[^"\']+["\']', "Hardcoded API key"),
            (r'secret\s*=\s*["\'](?!your-|placeholder|example)[^"\']+["\']', "Hardcoded secret"),
            (r'token\s*=\s*["\'](?!your-|placeholder|example)[^"\']+["\']', "Hardcoded token")
        ]
        
        python_files = list(self.base_dir.rglob("*.py"))
        for file_path in python_files:
            if "test" in str(file_path) or "example" in str(file_path):
                continue
                
            try:
                with open(file_path) as f:
                    content = f.read()
                
                for pattern, issue_type in sensitive_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        security_issues.append({
                            "severity": "CRITICAL",
                            "type": issue_type,
                            "file": str(file_path.relative_to(self.base_dir)),
                            "line": line_num,
                            "pattern": match.group(0)[:50] + "..."
                        })
                        security_score -= 10
                        
            except Exception:
                pass
        
        # Check authentication configuration
        auth_issues = self._check_authentication()
        security_issues.extend(auth_issues)
        security_score -= len(auth_issues) * 5
        
        # Check HTTPS/TLS configuration
        tls_issues = self._check_tls_configuration()
        security_issues.extend(tls_issues)
        security_score -= len(tls_issues) * 5
        
        # Check for vulnerable dependencies
        vuln_deps = self._check_vulnerable_dependencies()
        security_issues.extend(vuln_deps)
        security_score -= len(vuln_deps) * 3
        
        self.audit_results["security"] = {
            "score": max(0, security_score),
            "issues": security_issues,
            "authentication": {
                "jwt_enabled": self._is_jwt_enabled(),
                "rbac_configured": self._is_rbac_configured(),
                "api_key_management": self._check_api_key_management()
            },
            "encryption": {
                "secrets_encrypted": self._are_secrets_encrypted(),
                "tls_enabled": len(tls_issues) == 0
            }
        }
        
        print(f"  ✓ Security Score: {max(0, security_score)}/100")
        print(f"  ⚠️  Security issues found: {len(security_issues)}")
    
    def audit_performance(self):
        """Analyze performance configurations and bottlenecks"""
        perf_issues = []
        perf_metrics = {
            "connection_pooling": False,
            "caching_enabled": False,
            "async_operations": 0,
            "sync_operations": 0,
            "database_indexes": [],
            "optimization_opportunities": []
        }
        
        # Check for connection pooling
        print("  🔍 Analyzing connection pooling...")
        pool_patterns = [
            r'pool_size\s*=',
            r'max_connections\s*=',
            r'connection_pool',
            r'ConnectionPool'
        ]
        
        for pattern in pool_patterns:
            if self._search_in_files(pattern):
                perf_metrics["connection_pooling"] = True
                break
        
        if not perf_metrics["connection_pooling"]:
            perf_issues.append({
                "severity": "HIGH",
                "type": "Missing connection pooling",
                "impact": "Database connections not optimized",
                "recommendation": "Implement connection pooling for PostgreSQL and Redis"
            })
        
        # Check caching configuration
        cache_patterns = [
            r'@cache',
            r'redis.*cache',
            r'cache_ttl',
            r'CacheManager'
        ]
        
        for pattern in cache_patterns:
            if self._search_in_files(pattern):
                perf_metrics["caching_enabled"] = True
                break
        
        # Analyze async vs sync operations
        python_files = list(self.base_dir.rglob("*.py"))
        for file_path in python_files:
            try:
                with open(file_path) as f:
                    content = f.read()
                
                # Count async functions
                async_matches = re.findall(r'async\s+def\s+\w+', content)
                perf_metrics["async_operations"] += len(async_matches)
                
                # Count sync database operations
                sync_db_patterns = [
                    r'\.execute\(',
                    r'\.query\(',
                    r'\.commit\('
                ]
                
                for pattern in sync_db_patterns:
                    if re.search(pattern, content) and 'async' not in content:
                        perf_metrics["sync_operations"] += 1
                        
            except Exception:
                pass
        
        # Check for N+1 query patterns
        n_plus_one_patterns = [
            r'for\s+.*\s+in\s+.*:\s*\n\s*.*\.(get|query|find)',
            r'\.all\(\).*for.*\.(get|query|find)'
        ]
        
        for pattern in n_plus_one_patterns:
            matches = self._search_in_files(pattern)
            if matches:
                perf_issues.append({
                    "severity": "MEDIUM",
                    "type": "Potential N+1 query",
                    "pattern": pattern,
                    "recommendation": "Use eager loading or batch queries"
                })
        
        self.audit_results["performance"] = {
            "metrics": perf_metrics,
            "issues": perf_issues,
            "recommendations": self._generate_performance_recommendations(perf_metrics)
        }
        
        print(f"  ✓ Async operations: {perf_metrics['async_operations']}")
        print(f"  ✓ Sync operations: {perf_metrics['sync_operations']}")
        print(f"  ⚠️  Performance issues: {len(perf_issues)}")
    
    def audit_compatibility(self):
        """Check version compatibility and dependencies"""
        compat_issues = []
        
        # Check Python version
        print("  🔍 Checking Python compatibility...")
        python_version = sys.version_info
        if python_version < (3, 10):
            compat_issues.append({
                "severity": "CRITICAL",
                "component": "Python",
                "issue": f"Python {python_version.major}.{python_version.minor} is below minimum required 3.10",
                "recommendation": "Upgrade to Python 3.10 or higher"
            })
        
        # Check dependency versions
        requirements_files = [
            "requirements.txt",
            "pyproject.toml",
            "setup.py"
        ]
        
        dependencies = {}
        for req_file in requirements_files:
            req_path = self.base_dir / req_file
            if req_path.exists():
                deps = self._parse_dependencies(req_path)
                dependencies.update(deps)
        
        # Check for version conflicts
        version_conflicts = self._check_version_conflicts(dependencies)
        compat_issues.extend(version_conflicts)
        
        # Check deprecated imports
        deprecated_imports = [
            ("from collections import", "from collections.abc import", "Python 3.9+"),
            ("from typing import", "from typing_extensions import", "For backward compatibility"),
            ("asyncio.coroutine", "async def", "Deprecated in Python 3.10")
        ]
        
        for old_import, new_import, reason in deprecated_imports:
            if self._search_in_files(old_import):
                compat_issues.append({
                    "severity": "MEDIUM",
                    "type": "Deprecated import",
                    "old": old_import,
                    "new": new_import,
                    "reason": reason
                })
        
        self.audit_results["compatibility"] = {
            "python_version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
            "dependencies": dependencies,
            "issues": compat_issues
        }
        
        print(f"  ✓ Dependencies analyzed: {len(dependencies)}")
        print(f"  ⚠️  Compatibility issues: {len(compat_issues)}")
    
    def audit_deployment(self):
        """Analyze deployment pipeline and configurations"""
        deploy_issues = []
        deploy_config = {
            "docker_configured": False,
            "ci_cd_configured": False,
            "monitoring_configured": False,
            "backup_configured": False,
            "scaling_configured": False
        }
        
        # Check Docker configuration
        docker_files = [
            "Dockerfile",
            "docker-compose.yml",
            "docker-compose.local.yml",
            ".dockerignore"
        ]
        
        docker_count = 0
        for docker_file in docker_files:
            if (self.base_dir / docker_file).exists():
                docker_count += 1
        
        deploy_config["docker_configured"] = docker_count >= 2
        
        if not deploy_config["docker_configured"]:
            deploy_issues.append({
                "severity": "HIGH",
                "component": "Docker",
                "issue": "Incomplete Docker configuration",
                "recommendation": "Add Dockerfile and docker-compose.yml"
            })
        
        # Check CI/CD configuration
        ci_cd_files = [
            ".github/workflows",
            ".gitlab-ci.yml",
            "Jenkinsfile",
            ".circleci/config.yml"
        ]
        
        for ci_file in ci_cd_files:
            if (self.base_dir / ci_file).exists():
                deploy_config["ci_cd_configured"] = True
                break
        
        # Check monitoring configuration
        monitoring_patterns = [
            r'prometheus',
            r'grafana',
            r'datadog',
            r'newrelic',
            r'sentry'
        ]
        
        for pattern in monitoring_patterns:
            if self._search_in_files(pattern):
                deploy_config["monitoring_configured"] = True
                break
        
        # Check backup configuration
        backup_patterns = [
            r'backup',
            r'pg_dump',
            r'redis.*save',
            r'snapshot'
        ]
        
        for pattern in backup_patterns:
            if self._search_in_files(pattern):
                deploy_config["backup_configured"] = True
                break
        
        # Check scaling configuration
        scaling_patterns = [
            r'replicas',
            r'autoscale',
            r'load.*balance',
            r'horizontal.*pod'
        ]
        
        for pattern in scaling_patterns:
            if self._search_in_files(pattern):
                deploy_config["scaling_configured"] = True
                break
        
        self.audit_results["deployment"] = {
            "configuration": deploy_config,
            "issues": deploy_issues,
            "readiness_score": sum(deploy_config.values()) / len(deploy_config) * 100
        }
        
        print(f"  ✓ Deployment readiness: {self.audit_results['deployment']['readiness_score']:.0f}%")
        print(f"  ⚠️  Deployment issues: {len(deploy_issues)}")
    
    def generate_recommendations(self):
        """Generate actionable recommendations based on audit findings"""
        recommendations = []
        
        # Critical recommendations
        if self.audit_results["critical_issues"]:
            recommendations.append({
                "priority": "CRITICAL",
                "category": "Configuration",
                "recommendation": "Fix critical configuration issues immediately",
                "actions": [
                    "Create missing .mcp.json configuration",
                    "Fix invalid JSON in configuration files",
                    "Ensure all required environment variables are set"
                ]
            })
        
        # Security recommendations
        security_score = self.audit_results["security"]["score"]
        if security_score < 80:
            recommendations.append({
                "priority": "HIGH",
                "category": "Security",
                "recommendation": "Implement security hardening measures",
                "actions": [
                    "Remove all hardcoded credentials",
                    "Implement JWT authentication",
                    "Enable TLS/HTTPS for all endpoints",
                    "Set up API key rotation",
                    "Implement rate limiting"
                ]
            })
        
        # Performance recommendations
        perf_metrics = self.audit_results["performance"]["metrics"]
        if not perf_metrics["connection_pooling"]:
            recommendations.append({
                "priority": "HIGH",
                "category": "Performance",
                "recommendation": "Implement connection pooling",
                "actions": [
                    "Add PostgreSQL connection pooling with pgbouncer or built-in pool",
                    "Configure Redis connection pool",
                    "Set appropriate pool sizes based on load"
                ]
            })
        
        if not perf_metrics["caching_enabled"]:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Performance",
                "recommendation": "Implement caching strategy",
                "actions": [
                    "Add Redis caching for frequently accessed data",
                    "Implement query result caching",
                    "Set appropriate TTL values"
                ]
            })
        
        # Deployment recommendations
        deploy_readiness = self.audit_results["deployment"]["readiness_score"]
        if deploy_readiness < 60:
            recommendations.append({
                "priority": "HIGH",
                "category": "Deployment",
                "recommendation": "Improve deployment infrastructure",
                "actions": [
                    "Create comprehensive Docker configuration",
                    "Set up CI/CD pipeline",
                    "Implement monitoring and alerting",
                    "Configure automated backups",
                    "Add horizontal scaling capability"
                ]
            })
        
        # Architecture recommendations
        if perf_metrics["sync_operations"] > perf_metrics["async_operations"]:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Architecture",
                "recommendation": "Migrate to async architecture",
                "actions": [
                    "Convert synchronous database operations to async",
                    "Use async frameworks consistently",
                    "Implement async task queues for long-running operations"
                ]
            })
        
        self.audit_results["recommendations"] = recommendations
        
        print(f"  ✓ Generated {len(recommendations)} recommendations")
    
    def _check_authentication(self) -> List[Dict]:
        """Check authentication configuration"""
        issues = []
        
        # Check for JWT implementation
        if not self._search_in_files(r'jwt|JWT|JsonWebToken'):
            issues.append({
                "severity": "HIGH",
                "type": "Missing JWT authentication",
                "recommendation": "Implement JWT-based authentication"
            })
        
        # Check for API key management
        if not self._search_in_files(r'api_key.*validate|verify.*api.*key'):
            issues.append({
                "severity": "MEDIUM",
                "type": "No API key validation",
                "recommendation": "Implement API key validation middleware"
            })
        
        return issues
    
    def _check_tls_configuration(self) -> List[Dict]:
        """Check TLS/HTTPS configuration"""
        issues = []
        
        # Check for HTTPS in configuration
        if not self._search_in_files(r'https://|ssl|tls|certificate'):
            issues.append({
                "severity": "HIGH",
                "type": "No HTTPS/TLS configuration",
                "recommendation": "Enable HTTPS with proper certificates"
            })
        
        return issues
    
    def _check_vulnerable_dependencies(self) -> List[Dict]:
        """Check for known vulnerable dependencies"""
        issues = []
        vulnerable_packages = {
            "requests": "2.31.0",  # Example: CVE-2023-32681
            "cryptography": "41.0.0",  # Example: security updates
            "pydantic": "2.0.0"  # Example: validation bypasses
        }
        
        # This is a simplified check - in production, use safety or similar tools
        requirements_path = self.base_dir / "requirements.txt"
        if requirements_path.exists():
            with open(requirements_path) as f:
                content = f.read()
            
            for package, min_version in vulnerable_packages.items():
                pattern = f"{package}==([0-9.]+)"
                match = re.search(pattern, content)
                if match:
                    version = match.group(1)
                    if self._compare_versions(version, min_version) < 0:
                        issues.append({
                            "severity": "HIGH",
                            "type": "Vulnerable dependency",
                            "package": package,
                            "current_version": version,
                            "minimum_safe_version": min_version
                        })
        
        return issues
    
    def _is_jwt_enabled(self) -> bool:
        """Check if JWT is enabled"""
        return bool(self._search_in_files(r'jwt|JWT|JsonWebToken'))
    
    def _is_rbac_configured(self) -> bool:
        """Check if RBAC is configured"""
        return bool(self._search_in_files(r'role.*based|RBAC|permissions.*check'))
    
    def _check_api_key_management(self) -> str:
        """Check API key management status"""
        if self._search_in_files(r'api.*key.*rotation|rotate.*api.*key'):
            return "rotation_enabled"
        elif self._search_in_files(r'api_key|API_KEY'):
            return "basic"
        else:
            return "none"
    
    def _are_secrets_encrypted(self) -> bool:
        """Check if secrets are encrypted"""
        return bool(self._search_in_files(r'encrypt.*secret|Fernet|cryptography'))
    
    def _search_in_files(self, pattern: str) -> bool:
        """Search for pattern in Python files"""
        python_files = list(self.base_dir.rglob("*.py"))
        for file_path in python_files[:100]:  # Limit search for performance
            try:
                with open(file_path) as f:
                    content = f.read()
                if re.search(pattern, content, re.IGNORECASE):
                    return True
            except Exception:
                pass
        return False
    
    def _parse_dependencies(self, file_path: Path) -> Dict[str, str]:
        """Parse dependencies from requirements file"""
        dependencies = {}
        
        if file_path.name == "requirements.txt":
            with open(file_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        match = re.match(r'([a-zA-Z0-9-_]+)==([0-9.]+)', line)
                        if match:
                            dependencies[match.group(1)] = match.group(2)
        
        return dependencies
    
    def _check_version_conflicts(self, dependencies: Dict[str, str]) -> List[Dict]:
        """Check for version conflicts in dependencies"""
        conflicts = []
        
        # Known compatibility issues
        compatibility_matrix = {
            "fastapi": {"pydantic": ">=2.0.0"},
            "sqlalchemy": {"psycopg2": ">=2.9.0"},
            "redis": {"hiredis": ">=2.0.0"}
        }
        
        for package, requirements in compatibility_matrix.items():
            if package in dependencies:
                for required_pkg, required_version in requirements.items():
                    if required_pkg in dependencies:
                        if not self._version_satisfies(dependencies[required_pkg], required_version):
                            conflicts.append({
                                "severity": "MEDIUM",
                                "type": "Version conflict",
                                "package": package,
                                "requires": f"{required_pkg} {required_version}",
                                "found": f"{required_pkg}=={dependencies[required_pkg]}"
                            })
        
        return conflicts
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings"""
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            v1 = v1_parts[i] if i < len(v1_parts) else 0
            v2 = v2_parts[i] if i < len(v2_parts) else 0
            
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
        
        return 0
    
    def _version_satisfies(self, version: str, requirement: str) -> bool:
        """Check if version satisfies requirement"""
        if requirement.startswith(">="):
            required_version = requirement[2:]
            return self._compare_versions(version, required_version) >= 0
        elif requirement.startswith(">"):
            required_version = requirement[1:]
            return self._compare_versions(version, required_version) > 0
        elif requirement.startswith("=="):
            required_version = requirement[2:]
            return self._compare_versions(version, required_version) == 0
        
        return True
    
    def _generate_performance_recommendations(self, metrics: Dict) -> List[str]:
        """Generate performance recommendations based on metrics"""
        recommendations = []
        
        if not metrics["connection_pooling"]:
            recommendations.append("Implement database connection pooling to reduce connection overhead")
        
        if not metrics["caching_enabled"]:
            recommendations.append("Add Redis caching layer for frequently accessed data")
        
        if metrics["sync_operations"] > metrics["async_operations"]:
            recommendations.append("Migrate to async operations for better concurrency")
        
        if metrics["sync_operations"] > 50:
            recommendations.append("Consider using batch operations to reduce database round trips")
        
        return recommendations
    
    def save_audit_report(self):
        """Save audit report to file"""
        report_path = self.base_dir / f"mcp_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w') as f:
            json.dump(self.audit_results, f, indent=2, default=str)
        
        print(f"\n📄 Audit report saved to: {report_path}")
        
        # Generate summary
        print("\n" + "=" * 60)
        print("AUDIT SUMMARY")
        print("=" * 60)
        
        print(f"\n🔴 Critical Issues: {len(self.audit_results['critical_issues'])}")
        for issue in self.audit_results['critical_issues'][:3]:
            print(f"   - {issue['component']}: {issue['issue']}")
        
        print(f"\n🟡 Warnings: {len(self.audit_results['warnings'])}")
        for warning in self.audit_results['warnings'][:3]:
            print(f"   - {warning['component']}: {warning['issue']}")
        
        print(f"\n🔒 Security Score: {self.audit_results['security']['score']}/100")
        print(f"🚀 Deployment Readiness: {self.audit_results['deployment']['readiness_score']:.0f}%")
        
        print(f"\n💡 Top Recommendations:")
        for rec in self.audit_results['recommendations'][:3]:
            print(f"   [{rec['priority']}] {rec['category']}: {rec['recommendation']}")
        
        print("\n" + "=" * 60)


def main():
    """Run the MCP infrastructure audit"""
    auditor = MCPInfrastructureAuditor()
    results = auditor.run_comprehensive_audit()
    
    # Return exit code based on critical issues
    if results['critical_issues']:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
