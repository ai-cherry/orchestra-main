#!/usr/bin/env python3
"""
Final Naming Cleanup Script
Fixes the remaining edge cases in variable names and constants that weren't 
caught by the previous refactoring scripts.
"""

import os
import re
from pathlib import Path
from typing import Dict, List
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinalNamingCleanup:
    """Final cleanup for remaining naming issues"""
    
    def __init__(self, root_dir: Path, dry_run: bool = False):
        self.root_dir = Path(root_dir)
        self.dry_run = dry_run
        
        # Remaining problematic patterns to fix
        self.final_fixes = {
            # Variable/constant names that got mangled
            "CONDUCTOR": "CONDUCTOR",
            "COORDINATION": "COORDINATION",
            "coordination": "coordination",
            "conductor": "conductor",
            
            # Environment variables
            "MCP_CHERRY_AI_MEMORY_HOST": "MCP_CHERRY_AI_MEMORY_HOST",
            "CONDUCTOR_URL": "CONDUCTOR_URL",
            "CONDUCTOR_PID": "CONDUCTOR_PID",
            "CONDUCTOR_DOMAIN": "CONDUCTOR_DOMAIN",
            
            # Config field names
            "COORDINATION_MAX_CONCURRENT_AGENTS": "COORDINATION_MAX_CONCURRENT_AGENTS",
            "COORDINATION_AGENT_TIMEOUT": "COORDINATION_AGENT_TIMEOUT", 
            "COORDINATION_AGENT_RETRY_ATTEMPTS": "COORDINATION_AGENT_RETRY_ATTEMPTS",
            "COORDINATION_MAX_WORKFLOW_STEPS": "COORDINATION_MAX_WORKFLOW_STEPS",
            "COORDINATION_WORKFLOW_TIMEOUT": "COORDINATION_WORKFLOW_TIMEOUT",
            "COORDINATION_EVENT_QUEUE_SIZE": "COORDINATION_EVENT_QUEUE_SIZE",
            "COORDINATION_EVENT_PROCESSING_INTERVAL": "COORDINATION_EVENT_PROCESSING_INTERVAL",
            "COORDINATION_MAX_MEMORY_USAGE": "COORDINATION_MAX_MEMORY_USAGE",
            "COORDINATION_MAX_CPU_USAGE": "COORDINATION_MAX_CPU_USAGE",
            
            # Enum/constant values
            "ServiceType.CONDUCTOR": "ServiceType.CONDUCTOR",
            "RooMode.CONDUCTOR": "RooMode.CONDUCTOR",
            "AgentModeType.CONDUCTOR": "AgentModeType.CONDUCTOR",
            "UseCase.WORKFLOW_COORDINATION": "UseCase.WORKFLOW_COORDINATION",
            "_HAS_ENHANCED_CONDUCTOR": "_HAS_ENHANCED_CONDUCTOR",
            
            # Comments and messages
            "AI CONDUCTOR": "AI CONDUCTOR",
            "ROO + AI CONDUCTOR": "ROO + AI CONDUCTOR",
            "INTERACTIVE CONDUCTOR": "INTERACTIVE CONDUCTOR",
            "ENHANCED COORDINATION": "ENHANCED COORDINATION",
            "AI CONDUCTOR DEMONSTRATION": "AI CONDUCTOR DEMONSTRATION",
            "CONDUCTOR STARTUP COMPLETE": "CONDUCTOR STARTUP COMPLETE",
            "MULTI-MODEL DOMAIN COORDINATION": "MULTI-MODEL DOMAIN COORDINATION",
            "AI COORDINATION SYSTEM": "AI COORDINATION SYSTEM",
            "CONDUCTOR_LANDING_PAGE": "CONDUCTOR_LANDING_PAGE",
            "CONDUCTOR_IMPLEMENTATION": "CONDUCTOR_IMPLEMENTATION",
            
            # File paths and references
            "AI_CONDUCTOR_GUIDE.md": "AI_CONDUCTOR_GUIDE.md",
            "ENHANCED_COORDINATION_GUIDE.md": "ENHANCED_COORDINATION_GUIDE.md",
            
            # Constants
            "WORKFLOW_COORDINATION": "WORKFLOW_COORDINATION",
        }
    
    def fix_file_content(self, file_path: Path) -> bool:
        """Fix content of a single file"""
        try:
            # Skip certain directories
            skip_patterns = [".git/", "venv/", "__pycache__/", "node_modules/"]
            if any(pattern in str(file_path) for pattern in skip_patterns):
                return False
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply fixes
            for old_pattern, new_pattern in self.final_fixes.items():
                if old_pattern in content:
                    content = content.replace(old_pattern, new_pattern)
                    logger.info(f"  Fixed '{old_pattern}' → '{new_pattern}' in {file_path.name}")
            
            # Special regex patterns for complex cases
            content = re.sub(r'\bcherry_ai([A-Z_]*?)TOR\b', r'CONDUCTOR', content)
            content = re.sub(r'\bcherry_ai([A-Z_]*?)TION\b', r'COORDINATION', content)
            
            if content != original_content:
                if not self.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                logger.info(f"  Updated: {file_path.relative_to(self.root_dir)}")
                return True
                
        except Exception as e:
            logger.error(f"Error fixing {file_path}: {e}")
            
        return False
    
    def fix_all_files(self) -> None:
        """Fix all remaining files"""
        logger.info(f"Starting final naming cleanup (dry_run={self.dry_run})")
        
        # File extensions to process
        extensions = [".py", ".json", ".yml", ".yaml", ".md", ".sh", ".env", ".txt"]
        
        # Find all files to update
        files_to_update = []
        for ext in extensions:
            files_to_update.extend(self.root_dir.rglob(f"*{ext}"))
        
        fixed_count = 0
        for file_path in files_to_update:
            if self.fix_file_content(file_path):
                fixed_count += 1
        
        logger.info(f"✓ Fixed {fixed_count} files in final cleanup")
    
    def verify_completion(self) -> bool:
        """Verify that all naming issues are resolved"""
        logger.info("Running final verification...")
        
        problematic_patterns = [
            r'\bCONDUCTOR\b',
            r'\bCOORDINATION\b',
            r'\bMCP_cherry_ai_\w+',
            r'\bServiceType\.CONDUCTOR\b',
            r'\bRooMode\.CONDUCTOR\b',
            r'\bWORKFLOW_COORDINATION\b'
        ]
        
        issues = []
        
        # Check key files
        key_files = [
            ".mcp.json",
            "core/config/unified_config.py", 
            "core/llm_types.py",
            "mcp_server/models/agent_mode.py",
            "ai_components/coordination/unified_api_router.py"
        ]
        
        for file_path in key_files:
            full_path = self.root_dir / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                    
                    for pattern in problematic_patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            issues.append(f"Found '{pattern}' in {file_path}: {matches}")
                            
                except Exception:
                    continue
        
        if issues:
            logger.warning("Final verification found remaining issues:")
            for issue in issues:
                logger.warning(f"  - {issue}")
            return False
        else:
            logger.info("✓ Final verification passed - all naming issues resolved")
            return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Final naming cleanup")
    parser.add_argument("--root-dir", default=".", help="Root directory of project")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--execute", action="store_true", help="Execute fixes")
    
    args = parser.parse_args()
    
    if not args.execute and not args.dry_run:
        args.dry_run = True
        logger.info("No mode specified, running in dry-run mode")
    
    cleanup = FinalNamingCleanup(
        root_dir=Path(args.root_dir),
        dry_run=args.dry_run
    )
    
    cleanup.fix_all_files()
    
    if not args.dry_run:
        success = cleanup.verify_completion()
        if success:
            print("\n✅ Final cleanup completed successfully!")
            print("🎯 Cherry AI naming scheme is now fully aligned!")
        else:
            print("\n⚠️ Final cleanup completed with some remaining issues")
    else:
        print("\n🔍 Dry run completed - run with --execute to apply final fixes")

if __name__ == "__main__":
    main() 