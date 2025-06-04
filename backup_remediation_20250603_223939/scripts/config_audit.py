# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
Configuration Files Audit Script for Cherry AI
Comprehensive audit of all configuration files for security, consistency, and validity.
"""

import os
import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict
from datetime import datetime

class ConfigurationAuditor:
    """Comprehensive configuration files auditor."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "duplicate_env_vars": [],
            "naming_convention_issues": [],
            "security_issues": [],
            "schema_mismatches": [],
            "recommendations": []
        }
        self.env_vars = defaultdict(list)  # var_name -> [(file, value)]
        self.config_schemas = {}
        
    def find_config_files(self) -> Dict[str, List[Path]]:
        """Find all configuration files by type."""
        config_files = {
            "env_files": [],
            "yaml_configs": [],
            "json_configs": [],
            "docker_configs": [],
            "pulumi_configs": [],
            "python_configs": []
        }
        
        # Find .env files
        for env_file in self.root_path.rglob("*.env*"):
            if self._should_include(env_file):
                config_files["env_files"].append(env_file)
        
        # Find .envrc files
        for envrc_file in self.root_path.rglob(".envrc*"):
            if self._should_include(envrc_file):
                config_files["env_files"].append(envrc_file)
        
        # Find YAML configs
        for yaml_file in self.root_path.rglob("*.yaml"):
            if self._should_include(yaml_file) and "config" in str(yaml_file).lower():
                config_files["yaml_configs"].append(yaml_file)
        
        for yml_file in self.root_path.rglob("*.yml"):
            if self._should_include(yml_file):
                config_files["yaml_configs"].append(yml_file)
        
        # Find JSON configs
        for json_file in self.root_path.rglob("*.json"):
            if self._should_include(json_file) and ("config" in str(json_file).lower() or 
                                                   "settings" in str(json_file).lower()):
                config_files["json_configs"].append(json_file)
        
        # Find Docker configs
        for docker_file in self.root_path.rglob("Dockerfile*"):
            if self._should_include(docker_file):
                config_files["docker_configs"].append(docker_file)
                
        for compose_file in self.root_path.rglob("docker-compose*"):
            if self._should_include(compose_file):
                config_files["docker_configs"].append(compose_file)
        
        # Find Pulumi configs
        for pulumi_file in self.root_path.rglob("Pulumi.*"):
            if self._should_include(pulumi_file):
                config_files["pulumi_configs"].append(pulumi_file)
        
        # Find Python config files
        for py_file in self.root_path.rglob("*config*.py"):
            if self._should_include(py_file):
                config_files["python_configs"].append(py_file)
                
        for py_file in self.root_path.rglob("*settings*.py"):
            if self._should_include(py_file):
                config_files["python_configs"].append(py_file)
        
        return config_files
    
    def _should_include(self, file_path: Path) -> bool:
        """Check if file should be included in audit."""
        exclude_dirs = {"venv", "node_modules", "__pycache__", ".git", "build", "dist"}
        
        for parent in file_path.parents:
            if parent.name in exclude_dirs:
                return False
        
        return True
    
    def audit_env_files(self, env_files: List[Path]) -> None:
        """Audit .env files for duplicates and security issues."""
        print(f"🔍 Auditing {len(env_files)} environment files...")
        
        for env_file in env_files:
            try:
                content = env_file.read_text(encoding='utf-8')
                self._parse_env_content(content, env_file)
            except Exception as e:
                print(f"⚠️  Error reading {env_file}: {e}")
        
        # Find duplicates
        self._find_duplicate_env_vars()
        
        # Check for security issues
        self._check_env_security()
        
        # Check naming conventions
        self._check_env_naming_conventions()
    
    def _parse_env_content(self, content: str, file_path: Path) -> None:
        """Parse environment file content."""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse environment variable
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                
                self.env_vars[key].append({
                    "file": str(file_path),
                    "line": line_num,
                    "value": value
                })
    
    def _find_duplicate_env_vars(self) -> None:
        """Find duplicate environment variables across files."""
        for var_name, occurrences in self.env_vars.items():
            if len(occurrences) > 1:
                # Check if values are different
                values = set(occ["value"] for occ in occurrences)
                if len(values) > 1:
                    self.audit_results["duplicate_env_vars"].append({
                        "variable": var_name,
                        "occurrences": occurrences,
                        "different_values": True,
                        "severity": "high"
                    })
                else:
                    self.audit_results["duplicate_env_vars"].append({
                        "variable": var_name,
                        "occurrences": occurrences,
                        "different_values": False,
                        "severity": "medium"
                    })
    
    def _check_env_security(self) -> None:
        """Check for hardcoded credentials and sensitive data."""
        sensitive_patterns = {
            "api_key": r".*[Aa][Pp][Ii]_?[Kk][Ee][Yy].*",
            "password": r".*[Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd].*",
            "secret": r".*[Ss][Ee][Cc][Rr][Ee][Tt].*",
            "token": r".*[Tt][Oo][Kk][Ee][Nn].*",
            "private_key": r".*[Pp][Rr][Ii][Vv][Aa][Tt][Ee]_?[Kk][Ee][Yy].*",
            "credential": r".*[Cc][Rr][Ee][Dd][Ee][Nn][Tt][Ii][Aa][Ll].*"
        }
        
        hardcoded_patterns = {
            "base64_encoded": r"^[A-Za-z0-9+/]{20,}={0,2}$",
            "hex_key": r"^[a-fA-F0-9]{32,}$",
            "jwt_token": r"^eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*$",
            "aws_access_key": r"^AKIA[0-9A-Z]{16}$",
            "github_token": r"^ghp_[a-zA-Z0-9]{36}$"
        }
        
        for var_name, occurrences in self.env_vars.items():
            # Check if variable name suggests sensitive data
            for sensitive_type, pattern in sensitive_patterns.items():
                if re.match(pattern, var_name):
                    for occ in occurrences:
                        value = occ["value"]
                        
                        # Check if value looks hardcoded
                        is_hardcoded = False
                        hardcoded_type = "unknown"
                        
                        if value and not value.startswith("${") and value != "":
                            for hc_type, hc_pattern in hardcoded_patterns.items():
                                if re.match(hc_pattern, value):
                                    is_hardcoded = True
                                    hardcoded_type = hc_type
                                    break
                            
                            # Additional checks for obvious hardcoded values
                            if (len(value) > 10 and 
                                not value.lower() in ["localhost", "127.0.0.1", "example.com", "test", "development"] and
                                not value.startswith("/") and
                                not "." in value or len(value) > 50):
                                is_hardcoded = True
                                hardcoded_type = "suspicious_length"
                        
                        self.audit_results["security_issues"].append({
                            "variable": var_name,
                            "file": occ["file"],
                            "line": occ["line"],
                            "sensitive_type": sensitive_type,
                            "is_hardcoded": is_hardcoded,
                            "hardcoded_type": hardcoded_type,
                            "value_length": len(value),
                            "severity": "high" if is_hardcoded else "medium"
                        })
    
    def _check_env_naming_conventions(self) -> None:
        """Check environment variable naming conventions."""
        for var_name, occurrences in self.env_vars.items():
            issues = []
            
            # Check if all uppercase (standard convention)
            if not var_name.isupper():
                issues.append("not_uppercase")
            
            # Check for spaces or invalid characters
            if not re.match(r'^[A-Z0-9_]+$', var_name):
                issues.append("invalid_characters")
            
            # Check for consistent prefixing
            if not any(var_name.startswith(prefix) # TODO: Consider using list comprehension for better performance
 for prefix in 
                      ["cherry_ai_", "PORTKEY_", "VULTR_", "POSTGRES_", "WEAVIATE_", "MCP_"]):
                issues.append("no_standard_prefix")
            
            if issues:
                self.audit_results["naming_convention_issues"].append({
                    "variable": var_name,
                    "issues": issues,
                    "occurrences": len(occurrences),
                    "severity": "low"
                })
    
    def audit_yaml_configs(self, yaml_files: List[Path]) -> None:
        """Audit YAML configuration files."""
        print(f"📄 Auditing {len(yaml_files)} YAML configuration files...")
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                    self._analyze_config_structure(content, yaml_file, "yaml")
            except Exception as e:
                print(f"⚠️  Error parsing YAML {yaml_file}: {e}")
    
    def audit_json_configs(self, json_files: List[Path]) -> None:
        """Audit JSON configuration files."""
        print(f"📄 Auditing {len(json_files)} JSON configuration files...")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    self._analyze_config_structure(content, json_file, "json")
            except Exception as e:
                print(f"⚠️  Error parsing JSON {json_file}: {e}")
    
    def _analyze_config_structure(self, content: Any, file_path: Path, file_type: str) -> None:
        """Analyze configuration structure # TODO: Consider using list comprehension for better performance
 for issues."""
        if isinstance(content, dict):
            # Check for hardcoded sensitive values
            self._check_config_security(content, file_path, file_type)
            
            # Check for schema consistency
            self._check_config_schema(content, file_path, file_type)
    
    def _check_config_security(self, config: Dict, file_path: Path, file_type: str) -> None:
        """Check configuration for security issues."""
        def check_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Check for sensitive keys
                    if any(sensitive in key.lower() for sensitive in 
                          ["password", "secret", "key", "token", "credential"]):
                        if isinstance(value, str) and value and not value.startswith("${"):
                            self.audit_results["security_issues"].append({
                                "file": str(file_path),
                                "file_type": file_type,
                                "path": current_path,
                                "issue": "hardcoded_sensitive_value",
                                "key": key,
                                "severity": "high"
                            })
                    
                    check_recursive(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_recursive(item, f"{path}[{i}]")
        
        check_recursive(config)
    
    def _check_config_schema(self, config: Dict, file_path: Path, file_type: str) -> None:
        """Check configuration schema consistency."""
        # Define expected schemas for common config types
        expected_schemas = {
            "persona": ["name", "description", "model", "temperature"],
            "database": ["host", "port", "database", "user"],
            "api": ["base_url", "timeout", "retry_count"],
            "llm": ["provider", "model", "temperature", "max_tokens"]
        }
        
        # Try to identify config type and validate
        for schema_type, required_fields in expected_schemas.items():
            if schema_type in str(file_path).lower():
                missing_fields = []
                # TODO: Consider using list comprehension for better performance

                for field in required_fields:
                    if field not in config:
                        missing_fields.append(field)
                
                if missing_fields:
                    self.audit_results["schema_mismatches"].append({
                        "file": str(file_path),
                        "file_type": file_type,
                        "schema_type": schema_type,
                        "missing_fields": missing_fields,
                        "severity": "medium"
                    })
    
    def audit_docker_configs(self, docker_files: List[Path]) -> None:
        """Audit Docker configuration files."""
        print(f"🐳 Auditing {len(docker_files)} Docker configuration files...")
        
        for docker_file in docker_files:
            try:
                content = docker_file.read_text(encoding='utf-8')
                self._check_docker_security(content, docker_file)
            except Exception as e:
                print(f"⚠️  Error reading Docker file {docker_file}: {e}")
    
    def _check_docker_security(self, content: str, file_path: Path) -> None:
        """Check Docker files for security issues."""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for hardcoded secrets in ENV instructions
            if line.startswith('ENV '):
                env_part = line[4:].strip()
                if '=' in env_part:
                    key, value = env_part.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    if any(sensitive in key.lower() for sensitive in 
                          ["password", "secret", "key", "token"]):
                        if value and not value.startswith("${"):
                            self.audit_results["security_issues"].append({
                                "file": str(file_path),
                                "file_type": "docker",
                                "line": line_num,
                                "issue": "hardcoded_env_secret",
                                "variable": key,
                                "severity": "high"
                            })
            
            # Check for running as root
            if line.startswith('USER ') and 'root' in line:
                self.audit_results["security_issues"].append({
                    "file": str(file_path),
                    "file_type": "docker",
                    "line": line_num,
                    "issue": "running_as_root",
                    "severity": "medium"
                })
    
    def generate_recommendations(self) -> None:
        """Generate security and consistency recommendations."""
        recommendations = []
        
        # Duplicate environment variables
        if self.audit_results["duplicate_env_vars"]:
            recommendations.append({
                "category": "Environment Variables",
                "issue": "Duplicate environment variables found",
                "recommendation": "Consolidate duplicate environment variables into a single source file",
                "priority": "high"
            })
        
        # Security issues
        high_security_issues = [issue for issue in self.audit_results["security_issues"] 
                              if issue["severity"] == "high"]
        if high_security_issues:
            recommendations.append({
                "category": "Security",
                "issue": f"{len(high_security_issues)} hardcoded credentials found",
                "recommendation": "Replace hardcoded credentials with environment variables or secret management",
                "priority": "critical"
            })
        
        # Naming conventions
        if self.audit_results["naming_convention_issues"]:
            recommendations.append({
                "category": "Naming Conventions",
                "issue": "Inconsistent environment variable naming",
                "recommendation": "Standardize environment variables to use UPPERCASE with project prefixes",
                "priority": "medium"
            })
        
        self.audit_results["recommendations"] = recommendations
    
    def run_audit(self) -> Dict:
        """Run complete configuration audit."""
        print("🔍 Starting Configuration Files Audit...")
        
        # Find all config files
        config_files = self.find_config_files()
        
        # Audit each type
        self.audit_env_files(config_files["env_files"])
        self.audit_yaml_configs(config_files["yaml_configs"])
        self.audit_json_configs(config_files["json_configs"])
        self.audit_docker_configs(config_files["docker_configs"])
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Compile summary
        self.audit_results["summary"] = {
            "total_env_files": len(config_files["env_files"]),
            "total_yaml_configs": len(config_files["yaml_configs"]),
            "total_json_configs": len(config_files["json_configs"]),
            "total_docker_configs": len(config_files["docker_configs"]),
            "total_pulumi_configs": len(config_files["pulumi_configs"]),
            "total_python_configs": len(config_files["python_configs"]),
            "duplicate_env_vars_count": len(self.audit_results["duplicate_env_vars"]),
            "security_issues_count": len(self.audit_results["security_issues"]),
            "naming_issues_count": len(self.audit_results["naming_convention_issues"]),
            "schema_issues_count": len(self.audit_results["schema_mismatches"])
        }
        
        return self.audit_results
    
    def generate_report(self) -> str:
        """Generate comprehensive audit report."""
        summary = self.audit_results["summary"]
        
        report = f"""
🔒 Configuration Files Security & Consistency Audit Report
===========================================================
Generated: {self.audit_results['timestamp']}

📊 AUDIT SUMMARY
----------------
Configuration Files Analyzed:
• Environment Files: {summary['total_env_files']}
• YAML Configs: {summary['total_yaml_configs']}
• JSON Configs: {summary['total_json_configs']}
• Docker Configs: {summary['total_docker_configs']}
• Pulumi Configs: {summary['total_pulumi_configs']}
• Python Configs: {summary['total_python_configs']}

🚨 ISSUES FOUND
---------------
• Duplicate Environment Variables: {summary['duplicate_env_vars_count']}
• Security Issues: {summary['security_issues_count']}
• Naming Convention Issues: {summary['naming_issues_count']}
• Schema Mismatches: {summary['schema_issues_count']}

"""
        
        # Duplicate Environment Variables
        if self.audit_results["duplicate_env_vars"]:
            report += """
🔄 DUPLICATE ENVIRONMENT VARIABLES
----------------------------------
"""
            for dup in self.audit_results["duplicate_env_vars"][:10]:
                report += f"⚠️  {dup['variable']} - Found in {len(dup['occurrences'])} files\n"
                for occ in dup['occurrences']:
                    report += f"   📁 {occ['file']}:{occ['line']}\n"
                report += "\n"
        
        # Security Issues
        high_security = [issue for issue in self.audit_results["security_issues"] 
                        if issue["severity"] == "high"]
        if high_security:
            report += """
🚨 CRITICAL SECURITY ISSUES
---------------------------
"""
            for issue in high_security[:10]:
                if "variable" in issue:
                    report += f"❌ Hardcoded credential: {issue['variable']} in {issue['file']}\n"
                else:
                    report += f"❌ {issue['issue']} in {issue['file']}\n"
        
        # Recommendations
        if self.audit_results["recommendations"]:
            report += """
🔧 PRIORITY RECOMMENDATIONS
---------------------------
"""
            for rec in self.audit_results["recommendations"]:
                priority_icon = {"critical": "🔴", "high": "🟡", "medium": "🟠", "low": "🟢"}
                icon = priority_icon.get(rec["priority"], "ℹ️")
                report += f"{icon} {rec['category']}: {rec['recommendation']}\n"
        
        report += """
📋 NEXT STEPS
-------------
1. Address critical security issues immediately
2. Consolidate duplicate environment variables
3. Implement consistent naming conventions
4. Set up configuration validation in CI/CD
5. Consider using a secrets management solution
"""
        
        return report


def main():
    """Run the configuration audit."""
    auditor = ConfigurationAuditor(".")
    results = auditor.run_audit()
    
    # Generate and save report
    report = auditor.generate_report()
    print(report)
    
    # Save detailed results to JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_file = f"config_audit_results_{timestamp}.json"
    
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed audit results saved to: {json_file}")
    
    return results


if __name__ == "__main__":
    main() 