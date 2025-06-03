#!/usr/bin/env python3
"""
Automated Broken Import Fixer for Orchestra AI
Fixes the most common import issues found in the codebase analysis.
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Set
import subprocess

class ImportFixer:
    """Automatically fixes common broken import issues."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.fixes_applied = []
        self.missing_packages = set()
        
    def get_python_files(self) -> List[Path]:
        """Get all Python files to process."""
        exclude_dirs = {"venv", "node_modules", "__pycache__", ".git"}
        
        python_files = []
        for py_file in self.root_path.rglob("*.py"):
            exclude = False
            for parent in py_file.parents:
                if parent.name in exclude_dirs:
                    exclude = True
                    break
            if not exclude:
                python_files.append(py_file)
        
        return python_files
    
    def create_missing_modules(self) -> None:
        """Create commonly missing internal modules."""
        missing_modules = {
            "packages/shared/src/memory/redis_semantic_cacher.py": '''"""
Redis Semantic Caching Module
Placeholder for Redis-based semantic caching functionality.
"""

from typing import Any, Optional, Dict
import redis
import json
import hashlib

class RedisSemanticCacher:
    """Redis-based semantic caching implementation."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
    
    def get_cache_key(self, query: str) -> str:
        """Generate cache key for query."""
        return hashlib.md5(query.encode()).hexdigest()
    
    def get(self, query: str) -> Optional[Any]:
        """Get cached result for query."""
        key = self.get_cache_key(query)
        result = self.redis_client.get(key)
        return json.loads(result) if result else None
    
    def set(self, query: str, result: Any, ttl: int = 3600) -> None:
        """Cache result for query."""
        key = self.get_cache_key(query)
        self.redis_client.setex(key, ttl, json.dumps(result))
'''
        }
        
        for module_path, content in missing_modules.items():
            full_path = self.root_path / module_path
            
            # Create directory if it doesn't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py files for package structure
            current_dir = full_path.parent
            while current_dir != self.root_path:
                init_file = current_dir / "__init__.py"
                if not init_file.exists():
                    init_file.touch()
                current_dir = current_dir.parent
            
            # Write the module content
            if not full_path.exists():
                full_path.write_text(content)
                self.fixes_applied.append(f"Created missing module: {module_path}")
                print(f"✅ Created: {module_path}")
    
    def fix_import_aliases(self, file_path: Path) -> bool:
        """Fix common import alias issues."""
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            
            # Common import fixes
            fixes = {
                # Fix BeautifulSoup import
                r'from bs4 import BeautifulSoup as bs': 'from bs4 import BeautifulSoup',
                r'import bs4 as bs': 'import bs4',
                
                # Fix relative import issues
                r'from \.([^.]\w+) import': r'from shared.\1 import',
                r'from \.\.([^.]\w+) import': r'from core.\1 import',
                
                # Fix common package name issues
                r'from sentence_transformers': 'from sentence_transformers',  # Ensure correct package
                r'from playwright\.async_api': 'from playwright.async_api',
            }
            
            changes_made = False
            for pattern, replacement in fixes.items():
                new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                if new_content != content:
                    content = new_content
                    changes_made = True
            
            if changes_made:
                file_path.write_text(content, encoding='utf-8')
                self.fixes_applied.append(f"Fixed imports in: {file_path}")
                return True
                
        except Exception as e:
            print(f"⚠️  Error fixing {file_path}: {e}")
        
        return False
    
    def detect_missing_packages(self, file_path: Path) -> Set[str]:
        """Detect missing third-party packages in a file."""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Common missing packages and their install names
            package_mappings = {
                'bs4': 'beautifulsoup4',
                'playwright': 'playwright',
                'selenium': 'selenium',
                'colorama': 'colorama',
                'tabulate': 'tabulate',
                'sentence_transformers': 'sentence-transformers',
                'langchain_google_genai': 'langchain-google-genai',
                'langchain_redis': 'langchain-redis',
                'redisvl': 'redisvl',
            }
            
            missing = set()
            for import_name, package_name in package_mappings.items():
                if re.search(rf'(^|\s)import {import_name}($|\s|\.)', content, re.MULTILINE):
                    try:
                        __import__(import_name)
                    except ImportError:
                        missing.add(package_name)
                        
                if re.search(rf'from {import_name}', content):
                    try:
                        __import__(import_name)
                    except ImportError:
                        missing.add(package_name)
            
            return missing
            
        except Exception as e:
            print(f"⚠️  Error checking {file_path}: {e}")
            return set()
    
    def install_missing_packages(self, packages: Set[str]) -> None:
        """Install missing packages using pip."""
        if not packages:
            return
            
        print(f"📦 Installing missing packages: {', '.join(packages)}")
        
        try:
            # Install packages that are safe to install
            safe_packages = {'colorama', 'tabulate', 'beautifulsoup4'}
            to_install = packages & safe_packages
            
            if to_install:
                cmd = [sys.executable, '-m', 'pip', 'install'] + list(to_install)
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Successfully installed: {', '.join(to_install)}")
                    self.fixes_applied.append(f"Installed packages: {', '.join(to_install)}")
                else:
                    print(f"❌ Failed to install packages: {result.stderr}")
            
            # Report packages that need manual installation
            manual_packages = packages - safe_packages
            if manual_packages:
                print(f"⚠️  Manual installation needed: {', '.join(manual_packages)}")
                
        except Exception as e:
            print(f"❌ Error installing packages: {e}")
    
    def fix_syntax_errors(self, file_path: Path) -> bool:
        """Fix common syntax errors that prevent import."""
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            
            # Fix common syntax issues
            fixes = [
                # Fix unterminated strings
                (r'"""[^"]*$', '"""'),
                (r"'''[^']*$", "'''"),
                
                # Fix incomplete try blocks
                (r'(\s+)try:\s*$', r'\1try:\n\1    pass'),
                
                # Fix incomplete except blocks
                (r'(\s+)except[^:]*:\s*$', r'\1except Exception:\n\1    pass'),
            ]
            
            for pattern, replacement in fixes:
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            
            if content != original_content:
                file_path.write_text(content, encoding='utf-8')
                self.fixes_applied.append(f"Fixed syntax in: {file_path}")
                return True
                
        except Exception as e:
            print(f"⚠️  Error fixing syntax in {file_path}: {e}")
        
        return False
    
    def run_fixes(self) -> Dict[str, int]:
        """Run all import fixes."""
        print("🔧 Starting automatic import fixes...")
        
        # Create missing modules first
        self.create_missing_modules()
        
        # Get all Python files
        python_files = self.get_python_files()
        print(f"📁 Processing {len(python_files)} Python files...")
        
        stats = {
            "files_processed": 0,
            "imports_fixed": 0,
            "syntax_fixed": 0,
            "packages_detected": 0
        }
        
        all_missing_packages = set()
        
        for file_path in python_files:
            stats["files_processed"] += 1
            
            # Check for missing packages
            missing_packages = self.detect_missing_packages(file_path)
            all_missing_packages.update(missing_packages)
            
            # Fix syntax errors first
            if self.fix_syntax_errors(file_path):
                stats["syntax_fixed"] += 1
            
            # Fix import issues
            if self.fix_import_aliases(file_path):
                stats["imports_fixed"] += 1
        
        # Install missing packages
        if all_missing_packages:
            stats["packages_detected"] = len(all_missing_packages)
            self.install_missing_packages(all_missing_packages)
        
        return stats
    
    def generate_report(self, stats: Dict[str, int]) -> str:
        """Generate a summary report of fixes applied."""
        report = f"""
🐍 Import Fixes Applied - Summary Report
========================================

📊 STATISTICS:
• Files Processed: {stats['files_processed']}
• Import Issues Fixed: {stats['imports_fixed']}
• Syntax Issues Fixed: {stats['syntax_fixed']}
• Missing Packages Detected: {stats['packages_detected']}

✅ FIXES APPLIED:
"""
        
        for fix in self.fixes_applied:
            report += f"• {fix}\n"
        
        report += """
🚀 NEXT STEPS:
1. Run the Python codebase analyzer again to verify fixes
2. Test critical imports manually
3. Address remaining circular dependencies
4. Consider consolidating duplicate functions

📋 VERIFICATION:
Run this command to test some critical imports:
python3 -c "
try:
    import bs4
    print('✅ beautifulsoup4')
    
    import colorama
    print('✅ colorama')
    
    import tabulate
    print('✅ tabulate')
    
    from packages.shared.src.memory.redis_semantic_cacher import RedisSemanticCacher
    print('✅ redis_semantic_cacher')
    
except ImportError as e:
    print(f'❌ Still missing: {e}')
"
"""
        
        return report


def main():
    """Run the import fixer."""
    fixer = ImportFixer(".")
    stats = fixer.run_fixes()
    
    report = fixer.generate_report(stats)
    print(report)
    
    # Save report to file
    with open("import_fixes_report.txt", "w") as f:
        f.write(report)
    
    print("\n📁 Report saved to: import_fixes_report.txt")


if __name__ == "__main__":
    main()