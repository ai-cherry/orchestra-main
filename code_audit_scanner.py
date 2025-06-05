#!/usr/bin/env python3
"""
Code Audit Scanner - Systematic analysis for syntax errors, formatting, and code quality issues
"""

import os
import json
import re
import ast
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple, Set

class CodeAuditScanner:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.results = {
            "scan_metadata": {
                "timestamp": datetime.now().isoformat(),
                "root_path": str(self.root_path)
            },
            "file_inventory": defaultdict(list),
            "syntax_errors": [],
            "formatting_issues": [],
            "naming_violations": [],
            "indentation_issues": [],
            "file_statistics": defaultdict(int)
        }
        
        # File extensions to analyze
        self.language_extensions = {
            "python": [".py"],
            "javascript": [".js", ".jsx"],
            "typescript": [".ts", ".tsx"],
            "shell": [".sh"],
            "yaml": [".yml", ".yaml"],
            "json": [".json"],
            "html": [".html"],
            "css": [".css"],
            "sql": [".sql"],
            "markdown": [".md"],
            "dockerfile": ["Dockerfile", ".dockerfile"]
        }
        
        # Directories to skip
        self.skip_dirs = {
            "__pycache__", ".git", "node_modules", ".venv", "venv",
            "dist", "build", ".pytest_cache", ".mypy_cache", "logs",
            ".idea", ".vscode", "coverage", ".coverage"
        }
        
        # Common naming convention patterns
        self.naming_patterns = {
            "python": {
                "function": re.compile(r'^[a-z_][a-z0-9_]*$'),
                "class": re.compile(r'^[A-Z][a-zA-Z0-9]*$'),
                "constant": re.compile(r'^[A-Z][A-Z0-9_]*$'),
                "variable": re.compile(r'^[a-z_][a-z0-9_]*$')
            },
            "javascript": {
                "function": re.compile(r'^[a-z][a-zA-Z0-9]*$'),
                "class": re.compile(r'^[A-Z][a-zA-Z0-9]*$'),
                "constant": re.compile(r'^[A-Z][A-Z0-9_]*$'),
                "variable": re.compile(r'^[a-z][a-zA-Z0-9]*$')
            }
        }

    def scan_codebase(self):
        """Main entry point for scanning the codebase"""
        print(f"Starting code audit scan at: {self.root_path}")
        print("=" * 80)
        
        # Step 1: Inventory files
        self._inventory_files()
        
        # Step 2: Analyze each file type
        self._analyze_python_files()
        self._analyze_javascript_typescript_files()
        self._analyze_shell_scripts()
        self._analyze_json_yaml_files()
        
        # Step 3: Generate summary report
        self._generate_summary()
        
        return self.results

    def _inventory_files(self):
        """Create an inventory of all files by type"""
        print("\n📁 Creating file inventory...")
        
        for root, dirs, files in os.walk(self.root_path):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            
            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.root_path)
                
                # Categorize by extension
                ext = file_path.suffix.lower()
                file_categorized = False
                
                for lang, extensions in self.language_extensions.items():
                    if ext in extensions or file in extensions:
                        self.results["file_inventory"][lang].append(str(relative_path))
                        self.results["file_statistics"][lang] += 1
                        file_categorized = True
                        break
                
                if not file_categorized and ext:
                    self.results["file_inventory"]["other"].append(str(relative_path))
                    self.results["file_statistics"]["other"] += 1

        # Print inventory summary
        print("\nFile inventory summary:")
        for lang, count in sorted(self.results["file_statistics"].items()):
            if count > 0:
                print(f"  {lang}: {count} files")

    def _analyze_python_files(self):
        """Analyze Python files for syntax and style issues"""
        python_files = self.results["file_inventory"].get("python", [])
        if not python_files:
            return
            
        print(f"\n🐍 Analyzing {len(python_files)} Python files...")
        
        for file_path in python_files:
            full_path = self.root_path / file_path
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check syntax
                try:
                    tree = ast.parse(content, filename=str(file_path))
                    # If parsing succeeds, check for style issues
                    self._check_python_style(file_path, content, tree)
                except SyntaxError as e:
                    self.results["syntax_errors"].append({
                        "file": file_path,
                        "language": "python",
                        "line": e.lineno,
                        "error": str(e),
                        "severity": "error"
                    })
                    
            except Exception as e:
                self.results["syntax_errors"].append({
                    "file": file_path,
                    "language": "python",
                    "error": f"Failed to read file: {str(e)}",
                    "severity": "error"
                })

    def _check_python_style(self, file_path: str, content: str, tree: ast.AST):
        """Check Python style issues"""
        lines = content.split('\n')
        
        # Check indentation consistency
        indent_chars = set()
        for i, line in enumerate(lines, 1):
            if line and line[0] in ' \t':
                indent = re.match(r'^[ \t]+', line)
                if indent:
                    indent_chars.add(indent.group()[0])
                    
        if len(indent_chars) > 1:
            self.results["indentation_issues"].append({
                "file": file_path,
                "issue": "Mixed tabs and spaces",
                "severity": "warning"
            })
        
        # Check line length
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                self.results["formatting_issues"].append({
                    "file": file_path,
                    "line": i,
                    "issue": f"Line too long ({len(line)} > 120 characters)",
                    "severity": "warning"
                })
        
        # Check naming conventions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not self.naming_patterns["python"]["function"].match(node.name):
                    self.results["naming_violations"].append({
                        "file": file_path,
                        "line": node.lineno,
                        "type": "function",
                        "name": node.name,
                        "issue": "Function name should be snake_case",
                        "severity": "warning"
                    })
            elif isinstance(node, ast.ClassDef):
                if not self.naming_patterns["python"]["class"].match(node.name):
                    self.results["naming_violations"].append({
                        "file": file_path,
                        "line": node.lineno,
                        "type": "class",
                        "name": node.name,
                        "issue": "Class name should be PascalCase",
                        "severity": "warning"
                    })

    def _analyze_javascript_typescript_files(self):
        """Analyze JavaScript/TypeScript files"""
        js_files = (self.results["file_inventory"].get("javascript", []) + 
                   self.results["file_inventory"].get("typescript", []))
        
        if not js_files:
            return
            
        print(f"\n📜 Analyzing {len(js_files)} JavaScript/TypeScript files...")
        
        for file_path in js_files:
            full_path = self.root_path / file_path
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self._check_javascript_style(file_path, content)
            except Exception as e:
                self.results["syntax_errors"].append({
                    "file": file_path,
                    "language": "javascript/typescript",
                    "error": f"Failed to read file: {str(e)}",
                    "severity": "error"
                })

    def _check_javascript_style(self, file_path: str, content: str):
        """Check JavaScript/TypeScript style issues"""
        lines = content.split('\n')
        
        # Basic syntax checks
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            self.results["syntax_errors"].append({
                "file": file_path,
                "language": "javascript",
                "error": f"Mismatched braces: {open_braces} opening, {close_braces} closing",
                "severity": "error"
            })
        
        # Check for common issues
        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 120:
                self.results["formatting_issues"].append({
                    "file": file_path,
                    "line": i,
                    "issue": f"Line too long ({len(line)} > 120 characters)",
                    "severity": "warning"
                })
            
            # Check for console.log statements
            if 'console.log' in line and not line.strip().startswith('//'):
                self.results["formatting_issues"].append({
                    "file": file_path,
                    "line": i,
                    "issue": "console.log statement found",
                    "severity": "info"
                })

    def _analyze_shell_scripts(self):
        """Analyze shell scripts"""
        shell_files = self.results["file_inventory"].get("shell", [])
        if not shell_files:
            return
            
        print(f"\n🐚 Analyzing {len(shell_files)} shell scripts...")
        
        for file_path in shell_files:
            full_path = self.root_path / file_path
            try:
                # Use shellcheck if available
                result = subprocess.run(
                    ['shellcheck', '-f', 'json', str(full_path)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and result.stdout:
                    issues = json.loads(result.stdout)
                    for issue in issues:
                        self.results["syntax_errors"].append({
                            "file": file_path,
                            "language": "shell",
                            "line": issue.get("line"),
                            "error": issue.get("message"),
                            "severity": issue.get("level", "warning")
                        })
            except (subprocess.SubprocessError, FileNotFoundError):
                # Fallback to basic checks if shellcheck not available
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content.startswith('#!/'):
                        self.results["formatting_issues"].append({
                            "file": file_path,
                            "line": 1,
                            "issue": "Missing shebang line",
                            "severity": "warning"
                        })

    def _analyze_json_yaml_files(self):
        """Analyze JSON and YAML files"""
        json_files = self.results["file_inventory"].get("json", [])
        yaml_files = self.results["file_inventory"].get("yaml", [])
        
        if json_files:
            print(f"\n📋 Analyzing {len(json_files)} JSON files...")
            for file_path in json_files:
                full_path = self.root_path / file_path
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    self.results["syntax_errors"].append({
                        "file": file_path,
                        "language": "json",
                        "line": e.lineno if hasattr(e, 'lineno') else None,
                        "error": str(e),
                        "severity": "error"
                    })
                except Exception as e:
                    self.results["syntax_errors"].append({
                        "file": file_path,
                        "language": "json",
                        "error": f"Failed to read file: {str(e)}",
                        "severity": "error"
                    })

    def _generate_summary(self):
        """Generate summary statistics"""
        self.results["summary"] = {
            "total_files_scanned": sum(self.results["file_statistics"].values()),
            "total_syntax_errors": len(self.results["syntax_errors"]),
            "total_formatting_issues": len(self.results["formatting_issues"]),
            "total_naming_violations": len(self.results["naming_violations"]),
            "total_indentation_issues": len(self.results["indentation_issues"]),
            "files_by_language": dict(self.results["file_statistics"])
        }

    def save_report(self, output_file: str = None):
        """Save the audit report to a JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"code_audit_report_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📊 Audit report saved to: {output_file}")
        return output_file

    def print_summary(self):
        """Print a summary of findings"""
        print("\n" + "=" * 80)
        print("CODE AUDIT SUMMARY")
        print("=" * 80)
        
        summary = self.results.get("summary", {})
        print(f"\nTotal files scanned: {summary.get('total_files_scanned', 0)}")
        print(f"Syntax errors found: {summary.get('total_syntax_errors', 0)}")
        print(f"Formatting issues: {summary.get('total_formatting_issues', 0)}")
        print(f"Naming violations: {summary.get('total_naming_violations', 0)}")
        print(f"Indentation issues: {summary.get('total_indentation_issues', 0)}")
        
        # Show critical errors
        if self.results["syntax_errors"]:
            print("\n⚠️  CRITICAL SYNTAX ERRORS:")
            for error in self.results["syntax_errors"][:10]:  # Show first 10
                print(f"  - {error['file']}: {error['error']}")
            if len(self.results["syntax_errors"]) > 10:
                print(f"  ... and {len(self.results['syntax_errors']) - 10} more")


def main():
    """Main entry point"""
    scanner = CodeAuditScanner()
    scanner.scan_codebase()
    scanner.print_summary()
    report_file = scanner.save_report()
    
    print(f"\n✅ Code audit complete! Check {report_file} for detailed results.")
    print("\nNext steps:")
    print("1. Review syntax errors in the report (highest priority)")
    print("2. Address formatting issues by language")
    print("3. Fix naming convention violations")
    print("4. Standardize indentation across the codebase")


if __name__ == "__main__":
    main()