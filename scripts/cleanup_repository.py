#!/usr/bin/env python3
"""
Repository Cleanup Script for AI Coding Optimization

This script cleans up backup directories, migration files, and other junk
that clutters the codebase and makes it harder for AI tools to understand
the project structure.

Focus: Performance, stability, and optimization over security/cost.
"""

import os
import shutil
import sys
from pathlib import Path
from typing import List, Tuple
import argparse
import json
from datetime import datetime

class RepositoryCleanup:
    """Clean up repository for optimal AI tool performance."""
    
        self.cleanup_patterns = [
            "*backup*",
            "*migration*", 
            "*refactor*",
            "*old*",
            "*deprecated*",
            "*unused*",
            "*temp*",
            "*tmp*"
        ]
        self.preserve_patterns = [
            ".git",
            ".ai-tools",
            "mcp_server",
            "admin-interface",
            "infrastructure",
            "venv",
            "node_modules"
        ]
        
    def scan_for_cleanup(self) -> List[Tuple[Path, int]]:
        """Scan for directories and files that can be cleaned up."""
        cleanup_candidates = []
        
        for pattern in self.cleanup_patterns:
            # Find directories matching cleanup patterns
                if path.is_dir() and self._should_cleanup(path):
                    size = self._calculate_directory_size(path)
                    cleanup_candidates.append((path, size))
                    
        return sorted(cleanup_candidates, key=lambda x: x[1], reverse=True)
    
    def _should_cleanup(self, path: Path) -> bool:
        """Check if a path should be cleaned up."""
        # Don't cleanup if it's in preserve patterns
        for preserve in self.preserve_patterns:
            if preserve in str(path):
                return False
                
        if len(relative_path.parts) < 2:
            return False
            
        return True
    
    def _calculate_directory_size(self, path: Path) -> int:
        """Calculate total size of directory in bytes."""
        total_size = 0
        try:
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except (OSError, PermissionError):
            pass
        return total_size
    
    def preview_cleanup(self) -> dict:
        """Preview what would be cleaned up."""
        candidates = self.scan_for_cleanup()
        
        total_size = sum(size for _, size in candidates)
        total_dirs = len(candidates)
        
        preview = {
            "total_directories": total_dirs,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "directories": []
        }
        
        for path, size in candidates:
            preview["directories"].append({
                "size_bytes": size,
                "size_mb": size / (1024 * 1024)
            })
            
        return preview
    
    def execute_cleanup(self, dry_run: bool = True) -> dict:
        """Execute the cleanup operation."""
        candidates = self.scan_for_cleanup()
        
        results = {
            "dry_run": dry_run,
            "timestamp": datetime.now().isoformat(),
            "total_directories": len(candidates),
            "total_size_freed": 0,
            "cleaned_directories": [],
            "errors": []
        }
        
        for path, size in candidates:
            try:
                if dry_run:
                    results["cleaned_directories"].append({
                        "size_mb": size / (1024 * 1024),
                        "action": "would_delete"
                    })
                else:
                    shutil.rmtree(path)
                    results["cleaned_directories"].append({
                        "size_mb": size / (1024 * 1024),
                        "action": "deleted"
                    })
                    
                results["total_size_freed"] += size
                
            except Exception as e:
                results["errors"].append({
                    "error": str(e)
                })
        
        results["total_size_freed_mb"] = results["total_size_freed"] / (1024 * 1024)
        return results
    
    def optimize_gitignore(self):
        """Optimize .gitignore for AI tools."""
        
        ai_tool_ignores = [
            "",
            "# AI Tools and Artifacts",
            "*.pyc",
            "__pycache__/",
            ".pytest_cache/",
            ".coverage",
            ".mypy_cache/",
            ".ruff_cache/",
            "",
            "# AI Tool Outputs",
            ".ai-memory/",
            ".cursor/",
            ".vscode/settings.json",
            "*.log",
            "*.tmp",
            "",
            "# Backup and Migration Files",
            "*backup*/",
            "*migration*/",
            "*refactor*/",
            "*old*/",
            "*deprecated*/",
            "*unused*/",
            "*temp*/",
            "*tmp*/",
            "",
            "# Environment and Secrets",
            ".env",
            ".env.local",
            ".env.*.local",
            "*.key",
            "*.pem",
            "",
            "# Dependencies",
            "node_modules/",
            "venv/",
            ".venv/",
            "",
            "# Build Outputs",
            "dist/",
            "build/",
            "*.egg-info/",
            "",
            "# IDE Files",
            ".idea/",
            "*.swp",
            "*.swo",
            "*~",
            "",
            "# OS Files",
            ".DS_Store",
            "Thumbs.db",
            ""
        ]
        
        try:
            # Read existing gitignore
            existing_content = ""
            if gitignore_path.exists():
                with open(gitignore_path, 'r') as f:
                    existing_content = f.read()
            
            # Add AI tool ignores if not already present
            new_content = existing_content
            for ignore_line in ai_tool_ignores:
                if ignore_line and ignore_line not in existing_content:
                    new_content += ignore_line + "\n"
            
            # Write updated gitignore
            with open(gitignore_path, 'w') as f:
                f.write(new_content)
                
            return True
            
        except Exception as e:
            print(f"Error updating .gitignore: {e}")
            return False
    
    def create_ai_tools_structure(self):
        """Create optimized directory structure for AI tools."""
        ai_tools_dirs = [
            ".ai-tools/cursor",
            ".ai-tools/codex",
            ".ai-tools/factory-ai",
            ".ai-tools/apis",
            ".ai-tools/prompts/coding",
            ".ai-tools/prompts/debugging", 
            ".ai-tools/prompts/architecture",
            ".ai-tools/prompts/optimization",
            "scripts/ai-tools",
            "docs/ai-tools"
        ]
        
        created_dirs = []
        for dir_path in ai_tools_dirs:
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(dir_path)
            except Exception as e:
                print(f"Error creating {dir_path}: {e}")
        
        return created_dirs
    
    def generate_cleanup_report(self, results: dict) -> str:
        """Generate a human-readable cleanup report."""
        report = f"""
# Repository Cleanup Report

**Timestamp:** {results['timestamp']}
**Mode:** {'Dry Run' if results['dry_run'] else 'Execution'}

## Summary
- **Directories processed:** {results['total_directories']}
- **Total space freed:** {results['total_size_freed_mb']:.1f} MB
- **Errors encountered:** {len(results['errors'])}

## Cleaned Directories
"""
        
        for item in results['cleaned_directories']:
            action = "🔍 Would delete" if results['dry_run'] else "🗑️ Deleted"
            report += f"- {action}: `{item['path']}` ({item['size_mb']:.1f} MB)\n"
        
        if results['errors']:
            report += "\n## Errors\n"
            for error in results['errors']:
                report += f"- ❌ `{error['path']}`: {error['error']}\n"
        
        report += f"""
## Recommendations

### For AI Tool Optimization:
1. **Repository Structure**: Clean, organized directories improve AI tool context understanding
2. **Performance**: Reduced file count improves scanning and indexing speed
3. **Focus**: AI tools can better focus on active code without backup distractions

### Next Steps:
1. Run with `--execute` to perform actual cleanup
2. Update AI tool configurations to use optimized structure
3. Set up automated cleanup in CI/CD pipeline
4. Configure AI tools to ignore backup patterns

**Focus:** Performance, stability, and optimization over security/cost.
"""
        
        return report

