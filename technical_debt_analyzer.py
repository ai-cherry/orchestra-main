import logging
logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""
Technical Debt Analyzer - Comprehensive analysis of code quality issues and refactoring opportunities
"""

import ast
import os
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Set
import importlib.util

class TechnicalDebtAnalyzer:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.findings = {
            "timestamp": datetime.now().isoformat(),
            "critical_issues": [],
            "high_priority": [],
            "medium_priority": [],
            "low_priority": [],
            "metrics": defaultdict(int),
            "refactoring_opportunities": []
        }
        
        # Skip directories
        self.skip_dirs = {
            "__pycache__", ".git", "node_modules", ".venv", "venv",
            "dist", "build", ".pytest_cache", ".mypy_cache", "logs",
            ""
        }
        
        # Code smell patterns
        self.code_smell_patterns = {
            "god_class": {"max_methods": 20, "max_lines": 500},
            "long_method": {"max_lines": 50},
            "long_parameter_list": {"max_params": 5},
            "duplicate_code": {"min_similarity": 0.8},
            "dead_code": {"unused_threshold": 0}
        }
        
    def analyze_codebase(self) -> Dict:
        """Perform comprehensive technical debt analysis"""
        print("🔍 TECHNICAL DEBT ANALYZER")
        print("=" * 80)
        print("Analyzing codebase for technical debt and improvement opportunities...\n")
        
        # Phase 1: Code structure analysis
        self._analyze_code_structure()
        
        # Phase 2: Dependency analysis
        self._analyze_dependencies()
        
        # Phase 3: Code quality metrics
        self._analyze_code_quality()
        
        # Phase 4: Testing coverage
        self._analyze_test_coverage()
        
        # Phase 5: Performance analysis
        self._analyze_performance_issues()
        
        # Phase 6: Security analysis
        self._analyze_security_issues()
        
        # Phase 7: Documentation analysis
        self._analyze_documentation()
        
        # Phase 8: Prioritize findings
        self._prioritize_findings()
        
        return self.findings
    
    def _analyze_code_structure(self):
        """Analyze code structure for complexity and smells"""
        print("📊 Analyzing code structure...")
        
        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Skip if file has syntax errors
                try:
                    tree = ast.parse(content)
                except SyntaxError:
                    continue
                
                # Analyze file
                file_analysis = self._analyze_python_file(py_file, content, tree)
                
                # Add findings based on severity
                for finding in file_analysis:
                    if finding['severity'] == 'critical':
                        self.findings['critical_issues'].append(finding)
                    elif finding['severity'] == 'high':
                        self.findings['high_priority'].append(finding)
                    elif finding['severity'] == 'medium':
                        self.findings['medium_priority'].append(finding)
                    else:
                        self.findings['low_priority'].append(finding)
                        
            except Exception as e:
                continue
    
    def _analyze_python_file(self, file_path: Path, content: str, tree: ast.AST) -> List[Dict]:
        """Analyze individual Python file for issues"""
        findings = []
        lines = content.splitlines()
        relative_path = file_path.relative_to(self.root_path)
        
        # Check file size
        if len(lines) > 1000:
            findings.append({
                "type": "large_file",
                "file": str(relative_path),
                "severity": "medium",
                "issue": f"File has {len(lines)} lines (recommended max: 1000)",
                "recommendation": "Split into smaller, focused modules",
                "effort": "4-8 hours",
                "impact": "Improves maintainability and testability"
            })
        
        # Analyze classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_findings = self._analyze_class(node, lines, relative_path)
                findings.extend(class_findings)
            elif isinstance(node, ast.FunctionDef):
                func_findings = self._analyze_function(node, lines, relative_path)
                findings.extend(func_findings)
        
        # Check for code smells
        smell_findings = self._check_code_smells(content, relative_path)
        findings.extend(smell_findings)
        
        return findings
    
    def _analyze_class(self, class_node: ast.ClassDef, lines: List[str], file_path: Path) -> List[Dict]:
        """Analyze class for complexity and design issues"""
        findings = []
        
        # Count methods
        methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef)]
        if len(methods) > self.code_smell_patterns["god_class"]["max_methods"]:
            findings.append({
                "type": "god_class",
                "file": str(file_path),
                "class": class_node.name,
                "severity": "high",
                "issue": f"Class has {len(methods)} methods (max recommended: {self.code_smell_patterns['god_class']['max_methods']})",
                "recommendation": "Apply Single Responsibility Principle - split into focused classes",
                "effort": "1-2 days",
                "impact": "Significantly improves maintainability and testability"
            })
        
        # Check for missing docstrings
        if not ast.get_docstring(class_node):
            findings.append({
                "type": "missing_docstring",
                "file": str(file_path),
                "class": class_node.name,
                "severity": "low",
                "issue": "Class lacks docstring",
                "recommendation": "Add comprehensive class documentation",
                "effort": "30 minutes",
                "impact": "Improves code understanding and API documentation"
            })
        
        return findings
    
    def _analyze_function(self, func_node: ast.FunctionDef, lines: List[str], file_path: Path) -> List[Dict]:
        """Analyze function for complexity issues"""
        findings = []
        
        # Calculate function length
        if hasattr(func_node, 'end_lineno'):
            func_length = func_node.end_lineno - func_node.lineno
            if func_length > self.code_smell_patterns["long_method"]["max_lines"]:
                findings.append({
                    "type": "long_method",
                    "file": str(file_path),
                    "function": func_node.name,
                    "severity": "medium",
                    "issue": f"Function has {func_length} lines (max recommended: {self.code_smell_patterns['long_method']['max_lines']})",
                    "recommendation": "Extract smaller functions with single responsibilities",
                    "effort": "2-4 hours",
                    "impact": "Improves readability and testability"
                })
        
        # Check parameter count
        param_count = len(func_node.args.args)
        if param_count > self.code_smell_patterns["long_parameter_list"]["max_params"]:
            findings.append({
                "type": "long_parameter_list",
                "file": str(file_path),
                "function": func_node.name,
                "severity": "medium",
                "issue": f"Function has {param_count} parameters (max recommended: {self.code_smell_patterns['long_parameter_list']['max_params']})",
                "recommendation": "Use parameter objects or builder pattern",
                "effort": "1-2 hours",
                "impact": "Improves function signature clarity"
            })
        
        # Check cyclomatic complexity
        complexity = self._calculate_cyclomatic_complexity(func_node)
        if complexity > 10:
            findings.append({
                "type": "high_complexity",
                "file": str(file_path),
                "function": func_node.name,
                "severity": "high",
                "issue": f"Cyclomatic complexity is {complexity} (max recommended: 10)",
                "recommendation": "Simplify logic, extract methods, use early returns",
                "effort": "4-8 hours",
                "impact": "Significantly improves maintainability and reduces bugs"
            })
        
        return findings
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def _check_code_smells(self, content: str, file_path: Path) -> List[Dict]:
        """Check for various code smells"""
        findings = []
        lines = content.splitlines()
        
        # Check for hardcoded values
        hardcoded_patterns = [
            (r'["\']https?://[^"\']+["\']', "hardcoded URL"),
            (r'["\'][0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}["\']', "hardcoded IP"),
            (r'(password|secret|key)\s*=\s*["\'][^"\']+["\']', "hardcoded credential", "critical"),
        ]
        
        for i, line in enumerate(lines):
            for pattern, smell_type, *severity in hardcoded_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({
                        "type": "hardcoded_value",
                        "file": str(file_path),
                        "line": i + 1,
                        "severity": severity[0] if severity else "medium",
                        "issue": f"Found {smell_type}",
                        "recommendation": "Move to configuration file or environment variable",
                        "effort": "30 minutes",
                        "impact": "Improves security and configuration management"
                    })
        
        # Check for TODO/FIXME comments
        todo_count = sum(1 for line in lines if 'TODO' in line or 'FIXME' in line)
        if todo_count > 5:
            findings.append({
                "type": "technical_debt_markers",
                "file": str(file_path),
                "severity": "low",
                "issue": f"Found {todo_count} TODO/FIXME comments",
                "recommendation": "Address technical debt or create tickets",
                "effort": "Variable",
                "impact": "Reduces accumulated technical debt"
            })
        
        # Check for print statements (should use logging)
        print_count = sum(1 for line in lines if re.match(r'^\s*print\s*\(', line))
        if print_count > 0:
            findings.append({
                "type": "print_statements",
                "file": str(file_path),
                "severity": "low",
                "issue": f"Found {print_count} print statements",
                "recommendation": "Replace with proper logging",
                "effort": "1 hour",
                "impact": "Improves debugging and production monitoring"
            })
        
        return findings
    
    def _analyze_dependencies(self):
        """Analyze project dependencies"""
        print("📦 Analyzing dependencies...")
        
        # Check requirements files
        req_files = list(Path(self.root_path).glob("requirements*.txt"))
        
        if not req_files:
            self.findings['high_priority'].append({
                "type": "missing_requirements",
                "severity": "high",
                "issue": "No requirements.txt file found",
                "recommendation": "Create requirements.txt with pinned versions",
                "effort": "1 hour",
                "impact": "Essential for reproducible deployments"
            })
        else:
            for req_file in req_files:
                self._analyze_requirements_file(req_file)
    
    def _analyze_requirements_file(self, req_file: Path):
        """Analyze requirements file for issues"""
        try:
            with open(req_file, 'r') as f:
                lines = f.readlines()
            
            unpinned = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '==' not in line and '>=' not in line:
                        unpinned.append(line)
            
            if unpinned:
                self.findings['medium_priority'].append({
                    "type": "unpinned_dependencies",
                    "file": str(req_file.relative_to(self.root_path)),
                    "severity": "medium",
                    "issue": f"Found {len(unpinned)} unpinned dependencies",
                    "recommendation": "Pin all dependencies to specific versions",
                    "effort": "1 hour",
                    "impact": "Ensures reproducible builds and prevents breaking changes",
                    "details": unpinned[:5]  # Show first 5
                })
        except Exception:
            pass
    
    def _analyze_code_quality(self):
        """Analyze overall code quality metrics"""
        print("📈 Analyzing code quality metrics...")
        
        # Check for duplicate code patterns
        self._check_duplicate_code()
        
        # Check for inconsistent naming
        self._check_naming_conventions()
        
        # Check error handling
        self._check_error_handling()
    
    def _check_duplicate_code(self):
        """Check for duplicate code patterns"""
        # This is a simplified check - in practice, use tools like pylint or flake8
        file_hashes = defaultdict(list)
        
        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                # Simple hash-based duplicate detection
                content_hash = hash(content)
                file_hashes[content_hash].append(py_file)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                continue
        
        # Report exact duplicates
        for hash_val, files in file_hashes.items():
            if len(files) > 1:
                self.findings['high_priority'].append({
                    "type": "duplicate_files",
                    "severity": "high",
                    "issue": f"Found {len(files)} identical files",
                    "recommendation": "Remove duplicates or extract to shared module",
                    "effort": "1-2 hours",
                    "impact": "Reduces maintenance burden",
                    "files": [str(f.relative_to(self.root_path)) for f in files]
                })
    
    def _check_naming_conventions(self):
        """Check for naming convention violations"""
        inconsistencies = defaultdict(int)
        
        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                            inconsistencies['function_names'] += 1
                    elif isinstance(node, ast.ClassDef):
                        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                            inconsistencies['class_names'] += 1
            except:
                continue
        
        if inconsistencies:
            self.findings['medium_priority'].append({
                "type": "naming_violations",
                "severity": "medium",
                "issue": f"Found naming convention violations",
                "recommendation": "Apply PEP 8 naming conventions consistently",
                "effort": "2-4 hours",
                "impact": "Improves code consistency and readability",
                "details": dict(inconsistencies)
            })
    
    def _check_error_handling(self):
        """Check for proper error handling"""
        bare_except_count = 0
        missing_error_handling = 0
        
        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ExceptHandler):
                        if node.type is None:  # bare except
                            bare_except_count += 1
            except:
                continue
        
        if bare_except_count > 0:
            self.findings['high_priority'].append({
                "type": "poor_error_handling",
                "severity": "high",
                "issue": f"Found {bare_except_count} bare except clauses",
                "recommendation": "Use specific exception types and proper error handling",
                "effort": "4-8 hours",
                "impact": "Prevents silent failures and improves debugging"
            })
    
    def _analyze_test_coverage(self):
        """Analyze test coverage"""
        print("🧪 Analyzing test coverage...")
        
        # Count test files vs source files
        test_files = list(Path(self.root_path).rglob("test_*.py"))
        test_files.extend(list(Path(self.root_path).rglob("*_test.py")))
        source_files = list(self._get_python_files())
        
        # Filter out test files from source files
        source_files = [f for f in source_files if not any(t in str(f) for t in ['test_', '_test.py', '/tests/'])]
        
        coverage_ratio = len(test_files) / len(source_files) if source_files else 0
        
        if coverage_ratio < 0.5:
            self.findings['critical_issues'].append({
                "type": "insufficient_test_coverage",
                "severity": "critical",
                "issue": f"Test coverage ratio is {coverage_ratio:.1%} (found {len(test_files)} test files for {len(source_files)} source files)",
                "recommendation": "Implement comprehensive test suite with >80% coverage",
                "effort": "1-2 weeks",
                "impact": "Critical for reliability and refactoring confidence"
            })
    
    def _analyze_performance_issues(self):
        """Analyze potential performance issues"""
        print("⚡ Analyzing performance issues...")
        
        performance_issues = []
        
        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                # Check for common performance anti-patterns
                if 'time.sleep' in content:
                    performance_issues.append({
                        "file": str(py_file.relative_to(self.root_path)),
                        "issue": "Uses time.sleep - consider async alternatives"
                    })
                
                # Check for inefficient string concatenation in loops
                if re.search(r'for .+ in .+:\s*\n\s*\w+\s*\+=\s*["\']', content):
                    performance_issues.append({
                        "file": str(py_file.relative_to(self.root_path)),
                        "issue": "String concatenation in loop - use join() or list comprehension"
                    })
            except:
                continue
        
        if performance_issues:
            self.findings['medium_priority'].append({
                "type": "performance_issues",
                "severity": "medium",
                "issue": f"Found {len(performance_issues)} potential performance issues",
                "recommendation": "Optimize identified performance bottlenecks",
                "effort": "1-2 days",
                "impact": "Improves application performance",
                "details": performance_issues[:5]
            })
    
    def _analyze_security_issues(self):
        """Analyze security issues"""
        print("🔒 Analyzing security issues...")
        
        security_issues = []
        
        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                # Check for SQL injection risks
                if re.search(r'(execute|cursor)\s*\(\s*["\'].*%[s|d]', content):
                    security_issues.append({
                        "file": str(py_file.relative_to(self.root_path)),
                        "issue": "Potential SQL injection - use parameterized queries"
                    })
                
                # Check for eval usage
                if 'eval(' in content:
                    security_issues.append({
                        "file": str(py_file.relative_to(self.root_path)),
                        "issue": "Uses eval() - security risk"
                    })
            except:
                continue
        
        if security_issues:
            self.findings['critical_issues'].append({
                "type": "security_vulnerabilities",
                "severity": "critical",
                "issue": f"Found {len(security_issues)} potential security issues",
                "recommendation": "Address security vulnerabilities immediately",
                "effort": "1-2 days",
                "impact": "Critical for application security",
                "details": security_issues
            })
    
    def _analyze_documentation(self):
        """Analyze documentation quality"""
        print("📚 Analyzing documentation...")
        
        # Check for README
        readme_files = list(Path(self.root_path).glob("README*"))
        if not readme_files:
            self.findings['high_priority'].append({
                "type": "missing_documentation",
                "severity": "high",
                "issue": "No README file found",
                "recommendation": "Create comprehensive README with setup instructions",
                "effort": "2-4 hours",
                "impact": "Essential for onboarding and project understanding"
            })
        
        # Check for docstrings
        missing_docstrings = 0
        total_functions = 0
        
        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        total_functions += 1
                        if not ast.get_docstring(node):
                            missing_docstrings += 1
            except:
                continue
        
        if total_functions > 0:
            docstring_coverage = (total_functions - missing_docstrings) / total_functions
            if docstring_coverage < 0.5:
                self.findings['medium_priority'].append({
                    "type": "poor_documentation",
                    "severity": "medium",
                    "issue": f"Only {docstring_coverage:.1%} of functions/classes have docstrings",
                    "recommendation": "Add comprehensive docstrings to all public APIs",
                    "effort": "1 week",
                    "impact": "Significantly improves code maintainability"
                })
    
    def _get_python_files(self) -> List[Path]:
        """Get all Python files in the project"""
        python_files = []
        for root, dirs, files in os.walk(self.root_path):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        return python_files
    
    def _prioritize_findings(self):
        """Prioritize findings based on risk and value"""
        # Calculate metrics
        self.findings['metrics'] = {
            'total_issues': (
                len(self.findings['critical_issues']) +
                len(self.findings['high_priority']) +
                len(self.findings['medium_priority']) +
                len(self.findings['low_priority'])
            ),
            'critical_count': len(self.findings['critical_issues']),
            'high_count': len(self.findings['high_priority']),
            'medium_count': len(self.findings['medium_priority']),
            'low_count': len(self.findings['low_priority'])
        }
        
        # Create refactoring roadmap
        self._create_refactoring_roadmap()
    
    def _create_refactoring_roadmap(self):
        """Create prioritized refactoring roadmap"""
        roadmap = []
        
        # Phase 1: Critical issues (1-2 weeks)
        if self.findings['critical_issues']:
            roadmap.append({
                "phase": 1,
                "name": "Critical Issues Resolution",
                "duration": "1-2 weeks",
                "issues": len(self.findings['critical_issues']),
                "focus": "Security vulnerabilities, missing tests, broken functionality",
                "impact": "Addresses immediate risks and stability concerns"
            })
        
        # Phase 2: High priority (2-4 weeks)
        if self.findings['high_priority']:
            roadmap.append({
                "phase": 2,
                "name": "High Priority Improvements",
                "duration": "2-4 weeks",
                "issues": len(self.findings['high_priority']),
                "focus": "Code complexity, duplicate code, poor error handling",
                "impact": "Significantly improves maintainability"
            })
        
        # Phase 3: Medium priority (4-6 weeks)
        if self.findings['medium_priority']:
            roadmap.append({
                "phase": 3,
                "name": "Code Quality Enhancement",
                "duration": "4-6 weeks",
                "issues": len(self.findings['medium_priority']),
                "focus": "Naming conventions, documentation, performance",
                "impact": "Improves developer experience and code consistency"
            })
        
        # Phase 4: Low priority (ongoing)
        if self.findings['low_priority']:
            roadmap.append({
                "phase": 4,
                "name": "Continuous Improvement",
                "duration": "Ongoing",
                "issues": len(self.findings['low_priority']),
                "focus": "Minor improvements, style issues, nice-to-haves",
                "impact": "Polishes codebase over time"
            })
        
        self.findings['refactoring_roadmap'] = roadmap

def generate_report(findings: Dict):
    """Generate comprehensive technical debt report"""
    print("\n" + "=" * 80)
    print("TECHNICAL DEBT ANALYSIS REPORT")
    print("=" * 80)
    
    metrics = findings['metrics']
    print(f"\n📊 SUMMARY:")
    print(f"  Total Issues Found: {metrics['total_issues']}")
    print(f"  Critical: {metrics['critical_count']}")
    print(f"  High: {metrics['high_count']}")
    print(f"  Medium: {metrics['medium_count']}")
    print(f"  Low: {metrics['low_count']}")
    
    # Critical issues
    if findings['critical_issues']:
        print(f"\n🚨 CRITICAL ISSUES (Immediate Action Required):")
        for issue in findings['critical_issues'][:5]:
            print(f"\n  Type: {issue['type']}")
            print(f"  Issue: {issue['issue']}")
            print(f"  Recommendation: {issue['recommendation']}")
            print(f"  Effort: {issue['effort']}")
            print(f"  Impact: {issue['impact']}")
    
    # Refactoring roadmap
    if findings.get('refactoring_roadmap'):
        print(f"\n📋 REFACTORING ROADMAP:")
        for phase in findings['refactoring_roadmap']:
            print(f"\n  Phase {phase['phase']}: {phase['name']}")
            print(f"    Duration: {phase['duration']}")
            print(f"    Issues to address: {phase['issues']}")
            print(f"    Focus: {phase['focus']}")
            print(f"    Impact: {phase['impact']}")
    
    # Save detailed report
    report_file = f"technical_debt_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(findings, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    print("\n💡 QUICK WINS:")
    print("  1. Add requirements.txt with pinned versions")
    print("  2. Replace print statements with logging")
    print("  3. Fix bare except clauses")
    print("  4. Add docstrings to public APIs")
    print("  5. Remove duplicate files")

def main():
    """Run technical debt analysis"""
    analyzer = TechnicalDebtAnalyzer()
    findings = analyzer.analyze_codebase()
    generate_report(findings)

if __name__ == "__main__":
    main()