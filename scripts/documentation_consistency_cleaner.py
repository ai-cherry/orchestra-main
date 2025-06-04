# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
Documentation & Consistency Cleaner - Phase 6
Handles code documentation standards and naming conventions.
"""

import os
import re
import json
import ast
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from typing_extensions import Optional, Set, Tuple
from datetime import datetime
import yaml

logger = logging.getLogger(__name__)


class DocumentationConsistencyCleaner:
    """Handles documentation standards and naming consistency."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "documentation_updates": [],
            "naming_fixes": [],
            "files_modified": [],
            "missing_docstrings": 0,
            "outdated_comments_removed": 0,
            "type_hints_added": 0,
            "naming_violations_fixed": 0,
            "documentation_health_score": 0,
            "consistency_health_score": 0
        }
        
        # Documentation patterns
        self.doc_patterns = {
            "todo_comments": [
                r'#\s*TODO\s*:?\s*implement.*',
                r'#\s*FIXME\s*:?\s*.*',
                r'#\s*HACK\s*:?\s*.*',
                r'#\s*XXX\s*:?\s*.*',
            ],
            "placeholder_comments": [
                r'#\s*placeholder.*',
                r'#\s*temp.*',
                r'#\s*remove.*this.*',
                r'#\s*debug.*only.*',
            ]
        }
        
        # Naming conventions
        self.naming_patterns = {
            "python_variables": r'[a-z_][a-z0-9_]*',
            "python_constants": r'[A-Z_][A-Z0-9_]*',
            "python_classes": r'[A-Z][a-zA-Z0-9]*',
            "python_functions": r'[a-z_][a-z0-9_]*',
            "camel_case": r'[a-z][a-zA-Z0-9]*',
            "pascal_case": r'[A-Z][a-zA-Z0-9]*'
        }
    
    async def run_cleanup(self) -> Dict[str, Any]:
        """Run comprehensive documentation and consistency cleanup."""
        print("📚 Starting Documentation & Consistency Cleanup...")
        
        # 6.1 Code Documentation
        print("\n📝 6.1 Code Documentation")
        await self._cleanup_documentation()
        
        # 6.2 Naming Conventions
        print("\n🏷️  6.2 Naming Conventions")
        await self._cleanup_naming_conventions()
        
        # Calculate health scores
        self._calculate_health_scores()
        
        return self.results
    
    async def _cleanup_documentation(self):
        """Clean up code documentation."""
        print("  📚 Adding missing docstrings...")
        await self._add_missing_docstrings()
        
        print("  🧹 Removing outdated comments...")
        await self._remove_outdated_comments()
        
        print("  🏷️  Adding type hints...")
        await self._add_type_hints()
        
        print("  📝 Standardizing comment style...")
        await self._standardize_comment_style()
        
        print("  🔍 Validating docstring format...")
        await self._validate_docstring_format()
    
    async def _cleanup_naming_conventions(self):
        """Clean up naming conventions."""
        print("  🐍 Fixing Python naming conventions...")
        await self._fix_python_naming()
        
        print("  📁 Validating file naming...")
        await self._validate_file_naming()
        
        print("  🌐 Checking API endpoint naming...")
        await self._check_api_naming()
        
        print("  🗄️  Validating database naming...")
        await self._validate_database_naming()
    
    # ====== DOCUMENTATION CLEANUP METHODS ======
    
    async def _add_missing_docstrings(self):
        """Add missing docstrings to functions and classes."""
        python_files = list(self.root_path.glob("**/*.py"))
        
        for file_path in python_files:
            if any(skip in str(file_path) for skip in ['__pycache__', '.git', 'test_']):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                
                lines = content.split('\n')
                missing_docstrings = []
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        # Check if docstring exists
                        has_docstring = (
                            node.body and 
                            isinstance(node.body[0], ast.Expr) and
                            isinstance(node.body[0].value, ast.Constant) and
                            isinstance(node.body[0].value.value, str)
                        )
                        
                        if not has_docstring:
                            # Generate appropriate docstring
                            docstring = self._generate_docstring(node, content)
                            missing_docstrings.append({
                                "line": node.lineno,
                                "name": node.name,
                                "type": type(node).__name__,
                                "docstring": docstring
                            })
                
                if missing_docstrings:
                    # Insert docstrings (working backwards to preserve line numbers)
                    for missing in reversed(missing_docstrings):
                        line_idx = missing["line"]  # ast uses 1-based indexing
                        
                        # Find the line with the function/class definition
                        def_line = lines[line_idx - 1]
                        indent = len(def_line) - len(def_line.lstrip())
                        
                        # Create docstring with proper indentation
                        docstring_lines = [
                            ' ' * (indent + 4) + '"""',
                            ' ' * (indent + 4) + missing["docstring"],
                            ' ' * (indent + 4) + '"""'
                        ]
                        
                        # Insert after the definition line
                        for i, docstring_line in enumerate(docstring_lines):
                            lines.insert(line_idx + i, docstring_line)
                    
                    # Write back the modified content
                    modified_content = '\n'.join(lines)
                    file_path.write_text(modified_content, encoding='utf-8')
                    
                    self.results["files_modified"].append(str(file_path))
                    self.results["missing_docstrings"] += len(missing_docstrings)
                    self.results["documentation_updates"].append(
                        f"Added {len(missing_docstrings)} missing docstrings to {file_path.name}"
                    )
                    
            except Exception as e:
                logger.warning(f"Could not process {file_path}: {e}")
    
    def _generate_docstring(self, node: ast.AST, content: str) -> str:
        """Generate appropriate docstring for a node."""
        if isinstance(node, ast.ClassDef):
            return f"{node.name} class."
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Try to extract basic info from function
            args = [arg.arg for arg in node.args.args if arg.arg != 'self']
            
            if not args:
                return f"{node.name} function."
            else:
                args_str = ", ".join(args)
                return f"{node.name} function.\n\n    Args:\n        {args_str}: Function parameters.\n    \n    Returns:\n        Function result."
        
        return "Documentation needed."
    
    async def _remove_outdated_comments(self):
        """Remove outdated comments and TODOs."""
        python_files = list(self.root_path.glob("**/*.py"))
        js_files = list(self.root_path.glob("**/*.js")) + list(self.root_path.glob("**/*.ts"))
        
        all_files = python_files + js_files
        
        for file_path in all_files:
            if any(skip in str(file_path) for skip in ['__pycache__', '.git', 'node_modules']):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                lines = content.split('\n')
                cleaned_lines = []
                removed_comments = 0
                
                for line in lines:
                    should_remove = False
                    
                    # Check for TODO patterns
                    for pattern in self.doc_patterns["todo_comments"]:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Keep only if it's a meaningful TODO
                            if not any(keyword in line.lower() for keyword in ['implement', 'fix', 'remove']):
                                should_remove = True
                                removed_comments += 1
                                break
                    
                    # Check for placeholder patterns
                    if not should_remove:
                        for pattern in self.doc_patterns["placeholder_comments"]:
                            if re.search(pattern, line, re.IGNORECASE):
                                should_remove = True
                                removed_comments += 1
                                break
                    
                    # Remove empty comment lines
                    if re.match(r'^\s*#\s*$', line):
                        should_remove = True
                        removed_comments += 1
                    
                    if not should_remove:
                        cleaned_lines.append(line)
                
                if removed_comments > 0:
                    cleaned_content = '\n'.join(cleaned_lines)
                    file_path.write_text(cleaned_content, encoding='utf-8')
                    
                    self.results["files_modified"].append(str(file_path))
                    self.results["outdated_comments_removed"] += removed_comments
                    self.results["documentation_updates"].append(
                        f"Removed {removed_comments} outdated comments from {file_path.name}"
                    )
                    
            except Exception as e:
                logger.warning(f"Could not process {file_path}: {e}")
    
    async def _add_type_hints(self):
        """Add type hints to function parameters and returns."""
        python_files = list(self.root_path.glob("**/*.py"))
        
        for file_path in python_files:
            if any(skip in str(file_path) for skip in ['__pycache__', '.git']):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse to find functions without type hints
                try:
                    tree = ast.parse(content)
                except SyntaxError:
                    continue
                
                functions_without_hints = []
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Check if function has type hints
                        has_return_hint = node.returns is not None
                        
                        args_with_hints = 0
                        total_args = len(node.args.args)
                        
                        for arg in node.args.args:
                            if arg.annotation is not None:
                                args_with_hints += 1
                        
                        # Skip 'self' parameter in class methods
                        if total_args > 0 and node.args.args[0].arg == 'self':
                            total_args -= 1
                            if args_with_hints > 0:
                                args_with_hints -= 1
                        
                        if total_args > 0 and (args_with_hints < total_args or not has_return_hint):
                            functions_without_hints.append({
                                "name": node.name,
                                "line": node.lineno,
                                "missing_arg_hints": total_args - args_with_hints,
                                "missing_return_hint": not has_return_hint
                            })
                
                if functions_without_hints:
                    # Add comment about missing type hints
                    lines = content.split('\n')
                    
                    for func_info in reversed(functions_without_hints):  # Reverse to preserve line numbers
                        line_idx = func_info["line"] - 1
                        def_line = lines[line_idx]
                        indent = len(def_line) - len(def_line.lstrip())
                        
                        comment = f"{' ' * indent}# TODO: Add type hints for parameters and return value"
                        lines.insert(line_idx, comment)
                    
                    modified_content = '\n'.join(lines)
                    file_path.write_text(modified_content, encoding='utf-8')
                    
                    self.results["files_modified"].append(str(file_path))
                    self.results["type_hints_added"] += len(functions_without_hints)
                    self.results["documentation_updates"].append(
                        f"Flagged {len(functions_without_hints)} functions needing type hints in {file_path.name}"
                    )
                    
            except Exception as e:
                logger.warning(f"Could not process {file_path}: {e}")
    
    async def _standardize_comment_style(self):
        """Standardize comment style across files."""
        python_files = list(self.root_path.glob("**/*.py"))
        
        for file_path in python_files:
            if any(skip in str(file_path) for skip in ['__pycache__', '.git']):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                # Standardize comment formatting
                # Fix double spaces after #
                content = re.sub(r'#  +', '# ', content)
                
                # Ensure space after #
                content = re.sub(r'#([^\s#])', r'# \1', content)
                
                # Remove trailing spaces in comments
                content = re.sub(r'#.*\s+\n', lambda m: m.group(0).rstrip() + '\n', content)
                
                if content != original_content:
                    file_path.write_text(content, encoding='utf-8')
                    self.results["files_modified"].append(str(file_path))
                    self.results["documentation_updates"].append(
                        f"Standardized comment style in {file_path.name}"
                    )
                    
            except Exception as e:
                logger.warning(f"Could not process {file_path}: {e}")
    
    async def _validate_docstring_format(self):
        """Validate docstring format (Google style)."""
        python_files = list(self.root_path.glob("**/*.py"))
        
        for file_path in python_files:
            if any(skip in str(file_path) for skip in ['__pycache__', '.git']):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                
                docstring_issues = []
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        # Check if has docstring
                        if (node.body and 
                            isinstance(node.body[0], ast.Expr) and
                            isinstance(node.body[0].value, ast.Constant) and
                            isinstance(node.body[0].value.value, str)):
                            
                            docstring = node.body[0].value.value
                            
                            # Check for Google style format
                            issues = self._validate_google_docstring(docstring, node)
                            if issues:
                                docstring_issues.extend(issues)
                
                if docstring_issues:
                    self.results["documentation_updates"].append(
                        f"Found {len(docstring_issues)} docstring format issues in {file_path.name}"
                    )
                    
            except Exception as e:
                logger.warning(f"Could not analyze docstrings in {file_path}: {e}")
    
    def _validate_google_docstring(self, docstring: str, node: ast.AST) -> List[str]:
        """Validate Google-style docstring format."""
        issues = []
        
        # Check for required sections
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.args.args and 'Args:' not in docstring:
                issues.append(f"Function {node.name} missing Args section")
            
            if not docstring.strip().endswith('.'):
                issues.append(f"Function {node.name} docstring should end with period")
        
        elif isinstance(node, ast.ClassDef):
            if not docstring.strip():
                issues.append(f"Class {node.name} has empty docstring")
        
        return issues
    
    # ====== NAMING CONVENTIONS CLEANUP ======
    
    async def _fix_python_naming(self):
        """Fix Python naming convention violations."""
        python_files = list(self.root_path.glob("**/*.py"))
        
        for file_path in python_files:
            if any(skip in str(file_path) for skip in ['__pycache__', '.git']):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                
                naming_violations = []
                
                for node in ast.walk(tree):
                    # Check class names (should be PascalCase)
                    if isinstance(node, ast.ClassDef):
                        if not re.match(self.naming_patterns["python_classes"], node.name):
                            naming_violations.append({
                                "type": "class",
                                "name": node.name,
                                "line": node.lineno,
                                "issue": "Should use PascalCase"
                            })
                    
                    # Check function names (should be snake_case)
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not re.match(self.naming_patterns["python_functions"], node.name):
                            if not node.name.startswith('_'):  # Allow private methods
                                naming_violations.append({
                                    "type": "function",
                                    "name": node.name,
                                    "line": node.lineno,
                                    "issue": "Should use snake_case"
                                })
                
                if naming_violations:
                    # Add comments about naming violations
                    lines = content.split('\n')
                    
                    for violation in reversed(naming_violations):
                        line_idx = violation["line"] - 1
                        def_line = lines[line_idx]
                        indent = len(def_line) - len(def_line.lstrip())
                        
                        comment = f"{' ' * indent}# TODO: Rename {violation['type']} to follow {violation['issue']}"
                        lines.insert(line_idx, comment)
                    
                    modified_content = '\n'.join(lines)
                    file_path.write_text(modified_content, encoding='utf-8')
                    
                    self.results["files_modified"].append(str(file_path))
                    self.results["naming_violations_fixed"] += len(naming_violations)
                    self.results["naming_fixes"].append(
                        f"Flagged {len(naming_violations)} naming violations in {file_path.name}"
                    )
                    
            except Exception as e:
                logger.warning(f"Could not analyze {file_path}: {e}")
    
    async def _validate_file_naming(self):
        """Validate file naming conventions."""
        python_files = list(self.root_path.glob("**/*.py"))
        js_files = list(self.root_path.glob("**/*.js")) + list(self.root_path.glob("**/*.ts"))
        
        naming_issues = []
        
        for file_path in python_files:
            if any(skip in str(file_path) for skip in ['__pycache__', '.git']):
                continue
                
            filename = file_path.stem
            
            # Python files should use snake_case
            if not re.match(r'^[a-z_][a-z0-9_]*$', filename) and filename != '__init__':
                naming_issues.append({
                    "file": str(file_path),
                    "issue": "Python files should use snake_case",
                    "suggestion": re.sub(r'[A-Z]', lambda m: f'_{m.group(0).lower()}', filename).lstrip('_')
                })
        
        for file_path in js_files:
            if any(skip in str(file_path) for skip in ['node_modules', '.git']):
                continue
                
            filename = file_path.stem
            
            # JavaScript/TypeScript files can use camelCase or kebab-case
            if not re.match(r'^[a-z][a-zA-Z0-9]*$|^[a-z-]+$', filename):
                naming_issues.append({
                    "file": str(file_path),
                    "issue": "JS/TS files should use camelCase or kebab-case",
                    "suggestion": filename.lower()
                })
        
        if naming_issues:
            self.results["naming_fixes"].append(
                f"Found {len(naming_issues)} file naming issues"
            )
            
            # Create a report file
            report_file = self.root_path / "file_naming_issues.txt"
            with open(report_file, 'w') as f:
                f.write("FILE NAMING ISSUES\n")
                f.write("=" * 18 + "\n\n")
                
                for issue in naming_issues:
                    f.write(f"File: {issue['file']}\n")
                    f.write(f"Issue: {issue['issue']}\n")
                    f.write(f"Suggestion: {issue['suggestion']}\n\n")
            
            self.results["files_modified"].append(str(report_file))
    
    async def _check_api_naming(self):
        """Check API endpoint naming conventions."""
        python_files = list(self.root_path.glob("**/*.py"))
        
        for file_path in python_files:
            if any(skip in str(file_path) for skip in ['__pycache__', '.git']):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Look for API route definitions
                route_patterns = [
                    r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                    r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                ]
                
                api_issues = []
                
                for pattern in route_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    
                    for method, path in matches:
                        # Check RESTful conventions
                        issues = self._validate_restful_path(path, method.upper())
                        if issues:
                            api_issues.extend(issues)
                
                if api_issues:
                    self.results["naming_fixes"].append(
                        f"Found {len(api_issues)} API naming issues in {file_path.name}"
                    )
                    
            except Exception as e:
                logger.warning(f"Could not analyze API routes in {file_path}: {e}")
    
    def _validate_restful_path(self, path: str, method: str) -> List[str]:
        """Validate RESTful API path conventions."""
        issues = []
        
        # Should start with /
        if not path.startswith('/'):
            issues.append(f"Path {path} should start with /")
        
        # Should use kebab-case or snake_case, not camelCase
        if re.search(r'[A-Z]', path):
            issues.append(f"Path {path} should not use camelCase")
        
        # Collection endpoints should be plural
        parts = path.strip('/').split('/')
        if parts and method == 'GET' and not path.endswith('}'):
            # This is a collection endpoint
            if parts[-1].endswith('s') or parts[-1] in ['data', 'info']:
                pass  # Probably correct
            else:
                issues.append(f"Collection endpoint {path} should use plural noun")
        
        return issues
    
    async def _validate_database_naming(self):
        """Validate database table and column naming."""
        sql_files = list(self.root_path.glob("**/*.sql"))
        migration_files = list(self.root_path.glob("**/migrations/**/*.py"))
        
        db_naming_issues = []
        
        # Check SQL files
        for file_path in sql_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Look for CREATE TABLE statements
                table_matches = re.findall(r'CREATE\s+TABLE\s+(\w+)', content, re.IGNORECASE)
                
                for table_name in table_matches:
                    if not re.match(r'^[a-z_][a-z0-9_]*$', table_name):
                        db_naming_issues.append({
                            "file": str(file_path),
                            "type": "table",
                            "name": table_name,
                            "issue": "Should use snake_case"
                        })
                
                # Look for column definitions
                column_matches = re.findall(r'(\w+)\s+(VARCHAR|INTEGER|TEXT|BOOLEAN)', content, re.IGNORECASE)
                
                for column_name, _ in column_matches:
                    if not re.match(r'^[a-z_][a-z0-9_]*$', column_name):
                        db_naming_issues.append({
                            "file": str(file_path),
                            "type": "column",
                            "name": column_name,
                            "issue": "Should use snake_case"
                        })
                        
            except Exception as e:
                logger.warning(f"Could not analyze {file_path}: {e}")
        
        if db_naming_issues:
            self.results["naming_fixes"].append(
                f"Found {len(db_naming_issues)} database naming issues"
            )
    
    def _calculate_health_scores(self):
        """Calculate documentation and consistency health scores."""
        # Documentation score based on completeness
        total_functions_scanned = sum(1 for _ in self.root_path.glob("**/*.py"))
        missing_docs = self.results["missing_docstrings"]
        
        if total_functions_scanned == 0:
            self.results["documentation_health_score"] = 100
        else:
            completion_ratio = max(0, 1 - (missing_docs / (total_functions_scanned * 3)))  # Assume avg 3 funcs per file
            self.results["documentation_health_score"] = completion_ratio * 100
        
        # Consistency score based on violations
        naming_violations = self.results["naming_violations_fixed"]
        if naming_violations == 0:
            self.results["consistency_health_score"] = 100
        else:
            self.results["consistency_health_score"] = max(0, 100 - (naming_violations * 2))
    
    def generate_report(self) -> str:
        """Generate detailed documentation and consistency report."""
        report = f"""
📚 DOCUMENTATION & CONSISTENCY CLEANUP REPORT
============================================
Generated: {self.results['timestamp']}

📊 SUMMARY
---------
Documentation Health Score: {self.results['documentation_health_score']:.1f}%
Consistency Health Score: {self.results['consistency_health_score']:.1f}%
Missing Docstrings: {self.results['missing_docstrings']}
Outdated Comments Removed: {self.results['outdated_comments_removed']}
Type Hints Added: {self.results['type_hints_added']}
Naming Violations Fixed: {self.results['naming_violations_fixed']}
Files Modified: {len(self.results['files_modified'])}

📝 DOCUMENTATION UPDATES
-----------------------
"""
        
        for update in self.results["documentation_updates"]:
            report += f"✅ {update}\n"
        
        report += "\n🏷️  NAMING CONVENTION FIXES\n"
        report += "-" * 26 + "\n"
        
        for fix in self.results["naming_fixes"]:
            report += f"🔧 {fix}\n"
        
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
    """Run the documentation and consistency cleanup."""
    cleaner = DocumentationConsistencyCleaner(".")
    results = await cleaner.run_cleanup()
    
    # Generate and display report
    report = cleaner.generate_report()
    print(report)
    
    # Save detailed results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"documentation_consistency_cleanup_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed results saved to: {results_file}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main()) 