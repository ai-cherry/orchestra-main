#!/usr/bin/env python3
"""
Automated Syntax Fixer
Focuses on fixing the widespread indentation errors blocking the system
"""

import os
import re
import ast
import json
import shutil
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IndentationFixer:
    """Fix Python indentation errors automatically"""
    
    def __init__(self, backup_dir: str = "syntax_fix_backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.fixed_files = []
        self.failed_files = []
        self.stats = {
            'total_files': 0,
            'fixed': 0,
            'failed': 0,
            'already_valid': 0
        }
    
    def fix_file(self, filepath: str) -> Tuple[bool, Optional[str]]:
        """Fix indentation in a single Python file"""
        try:
            # Create backup
            backup_path = self._create_backup(filepath)
            
            # Read file content
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file is already valid
            try:
                ast.parse(content)
                self.stats['already_valid'] += 1
                return True, "File already has valid syntax"
            except SyntaxError:
                pass
            
            # Try different fixing strategies
            fixed_content = None
            strategies = [
                self._fix_basic_indentation,
                self._fix_mixed_indentation,
                self._fix_missing_indentation,
                self._fix_extra_indentation
            ]
            
            for strategy in strategies:
                try:
                    fixed_content = strategy(content)
                    # Validate the fix
                    ast.parse(fixed_content)
                    break
                except:
                    continue
            
            if fixed_content is None:
                # Try aggressive fix
                fixed_content = self._aggressive_fix(content)
            
            # Validate final result
            try:
                ast.parse(fixed_content)
            except SyntaxError as e:
                self.failed_files.append((filepath, str(e)))
                self.stats['failed'] += 1
                return False, f"Failed to fix: {str(e)}"
            
            # Write fixed content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            self.fixed_files.append(filepath)
            self.stats['fixed'] += 1
            return True, "Successfully fixed"
            
        except Exception as e:
            self.failed_files.append((filepath, str(e)))
            self.stats['failed'] += 1
            return False, f"Error processing file: {str(e)}"
    
    def _create_backup(self, filepath: str) -> str:
        """Create backup of file before modification"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{Path(filepath).name}.{timestamp}.bak"
        backup_path = self.backup_dir / backup_name
        shutil.copy2(filepath, backup_path)
        return str(backup_path)
    
    def _fix_basic_indentation(self, content: str) -> str:
        """Fix basic indentation issues"""
        lines = content.split('\n')
        fixed_lines = []
        indent_stack = [0]
        
        for line in lines:
            stripped = line.lstrip()
            if not stripped or stripped.startswith('#'):
                fixed_lines.append(line)
                continue
            
            # Calculate expected indentation
            if stripped.startswith(('def ', 'class ', 'if ', 'elif ', 'else:', 
                                   'for ', 'while ', 'try:', 'except', 'finally:', 
                                   'with ')):
                if stripped.endswith(':'):
                    # This line starts a new block
                    current_indent = indent_stack[-1]
                    fixed_lines.append(' ' * current_indent + stripped)
                    indent_stack.append(current_indent + 4)
                else:
                    # Missing colon
                    current_indent = indent_stack[-1]
                    fixed_lines.append(' ' * current_indent + stripped + ':')
                    indent_stack.append(current_indent + 4)
            elif stripped in ['pass', 'continue', 'break', 'return', 'raise']:
                # These statements don't change indentation
                current_indent = indent_stack[-1] if indent_stack else 0
                fixed_lines.append(' ' * current_indent + stripped)
            elif stripped.startswith('return '):
                # Return statement
                current_indent = indent_stack[-1] if indent_stack else 0
                fixed_lines.append(' ' * current_indent + stripped)
            else:
                # Regular line
                current_indent = indent_stack[-1] if indent_stack else 0
                fixed_lines.append(' ' * current_indent + stripped)
            
            # Check if we need to dedent
            if stripped in ['pass', 'return', 'raise', 'break', 'continue']:
                if len(indent_stack) > 1:
                    indent_stack.pop()
        
        return '\n'.join(fixed_lines)
    
    def _fix_mixed_indentation(self, content: str) -> str:
        """Fix mixed tabs and spaces"""
        # Convert all tabs to 4 spaces
        content = content.replace('\t', '    ')
        
        # Now fix indentation
        return self._fix_basic_indentation(content)
    
    def _fix_missing_indentation(self, content: str) -> str:
        """Fix missing indentation after control structures"""
        lines = content.split('\n')
        fixed_lines = []
        needs_indent = False
        current_indent = 0
        
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            line_indent = len(line) - len(stripped)
            
            if needs_indent and stripped and not stripped.startswith('#'):
                # This line needs indentation
                fixed_lines.append(' ' * (current_indent + 4) + stripped)
                needs_indent = False
            else:
                fixed_lines.append(line)
                current_indent = line_indent
            
            # Check if next line needs indentation
            if stripped.endswith(':') and not stripped.startswith('#'):
                needs_indent = True
                current_indent = line_indent
        
        return '\n'.join(fixed_lines)
    
    def _fix_extra_indentation(self, content: str) -> str:
        """Fix extra indentation"""
        lines = content.split('\n')
        if not lines:
            return content
        
        # Find minimum indentation (excluding empty lines)
        min_indent = float('inf')
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent)
        
        if min_indent == float('inf') or min_indent == 0:
            return content
        
        # Remove extra indentation
        fixed_lines = []
        for line in lines:
            if line.strip():
                fixed_lines.append(line[min_indent:])
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _aggressive_fix(self, content: str) -> str:
        """Aggressive fix - reformat entire file"""
        try:
            # Try using black formatter
            import black
            return black.format_str(content, mode=black.Mode())
        except:
            pass
        
        try:
            # Try using autopep8
            import autopep8
            return autopep8.fix_code(content, options={'aggressive': 2})
        except:
            pass
        
        # Last resort - basic reformatting
        lines = content.split('\n')
        fixed_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                fixed_lines.append('')
                continue
            
            # Decrease indent for these keywords
            if stripped.startswith(('elif ', 'else:', 'except', 'finally:')):
                indent_level = max(0, indent_level - 1)
            
            # Add line with current indentation
            fixed_lines.append('    ' * indent_level + stripped)
            
            # Increase indent after these
            if stripped.endswith(':') and not stripped.startswith('#'):
                indent_level += 1
            
            # Decrease indent after these
            if stripped in ['pass', 'return', 'raise', 'break', 'continue']:
                indent_level = max(0, indent_level - 1)
        
        return '\n'.join(fixed_lines)
    
    def fix_files_from_audit(self, audit_report_path: str):
        """Fix all files with syntax errors from audit report"""
        # Load audit report
        with open(audit_report_path, 'r') as f:
            audit_data = json.load(f)
        
        syntax_errors = audit_data.get('syntax_errors', [])
        python_errors = [e for e in syntax_errors if e.get('language') == 'python']
        
        logger.info(f"Found {len(python_errors)} Python files with syntax errors")
        
        # Group by file to avoid processing same file multiple times
        files_to_fix = {}
        for error in python_errors:
            filepath = error['file']
            if filepath not in files_to_fix:
                files_to_fix[filepath] = []
            files_to_fix[filepath].append(error)
        
        logger.info(f"Processing {len(files_to_fix)} unique files...")
        
        # Process each file
        for filepath, errors in files_to_fix.items():
            self.stats['total_files'] += 1
            logger.info(f"Fixing {filepath}...")
            
            success, message = self.fix_file(filepath)
            if success:
                logger.info(f"  ✓ {message}")
            else:
                logger.error(f"  ✗ {message}")
    
    def generate_report(self) -> Dict:
        """Generate fix report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.stats,
            'fixed_files': self.fixed_files,
            'failed_files': self.failed_files,
            'backup_directory': str(self.backup_dir)
        }


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix Python syntax errors')
    parser.add_argument('--audit-report', 
                       default='audit_results_20250605/code_audit_report_20250605_004043.json',
                       help='Path to audit report')
    parser.add_argument('--single-file', help='Fix a single file')
    parser.add_argument('--dry-run', action='store_true', help='Test without making changes')
    
    args = parser.parse_args()
    
    # Create fixer
    fixer = IndentationFixer()
    
    if args.single_file:
        # Fix single file
        success, message = fixer.fix_file(args.single_file)
        print(f"Result: {message}")
    else:
        # Fix all files from audit
        fixer.fix_files_from_audit(args.audit_report)
        
        # Generate report
        report = fixer.generate_report()
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"syntax_fix_report_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("SYNTAX FIX SUMMARY")
        print("="*60)
        print(f"Total files processed: {report['statistics']['total_files']}")
        print(f"Successfully fixed: {report['statistics']['fixed']}")
        print(f"Failed to fix: {report['statistics']['failed']}")
        print(f"Already valid: {report['statistics']['already_valid']}")
        print(f"\nBackups saved to: {report['backup_directory']}")
        print(f"Report saved to: {report_path}")
        
        if report['failed_files']:
            print("\n" + "-"*60)
            print("FAILED FILES:")
            print("-"*60)
            for filepath, error in report['failed_files'][:10]:
                print(f"  {filepath}: {error}")
            if len(report['failed_files']) > 10:
                print(f"  ... and {len(report['failed_files']) - 10} more")


if __name__ == "__main__":
    main()