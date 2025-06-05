#!/usr/bin/env python3
"""
Fix Python indentation errors systematically
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict

class PythonIndentationFixer:
    def __init__(self, audit_report_path: str):
        with open(audit_report_path, 'r') as f:
            self.audit_data = json.load(f)
        
        # Extract Python indentation errors
        self.indent_errors = [
            error for error in self.audit_data.get('syntax_errors', [])
            if error['file'].endswith('.py') and 'unexpected indent' in error.get('error', '')
        ]
        
        # Group by directory for systematic fixing
        self.errors_by_dir = {}
        for error in self.indent_errors:
            dir_path = str(Path(error['file']).parent)
            if dir_path not in self.errors_by_dir:
                self.errors_by_dir[dir_path] = []
            self.errors_by_dir[dir_path].append(error)
    
    def analyze_indentation_pattern(self, file_path: str) -> Dict[str, any]:
        """Analyze the indentation pattern in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Detect indentation style
            spaces_count = {}
            tabs_count = 0
            mixed_lines = []
            
            for i, line in enumerate(lines, 1):
                if line.strip():  # Non-empty line
                    indent = len(line) - len(line.lstrip())
                    if indent > 0:
                        if '\t' in line[:indent]:
                            tabs_count += 1
                            if ' ' in line[:indent]:
                                mixed_lines.append(i)
                        else:
                            # Count spaces
                            if indent % 4 == 0:
                                spaces_count[4] = spaces_count.get(4, 0) + 1
                            elif indent % 2 == 0:
                                spaces_count[2] = spaces_count.get(2, 0) + 1
            
            # Determine predominant style
            if tabs_count > sum(spaces_count.values()):
                style = 'tabs'
            elif 4 in spaces_count and spaces_count.get(4, 0) > spaces_count.get(2, 0):
                style = '4spaces'
            else:
                style = '2spaces'
            
            return {
                'style': style,
                'mixed_lines': mixed_lines,
                'total_lines': len(lines)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def fix_file_indentation(self, file_path: str, target_style: str = '4spaces') -> Tuple[bool, str]:
        """Fix indentation in a single file"""
        try:
            # First, check if file has syntax errors
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', file_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                # Try to fix with autopep8
                print(f"  Attempting autopep8 fix for: {file_path}")
                fix_result = subprocess.run(
                    [sys.executable, '-m', 'autopep8', '--in-place', '--aggressive', file_path],
                    capture_output=True,
                    text=True
                )
                
                if fix_result.returncode == 0:
                    # Verify fix
                    verify_result = subprocess.run(
                        [sys.executable, '-m', 'py_compile', file_path],
                        capture_output=True,
                        text=True
                    )
                    if verify_result.returncode == 0:
                        return True, "Fixed with autopep8"
                    else:
                        return False, "autopep8 fix failed verification"
                else:
                    return False, f"autopep8 failed: {fix_result.stderr}"
            else:
                return True, "No indentation errors found"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def fix_directory(self, directory: str, max_files: int = None) -> Dict[str, any]:
        """Fix all Python files in a directory"""
        if directory not in self.errors_by_dir:
            return {"status": "no_errors", "directory": directory}
        
        errors = self.errors_by_dir[directory]
        if max_files:
            errors = errors[:max_files]
        
        results = {
            "directory": directory,
            "total_errors": len(self.errors_by_dir[directory]),
            "attempted": len(errors),
            "fixed": 0,
            "failed": 0,
            "details": []
        }
        
        print(f"\n📁 Fixing {len(errors)} files in: {directory}")
        
        for error in errors:
            file_path = error['file']
            success, message = self.fix_file_indentation(file_path)
            
            if success:
                results["fixed"] += 1
                print(f"  ✅ Fixed: {file_path}")
            else:
                results["failed"] += 1
                print(f"  ❌ Failed: {file_path} - {message}")
            
            results["details"].append({
                "file": file_path,
                "success": success,
                "message": message
            })
        
        return results
    
    def fix_critical_directories(self, limit: int = 5):
        """Fix directories with most errors first"""
        # Sort directories by error count
        sorted_dirs = sorted(
            self.errors_by_dir.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        print(f"🔧 PYTHON INDENTATION FIXER")
        print(f"=" * 80)
        print(f"Total indentation errors: {len(self.indent_errors)}")
        print(f"Affected directories: {len(self.errors_by_dir)}")
        print(f"\nFixing top {limit} directories with most errors...")
        
        all_results = []
        
        for i, (directory, errors) in enumerate(sorted_dirs[:limit]):
            if i > 0:
                print()  # Add spacing between directories
            
            result = self.fix_directory(directory)
            all_results.append(result)
        
        # Summary
        print(f"\n{'=' * 80}")
        print("SUMMARY:")
        total_fixed = sum(r["fixed"] for r in all_results)
        total_failed = sum(r["failed"] for r in all_results)
        total_attempted = sum(r["attempted"] for r in all_results)
        
        print(f"  Total files attempted: {total_attempted}")
        print(f"  Successfully fixed: {total_fixed}")
        print(f"  Failed to fix: {total_failed}")
        
        # Save results
        output_file = "python_indentation_fix_results.json"
        with open(output_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_errors": len(self.indent_errors),
                    "directories_processed": len(all_results),
                    "files_attempted": total_attempted,
                    "files_fixed": total_fixed,
                    "files_failed": total_failed
                },
                "directory_results": all_results
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {output_file}")
        
        # Next steps
        if total_failed > 0:
            print("\n⚠️  Some files require manual intervention.")
            print("Check the results file for details on failed fixes.")
        
        remaining = len(self.indent_errors) - total_attempted
        if remaining > 0:
            print(f"\n📌 {remaining} errors remain in other directories.")
            print("Run with a higher limit or fix remaining directories manually.")

def main():
    # Check for autopep8
    try:
        subprocess.run([sys.executable, '-m', 'autopep8', '--version'], 
                      capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("❌ autopep8 not installed. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'autopep8'])
    
    # Find latest audit report
    import glob
    reports = sorted(glob.glob("code_audit_report_*.json"))
    if not reports:
        print("❌ No audit report found. Run ./run_code_audit.sh first.")
        sys.exit(1)
    
    report_file = reports[-1]
    print(f"Using audit report: {report_file}")
    
    fixer = PythonIndentationFixer(report_file)
    
    # Fix top 5 directories with most errors
    fixer.fix_critical_directories(limit=5)

if __name__ == "__main__":
    main()