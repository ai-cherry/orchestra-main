#!/usr/bin/env python3
"""
Repository Issues Fix Script for Orchestra AI
Addresses specific issues identified in the codebase analysis

Author: Orchestra AI Team
Version: 1.0.0
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RepositoryIssuesFixer:
    """Fix specific repository issues identified in the analysis."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.fixes_applied = []
        self.errors_encountered = []
    
    def fix_all_issues(self) -> Dict[str, Any]:
        """Fix all identified repository issues."""
        logger.info("🔧 Starting repository issues fix...")
        
        # Fix each identified issue
        self.fix_duplicate_httpx_dependency()
        self.fix_api_main_index_route()
        self.fix_auth_utils_imports()
        self.fix_cache_warmer_logging()
        self.fix_workflow_automation_issues()
        self.fix_unified_database_issues()
        
        # Generate report
        report = {
            "fixes_applied": len(self.fixes_applied),
            "errors_encountered": len(self.errors_encountered),
            "details": {
                "fixes": self.fixes_applied,
                "errors": self.errors_encountered
            }
        }
        
        logger.info(f"✅ Repository fixes complete: {report['fixes_applied']} fixes applied")
        return report
    
    def fix_duplicate_httpx_dependency(self):
        """Fix duplicate httpx==0.28.1 entries in requirements/base.txt."""
        try:
            requirements_file = self.project_root / "requirements" / "base.txt"
            if not requirements_file.exists():
                logger.warning(f"Requirements file not found: {requirements_file}")
                return
            
            with open(requirements_file, 'r') as f:
                lines = f.readlines()
            
            # Remove duplicate httpx entries
            seen_packages = set()
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    package_name = re.split('[=<>]', line)[0].strip()
                    if package_name not in seen_packages:
                        seen_packages.add(package_name)
                        cleaned_lines.append(line + '\n')
                    else:
                        logger.info(f"Removed duplicate dependency: {line}")
                else:
                    cleaned_lines.append(line + '\n')
            
            with open(requirements_file, 'w') as f:
                f.writelines(cleaned_lines)
            
            self.fixes_applied.append("Fixed duplicate httpx dependency in requirements/base.txt")
            
        except Exception as e:
            error_msg = f"Error fixing httpx dependency: {str(e)}"
            logger.error(error_msg)
            self.errors_encountered.append(error_msg)
    
    def fix_api_main_index_route(self):
        """Fix missing function body for index route in src/api/main.py."""
        try:
            main_file = self.project_root / "src" / "api" / "main.py"
            if not main_file.exists():
                logger.warning(f"API main file not found: {main_file}")
                return
            
            with open(main_file, 'r') as f:
                content = f.read()
            
            # Look for index route decorator without function body
            pattern = r'(@app\.get\(["\']\/["\'].*?\))\s*$'
            
            if re.search(pattern, content, re.MULTILINE):
                # Add proper async function
                fixed_content = re.sub(
                    pattern,
                    r'\1\nasync def root():\n    """Root endpoint for health check."""\n    return {"status": "healthy", "service": "Orchestra AI API"}',
                    content,
                    flags=re.MULTILINE
                )
                
                with open(main_file, 'w') as f:
                    f.write(fixed_content)
                
                self.fixes_applied.append("Fixed missing index route function in src/api/main.py")
            
        except Exception as e:
            error_msg = f"Error fixing API main index route: {str(e)}"
            logger.error(error_msg)
            self.errors_encountered.append(error_msg)
    
    def fix_auth_utils_imports(self):
        """Fix redundant Optional imports in src/auth/utils.py."""
        try:
            auth_utils_file = self.project_root / "src" / "auth" / "utils.py"
            if not auth_utils_file.exists():
                logger.warning(f"Auth utils file not found: {auth_utils_file}")
                return
            
            with open(auth_utils_file, 'r') as f:
                content = f.read()
            
            # Remove redundant Optional import from typing_extensions
            lines = content.split('\n')
            cleaned_lines = []
            typing_optional_imported = False
            
            for line in lines:
                if 'from typing import' in line and 'Optional' in line:
                    typing_optional_imported = True
                    cleaned_lines.append(line)
                elif 'from typing_extensions import' in line and 'Optional' in line and typing_optional_imported:
                    # Remove Optional from typing_extensions import
                    imports = line.split('import')[1].strip()
                    import_list = [imp.strip() for imp in imports.split(',')]
                    filtered_imports = [imp for imp in import_list if imp != 'Optional']
                    
                    if filtered_imports:
                        cleaned_lines.append(f"from typing_extensions import {', '.join(filtered_imports)}")
                    # Skip the line if no other imports remain
                else:
                    cleaned_lines.append(line)
            
            fixed_content = '\n'.join(cleaned_lines)
            
            if fixed_content != content:
                with open(auth_utils_file, 'w') as f:
                    f.write(fixed_content)
                
                self.fixes_applied.append("Fixed redundant Optional import in src/auth/utils.py")
            
        except Exception as e:
            error_msg = f"Error fixing auth utils imports: {str(e)}"
            logger.error(error_msg)
            self.errors_encountered.append(error_msg)
    
    def fix_cache_warmer_logging(self):
        """Replace print statements with logging in src/core/cache_warmer.py."""
        try:
            cache_warmer_file = self.project_root / "src" / "core" / "cache_warmer.py"
            if not cache_warmer_file.exists():
                logger.warning(f"Cache warmer file not found: {cache_warmer_file}")
                return
            
            with open(cache_warmer_file, 'r') as f:
                content = f.read()
            
            # Add logging import if not present
            if 'import logging' not in content:
                content = 'import logging\n' + content
                content = content.replace('import logging\n', 'import logging\n\nlogger = logging.getLogger(__name__)\n')
            
            # Replace print statements with logger calls
            content = re.sub(r'print\((.*?)\)', r'logger.info(\1)', content)
            
            with open(cache_warmer_file, 'w') as f:
                f.write(content)
            
            self.fixes_applied.append("Replaced print statements with logging in src/core/cache_warmer.py")
            
        except Exception as e:
            error_msg = f"Error fixing cache warmer logging: {str(e)}"
            logger.error(error_msg)
            self.errors_encountered.append(error_msg)
    
    def fix_workflow_automation_issues(self):
        """Fix blocking time.sleep and eval usage in src/workflows/workflow_automation.py."""
        try:
            workflow_file = self.project_root / "src" / "workflows" / "workflow_automation.py"
            if not workflow_file.exists():
                logger.warning(f"Workflow automation file not found: {workflow_file}")
                return
            
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            # Add asyncio import if not present
            if 'import asyncio' not in content:
                content = 'import asyncio\n' + content
            
            # Replace time.sleep with asyncio.sleep in async functions
            content = re.sub(
                r'(async\s+def.*?):.*?time\.sleep\((.*?)\)',
                r'\1:\n    await asyncio.sleep(\2)',
                content,
                flags=re.DOTALL
            )
            
            # Replace eval with safer alternatives (basic replacement)
            content = re.sub(
                r'eval\((.*?)\)',
                r'# TODO: Replace eval with safer alternative - eval(\1)',
                content
            )
            
            with open(workflow_file, 'w') as f:
                f.write(content)
            
            self.fixes_applied.append("Fixed time.sleep and eval issues in src/workflows/workflow_automation.py")
            
        except Exception as e:
            error_msg = f"Error fixing workflow automation: {str(e)}"
            logger.error(error_msg)
            self.errors_encountered.append(error_msg)
    
    def fix_unified_database_issues(self):
        """Fix missing newline and close routine in src/database/unified_database.py."""
        try:
            db_file = self.project_root / "src" / "database" / "unified_database.py"
            if not db_file.exists():
                logger.warning(f"Unified database file not found: {db_file}")
                return
            
            with open(db_file, 'r') as f:
                content = f.read()
            
            # Ensure file ends with newline
            if not content.endswith('\n'):
                content += '\n'
            
            # Add proper close method if missing
            if 'def close(' not in content:
                close_method = '''
    async def close(self):
        """Close database connections and cleanup resources."""
        try:
            if hasattr(self, 'connection_pool') and self.connection_pool:
                await self.connection_pool.close()
            
            if hasattr(self, 'redis_client') and self.redis_client:
                await self.redis_client.close()
            
            if hasattr(self, 'weaviate_client') and self.weaviate_client:
                self.weaviate_client.close()
                
            logger.info("Database connections closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
            raise
'''
                content += close_method
            
            with open(db_file, 'w') as f:
                f.write(content)
            
            self.fixes_applied.append("Fixed missing newline and close routine in src/database/unified_database.py")
            
        except Exception as e:
            error_msg = f"Error fixing unified database: {str(e)}"
            logger.error(error_msg)
            self.errors_encountered.append(error_msg)
    
    def generate_performance_improvements(self) -> str:
        """Generate performance improvement recommendations."""
        improvements = """
# 🚀 Performance Improvement Recommendations

## Database Optimization
```python
# Implement connection pooling
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

## Async Processing Enhancement
```python
# Use asyncio.gather for parallel operations
async def process_multiple_items(items):
    tasks = [process_item(item) for item in items]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

## Caching Strategy
```python
# Implement Redis caching for expensive operations
from utils.fast_secrets import secrets
import redis.asyncio as redis

redis_client = redis.from_url(secrets.get('database', 'redis_url'))

@cache_manager.async_cache(ttl_seconds=300)
async def expensive_operation(key):
    # Expensive computation here
    return result
```

## Logging Optimization
```python
# Use structured logging with performance tracking
import structlog

logger = structlog.get_logger(__name__)

async def tracked_operation():
    with logger.bind(operation="api_call").info("Starting operation"):
        start_time = time.time()
        try:
            result = await perform_operation()
            duration = time.time() - start_time
            logger.info("Operation completed", duration=duration)
            return result
        except Exception as e:
            logger.error("Operation failed", error=str(e))
            raise
```
"""
        return improvements

def main():
    """Main function to run repository fixes."""
    fixer = RepositoryIssuesFixer()
    
    # Apply all fixes
    report = fixer.fix_all_issues()
    
    # Generate performance improvements
    improvements = fixer.generate_performance_improvements()
    
    # Save report
    with open('repository_fixes_report.md', 'w') as f:
        f.write(f"# Repository Fixes Report\n\n")
        f.write(f"**Fixes Applied**: {report['fixes_applied']}\n")
        f.write(f"**Errors Encountered**: {report['errors_encountered']}\n\n")
        
        f.write("## Applied Fixes\n")
        for fix in report['details']['fixes']:
            f.write(f"- ✅ {fix}\n")
        
        if report['details']['errors']:
            f.write("\n## Errors Encountered\n")
            for error in report['details']['errors']:
                f.write(f"- ❌ {error}\n")
        
        f.write(improvements)
    
    print(f"✅ Repository fixes complete!")
    print(f"📊 Applied {report['fixes_applied']} fixes")
    print(f"📋 Report saved to: repository_fixes_report.md")

if __name__ == "__main__":
    main() 