def main():
    parser = argparse.ArgumentParser(
        description="Clean up repository for optimal AI coding tool performance"
    )
    parser.add_argument(
        "--execute", 
        action="store_true",
        help="Actually perform cleanup (default is dry run)"
    )
    parser.add_argument(
        default=".",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format for results"
    )
    parser.add_argument(
        "--optimize-structure",
        action="store_true",
        help="Also optimize directory structure and .gitignore for AI tools"
    )
    
    args = parser.parse_args()
    
    # Initialize cleanup
    
    print("🤖 Repository Cleanup for AI Coding Optimization")
    print("=" * 50)
    print(f"Mode: {'EXECUTION' if args.execute else 'DRY RUN'}")
    print()
    
    # Execute cleanup
    results = cleanup.execute_cleanup(dry_run=not args.execute)
    
    # Optimize structure if requested
    if args.optimize_structure:
        print("🏗️ Optimizing repository structure for AI tools...")
        created_dirs = cleanup.create_ai_tools_structure()
        gitignore_updated = cleanup.optimize_gitignore()
        
        print(f"✅ Created {len(created_dirs)} AI tool directories")
        print(f"✅ Updated .gitignore: {gitignore_updated}")
        print()
    
    # Output results
    if args.output_format == "json":
        print(json.dumps(results, indent=2))
    else:
        report = cleanup.generate_cleanup_report(results)
        print(report)
    
    # Summary
    if not args.execute and results['total_directories'] > 0:
        print("\n⚠️  This was a dry run. Use --execute to actually perform cleanup.")
        print("💡 Tip: Review the directories above before executing cleanup.")
    elif args.execute:
        print(f"\n🎉 Cleanup complete! Freed {results['total_size_freed_mb']:.1f} MB")
        print("🚀 Repository optimized for AI coding tools!")

if __name__ == "__main__":
    main()

