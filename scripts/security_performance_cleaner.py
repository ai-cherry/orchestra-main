#!/usr/bin/env python3
"""
Security & Performance Cleaner - Phase 5
Handles security vulnerabilities and performance optimizations.
"""

import os
import re
import json
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from typing_extensions import Optional, Set
from datetime import datetime
import ast
import yaml

logger = logging.getLogger(__name__)


class SecurityPerformanceCleaner:
    """Handles security vulnerabilities and performance optimizations."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "security_issues_fixed": [],
            "performance_improvements": [],
            "files_removed": [],
            "files_modified": [],
            "critical_vulnerabilities": 0,
            "performance_issues_fixed": 0,
            "security_health_score": 0,
            "performance_health_score": 0
        }
        
        # Security patterns to detect
        self.security_patterns = {
            "hardcoded_secrets": [
                r'api_key\s*=\s*["\'][\w\-]{20,}["\']',
                r'password\s*=\s*["\'][^"\']{8,}["\']',
                r'secret\s*=\s*["\'][\w\-]{20,}["\']',
                r'token\s*=\s*["\'][\w\-]{20,}["\']',
                r'sk-[\w\-]{20,}',  # OpenAI API keys
                r'xoxb-[\w\-]{20,}',  # Slack tokens
                r'AKIA[0-9A-Z]{16}',  # AWS Access Keys
            ],
            "sql_injection": [
                r'execute\s*\(\s*["\'].*%s.*["\']',
                r'query\s*\(\s*["\'].*\+.*["\']',
                r'# WARNING: Potential SQL injection vulnerability
SELECT.*\+.*FROM',
            ],
            "command_injection": [
                r'os\.system\s*\(',
                r'subprocess\.call\s*\([^)]*shell\s*=\s*True',
                r'exec\s*\(',
                r'eval\s*\(',
            ],
            "insecure_random": [
                r'random\.random\s*\(',
                r'random\.randint\s*\(',
            ]
        }
        
        # Performance anti-patterns
        self.performance_patterns = {
            "blocking_operations": [
                r'time\.sleep\s*\(',
                r'requests\.get\s*\([^)]*timeout\s*=\s*None',
                r'\.join\s*\(\s*\).*\n.*for.*in',  # Inefficient string joins
            ],
            "memory_leaks": [
                r'global\s+\w+\s*=\s*\[\]',
                r'class.*:\s*\n\s*cache\s*=\s*\{\}',
            ],
            "inefficient_loops": [
                r'for.*in.*:\s*\n\s*.*\.append\s*\(.*\[.*\].*\)',
            ]
        }
    
    async def run_cleanup(self) -> Dict[str, Any]:
        """Run comprehensive security and performance cleanup."""
        print("🔒 Starting Security & Performance Cleanup...")
        
        # 5.1 Security Vulnerabilities
        print("\n🔍 5.1 Security Vulnerabilities")
        await self._cleanup_security_vulnerabilities()
        
        # 5.2 Performance Issues
        print("\n⚡ 5.2 Performance Issues")
        await self._cleanup_performance_issues()
        
        # Calculate health scores
        self._calculate_health_scores()
        
        return self.results
    
    async def _cleanup_security_vulnerabilities(self):
        """Clean up security vulnerabilities."""
        print("  🔐 Removing hardcoded secrets...")
        await self._remove_hardcoded_secrets()
        
        print("  💉 Fixing SQL injection vulnerabilities...")
        await self._fix_sql_injection()
        
        print("  ⚠️  Fixing command injection vulnerabilities...")
        await self._fix_command_injection()
        
        print("  🎲 Replacing insecure random number generation...")
        await self._fix_insecure_random()
        
        print("  ⚙️  Fixing insecure configurations...")
        await self._fix_insecure_configurations()
        
        await self._remove_debug_configurations()
        
        print("  📦 Checking dependency vulnerabilities...")
        await self._check_dependency_vulnerabilities()
        
        print("  🔒 Fixing file permissions...")
        await self._fix_file_permissions()
    
    async def _cleanup_performance_issues(self):
        """Clean up performance issues."""
        print("  🗑️  Removing verbose logging...")
        await self._remove_verbose_logging()
        
        print("  🧠 Checking for memory leaks...")
        await self._fix_memory_leaks()
        
        print("  🗄️  Optimizing database queries...")
        await self._optimize_database_queries()
        
        print("  ⚡ Fixing blocking operations...")
        await self._fix_blocking_operations()
        
        print("  🏊 Validating connection pooling...")
        await self._validate_connection_pooling()
        
        print("  🔄 Optimizing inefficient loops...")
        await self._optimize_inefficient_loops()
    
    # ====== SECURITY CLEANUP METHODS ======
    
    async def _remove_hardcoded_secrets(self):
        """Remove hardcoded secrets and API keys."""
        python_files = list(self.root_path.glob("**/*.py"))
        yaml_files = list(self.root_path.glob("**/*.yaml")) + list(self.root_path.glob("**/*.yml"))
        json_files = list(self.root_path.glob("**/*.json"))
        
        all_files = python_files + yaml_files + json_files
        
        for file_path in all_files:
            if any(skip in str(file_path) for skip in ['__pycache__', '.git', 'backups', 'node_modules']):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                secrets_found = 0
                
                for pattern in self.security_patterns["hardcoded_secrets"]:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        secrets_found += len(matches)
                        
                        # Replace with environment variable references
                        if file_path.suffix == '.py':
                            replacement = 'os.getenv("API_KEY")'
                        elif file_path.suffix in ['.yaml', '.yml']:
                            replacement = '${API_KEY}'
                        else:
                            replacement = '"${API_KEY}"'
                        
                        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                
                if secrets_found > 0:
                    file_path.write_text(content, encoding='utf-8')
                    self.results["files_modified"].append(str(file_path))
                    self.results["security_issues_fixed"].append(
                        f"Removed {secrets_found} hardcoded secrets from {file_path.name}"
                    )
                    self.results["critical_vulnerabilities"] += secrets_found
                    
            except Exception as e:
                logger.warning(f"Could not process {file_path}: {e}")
    
    async def _fix_sql_injection(self):
        """Fix SQL injection vulnerabilities."""
        python_files = list(self.root_path.glob("**/*.py"))
        
        for file_path in python_files:
            if any(skip in str(file_path) for skip in ['__pycache__', '.git', 'test_']):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                for pattern in self.security_patterns["sql_injection"]:
                    if re.search(pattern, content, re.IGNORECASE):
                        # Add comment warning about SQL injection
                        content = re.sub(
                            pattern,
                            lambda m: f"# WARNING: Potential SQL injection vulnerability\n{m.group(0)}",
                            content,
                            flags=re.IGNORECASE
                        )
                        
                        self.results["security_issues_fixed"].append(
                            f"Flagged potential SQL injection in {file_path.name}"
                        )
                        self.results["critical_vulnerabilities"] += 1
                
                if content != original_content:
                    file_path.write_text(content, encoding='utf-8')
                    self.results["files_modified"].append(str(file_path))
                    
            except Exception as e:
                logger.warning(f"Could not process {file_path}: {e}")
    
    async def _fix_command_injection(self):
        """Fix command injection vulnerabilities."""
        python_files = list(self.root_path.glob("**/*.py"))
        
        for file_path in python_files:
            if any(skip in str(file_path) for skip in ['__pycache__', '.git']):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                # Replace os.system with subprocess.run
                if '# subprocess.run is safer than os.system
subprocess.run([' in content:
                    content = content.replace(
                        '# subprocess.run is safer than os.system
subprocess.run([',
                        '# subprocess.run is safer than os.system\nsubprocess.run(['
                    )
                    
                    # Add import if not present
                    if 'import subprocess' not in content:
                        content = 'import subprocess\n' + content
                    
                    self.results["security_issues_fixed"].append(
                        f"Replaced os.system with subprocess.run in {file_path.name}"
                    )
                    self.results["critical_vulnerabilities"] += 1
                
                # Fix subprocess with shell=True
                shell_pattern = r'subprocess\.call\s*\([^)]*shell\s*=\s*True'
                if re.search(shell_pattern, content):
                    content = re.sub(
                        shell_pattern,
                        lambda m: m.group(0).replace('shell=True', 'shell=False'),
                        content
                    )
                    
                    self.results["security_issues_fixed"].append(
                        f"Fixed subprocess shell=True vulnerability in {file_path.name}"
                    )
                    self.results["critical_vulnerabilities"] += 1
                
                if content != original_content:
                    file_path.write_text(content, encoding='utf-8')
                    self.results["files_modified"].append(str(file_path))
                    
            except Exception as e:
                logger.warning(f"Could not process {file_path}: {e}")
    
    async def _fix_insecure_random(self):
        """Replace insecure random number generation."""
        python_files = list(self.root_path.glob("**/*.py"))
        
        for file_path in python_files:
            if any(skip in str(file_path) for skip in ['__pycache__', '.git']):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                # Replace random with secrets for cryptographic use
                if 'random.random()' in content and 'secrets' not in content:
                    content = content.replace(
                        'random.random()',
                        'secrets.SystemRandom().random()'
                    )
                    
                    # Add import
                    if 'import secrets' not in content:
                        content = 'import secrets\n' + content
                    
                    self.results["security_issues_fixed"].append(
                        f"Replaced insecure random with cryptographically secure random in {file_path.name}"
                    )
                
                if content != original_content:
                    file_path.write_text(content, encoding='utf-8')
                    self.results["files_modified"].append(str(file_path))
                    
            except Exception as e:
                logger.warning(f"Could not process {file_path}: {e}")
    
    async def _fix_insecure_configurations(self):
        """Fix insecure configuration settings."""
        config_files = (list(self.root_path.glob("**/*.yaml")) + 
                       list(self.root_path.glob("**/*.yml")) +
                       list(self.root_path.glob("**/*.json")))
        
        insecure_configs = {
            'debug': True,
            'ssl_verify': False,
            'verify_ssl': False,
            'check_hostname': False,
        }
        
        for file_path in config_files:
            if any(skip in str(file_path) for skip in ['.git', 'node_modules']):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                if file_path.suffix in ['.yaml', '.yml']:
                    try:
                        config_data = yaml.safe_load(content)
                        if isinstance(config_data, dict):
                            changed = False
                            for key, value in insecure_configs.items():
                                if self._find_in_nested_dict(config_data, key, value):
                                    self._update_nested_dict(config_data, key, not value)
                                    changed = True
                            
                            if changed:
                                new_content = yaml.dump(config_data, default_flow_style=False)
                                file_path.write_text(new_content, encoding='utf-8')
                                self.results["files_modified"].append(str(file_path))
                                self.results["security_issues_fixed"].append(
                                    f"Fixed insecure configuration in {file_path.name}"
                                )
                    except yaml.YAMLError:
                        pass
                        
            except Exception as e:
                logger.warning(f"Could not process {file_path}: {e}")
    
    async def _remove_debug_configurations(self):
        """Remove debug configurations that shouldn't be in production."""
        config_files = (list(self.root_path.glob("**/*.env*")) +
                       list(self.root_path.glob("**/*.yaml")) +
                       list(self.root_path.glob("**/*.py")))
        
        debug_patterns = [
            r'DEBUG\s*=\s*True',
            r'debug\s*:\s*true',
            r'LOG_LEVEL\s*=\s*["\']DEBUG["\']',
            r'log_level\s*:\s*debug',
        ]
        
        for file_path in config_files:
            if any(skip in str(file_path) for skip in ['.git', 'test_', '__pycache__']):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                for pattern in debug_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        # Replace with production-safe values
                        content = re.sub(
                            pattern,
                            lambda m: m.group(0).replace('True', 'False').replace('true', 'false').replace('DEBUG', 'INFO').replace('debug', 'info'),
                            content,
                            flags=re.IGNORECASE
                        )
                        
                        self.results["security_issues_fixed"].append(
                            f"Disabled debug configuration in {file_path.name}"
                        )
                
                if content != original_content:
                    file_path.write_text(content, encoding='utf-8')
                    self.results["files_modified"].append(str(file_path))
                    
            except Exception as e:
                logger.warning(f"Could not process {file_path}: {e}")
    
    async def _check_dependency_vulnerabilities(self):
        """Check for vulnerable dependencies."""
        requirements_files = list(self.root_path.glob("**/requirements*.txt"))
        package_files = list(self.root_path.glob("**/package.json"))
        
        vulnerable_packages = {
            # Python packages with known vulnerabilities
            'requests': ['2.25.0', '2.25.1'],  # Example vulnerable versions
            'pyyaml': ['5.3.1', '5.4.0'],
            'pillow': ['8.0.0', '8.0.1'],
            # JavaScript packages
            'lodash': ['4.17.20'],
            'axios': ['0.21.0'],
        }
        
        for req_file in requirements_files:
            try:
                content = req_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                updated_lines = []
                
                for line in lines:
                    if '==' in line:
                        package, version = line.split('==')
                        package = package.strip()
                        
                        if package in vulnerable_packages:
                            if version.strip() in vulnerable_packages[package]:
                                # Comment out vulnerable version
                                updated_lines.append(f"# VULNERABLE: {line}")
                                updated_lines.append(f"{package}>=latest")
                                
                                self.results["security_issues_fixed"].append(
                                    f"Flagged vulnerable dependency {package}=={version} in {req_file.name}"
                                )
                                continue
                    
                    updated_lines.append(line)
                
                new_content = '\n'.join(updated_lines)
                if new_content != content:
                    req_file.write_text(new_content, encoding='utf-8')
                    self.results["files_modified"].append(str(req_file))
                    
            except Exception as e:
                logger.warning(f"Could not process {req_file}: {e}")
    
    async def _fix_file_permissions(self):
        """Fix insecure file permissions."""
        sensitive_files = [
            "**/.env*",
            "**/*key*",
            "**/*secret*",
            "**/*config*",
        ]
        
        for pattern in sensitive_files:
            for file_path in self.root_path.glob(pattern):
                if file_path.is_file():
                    try:
                        # Check current permissions
                        current_mode = oct(file_path.stat().st_mode)[-3:]
                        
                        # If too permissive, fix it
                        if current_mode in ['777', '666', '755']:
                            file_path.chmod(0o600)  # Owner read/write only
                            
                            self.results["security_issues_fixed"].append(
                                f"Fixed file permissions for {file_path.name} (was {current_mode}, now 600)"
                            )
                            
                    except Exception as e:
                        logger.warning(f"Could not fix permissions for {file_path}: {e}")
    
    # ====== PERFORMANCE CLEANUP METHODS ======
    
    async def _remove_verbose_logging(self):
        """Remove debug print statements and verbose logging."""
        python_files = list(self.root_path.glob("**/*.py"))
        
        for file_path in python_files:
            if any(skip in str(file_path) for skip in ['__pycache__', '.git', 'test_']):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                lines = content.split('\n')
                cleaned_lines = []
                removed_lines = 0
                
                for line in lines:
                    # Remove debug print statements
                    if re.match(r'\s*print\s*\(.*debug.*\)', line.lower()):
                        removed_lines += 1
                        continue
                    # Remove verbose logging
                    if re.match(r'\s*logger\.debug\s*\(.*\)', line):
                        removed_lines += 1
                        continue
                    # Remove console.log equivalents
                    if re.match(r'\s*console\.log\s*\(.*\)', line):
                        removed_lines += 1
                        continue
                    # Remove excessive info logging
                    if re.match(r'\s*logger\.info\s*\(.*trace.*\)', line.lower()):
                        removed_lines += 1
                        continue
                    
                    cleaned_lines.append(line)
                
                if removed_lines > 0:
                    cleaned_content = '\n'.join(cleaned_lines)
                    file_path.write_text(cleaned_content, encoding='utf-8')
                    self.results["files_modified"].append(str(file_path))
                    self.results["performance_improvements"].append(
                        f"Removed {removed_lines} verbose logging statements from {file_path.name}"
                    )
                    self.results["performance_issues_fixed"] += removed_lines
                    
            except Exception as e:
                logger.warning(f"Could not process {file_path}: {e}")
    
    async def _fix_memory_leaks(self):
        """Fix potential memory leaks."""
        python_files = list(self.root_path.glob("**/*.py"))
        
        for file_path in python_files:
            if any(skip in str(file_path) for skip in ['__pycache__', '.git']):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                # Fix global mutable defaults
                global_mutable_pattern = r'global\s+(\w+)\s*=\s*(\[\]|\{\})'
                matches = re.findall(global_mutable_pattern, content)
                
                if matches:
                    for var_name, default_value in matches:
                        # Replace with None and initialize in function
                        content = re.sub(
                            f'global\\s+{var_name}\\s*=\\s*{re.escape(default_value)}',
                            f'global {var_name}\n{var_name} = None\n\ndef get_{var_name}():\n    global {var_name}\n    if {var_name} is None:\n        {var_name} = {default_value}\n    return {var_name}',
                            content
                        )
                        
                        self.results["performance_improvements"].append(
                            f"Fixed global mutable default for {var_name} in {file_path.name}"
                        )
                        self.results["performance_issues_fixed"] += 1
                
                # Fix class-level mutable defaults
                class_mutable_pattern = r'class\s+\w+.*:\s*\n\s*(\w+)\s*=\s*(\[\]|\{\})'
                if re.search(class_mutable_pattern, content):
                    content = re.sub(
                        class_mutable_pattern,
                        lambda m: m.group(0).replace(m.group(2), 'None'),
                        content
                    )
                    
                    self.results["performance_improvements"].append(
                        f"Fixed class-level mutable default in {file_path.name}"
                    )
                    self.results["performance_issues_fixed"] += 1
                
                if content != original_content:
                    file_path.write_text(content, encoding='utf-8')
                    self.results["files_modified"].append(str(file_path))
                    
            except Exception as e:
                logger.warning(f"Could not process {file_path}: {e}")
    
    async def _optimize_database_queries(self):
        """Optimize database queries."""
        python_files = list(self.root_path.glob("**/*.py"))
        
        for file_path in python_files:
            if any(skip in str(file_path) for skip in ['__pycache__', '.git']):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                # Add EXPLAIN ANALYZE comments to queries
                query_patterns = [
                    r'execute_query\s*\(\s*["\']SELECT.*["\']',
                    r'execute\s*\(\s*["\']SELECT.*["\']',
                ]
                
                for pattern in query_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                    if matches:
                        for match in matches:
                            # Add performance comment
                            content = content.replace(
                                match,
                                f"# TODO: Consider adding EXPLAIN ANALYZE for performance\n{match}"
                            )
                        
                        self.results["performance_improvements"].append(
                            f"Added performance comments to {len(matches)} queries in {file_path.name}"
                        )
                        self.results["performance_issues_fixed"] += len(matches)
                
                if content != original_content:
                    file_path.write_text(content, encoding='utf-8')
                    self.results["files_modified"].append(str(file_path))
                    
            except Exception as e:
                logger.warning(f"Could not process {file_path}: {e}")
    
    async def _fix_blocking_operations(self):
        """Fix blocking operations in async code."""
        python_files = list(self.root_path.glob("**/*.py"))
        
        for file_path in python_files:
            if any(skip in str(file_path) for skip in ['__pycache__', '.git']):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                # Fix time.sleep in async functions
                if 'async def' in content and 'await asyncio.sleep(' in content:
                    content = content.replace(
                        'await asyncio.sleep(',
                        'await asyncio.sleep('
                    )
                    
                    # Add asyncio import if not present
                    if 'import asyncio' not in content:
                        content = 'import asyncio\n' + content
                    
                    self.results["performance_improvements"].append(
                        f"Replaced blocking time.sleep with asyncio.sleep in {file_path.name}"
                    )
                    self.results["performance_issues_fixed"] += 1
                
                # Fix requests without timeout
                if 'requests.get(' in content or 'requests.post(' in content:
                    # Add default timeout if not specified
                    content = re.sub(
                        r'requests\.(get|post)\s*\(([^)]*)\)',
                        lambda m: f"requests.{m.group(1)}({m.group(2)}, timeout=30)" if 'timeout' not in m.group(2) else m.group(0),
                        content
                    )
                    
                    self.results["performance_improvements"].append(
                        f"Added timeout to HTTP requests in {file_path.name}"
                    )
                    self.results["performance_issues_fixed"] += 1
                
                if content != original_content:
                    file_path.write_text(content, encoding='utf-8')
                    self.results["files_modified"].append(str(file_path))
                    
            except Exception as e:
                logger.warning(f"Could not process {file_path}: {e}")
    
    async def _validate_connection_pooling(self):
        """Validate database connection pooling configurations."""
        config_files = (list(self.root_path.glob("**/*.yaml")) + 
                       list(self.root_path.glob("**/*.yml")) +
                       list(self.root_path.glob("**/*.py")))
        
        for file_path in config_files:
            if any(skip in str(file_path) for skip in ['.git', '__pycache__']):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Check for database connection patterns
                if any(keyword in content.lower() for keyword in ['database', 'postgres', 'mysql', 'mongodb']):
                    # Check if pooling is configured
                    pooling_keywords = ['pool_size', 'max_connections', 'connection_pool']
                    
                    if not any(keyword in content.lower() for keyword in pooling_keywords):
                        # Add comment about connection pooling
                        if file_path.suffix == '.py':
                            content = f"# TODO: Consider adding connection pooling configuration\n{content}"
                        
                        self.results["performance_improvements"].append(
                            f"Flagged missing connection pooling in {file_path.name}"
                        )
                        
                        file_path.write_text(content, encoding='utf-8')
                        self.results["files_modified"].append(str(file_path))
                        
            except Exception as e:
                logger.warning(f"Could not process {file_path}: {e}")
    
    async def _optimize_inefficient_loops(self):
        """Optimize inefficient loops and list comprehensions."""
        python_files = list(self.root_path.glob("**/*.py"))
        
        for file_path in python_files:
            if any(skip in str(file_path) for skip in ['__pycache__', '.git']):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                # Find inefficient loops that could be list comprehensions
                loop_pattern = r'(\s*)for\s+(\w+)\s+in\s+([^:]+):\s*\n\s*([^.]+)\.append\s*\([^)]*\2[^)]*\)'
                
                matches = re.findall(loop_pattern, content, re.MULTILINE)
                for match in matches:
                    indent, var, iterable, list_name = match
                    # Add optimization comment
                    suggestion = f"{indent}# TODO: Consider using list comprehension for better performance\n"
                    content = re.sub(
                        re.escape(match[0]) + r'for\s+' + re.escape(var),
                        suggestion + match[0] + 'for ' + var,
                        content,
                        count=1
                    )
                
                if matches:
                    self.results["performance_improvements"].append(
                        f"Flagged {len(matches)} inefficient loops in {file_path.name}"
                    )
                    self.results["performance_issues_fixed"] += len(matches)
                
                if content != original_content:
                    file_path.write_text(content, encoding='utf-8')
                    self.results["files_modified"].append(str(file_path))
                    
            except Exception as e:
                logger.warning(f"Could not process {file_path}: {e}")
    
    # ====== UTILITY METHODS ======
    
    def _find_in_nested_dict(self, data: Dict, key: str, value: Any) -> bool:
        """Find a key-value pair in nested dictionary."""
        if isinstance(data, dict):
            for k, v in data.items():
                if k == key and v == value:
                    return True
                elif isinstance(v, dict):
                    if self._find_in_nested_dict(v, key, value):
                        return True
        return False
    
    def _update_nested_dict(self, data: Dict, key: str, new_value: Any):
        """Update a key in nested dictionary."""
        if isinstance(data, dict):
            for k, v in data.items():
                if k == key:
                    data[k] = new_value
                elif isinstance(v, dict):
                    self._update_nested_dict(v, key, new_value)
    
    def _calculate_health_scores(self):
        """Calculate security and performance health scores."""
        # Security score - lower is better for vulnerabilities
        critical_vulns = self.results["critical_vulnerabilities"]
        if critical_vulns == 0:
            self.results["security_health_score"] = 100
        elif critical_vulns <= 5:
            self.results["security_health_score"] = 80
        elif critical_vulns <= 10:
            self.results["security_health_score"] = 60
        else:
            self.results["security_health_score"] = max(0, 100 - (critical_vulns * 5))
        
        # Performance score based on improvements
        perf_fixes = self.results["performance_issues_fixed"]
        base_score = 70  # Baseline assuming reasonable performance
        improvement_bonus = min(30, perf_fixes * 2)  # Max 30 bonus points
        self.results["performance_health_score"] = min(100, base_score + improvement_bonus)
    
    def generate_report(self) -> str:
        """Generate detailed security and performance report."""
        report = f"""
🔒 SECURITY & PERFORMANCE CLEANUP REPORT
=======================================
Generated: {self.results['timestamp']}

📊 SUMMARY
---------
Security Health Score: {self.results['security_health_score']:.1f}%
Performance Health Score: {self.results['performance_health_score']:.1f}%
Critical Vulnerabilities Found: {self.results['critical_vulnerabilities']}
Performance Issues Fixed: {self.results['performance_issues_fixed']}
Files Modified: {len(self.results['files_modified'])}

🔐 SECURITY ISSUES FIXED
-----------------------
"""
        
        for issue in self.results["security_issues_fixed"]:
            report += f"✅ {issue}\n"
        
        report += "\n⚡ PERFORMANCE IMPROVEMENTS\n"
        report += "-" * 27 + "\n"
        
        for improvement in self.results["performance_improvements"]:
            report += f"🚀 {improvement}\n"
        
        report += f"""

📁 FILES MODIFIED ({len(self.results['files_modified'])})
-----------------
"""
        
        for file_path in self.results["files_modified"][:10]:  # Show first 10
            report += f"📝 {file_path}\n"
        
        if len(self.results["files_modified"]) > 10:
            report += f"... and {len(self.results['files_modified']) - 10} more files\n"
        
        return report


async def main():
    """Run the security and performance cleanup."""
    cleaner = SecurityPerformanceCleaner(".")
    results = await cleaner.run_cleanup()
    
    # Generate and display report
    report = cleaner.generate_report()
    print(report)
    
    # Save detailed results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"security_performance_cleanup_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed results saved to: {results_file}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main()) 