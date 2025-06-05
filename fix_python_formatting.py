#!/usr/bin/env python3
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
