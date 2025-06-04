#!/usr/bin/env python3
"""Quick syntax checker for Python files"""

import ast
import os
from pathlib import Path

def check_syntax():
    errors = []
    checked = 0
    
    for root, dirs, files in os.walk('.'):
        # Skip virtual environments and cache directories
        if 'venv' in root or '__pycache__' in root or '.git' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                checked += 1
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        ast.parse(content)
                except SyntaxError as e:
                    errors.append({
                        'file': filepath,
                        'line': e.lineno,
                        'msg': e.msg
                    })
                except Exception as e:
                    errors.append({
                        'file': filepath,
                        'line': 0,
                        'msg': str(e)
                    })
    
    print(f"Checked {checked} Python files")
    
    if errors:
        print(f"\nFound {len(errors)} syntax errors:")
        for error in errors:
            print(f"  {error['file']}:{error['line']} - {error['msg']}")
    else:
        print("✅ No syntax errors found!")

if __name__ == "__main__":
    check_syntax()