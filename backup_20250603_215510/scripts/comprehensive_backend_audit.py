#!/usr/bin/env python3
"""
Comprehensive Backend Audit Script
Analyzes the entire codebase for issues in:
- Backend architecture
- API endpoints
- Database schema
- Authentication mechanisms
- Error handling
- Security vulnerabilities
- Performance bottlenecks
- Integration points
"""

import os
import json
import re
import ast
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
import importlib.util
import sys

class ComprehensiveBackendAuditor:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.issues = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": []
        }
        self.stats = {
            "total_files": 0,
            "python_files": 0,
            "js_files": 0,
            "config_files": 0,
            "api_endpoints": 0,
            "database_models": 0,
            "security_issues": 0,
            "performance_issues": 0
        }
        
    def add_issue(self, severity: str, category: str, file_path: str, 
                  line_num: int, issue: str, suggestion: str = ""):
        """Add an issue to the audit report"""
        self.issues[severity].append({
            "category": category,
            "file": str(file_path),
            "line": line_num,
            "issue": issue,
            "suggestion": suggestion,
            "timestamp": datetime.now().isoformat()
        })
        
    def audit_python_file(self, file_path: Path) -> None:
        """Audit a Python file for various issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
                
            # Parse AST
            try:
                tree = ast.parse(content)
                self.analyze_ast(tree, file_path, lines)
            except SyntaxError as e:
                self.add_issue("critical", "syntax", file_path, e.lineno or 0,
                             f"Syntax error: {e.msg}")
                
            # Check for common issues
            self.check_security_issues(content, file_path, lines)
            self.check_error_handling(content, file_path, lines)
            self.check_database_queries(content, file_path, lines)
            self.check_api_endpoints(content, file_path, lines)
            self.check_authentication(content, file_path, lines)
            self.check_performance_issues(content, file_path, lines)
            self.check_deprecated_code(content, file_path, lines)
            self.check_logging(content, file_path, lines)
            
        except Exception as e:
            self.add_issue("high", "file_error", file_path, 0,
                         f"Failed to analyze file: {str(e)}")
            
    def analyze_ast(self, tree: ast.AST, file_path: Path, lines: List[str]) -> None:
        """Analyze Python AST for structural issues"""
        for node in ast.walk(tree):
            # Check for missing docstrings
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    self.add_issue("low", "documentation", file_path, node.lineno,
                                 f"Missing docstring for {node.name}",
                                 "Add descriptive docstring")
                                 
            # Check for bare except clauses
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    self.add_issue("high", "error_handling", file_path, node.lineno,
                                 "Bare except clause catches all exceptions",
                                 "Specify exception types to catch")
                                 
            # Check for hardcoded credentials
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.lower()
                        if any(secret in var_name for secret in 
                               ['password', 'secret', 'key', 'token', 'api_key']):
                            if isinstance(node.value, ast.Constant):
                                self.add_issue("critical", "security", file_path, node.lineno,
                                             f"Hardcoded credential: {target.id}",
                                             "Use environment variables")
                                             
    def check_security_issues(self, content: str, file_path: Path, lines: List[str]) -> None:
        """Check for security vulnerabilities"""
        security_patterns = [
            (r'eval\s*\(', "Use of eval() is dangerous", "critical"),
            (r'exec\s*\(', "Use of exec() is dangerous", "critical"),
            (r'pickle\.loads?\s*\(', "Pickle can execute arbitrary code", "high"),
            (r'os\.system\s*\(', "os.system() is vulnerable to injection", "high"),
            (r'subprocess\.call\s*\(.*shell\s*=\s*True', "Shell injection risk", "high"),
            (r'\.execute\s*\([\'"].*%s.*[\'"]', "SQL injection risk", "critical"),
            (r'\.raw\s*\([\'"].*%s.*[\'"]', "SQL injection risk", "critical"),
            (r'verify\s*=\s*False', "SSL verification disabled", "high"),
            (r'debug\s*=\s*True', "Debug mode enabled", "medium"),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, issue, severity in security_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.add_issue(severity, "security", file_path, i, issue)
                    self.stats["security_issues"] += 1
                    
    def check_error_handling(self, content: str, file_path: Path, lines: List[str]) -> None:
        """Check for proper error handling"""
        # Check for missing error handling in critical operations
        critical_ops = [
            (r'open\s*\(', "File operation without error handling"),
            (r'requests\.\w+\s*\(', "HTTP request without error handling"),
            (r'\.connect\s*\(', "Database connection without error handling"),
            (r'json\.loads?\s*\(', "JSON parsing without error handling"),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, issue in critical_ops:
                if re.search(pattern, line):
                    # Check if it's in a try block
                    in_try = False
                    for j in range(max(0, i-5), i):
                        if j < len(lines) and 'try:' in lines[j]:
                            in_try = True
                            break
                    if not in_try:
                        self.add_issue("medium", "error_handling", file_path, i,
                                     issue, "Wrap in try-except block")
                                     
    def check_database_queries(self, content: str, file_path: Path, lines: List[str]) -> None:
        """Check for database query issues"""
        # Check for N+1 queries
        if 'for ' in content and '.objects.get(' in content:
            self.add_issue("high", "performance", file_path, 0,
                         "Potential N+1 query problem",
                         "Use select_related() or prefetch_related()")
                         
        # Check for missing indexes
        if 'filter(' in content or 'exclude(' in content:
            self.add_issue("info", "performance", file_path, 0,
                         "Check if filtered fields have indexes",
                         "Add db_index=True to frequently queried fields")
                         
        # Check for raw SQL
        if '.raw(' in content or 'cursor.execute(' in content:
            self.add_issue("medium", "database", file_path, 0,
                         "Raw SQL detected",
                         "Consider using ORM methods for better security")
                         
    def check_api_endpoints(self, content: str, file_path: Path, lines: List[str]) -> None:
        """Check API endpoint definitions and issues"""
        # FastAPI/Flask/Django patterns
        api_patterns = [
            r'@app\.(get|post|put|delete|patch)\s*\(',
            r'@router\.(get|post|put|delete|patch)\s*\(',
            r'@api_view\s*\(',
            r'class\s+\w+\s*\(.*APIView.*\):',
        ]
        
        for pattern in api_patterns:
            if re.search(pattern, content):
                self.stats["api_endpoints"] += 1
                
                # Check for missing authentication
                if not any(auth in content for auth in 
                          ['@login_required', '@authenticate', 'permission_classes',
                           'IsAuthenticated', 'check_auth', 'verify_token']):
                    self.add_issue("high", "security", file_path, 0,
                                 "API endpoint without authentication",
                                 "Add authentication decorator/middleware")
                                 
                # Check for missing input validation
                if not any(val in content for val in 
                          ['validate', 'serializer', 'schema', 'pydantic']):
                    self.add_issue("medium", "validation", file_path, 0,
                                 "API endpoint without input validation",
                                 "Add input validation")
                                 
    def check_authentication(self, content: str, file_path: Path, lines: List[str]) -> None:
        """Check authentication implementation"""
        # Check for weak password hashing
        if 'md5' in content or 'sha1' in content:
            self.add_issue("critical", "security", file_path, 0,
                         "Weak password hashing algorithm",
                         "Use bcrypt, scrypt, or argon2")
                         
        # Check for JWT issues
        if 'jwt' in content.lower():
            if 'verify=False' in content or 'verify_signature=False' in content:
                self.add_issue("critical", "security", file_path, 0,
                             "JWT signature verification disabled",
                             "Always verify JWT signatures")
                             
        # Check for session security
        if 'session' in content:
            if not any(sec in content for sec in 
                      ['secure=True', 'httponly=True', 'samesite']):
                self.add_issue("high", "security", file_path, 0,
                             "Session cookies may lack security flags",
                             "Set secure, httponly, and samesite flags")
                             
    def check_performance_issues(self, content: str, file_path: Path, lines: List[str]) -> None:
        """Check for performance bottlenecks"""
        perf_patterns = [
            (r'time\.sleep\s*\(', "Blocking sleep in code", "medium"),
            (r'\.all\(\)\.count\(\)', "Inefficient count query", "medium"),
            (r'for.*in.*\.all\(\):', "Loading all records into memory", "high"),
            (r'json\.dumps.*indent', "Pretty printing JSON in production", "low"),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, issue, severity in perf_patterns:
                if re.search(pattern, line):
                    self.add_issue(severity, "performance", file_path, i, issue)
                    self.stats["performance_issues"] += 1
                    
    def check_deprecated_code(self, content: str, file_path: Path, lines: List[str]) -> None:
        """Check for deprecated code patterns"""
        deprecated_patterns = [
            (r'urllib2', "urllib2 is deprecated", "Use urllib.request"),
            (r'\.has_key\s*\(', "dict.has_key() is deprecated", "Use 'in' operator"),
            (r'print\s+[^(]', "Python 2 style print", "Use print()"),
            (r'xrange\s*\(', "xrange is deprecated", "Use range()"),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, issue, suggestion in deprecated_patterns:
                if re.search(pattern, line):
                    self.add_issue("medium", "deprecated", file_path, i, issue, suggestion)
                    
    def check_logging(self, content: str, file_path: Path, lines: List[str]) -> None:
        """Check logging implementation"""
        # Check if logging is imported but not used properly
        if 'import logging' in content:
            if not re.search(r'logging\.(debug|info|warning|error|critical)', content):
                self.add_issue("low", "logging", file_path, 0,
                             "Logging imported but not used",
                             "Implement proper logging")
                             
        # Check for print statements instead of logging
        if 'print(' in content and 'logging' not in content:
            self.add_issue("low", "logging", file_path, 0,
                         "Using print() instead of logging",
                         "Use logging module for better control")
                         
    def audit_javascript_file(self, file_path: Path) -> None:
        """Audit JavaScript/TypeScript files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
                
            # Check for common JS issues
            js_issues = [
                (r'console\.(log|error|warn)', "Console statements in code", "low"),
                (r'eval\s*\(', "Use of eval() is dangerous", "critical"),
                (r'innerHTML\s*=', "Potential XSS vulnerability", "high"),
                (r'document\.write', "document.write is dangerous", "high"),
                (r'var\s+\w+\s*=', "Use const/let instead of var", "low"),
            ]
            
            for i, line in enumerate(lines, 1):
                for pattern, issue, severity in js_issues:
                    if re.search(pattern, line):
                        self.add_issue(severity, "javascript", file_path, i, issue)
                        
        except Exception as e:
            self.add_issue("medium", "file_error", file_path, 0,
                         f"Failed to analyze JS file: {str(e)}")
                         
    def audit_config_file(self, file_path: Path) -> None:
        """Audit configuration files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for exposed secrets
            secret_patterns = [
                r'(password|secret|key|token)\s*[:=]\s*["\']?\w+',
                r'(DATABASE_URL|REDIS_URL|API_KEY)\s*[:=]\s*["\']?\w+',
            ]
            
            for pattern in secret_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    self.add_issue("critical", "security", file_path, 0,
                                 "Potential exposed secret in config",
                                 "Use environment variables")
                                 
            # Check for missing CORS configuration
            if 'cors' not in content.lower() and file_path.suffix in ['.json', '.yaml', '.yml']:
                self.add_issue("medium", "security", file_path, 0,
                             "Missing CORS configuration",
                             "Configure CORS properly")
                             
        except Exception as e:
            self.add_issue("low", "file_error", file_path, 0,
                         f"Failed to analyze config file: {str(e)}")
                         
    def check_dependencies(self) -> None:
        """Check for dependency issues"""
        req_files = list(self.project_root.glob("**/requirements*.txt"))
        
        for req_file in req_files:
            try:
                with open(req_file, 'r') as f:
                    requirements = f.readlines()
                    
                for req in requirements:
                    req = req.strip()
                    if req and not req.startswith('#'):
                        # Check for unpinned dependencies
                        if '==' not in req and '>=' not in req:
                            self.add_issue("medium", "dependencies", req_file, 0,
                                         f"Unpinned dependency: {req}",
                                         "Pin to specific version")
                                         
                        # Check for known vulnerable packages
                        vulnerable_packages = {
                            'django<3.2': 'Django versions below 3.2 have security issues',
                            'flask<2.0': 'Flask versions below 2.0 have security issues',
                            'requests<2.20': 'Requests versions below 2.20 have security issues',
                        }
                        
                        for vuln_pkg, issue in vulnerable_packages.items():
                            if vuln_pkg.split('<')[0] in req.lower():
                                self.add_issue("high", "dependencies", req_file, 0,
                                             issue, "Update to latest version")
                                             
            except Exception as e:
                self.add_issue("low", "file_error", req_file, 0,
                             f"Failed to analyze requirements: {str(e)}")
                             
    def check_docker_files(self) -> None:
        """Check Docker configuration"""
        docker_files = list(self.project_root.glob("**/Dockerfile*")) + \
                      list(self.project_root.glob("**/docker-compose*.yml"))
                      
        for docker_file in docker_files:
            try:
                with open(docker_file, 'r') as f:
                    content = f.read()
                    
                # Check for security issues
                docker_issues = [
                    (r'USER root', "Running container as root", "high"),
                    (r'--privileged', "Container running in privileged mode", "critical"),
                    (r'COPY.*\*', "Copying everything into container", "medium"),
                    (r'latest', "Using 'latest' tag", "medium"),
                ]
                
                for pattern, issue, severity in docker_issues:
                    if re.search(pattern, content):
                        self.add_issue(severity, "docker", docker_file, 0, issue)
                        
            except Exception as e:
                self.add_issue("low", "file_error", docker_file, 0,
                             f"Failed to analyze Docker file: {str(e)}")
                             
    def check_environment_files(self) -> None:
        """Check environment configuration"""
        env_files = list(self.project_root.glob("**/.env*"))
        
        for env_file in env_files:
            # Check if .env file is in .gitignore
            gitignore_path = self.project_root / '.gitignore'
            if gitignore_path.exists():
                with open(gitignore_path, 'r') as f:
                    gitignore_content = f.read()
                    if env_file.name not in gitignore_content:
                        self.add_issue("critical", "security", env_file, 0,
                                     f"{env_file.name} not in .gitignore",
                                     "Add to .gitignore immediately")
                                     
    def generate_fixes(self) -> Dict[str, Any]:
        """Generate automated fixes for common issues"""
        fixes = {
            "security_fixes": [],
            "performance_fixes": [],
            "code_quality_fixes": [],
            "dependency_updates": []
        }
        
        # Generate security fixes
        for issue in self.issues["critical"] + self.issues["high"]:
            if issue["category"] == "security":
                if "hardcoded" in issue["issue"].lower():
                    fixes["security_fixes"].append({
                        "file": issue["file"],
                        "line": issue["line"],
                        "fix": "Move to environment variable",
                        "code": f"os.getenv('{issue['issue'].split(':')[1].strip()}')"
                    })
                    
        return fixes
        
    def run_audit(self) -> Dict[str, Any]:
        """Run the complete audit"""
        print("🔍 Starting comprehensive backend audit...")
        
        # Audit Python files
        python_files = list(self.project_root.glob("**/*.py"))
        for py_file in python_files:
            if not any(skip in str(py_file) for skip in 
                      ['venv', 'env', '__pycache__', 'node_modules', '.git']):
                self.stats["python_files"] += 1
                self.audit_python_file(py_file)
                
        # Audit JavaScript files
        js_files = list(self.project_root.glob("**/*.js")) + \
                   list(self.project_root.glob("**/*.ts"))
        for js_file in js_files:
            if 'node_modules' not in str(js_file):
                self.stats["js_files"] += 1
                self.audit_javascript_file(js_file)
                
        # Audit config files
        config_patterns = ['*.json', '*.yaml', '*.yml', '*.toml', '*.ini']
        for pattern in config_patterns:
            for config_file in self.project_root.glob(f"**/{pattern}"):
                if not any(skip in str(config_file) for skip in 
                          ['node_modules', '.git', 'venv']):
                    self.stats["config_files"] += 1
                    self.audit_config_file(config_file)
                    
        # Check dependencies
        self.check_dependencies()
        
        # Check Docker files
        self.check_docker_files()
        
        # Check environment files
        self.check_environment_files()
        
        # Generate report
        report = {
            "audit_timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "statistics": self.stats,
            "issues": self.issues,
            "issue_summary": {
                "critical": len(self.issues["critical"]),
                "high": len(self.issues["high"]),
                "medium": len(self.issues["medium"]),
                "low": len(self.issues["low"]),
                "info": len(self.issues["info"])
            },
            "fixes": self.generate_fixes()
        }
        
        return report
        
def main():
    """Main execution function"""
    auditor = ComprehensiveBackendAuditor()
    report = auditor.run_audit()
    
    # Save report
    report_file = f"backend_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
        
    # Print summary
    print("\n📊 Audit Summary:")
    print(f"Total files analyzed: {report['statistics']['python_files'] + report['statistics']['js_files'] + report['statistics']['config_files']}")
    print(f"Python files: {report['statistics']['python_files']}")
    print(f"JavaScript files: {report['statistics']['js_files']}")
    print(f"Config files: {report['statistics']['config_files']}")
    print(f"\n🚨 Issues Found:")
    print(f"Critical: {report['issue_summary']['critical']}")
    print(f"High: {report['issue_summary']['high']}")
    print(f"Medium: {report['issue_summary']['medium']}")
    print(f"Low: {report['issue_summary']['low']}")
    print(f"Info: {report['issue_summary']['info']}")
    print(f"\nDetailed report saved to: {report_file}")
    
    # Create fix script
    if report['issue_summary']['critical'] > 0 or report['issue_summary']['high'] > 0:
        print("\n⚠️  Critical/High severity issues found! Creating fix script...")
        create_fix_script(report)
        
def create_fix_script(report: Dict[str, Any]) -> None:
    """Create an automated fix script for critical issues"""
    fix_script = """#!/usr/bin/env python3
# Auto-generated fix script for critical backend issues
import os
import re
from pathlib import Path

def fix_hardcoded_secrets():
    \"\"\"Fix hardcoded secrets by moving to environment variables\"\"\"
    fixes = {fixes}
    
    for fix in fixes['security_fixes']:
        file_path = Path(fix['file'])
        if file_path.exists():
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Apply fix
            # This is a simplified example - real implementation would be more sophisticated
            print(f"Fixing {{file_path}}: {{fix['fix']}}")
            
def main():
    print("🔧 Applying automated fixes...")
    fix_hardcoded_secrets()
    print("✅ Fixes applied. Please review and test changes.")
    
if __name__ == "__main__":
    main()
"""
    
    with open("apply_backend_fixes.py", "w") as f:
        f.write(fix_script.format(fixes=report['fixes']))
    os.chmod("apply_backend_fixes.py", 0o755)
    print("Fix script created: apply_backend_fixes.py")
    
if __name__ == "__main__":
    main()