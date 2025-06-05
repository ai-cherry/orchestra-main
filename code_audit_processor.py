#!/usr/bin/env python3
"""
Code Audit Processor - Processes audit results and creates fix strategies
"""

import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple

class CodeAuditProcessor:
    def __init__(self, audit_report_path: str):
        self.report_path = audit_report_path
        with open(audit_report_path, 'r') as f:
            self.audit_data = json.load(f)
        
        self.fix_strategies = {
            "syntax_errors": self._create_syntax_fix_strategy,
            "formatting_issues": self._create_formatting_fix_strategy,
            "naming_violations": self._create_naming_fix_strategy,
            "indentation_issues": self._create_indentation_fix_strategy
        }
        
    def create_fix_plan(self):
        """Create a comprehensive fix plan based on audit results"""
        print("📋 Creating Fix Plan from Audit Results")
        print("=" * 80)
        
        fix_plan = {
            "metadata": {
                "audit_report": self.report_path,
                "created_at": datetime.now().isoformat(),
                "total_issues": sum([
                    len(self.audit_data.get("syntax_errors", [])),
                    len(self.audit_data.get("formatting_issues", [])),
                    len(self.audit_data.get("naming_violations", [])),
                    len(self.audit_data.get("indentation_issues", []))
                ])
            },
            "priority_fixes": [],
            "batch_fixes": defaultdict(list),
            "file_groups": defaultdict(list)
        }
        
        # Process each type of issue
        for issue_type, strategy_func in self.fix_strategies.items():
            issues = self.audit_data.get(issue_type, [])
            if issues:
                strategy_func(issues, fix_plan)
        
        # Group files by directory for batch processing
        self._group_files_by_directory(fix_plan)
        
        # Save fix plan
        output_file = f"code_fix_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(fix_plan, f, indent=2)
        
        print(f"\n✅ Fix plan created: {output_file}")
        return fix_plan
    
    def _create_syntax_fix_strategy(self, issues: List[Dict], fix_plan: Dict):
        """Create strategy for fixing syntax errors"""
        print(f"\n🔴 Processing {len(issues)} syntax errors...")
        
        # Group by language
        by_language = defaultdict(list)
        for issue in issues:
            by_language[issue.get("language", "unknown")].append(issue)
        
        for lang, lang_issues in by_language.items():
            fix_plan["priority_fixes"].append({
                "type": "syntax_errors",
                "language": lang,
                "count": len(lang_issues),
                "priority": "CRITICAL",
                "strategy": f"Fix {lang} syntax errors first - these block all other operations",
                "files": [issue["file"] for issue in lang_issues[:10]]  # First 10 files
            })
    
    def _create_formatting_fix_strategy(self, issues: List[Dict], fix_plan: Dict):
        """Create strategy for fixing formatting issues"""
        print(f"\n🟡 Processing {len(issues)} formatting issues...")
        
        # Group by issue type
        by_issue_type = defaultdict(list)
        for issue in issues:
            issue_desc = issue.get("issue", "unknown")
            if "line too long" in issue_desc.lower():
                by_issue_type["long_lines"].append(issue)
            elif "console.log" in issue_desc.lower():
                by_issue_type["console_logs"].append(issue)
            else:
                by_issue_type["other"].append(issue)
        
        for issue_type, type_issues in by_issue_type.items():
            if type_issues:
                fix_plan["batch_fixes"]["formatting"].append({
                    "issue_type": issue_type,
                    "count": len(type_issues),
                    "automated_fix": issue_type in ["long_lines", "console_logs"],
                    "sample_files": [issue["file"] for issue in type_issues[:5]]
                })
    
    def _create_naming_fix_strategy(self, issues: List[Dict], fix_plan: Dict):
        """Create strategy for fixing naming violations"""
        print(f"\n🟠 Processing {len(issues)} naming violations...")
        
        # Group by type (function, class, etc.)
        by_type = defaultdict(list)
        for issue in issues:
            by_type[issue.get("type", "unknown")].append(issue)
        
        for name_type, type_issues in by_type.items():
            fix_plan["batch_fixes"]["naming"].append({
                "type": name_type,
                "count": len(type_issues),
                "pattern": type_issues[0].get("issue", "") if type_issues else "",
                "requires_refactoring": True,
                "sample_violations": [
                    {"file": issue["file"], "name": issue.get("name", "")} 
                    for issue in type_issues[:5]
                ]
            })
    
    def _create_indentation_fix_strategy(self, issues: List[Dict], fix_plan: Dict):
        """Create strategy for fixing indentation issues"""
        print(f"\n🟢 Processing {len(issues)} indentation issues...")
        
        affected_files = [issue["file"] for issue in issues]
        fix_plan["batch_fixes"]["indentation"] = {
            "total_files": len(set(affected_files)),
            "automated_fix": True,
            "strategy": "Use autopep8 for Python, prettier for JS/TS",
            "files": list(set(affected_files))
        }
    
    def _group_files_by_directory(self, fix_plan: Dict):
        """Group files by directory for efficient batch processing"""
        all_files = set()
        
        # Collect all files with issues
        for issue in self.audit_data.get("syntax_errors", []):
            all_files.add(issue["file"])
        for issue in self.audit_data.get("formatting_issues", []):
            all_files.add(issue["file"])
        for issue in self.audit_data.get("naming_violations", []):
            all_files.add(issue["file"])
        for issue in self.audit_data.get("indentation_issues", []):
            all_files.add(issue["file"])
        
        # Group by directory
        for file_path in all_files:
            dir_path = str(Path(file_path).parent)
            fix_plan["file_groups"][dir_path].append(file_path)
    
    def generate_fix_scripts(self):
        """Generate automated fix scripts for common issues"""
        print("\n🔧 Generating automated fix scripts...")
        
        # Python formatter script
        self._create_python_formatter()
        
        # JavaScript/TypeScript formatter script
        self._create_javascript_formatter()
        
        # Batch fix runner
        self._create_batch_fix_runner()
        
        print("✅ Fix scripts generated!")
    
    def _create_python_formatter(self):
        """Create Python formatting fix script"""
        script_content = '''#!/usr/bin/env python3
"""Auto-fix Python formatting issues"""

import subprocess
import sys
from pathlib import Path

def fix_python_file(file_path):
    """Fix formatting issues in a Python file"""
    print(f"Fixing: {file_path}")
    
    # Run autopep8
    subprocess.run([
        sys.executable, "-m", "autopep8",
        "--in-place",
        "--aggressive",
        "--max-line-length", "120",
        str(file_path)
    ])
    
    # Run isort for imports
    subprocess.run([
        sys.executable, "-m", "isort",
        str(file_path)
    ])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        for file_path in sys.argv[1:]:
            fix_python_file(file_path)
    else:
        print("Usage: python fix_python_formatting.py <file1> <file2> ...")
'''
        
        with open("fix_python_formatting.py", "w") as f:
            f.write(script_content)
        os.chmod("fix_python_formatting.py", 0o755)
    
    def _create_javascript_formatter(self):
        """Create JavaScript/TypeScript formatting fix script"""
        script_content = '''#!/bin/bash
# Auto-fix JavaScript/TypeScript formatting issues

echo "🔧 Fixing JavaScript/TypeScript formatting..."

# Check if prettier is installed
if ! command -v prettier &> /dev/null; then
    echo "Prettier not found. Install with: npm install -g prettier"
    exit 1
fi

# Fix files passed as arguments
if [ $# -eq 0 ]; then
    echo "Usage: ./fix_javascript_formatting.sh <file1> <file2> ..."
    exit 1
fi

for file in "$@"; do
    echo "Fixing: $file"
    prettier --write --print-width 120 --tab-width 2 "$file"
done

echo "✅ JavaScript/TypeScript formatting complete!"
'''
        
        with open("fix_javascript_formatting.sh", "w") as f:
            f.write(script_content)
        os.chmod("fix_javascript_formatting.sh", 0o755)
    
    def _create_batch_fix_runner(self):
        """Create batch fix runner script"""
        script_content = '''#!/usr/bin/env python3
"""Batch fix runner for code quality issues"""

import json
import subprocess
import sys
from pathlib import Path

def load_fix_plan(plan_file):
    """Load the fix plan"""
    with open(plan_file, 'r') as f:
        return json.load(f)

def fix_indentation_issues(files):
    """Fix indentation issues in files"""
    python_files = [f for f in files if f.endswith('.py')]
    js_files = [f for f in files if f.endswith(('.js', '.jsx', '.ts', '.tsx'))]
    
    if python_files:
        print(f"Fixing indentation in {len(python_files)} Python files...")
        subprocess.run([sys.executable, "fix_python_formatting.py"] + python_files)
    
    if js_files:
        print(f"Fixing indentation in {len(js_files)} JS/TS files...")
        subprocess.run(["./fix_javascript_formatting.sh"] + js_files)

def main():
    if len(sys.argv) < 2:
        print("Usage: python batch_fix_runner.py <fix_plan.json>")
        sys.exit(1)
    
    plan = load_fix_plan(sys.argv[1])
    
    # Fix indentation issues first (automated)
    indentation_data = plan.get("batch_fixes", {}).get("indentation", {})
    if indentation_data.get("files"):
        fix_indentation_issues(indentation_data["files"])
    
    print("\\n✅ Automated fixes complete!")
    print("\\nNext steps:")
    print("1. Review and fix syntax errors manually")
    print("2. Address naming convention violations")
    print("3. Run tests to ensure fixes didn't break functionality")

if __name__ == "__main__":
    main()
'''
        
        with open("batch_fix_runner.py", "w") as f:
            f.write(script_content)
        os.chmod("batch_fix_runner.py", 0o755)

    def print_action_plan(self):
        """Print a human-readable action plan"""
        print("\n" + "=" * 80)
        print("RECOMMENDED ACTION PLAN")
        print("=" * 80)
        
        summary = self.audit_data.get("summary", {})
        
        print("\n📊 Issue Summary:")
        print(f"  - Syntax Errors: {summary.get('total_syntax_errors', 0)} (CRITICAL)")
        print(f"  - Formatting Issues: {summary.get('total_formatting_issues', 0)}")
        print(f"  - Naming Violations: {summary.get('total_naming_violations', 0)}")
        print(f"  - Indentation Issues: {summary.get('total_indentation_issues', 0)}")
        
        print("\n🎯 Recommended Approach:")
        print("\n1. PHASE 1 - Critical Fixes (Manual):")
        print("   - Fix all syntax errors first")
        print("   - Start with Python files (use 'python -m py_compile <file>')")
        print("   - Then JavaScript/TypeScript (use ESLint)")
        
        print("\n2. PHASE 2 - Automated Formatting:")
        print("   - Run: python batch_fix_runner.py <fix_plan.json>")
        print("   - This will fix indentation and basic formatting")
        
        print("\n3. PHASE 3 - Naming Conventions (Semi-automated):")
        print("   - Review naming violations in the fix plan")
        print("   - Use find/replace with careful review")
        
        print("\n4. PHASE 4 - Validation:")
        print("   - Run all tests")
        print("   - Re-run code audit to verify fixes")
        
        print("\n💡 Pro Tips:")
        print("   - Work on one directory at a time")
        print("   - Commit after each phase")
        print("   - Use version control to track changes")


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python code_audit_processor.py <audit_report.json>")
        print("\nFirst run: python code_audit_scanner.py")
        sys.exit(1)
    
    processor = CodeAuditProcessor(sys.argv[1])
    processor.create_fix_plan()
    processor.generate_fix_scripts()
    processor.print_action_plan()


if __name__ == "__main__":
    main()