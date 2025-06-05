import logging
logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""
Fix corrupted Python files with structural issues
"""

import re
import os
import json
from pathlib import Path
from typing import List, Tuple

class CorruptedPythonFixer:
    def __init__(self):
        self.fixed_count = 0
        self.failed_count = 0
        self.results = []
    
    def fix_file(self, file_path: str) -> Tuple[bool, str]:
        """Attempt to fix a corrupted Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                return False, "Empty file"
            
            # Detect and fix common corruption patterns
            fixed_lines = []
            
            # 1. Find shebang and move to top
            shebang_line = None
            for i, line in enumerate(lines):
                if line.strip().startswith('#!/usr/bin/env python'):
                    shebang_line = line
                    lines[i] = ''  # Remove from original position
                    break
            
            # 2. Collect imports
            imports = []
            other_lines = []
            
            # 3. Process lines and fix structure
            in_function = False
            in_class = False
            indent_level = 0
            
            for line in lines:
                stripped = line.strip()
                
                # Skip empty lines from removed content
                if not line.strip() and not line:
                    continue
                
                # Detect imports
                if (stripped.startswith('import ') or 
                    stripped.startswith('from ') and ' import ' in stripped):
                    imports.append(line)
                    continue
                
                # Detect orphaned docstrings (docstrings at wrong indentation)
                if (stripped.startswith('"""') and 
                    not in_function and not in_class and
                    len(line) - len(line.lstrip()) > 0):
                    # This is likely an orphaned docstring, skip it
                    continue
                
                # Detect function/class definitions
                if stripped.startswith('def '):
                    in_function = True
                    indent_level = len(line) - len(line.lstrip())
                elif stripped.startswith('class '):
                    in_class = True
                    indent_level = len(line) - len(line.lstrip())
                
                # Fix TODO comments that should be at top
                if stripped.startswith('# TODO:') and len(other_lines) < 5:
                    other_lines.insert(0, line)
                    continue
                
                other_lines.append(line)
            
            # Reconstruct file
            if shebang_line:
                fixed_lines.append(shebang_line)
            
            # Add module docstring if missing
            has_module_docstring = False
            for line in other_lines[:10]:
                if line.strip().startswith('"""'):
                    has_module_docstring = True
                    break
            
            if not has_module_docstring:
                module_name = Path(file_path).stem.replace('_', ' ').title()
                fixed_lines.append(f'"""{module_name} module"""\n')
            
            # Add imports after docstring
            if imports:
                fixed_lines.append('\n')
                fixed_lines.extend(sorted(set(imports)))
                fixed_lines.append('\n')
            
            # Add remaining content
            fixed_lines.extend(other_lines)
            
            # Write fixed content
            backup_path = file_path + '.backup'
            os.rename(file_path, backup_path)
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(fixed_lines)
                
                # Test if file is now valid Python
                compile(open(file_path).read(), file_path, 'exec')
                
                # Success - remove backup
                os.remove(backup_path)
                return True, "Fixed successfully"
                
            except SyntaxError as e:
                # Restore backup
                os.rename(backup_path, file_path)
                return False, f"Still has syntax errors: {e}"
                
        except Exception as e:
            return False, f"Error processing file: {e}"
    
    def fix_directory(self, directory: str, file_list: List[str]):
        """Fix all files in a directory"""
        print(f"\n📁 Fixing {len(file_list)} files in: {directory}")
        
        for file_path in file_list:
            if not file_path.endswith('.py'):
                continue
                
            success, message = self.fix_file(file_path)
            
            if success:
                self.fixed_count += 1
                print(f"  ✅ Fixed: {file_path}")
            else:
                self.failed_count += 1
                print(f"  ❌ Failed: {file_path} - {message}")
            
            self.results.append({
                "file": file_path,
                "success": success,
                "message": message
            })

def main():
    # Load the indentation fix results to see what failed
    try:
        with open('python_indentation_fix_results.json', 'r') as f:
            fix_results = json.load(f)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print("Could not load previous fix results")
        return
    
    fixer = CorruptedPythonFixer()
    
    print("🔧 CORRUPTED PYTHON FILE FIXER")
    print("=" * 80)
    print("Attempting to fix files with structural issues...")
    
    # Get failed files from each directory
    for dir_result in fix_results['directory_results']:
        directory = dir_result['directory']
        failed_files = [
            detail['file'] for detail in dir_result['details'] 
            if not detail['success']
        ]
        
        if failed_files:
            fixer.fix_directory(directory, failed_files[:10])  # Fix up to 10 per directory
    
    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY:")
    print(f"  Successfully fixed: {fixer.fixed_count}")
    print(f"  Failed to fix: {fixer.failed_count}")
    
    # Save results
    output_file = "corrupted_files_fix_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "fixed_count": fixer.fixed_count,
            "failed_count": fixer.failed_count,
            "details": fixer.results
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: {output_file}")
    
    if fixer.fixed_count > 0:
        print("\n✅ Some files were fixed! Re-run the audit to check remaining issues.")
    
    if fixer.failed_count > 0:
        print("\n⚠️  Some files still need manual intervention.")
        print("These files have severe structural issues that require human review.")

if __name__ == "__main__":
    main()