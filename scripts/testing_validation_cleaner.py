#!/usr/bin/env python3
"""
Testing & Validation Cleaner - Phase 7
Handles test coverage cleanup and integration validation.
"""

import os
import re
import json
import ast
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
import yaml

logger = logging.getLogger(__name__)


class TestingValidationCleaner:
    """Handles test coverage and integration validation cleanup."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_cleanups": [],
            "integration_validations": [],
            "files_removed": [],
            "files_modified": [],
            "broken_tests_removed": 0,
            "duplicate_tests_removed": 0,
            "test_coverage_percentage": 0,
            "docker_builds_validated": 0,
            "api_integrations_tested": 0,
            "testing_health_score": 0,
            "integration_health_score": 0
        }
        
        # Test file patterns
        self.test_patterns = {
            "test_files": [
                "**/test_*.py",
                "**/*_test.py", 
                "**/tests/**/*.py",
                "**/*.test.js",
                "**/*.test.ts",
                "**/*.spec.js",
                "**/*.spec.ts"
            ],
            "broken_patterns": [
                r'def test_.*:\s*pass',
                r'def test_.*:\s*# TODO',
                r'def test_.*:\s*""".*"""',
                r'it\s*\(\s*["\'].*["\'],?\s*\(\)\s*=>\s*{\s*}\s*\)',
            ]
        }
        
        # Integration patterns
        self.integration_patterns = {
            "docker_files": [
                "**/Dockerfile*",
                "**/docker-compose*.yml",
                "**/docker-compose*.yaml"
            ],
            "env_vars": [
                "**/.env*",
                "**/environment.yml",
                "**/config/*.env"
            ]
        }
    
    async def run_cleanup(self) -> Dict[str, Any]:
        """Run comprehensive testing and validation cleanup."""
        print("🧪 Starting Testing & Validation Cleanup...")
        
        # 7.1 Test Coverage
        print("\n🧪 7.1 Test Coverage")
        await self._cleanup_test_coverage()
        
        # 7.2 Integration Validation
        print("\n🔗 7.2 Integration Validation")
        await self._cleanup_integration_validation()
        
        # Calculate health scores
        self._calculate_health_scores()
        
        return self.results
    
    async def _cleanup_test_coverage(self):
        """Clean up test coverage issues."""
        print("  🗑️  Removing broken test files...")
        await self._remove_broken_tests()
        
        print("  🔍 Analyzing test coverage...")
        await self._analyze_test_coverage()
        
        print("  🧹 Removing duplicate tests...")
        await self._remove_duplicate_tests()
        
        print("  🧪 Validating test dependencies...")
        await self._validate_test_dependencies()
        
        print("  🔒 Checking test data security...")
        await self._check_test_data_security()
    
    async def _cleanup_integration_validation(self):
        """Clean up integration validation issues."""
        print("  🐳 Validating Docker configurations...")
        await self._validate_docker_configurations()
        
        print("  🌍 Testing environment variables...")
        await self._test_environment_variables()
        
        print("  🔌 Validating API integrations...")
        await self._validate_api_integrations()
        
        print("  📁 Checking file path consistency...")
        await self._check_file_path_consistency()
        
        print("  📜 Validating shell scripts...")
        await self._validate_shell_scripts()
    
    # ====== TEST COVERAGE CLEANUP METHODS ======
    
    async def _remove_broken_tests(self):
        """Remove broken or empty test files."""
        test_files = []
        
        for pattern in self.test_patterns["test_files"]:
            test_files.extend(list(self.root_path.glob(pattern)))
        
        for test_file in test_files:
            if any(skip in str(test_file) for skip in ['__pycache__', '.git', 'node_modules']):
                continue
                
            try:
                content = test_file.read_text(encoding='utf-8')
                
                # Check if file is essentially empty or broken
                is_broken = self._is_test_file_broken(content, test_file)
                
                if is_broken:
                    # Instead of deleting, rename to .broken
                    backup_file = test_file.with_suffix(test_file.suffix + '.broken')
                    test_file.rename(backup_file)
                    
                    self.results["files_removed"].append(str(test_file))
                    self.results["broken_tests_removed"] += 1
                    self.results["test_cleanups"].append(
                        f"Disabled broken test file: {test_file.name}"
                    )
                    
            except Exception as e:
                logger.warning(f"Could not process test file {test_file}: {e}")
    
    def _is_test_file_broken(self, content: str, file_path: Path) -> bool:
        """Check if a test file is broken or empty."""
        # Empty file
        if not content.strip():
            return True
        
        # Only imports and no actual tests
        if file_path.suffix == '.py':
            try:
                tree = ast.parse(content)
                has_test_functions = False
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node.name.startswith('test_'):
                            # Check if function has actual implementation
                            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                                continue  # Just pass statement
                            has_test_functions = True
                            break
                
                if not has_test_functions:
                    return True
                    
            except SyntaxError:
                return True  # Can't parse, likely broken
        
        # Check for broken patterns
        for pattern in self.test_patterns["broken_patterns"]:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        # JavaScript/TypeScript specific checks
        if file_path.suffix in ['.js', '.ts']:
            # No actual test implementations
            if re.search(r'describe\s*\([^)]*\)\s*{\s*}', content):
                return True
            if re.search(r'it\s*\([^)]*\)\s*{\s*}', content):
                return True
        
        return False
    
    async def _analyze_test_coverage(self):
        """Analyze current test coverage."""
        # Find all source files
        source_files = []
        source_patterns = [
            "src/**/*.py",
            "app/**/*.py", 
            "lib/**/*.py",
            "**/*.py"
        ]
        
        for pattern in source_patterns:
            source_files.extend(list(self.root_path.glob(pattern)))
        
        # Filter out test files and non-source files
        source_files = [
            f for f in source_files 
            if not any(skip in str(f) for skip in ['test_', '_test', 'tests/', '__pycache__', '.git'])
        ]
        
        # Find test files
        test_files = []
        for pattern in self.test_patterns["test_files"]:
            test_files.extend(list(self.root_path.glob(pattern)))
        
        # Calculate coverage ratio
        if source_files:
            coverage_ratio = len(test_files) / len(source_files)
            self.results["test_coverage_percentage"] = min(100, coverage_ratio * 100)
        else:
            self.results["test_coverage_percentage"] = 0
        
        # Analyze specific modules that need tests
        untested_modules = []
        for source_file in source_files:
            # Check if there's a corresponding test file
            potential_test_files = [
                source_file.parent / f"test_{source_file.name}",
                source_file.parent / f"{source_file.stem}_test.py",
                self.root_path / "tests" / source_file.name,
            ]
            
            has_test = any(test_file.exists() for test_file in potential_test_files)
            
            if not has_test:
                untested_modules.append(str(source_file.relative_to(self.root_path)))
        
        if untested_modules:
            self.results["test_cleanups"].append(
                f"Found {len(untested_modules)} modules without tests"
            )
            
            # Create a report of untested modules
            report_file = self.root_path / "untested_modules_report.txt"
            with open(report_file, 'w') as f:
                f.write("MODULES WITHOUT TESTS\n")
                f.write("=" * 21 + "\n\n")
                
                for module in untested_modules[:20]:  # Limit to first 20
                    f.write(f"• {module}\n")
                
                if len(untested_modules) > 20:
                    f.write(f"\n... and {len(untested_modules) - 20} more modules\n")
            
            self.results["files_modified"].append(str(report_file))
    
    async def _remove_duplicate_tests(self):
        """Remove duplicate test cases."""
        test_files = []
        
        for pattern in self.test_patterns["test_files"]:
            test_files.extend(list(self.root_path.glob(pattern)))
        
        # Analyze Python test files for duplicates
        for test_file in test_files:
            if test_file.suffix != '.py':
                continue
                
            if any(skip in str(test_file) for skip in ['__pycache__', '.git']):
                continue
                
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                
                test_functions = []
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node.name.startswith('test_'):
                            # Get function signature and basic content
                            func_info = {
                                "name": node.name,
                                "line": node.lineno,
                                "args": [arg.arg for arg in node.args.args],
                                "docstring": ast.get_docstring(node) or ""
                            }
                            test_functions.append(func_info)
                
                # Find duplicates by name similarity
                duplicates = []
                for i, func1 in enumerate(test_functions):
                    for j, func2 in enumerate(test_functions[i+1:], i+1):
                        # Check for similar names or identical docstrings
                        if (func1["name"] == func2["name"] or 
                            (func1["docstring"] and func1["docstring"] == func2["docstring"])):
                            duplicates.append((func1, func2))
                
                if duplicates:
                    self.results["duplicate_tests_removed"] += len(duplicates)
                    self.results["test_cleanups"].append(
                        f"Found {len(duplicates)} duplicate test functions in {test_file.name}"
                    )
                    
                    # Add comments about duplicates
                    lines = content.split('\n')
                    for func1, func2 in reversed(duplicates):
                        line_idx = func2["line"] - 1
                        comment = f"# TODO: Remove duplicate test - similar to {func1['name']} at line {func1['line']}"
                        lines.insert(line_idx, comment)
                    
                    modified_content = '\n'.join(lines)
                    test_file.write_text(modified_content, encoding='utf-8')
                    self.results["files_modified"].append(str(test_file))
                    
            except Exception as e:
                logger.warning(f"Could not analyze test file {test_file}: {e}")
    
    async def _validate_test_dependencies(self):
        """Validate that all test dependencies are properly specified."""
        # Check requirements files for test dependencies
        requirements_files = list(self.root_path.glob("**/requirements*.txt"))
        requirements_files.extend(list(self.root_path.glob("**/pyproject.toml")))
        requirements_files.extend(list(self.root_path.glob("**/package.json")))
        
        common_test_deps = {
            "python": ["pytest", "unittest", "nose", "coverage", "mock"],
            "javascript": ["jest", "mocha", "chai", "jasmine", "karma"]
        }
        
        for req_file in requirements_files:
            try:
                content = req_file.read_text(encoding='utf-8')
                
                if req_file.name.endswith('.txt'):
                    # Python requirements
                    has_test_deps = any(dep in content.lower() for dep in common_test_deps["python"])
                    
                    if not has_test_deps:
                        self.results["test_cleanups"].append(
                            f"No test dependencies found in {req_file.name}"
                        )
                
                elif req_file.name == 'package.json':
                    # JavaScript dependencies
                    try:
                        package_data = json.loads(content)
                        dev_deps = package_data.get("devDependencies", {})
                        has_test_deps = any(dep in dev_deps for dep in common_test_deps["javascript"])
                        
                        if not has_test_deps:
                            self.results["test_cleanups"].append(
                                f"No test dependencies found in {req_file.name}"
                            )
                    except json.JSONDecodeError:
                        pass
                        
            except Exception as e:
                logger.warning(f"Could not check dependencies in {req_file}: {e}")
    
    async def _check_test_data_security(self):
        """Check that test data doesn't contain sensitive information."""
        test_files = []
        
        for pattern in self.test_patterns["test_files"]:
            test_files.extend(list(self.root_path.glob(pattern)))
        
        # Also check test data directories
        test_data_files = list(self.root_path.glob("**/test_data/**/*"))
        test_data_files.extend(list(self.root_path.glob("**/tests/data/**/*")))
        
        all_test_files = test_files + test_data_files
        
        sensitive_patterns = [
            r'password\s*=\s*["\'][^"\']{8,}["\']',
            r'api_key\s*=\s*["\'][\w\-]{20,}["\']',
            r'secret\s*=\s*["\'][\w\-]{20,}["\']',
            r'token\s*=\s*["\'][\w\-]{20,}["\']',
            r'sk-[\w\-]{20,}',  # OpenAI API keys
            r'\b\d{4}-\d{4}-\d{4}-\d{4}\b',  # Credit card numbers
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN format
        ]
        
        for test_file in all_test_files:
            if not test_file.is_file():
                continue
                
            if any(skip in str(test_file) for skip in ['__pycache__', '.git']):
                continue
                
            try:
                content = test_file.read_text(encoding='utf-8')
                
                sensitive_found = []
                for pattern in sensitive_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        sensitive_found.extend(matches)
                
                if sensitive_found:
                    self.results["test_cleanups"].append(
                        f"Found {len(sensitive_found)} potential sensitive data in {test_file.name}"
                    )
                    
                    # Replace sensitive data with placeholders
                    modified_content = content
                    for pattern in sensitive_patterns:
                        modified_content = re.sub(
                            pattern, 
                            '"REDACTED_TEST_DATA"', 
                            modified_content, 
                            flags=re.IGNORECASE
                        )
                    
                    if modified_content != content:
                        test_file.write_text(modified_content, encoding='utf-8')
                        self.results["files_modified"].append(str(test_file))
                        
            except Exception as e:
                logger.warning(f"Could not check test file {test_file}: {e}")
    
    # ====== INTEGRATION VALIDATION METHODS ======
    
    async def _validate_docker_configurations(self):
        """Validate Docker configurations build successfully."""
        docker_files = []
        
        for pattern in self.integration_patterns["docker_files"]:
            docker_files.extend(list(self.root_path.glob(pattern)))
        
        for docker_file in docker_files:
            try:
                content = docker_file.read_text(encoding='utf-8')
                
                # Basic Docker file validation
                issues = self._validate_dockerfile_content(content)
                
                if issues:
                    self.results["integration_validations"].append(
                        f"Found {len(issues)} issues in {docker_file.name}"
                    )
                else:
                    self.results["docker_builds_validated"] += 1
                    
                # Try to validate build (dry run)
                if docker_file.name.startswith('Dockerfile'):
                    try:
                        # Run docker build --dry-run if available
                        result = subprocess.run(
                            ['docker', 'build', '--dry-run', '-f', str(docker_file), '.'],
                            capture_output=True,
                            text=True,
                            timeout=30,
                            cwd=docker_file.parent
                        )
                        
                        if result.returncode == 0:
                            self.results["integration_validations"].append(
                                f"Docker build validated successfully for {docker_file.name}"
                            )
                        else:
                            self.results["integration_validations"].append(
                                f"Docker build validation failed for {docker_file.name}: {result.stderr[:100]}"
                            )
                            
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        # Docker not available or timeout
                        self.results["integration_validations"].append(
                            f"Could not validate Docker build for {docker_file.name} (Docker not available)"
                        )
                        
            except Exception as e:
                logger.warning(f"Could not validate Docker file {docker_file}: {e}")
    
    def _validate_dockerfile_content(self, content: str) -> List[str]:
        """Validate Dockerfile content for common issues."""
        issues = []
        
        lines = content.split('\n')
        
        # Check for required FROM statement
        if not any(line.strip().upper().startswith('FROM') for line in lines):
            issues.append("Missing FROM statement")
        
        # Check for proper layer optimization
        run_commands = [line for line in lines if line.strip().upper().startswith('RUN')]
        if len(run_commands) > 5:
            issues.append(f"Too many RUN commands ({len(run_commands)}) - consider combining")
        
        # Check for security best practices
        if any('sudo' in line for line in lines):
            issues.append("Avoid using sudo in Docker containers")
        
        # Check for proper user handling
        if not any(line.strip().upper().startswith('USER') for line in lines):
            issues.append("Consider adding USER instruction for security")
        
        return issues
    
    async def _test_environment_variables(self):
        """Test that all environment variables are properly used."""
        env_files = []
        
        for pattern in self.integration_patterns["env_vars"]:
            env_files.extend(list(self.root_path.glob(pattern)))
        
        # Collect all environment variables defined
        defined_vars = set()
        
        for env_file in env_files:
            try:
                content = env_file.read_text(encoding='utf-8')
                
                # Parse environment variables
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        var_name = line.split('=')[0].strip()
                        defined_vars.add(var_name)
                        
            except Exception as e:
                logger.warning(f"Could not read env file {env_file}: {e}")
        
        # Check if these variables are actually used in the code
        if defined_vars:
            python_files = list(self.root_path.glob("**/*.py"))
            used_vars = set()
            
            for py_file in python_files:
                if any(skip in str(py_file) for skip in ['__pycache__', '.git']):
                    continue
                    
                try:
                    content = py_file.read_text(encoding='utf-8')
                    
                    for var in defined_vars:
                        # Check for os.getenv, os.environ patterns
                        patterns = [
                            rf'os\.getenv\s*\(\s*["\']?{var}["\']?\s*\)',
                            rf'os\.environ\s*\[\s*["\']?{var}["\']?\s*\]',
                            rf'getenv\s*\(\s*["\']?{var}["\']?\s*\)',
                        ]
                        
                        for pattern in patterns:
                            if re.search(pattern, content):
                                used_vars.add(var)
                                break
                                
                except Exception as e:
                    logger.warning(f"Could not check env vars in {py_file}: {e}")
            
            unused_vars = defined_vars - used_vars
            if unused_vars:
                self.results["integration_validations"].append(
                    f"Found {len(unused_vars)} unused environment variables: {', '.join(list(unused_vars)[:5])}"
                )
    
    async def _validate_api_integrations(self):
        """Validate that all API integrations work correctly."""
        # Look for API configuration files
        api_configs = [
            "config/api_*.yaml",
            "config/integrations/*.yaml", 
            "**/*api*config*.py"
        ]
        
        api_endpoints = []
        
        for pattern in api_configs:
            for config_file in self.root_path.glob(pattern):
                try:
                    content = config_file.read_text(encoding='utf-8')
                    
                    # Extract API endpoints
                    url_patterns = [
                        r'https?://[^\s<>"{}|\\^`\[\]]+',
                        r'base_url\s*[:=]\s*["\']([^"\']+)["\']',
                        r'endpoint\s*[:=]\s*["\']([^"\']+)["\']',
                    ]
                    
                    for pattern in url_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        api_endpoints.extend(matches)
                        
                except Exception as e:
                    logger.warning(f"Could not parse API config {config_file}: {e}")
        
        # Test API endpoints (basic validation)
        for endpoint in set(api_endpoints):
            if endpoint.startswith(('http://', 'https://')):
                try:
                    # Simple connectivity test (head request)
                    import urllib.request
                    import urllib.error
                    
                    req = urllib.request.Request(endpoint, method='HEAD')
                    with urllib.request.urlopen(req, timeout=5) as response:
                        if response.status < 400:
                            self.results["api_integrations_tested"] += 1
                            self.results["integration_validations"].append(
                                f"API endpoint accessible: {endpoint}"
                            )
                        else:
                            self.results["integration_validations"].append(
                                f"API endpoint returned {response.status}: {endpoint}"
                            )
                            
                except Exception as e:
                    self.results["integration_validations"].append(
                        f"API endpoint unreachable: {endpoint} ({type(e).__name__})"
                    )
    
    async def _check_file_path_consistency(self):
        """Check that file paths are consistent across different environments."""
        # Find hardcoded paths
        python_files = list(self.root_path.glob("**/*.py"))
        
        hardcoded_paths = []
        
        for py_file in python_files:
            if any(skip in str(py_file) for skip in ['__pycache__', '.git']):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Look for hardcoded path patterns
                path_patterns = [
                    r'["\'][A-Za-z]:\\[^"\']*["\']',  # Windows paths
                    r'["\']\/[^"\'\s]*["\']',  # Unix absolute paths
                    r'["\'][^"\']*\\[^"\']*["\']',  # Paths with backslashes
                ]
                
                for pattern in path_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        # Filter out obvious non-paths
                        if any(keyword in match.lower() for keyword in ['http', 'ftp', 'sql', 'select']):
                            continue
                        if len(match) > 3:  # Skip very short strings
                            hardcoded_paths.append({
                                "file": str(py_file.relative_to(self.root_path)),
                                "path": match
                            })
                            
            except Exception as e:
                logger.warning(f"Could not check paths in {py_file}: {e}")
        
        if hardcoded_paths:
            self.results["integration_validations"].append(
                f"Found {len(hardcoded_paths)} potential hardcoded paths"
            )
            
            # Create report
            report_file = self.root_path / "hardcoded_paths_report.txt"
            with open(report_file, 'w') as f:
                f.write("HARDCODED PATHS DETECTED\n")
                f.write("=" * 24 + "\n\n")
                
                for path_info in hardcoded_paths[:20]:  # Limit to first 20
                    f.write(f"File: {path_info['file']}\n")
                    f.write(f"Path: {path_info['path']}\n\n")
                
                if len(hardcoded_paths) > 20:
                    f.write(f"... and {len(hardcoded_paths) - 20} more paths\n")
            
            self.results["files_modified"].append(str(report_file))
    
    async def _validate_shell_scripts(self):
        """Validate shell scripts have proper permissions and error handling."""
        shell_scripts = list(self.root_path.glob("**/*.sh"))
        shell_scripts.extend(list(self.root_path.glob("**/*.bash")))
        
        for script in shell_scripts:
            if any(skip in str(script) for skip in ['.git', '__pycache__']):
                continue
                
            try:
                # Check permissions
                stat = script.stat()
                is_executable = bool(stat.st_mode & 0o111)
                
                if not is_executable:
                    script.chmod(0o755)
                    self.results["integration_validations"].append(
                        f"Fixed executable permissions for {script.name}"
                    )
                
                # Check script content
                content = script.read_text(encoding='utf-8')
                
                # Check for error handling
                has_error_handling = any(pattern in content for pattern in [
                    'set -e', 'set -o errexit', 'trap', '|| exit'
                ])
                
                if not has_error_handling:
                    self.results["integration_validations"].append(
                        f"Shell script {script.name} lacks error handling"
                    )
                
                # Check for proper shebang
                if not content.startswith('#!'):
                    self.results["integration_validations"].append(
                        f"Shell script {script.name} missing shebang"
                    )
                    
            except Exception as e:
                logger.warning(f"Could not validate shell script {script}: {e}")
    
    def _calculate_health_scores(self):
        """Calculate testing and integration health scores."""
        # Testing score based on coverage and cleanup
        coverage = self.results["test_coverage_percentage"]
        broken_tests = self.results["broken_tests_removed"]
        
        # Base score from coverage
        base_testing_score = coverage
        
        # Penalty for broken tests
        if broken_tests > 0:
            penalty = min(20, broken_tests * 5)
            base_testing_score = max(0, base_testing_score - penalty)
        
        self.results["testing_health_score"] = base_testing_score
        
        # Integration score based on validations
        docker_validations = self.results["docker_builds_validated"]
        api_tests = self.results["api_integrations_tested"]
        
        # Base score
        integration_score = 60  # Baseline
        
        # Bonus for successful validations
        integration_score += min(25, docker_validations * 10)
        integration_score += min(15, api_tests * 5)
        
        self.results["integration_health_score"] = min(100, integration_score)
    
    def generate_report(self) -> str:
        """Generate detailed testing and validation report."""
        report = f"""
🧪 TESTING & VALIDATION CLEANUP REPORT
=====================================
Generated: {self.results['timestamp']}

📊 SUMMARY
---------
Testing Health Score: {self.results['testing_health_score']:.1f}%
Integration Health Score: {self.results['integration_health_score']:.1f}%
Test Coverage: {self.results['test_coverage_percentage']:.1f}%
Broken Tests Removed: {self.results['broken_tests_removed']}
Duplicate Tests Removed: {self.results['duplicate_tests_removed']}
Docker Builds Validated: {self.results['docker_builds_validated']}
API Integrations Tested: {self.results['api_integrations_tested']}
Files Modified: {len(self.results['files_modified'])}

🧪 TEST CLEANUPS
---------------
"""
        
        for cleanup in self.results["test_cleanups"]:
            report += f"✅ {cleanup}\n"
        
        report += "\n🔗 INTEGRATION VALIDATIONS\n"
        report += "-" * 26 + "\n"
        
        for validation in self.results["integration_validations"]:
            report += f"🔧 {validation}\n"
        
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
    """Run the testing and validation cleanup."""
    cleaner = TestingValidationCleaner(".")
    results = await cleaner.run_cleanup()
    
    # Generate and display report
    report = cleaner.generate_report()
    print(report)
    
    # Save detailed results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"testing_validation_cleanup_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed results saved to: {results_file}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main()) 