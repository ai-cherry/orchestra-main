#!/usr/bin/env python3
"""
Import Error Fixer
Fixes import statement issues and resolves module dependencies.
"""

import os
import re
import ast
import sys
import logging
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime

logger = logging.getLogger(__name__)

class ImportErrorFixer:
    """Fixes import errors and dependencies."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.fixes_applied = []
        self.import_map = {}
        
    def run_import_fixes(self) -> Dict:
        """Run comprehensive import fixes."""
        print("📦 Starting Import Error Fixes...")
        print("=" * 50)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "files_fixed": 0,
            "import_errors_fixed": 0,
            "circular_imports_resolved": 0,
            "missing_imports_added": 0,
            "fixes_applied": []
        }
        
        # Build import map
        print("🗺️  Building import map...")
        self._build_import_map()
        
        # Fix import errors
        python_files = list(self.root_path.glob("**/*.py"))
        python_files = [f for f in python_files if not any(skip in str(f) for skip in ['__pycache__', '.git', 'venv'])]
        
        print(f"🔍 Fixing imports in {len(python_files)} Python files...")
        
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content
                
                # Apply import fixes
                content = self._fix_import_statements(content, py_file)
                content = self._add_missing_imports(content, py_file)
                content = self._resolve_relative_imports(content, py_file)
                content = self._fix_circular_imports(content, py_file)
                content = self._organize_imports(content, py_file)
                
                if content != original_content:
                    py_file.write_text(content, encoding='utf-8')
                    results["files_fixed"] += 1
                    print(f"✅ Fixed imports: {py_file.relative_to(self.root_path)}")
                    
            except Exception as e:
                logger.warning(f"Could not process {py_file}: {e}")
        
        results["fixes_applied"] = self.fixes_applied
        results["import_errors_fixed"] = len([f for f in self.fixes_applied if 'import' in f.lower()])
        
        print(f"\n🎯 IMPORT FIXES COMPLETE")
        print(f"Files Fixed: {results['files_fixed']}")
        print(f"Import Errors Fixed: {results['import_errors_fixed']}")
        
        return results
    
    def _build_import_map(self):
        """Build a map of available modules and their paths."""
        python_files = list(self.root_path.glob("**/*.py"))
        
        for py_file in python_files:
            if any(skip in str(py_file) for skip in ['__pycache__', '.git', 'venv']):
                continue
                
            try:
                # Calculate module path
                rel_path = py_file.relative_to(self.root_path)
                if rel_path.name == '__init__.py':
                    module_path = '.'.join(rel_path.parent.parts)
                else:
                    module_path = '.'.join(rel_path.with_suffix('').parts)
                
                self.import_map[module_path] = str(py_file)
                
                # Also map without package prefixes for easier matching
                if '.' in module_path:
                    short_name = module_path.split('.')[-1]
                    if short_name not in self.import_map:
                        self.import_map[short_name] = str(py_file)
                        
            except Exception as e:
                logger.warning(f"Could not map {py_file}: {e}")
    
    def _fix_import_statements(self, content: str, file_path: Path) -> str:
        """Fix malformed import statements."""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            original_line = line
            
            # Fix incomplete imports
            if line.strip() == 'import' or line.strip() == 'from':
                continue  # Skip completely broken imports
            
            # Fix imports with trailing commas
            if line.strip().startswith('import ') and line.strip().endswith(','):
                line = line.rstrip(',').strip()
                self.fixes_applied.append(f"Fixed trailing comma in import in {file_path.name}")
            
            # Fix from imports without module name
            if re.match(r'^\s*from\s+import', line):
                continue  # Skip malformed from import
            
            # Fix imports with extra spaces
            if line.strip().startswith('import '):
                cleaned = re.sub(r'\s+', ' ', line.strip())
                if cleaned != line.strip():
                    line = ' ' * (len(line) - len(line.lstrip())) + cleaned
                    self.fixes_applied.append(f"Cleaned import spacing in {file_path.name}")
            
            # Fix from imports with extra spaces
            if line.strip().startswith('from '):
                cleaned = re.sub(r'\s+', ' ', line.strip())
                if cleaned != line.strip():
                    line = ' ' * (len(line) - len(line.lstrip())) + cleaned
                    self.fixes_applied.append(f"Cleaned from import spacing in {file_path.name}")
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _add_missing_imports(self, content: str, file_path: Path) -> str:
        """Add commonly missing imports."""
        lines = content.split('\n')
        
        # Check what's being used in the code
        full_content = '\n'.join(lines)
        missing_imports = []
        
        # Common patterns and their required imports
        import_patterns = {
            r'\bPath\b': 'from pathlib import Path',
            r'\bdatetime\b': 'from datetime import datetime',
            r'\bjson\b': 'import json',
            r'\bre\b': 'import re',
            r'\bos\b': 'import os',
            r'\bsys\b': 'import sys',
            r'\blogging\b': 'import logging',
            r'\basyncio\b': 'import asyncio',
            r'\btyping\b': 'import typing',
            r'\bDict\b|\bList\b|\bOptional\b': 'from typing import Dict, List, Optional',
            r'\bFastAPI\b': 'from fastapi import FastAPI',
            r'\bAPIRouter\b': 'from fastapi import APIRouter',
            r'\bHTTPException\b': 'from fastapi import HTTPException',
            r'\bpandas\b|\bpd\.': 'import pandas as pd',
            r'\bnumpy\b|\bnp\.': 'import numpy as np',
        }
        
        existing_imports = set()
        for line in lines:
            if line.strip().startswith(('import ', 'from ')):
                existing_imports.add(line.strip())
        
        for pattern, import_stmt in import_patterns.items():
            if re.search(pattern, full_content) and import_stmt not in existing_imports:
                # Check if any variation of this import already exists
                import_module = import_stmt.split()[-1]
                if not any(import_module in existing for existing in existing_imports):
                    missing_imports.append(import_stmt)
                    self.fixes_applied.append(f"Added missing import {import_stmt} to {file_path.name}")
        
        if missing_imports:
            # Find the right place to insert imports
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith(('"""', "'''")) or line.strip().startswith('#'):
                    continue
                if line.strip() == '':
                    continue
                if line.strip().startswith(('import ', 'from ')):
                    insert_idx = i + 1
                    continue
                break
            
            # Insert missing imports
            for import_stmt in missing_imports:
                lines.insert(insert_idx, import_stmt)
                insert_idx += 1
            
            # Add empty line after imports if needed
            if insert_idx < len(lines) and lines[insert_idx].strip():
                lines.insert(insert_idx, '')
        
        return '\n'.join(lines)
    
    def _resolve_relative_imports(self, content: str, file_path: Path) -> str:
        """Resolve relative import issues."""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            if line.strip().startswith('from .'):
                # Try to resolve relative import
                rel_import = line.strip()
                match = re.match(r'from\s+(\.+)(\w+)?\s+import\s+(.+)', rel_import)
                
                if match:
                    dots, module, imports = match.groups()
                    
                    # Calculate absolute path
                    current_package = file_path.parent.relative_to(self.root_path)
                    
                    if dots == '.':  # Same directory
                        if module:
                            abs_module = '.'.join(current_package.parts + (module,))
                        else:
                            abs_module = '.'.join(current_package.parts)
                    else:
                        # Multiple dots - go up directories
                        num_up = len(dots) - 1
                        parent_parts = current_package.parts[:-num_up] if num_up < len(current_package.parts) else ()
                        if module:
                            abs_module = '.'.join(parent_parts + (module,))
                        else:
                            abs_module = '.'.join(parent_parts)
                    
                    # Check if absolute module exists
                    if abs_module in self.import_map:
                        new_line = f"from {abs_module} import {imports}"
                        if new_line != line:
                            line = new_line
                            self.fixes_applied.append(f"Resolved relative import to absolute in {file_path.name}")
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_circular_imports(self, content: str, file_path: Path) -> str:
        """Fix circular import issues."""
        lines = content.split('\n')
        
        # Look for imports that might cause circular dependencies
        current_module = str(file_path.relative_to(self.root_path).with_suffix('')).replace('/', '.')
        
        for i, line in enumerate(lines):
            if line.strip().startswith(('import ', 'from ')):
                # Check if importing something that might import us back
                imported_module = self._extract_module_name(line)
                
                if imported_module and imported_module in self.import_map:
                    imported_file = Path(self.import_map[imported_module])
                    
                    try:
                        imported_content = imported_file.read_text(encoding='utf-8')
                        if current_module in imported_content:
                            # Potential circular import - move to function level
                            if not line.strip().startswith('    '):  # Not already indented
                                # Comment out the import and add a note
                                lines[i] = f"# {line.strip()}  # Moved to avoid circular import"
                                self.fixes_applied.append(f"Commented potential circular import in {file_path.name}")
                    except:
                        pass
        
        return '\n'.join(lines)
    
    def _organize_imports(self, content: str, file_path: Path) -> str:
        """Organize imports in proper order."""
        lines = content.split('\n')
        
        # Separate imports from rest of code
        imports = []
        other_lines = []
        import_section = True
        
        for line in lines:
            if line.strip().startswith(('"""', "'''")) and '"""' in line[3:]:
                other_lines.append(line)
            elif line.strip().startswith('#') and import_section:
                other_lines.append(line)
            elif line.strip().startswith(('import ', 'from ')):
                imports.append(line)
            elif line.strip() == '':
                if import_section and imports:
                    continue  # Skip empty lines in import section
                other_lines.append(line)
            else:
                import_section = False
                other_lines.append(line)
        
        if imports:
            # Sort imports: standard library, third party, local
            stdlib_imports = []
            thirdparty_imports = []
            local_imports = []
            
            stdlib_modules = {
                'os', 'sys', 'json', 're', 'datetime', 'pathlib', 'typing', 'logging',
                'asyncio', 'functools', 'itertools', 'collections', 'subprocess',
                'time', 'urllib', 'http', 'email', 'xml', 'html', 'csv', 'sqlite3'
            }
            
            for imp in imports:
                module = self._extract_module_name(imp)
                if module:
                    if module.split('.')[0] in stdlib_modules:
                        stdlib_imports.append(imp)
                    elif imp.strip().startswith('from .') or module.startswith(('core', 'src', 'scripts')):
                        local_imports.append(imp)
                    else:
                        thirdparty_imports.append(imp)
                else:
                    thirdparty_imports.append(imp)
            
            # Reconstruct content with organized imports
            organized_lines = []
            
            # Add module docstring if it exists
            if other_lines and other_lines[0].strip().startswith(('"""', "'''")):
                organized_lines.append(other_lines.pop(0))
                # Add any following comment lines
                while other_lines and (other_lines[0].strip().startswith('#') or other_lines[0].strip() == ''):
                    organized_lines.append(other_lines.pop(0))
            
            # Add organized imports
            if stdlib_imports:
                organized_lines.extend(sorted(stdlib_imports))
                organized_lines.append('')
            
            if thirdparty_imports:
                organized_lines.extend(sorted(thirdparty_imports))
                organized_lines.append('')
            
            if local_imports:
                organized_lines.extend(sorted(local_imports))
                organized_lines.append('')
            
            # Add rest of the code
            organized_lines.extend(other_lines)
            
            return '\n'.join(organized_lines)
        
        return content
    
    def _extract_module_name(self, import_line: str) -> str:
        """Extract module name from import statement."""
        line = import_line.strip()
        
        if line.startswith('import '):
            module = line[7:].split()[0].split('.')[0]
            return module
        elif line.startswith('from '):
            match = re.match(r'from\s+([^\s]+)\s+import', line)
            if match:
                return match.group(1)
        
        return ''

def main():
    """Run the import error fixes."""
    fixer = ImportErrorFixer(".")
    results = fixer.run_import_fixes()
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"import_fixes_{timestamp}.json"
    
    import json
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Results saved to: {results_file}")
    return results

if __name__ == "__main__":
    main() 