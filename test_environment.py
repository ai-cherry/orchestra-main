#!/usr/bin/env python3
"""Test script to verify the Orchestra AI development environment."""

import sys
from typing import Dict, List

def check_python_version() -> bool:
    """Check if Python version is 3.10.x"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    return version.major == 3 and version.minor == 10

def check_imports() -> Dict[str, bool]:
    """Check if all required packages can be imported."""
    packages = [
        "fastapi",
        "uvicorn", 
        "pydantic",
        "sqlalchemy",
        "asyncpg",
        "redis",
        "passlib",
        "jose",
        "httpx",
        "psutil",
        "yaml"
    ]
    
    results = {}
    for package in packages:
        try:
            if package == "jose":
                __import__("jose")
            elif package == "yaml":
                __import__("yaml")
            else:
                __import__(package)
            results[package] = True
            print(f"✅ {package} - imported successfully")
        except ImportError as e:
            results[package] = False
            print(f"❌ {package} - import failed: {e}")
    
    return results

def main():
    """Run all environment checks."""
    print("=== Orchestra AI Environment Check ===\n")
    
    # Check Python version
    print("1. Python Version Check:")
    if check_python_version():
        print("✅ Python 3.10 is correctly installed\n")
    else:
        print("❌ Warning: Not using Python 3.10\n")
    
    # Check imports
    print("2. Package Import Check:")
    results = check_imports()
    
    # Summary
    print("\n=== Summary ===")
    total = len(results)
    successful = sum(1 for v in results.values() if v)
    print(f"Successfully imported: {successful}/{total} packages")
    
    if successful == total:
        print("\n🎉 Environment is ready for Orchestra AI development!")
    else:
        print("\n⚠️  Some packages failed to import. Please check the errors above.")
    
    return successful == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 