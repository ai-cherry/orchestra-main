#!/usr/bin/env python3
"""
Fix Naming Edge Cases
Corrects issues from the initial refactoring script where overly aggressive replacements
created incorrect naming patterns like 'conductor' instead of 'conductor'.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NamingEdgeCaseFixer:
    """Fixes edge cases in naming convention refactoring"""
    
    def __init__(self, root_dir: Path, dry_run: bool = False):
        self.root_dir = Path(root_dir)
        self.dry_run = dry_run
        
        # Specific edge case mappings to fix
        self.edge_case_fixes = {
            # Incorrectly transformed words
            "conductor": "conductor",
            "coordination": "coordination", 
            "conductor": "conductor",
            "coordination": "coordination",
            "coordination": "coordination",
            "coordinating": "coordinating",
            "coordinate": "coordinate",
            "coordinated": "coordinated", 
            "coordinates": "coordinates",
            "coordinating": "coordinating",
            
            # Class name fixes
            "Workflowconductor": "WorkflowConductor",
            "UnifiedWorkflowconductor": "UnifiedWorkflowConductor", 
            "Migrationconductor": "MigrationConductor",
            "PayReadyETLconductor": "PayReadyETLConductor",
            "MCPconductor": "MCPConductor",
            "AIconductor": "AIConductor",
            "Serviceconductor": "ServiceConductor",
            
            # Environment variable fixes
            "CHERRY_AI_CONDUCTOR_PORT": "CHERRY_AI_CONDUCTOR_PORT",
            "CHERRY_AI_CONDUCTOR_PORT": "CHERRY_AI_CONDUCTOR_PORT",
            "CHERRY_AI_CONDUCTOR_PORT": "CHERRY_AI_CONDUCTOR_PORT",
            
            # File reference fixes
            "unified_mcp_conductor.py": "unified_mcp_conductor.py",
            "ai_conductor.py": "ai_conductor.py", 
            "conductor_cli.py": "conductor_cli.py",
            "conductor-mcp": "conductor-mcp",
            "conductor.log": "conductor.log",
            
            # Description fixes
            "Cherry AI": "Cherry AI",
            "ai-conductor-dashboard": "ai-conductor-dashboard",
            "AI conductor": "AI Conductor",
            "conductor MCP": "Conductor MCP",
            "conductor configuration": "conductor configuration",
            "conductor Status": "Conductor Status",
            "roo_conductor_agent": "roo_conductor_agent",
            
            # Database/config fixes
            "POSTGRES_USER.*conductor": "POSTGRES_USER=conductor",
            "POSTGRES_DB.*conductor": "POSTGRES_DB=cherry_ai",
        }
        
        # Patterns that need careful regex replacement
        self.regex_fixes = [
            # Fix compound words that got mangled
            (r'\bcherry_ai(tor|tion|trat|tral)\b', self._fix_compound_words),
            (r'\bcherry_ai([A-Z]\w*)', self._fix_camel_case),
            (r'Cherry AI\b', 'Cherry AI'),
            (r'\bai_cherry_ai\b', 'ai_conductor'),
            # Fix environment variable patterns
            (r'MCP_cherry_ai([A-Z_]*?)_PORT', r'CHERRY_AI_CONDUCTOR_PORT'),
            # Fix service names
            (r'conductor-mcp\b', 'conductor-mcp'),
            (r'conductor-mcp\b', 'conductor-mcp'),
        ]
    
    def _fix_compound_words(self, match) -> str:
        """Fix compound words that got mangled during replacement"""
        suffix = match.group(1)
        if suffix in ['tor', 'tors']:
            return 'conductor'
        elif suffix in ['tion', 'tions']:
            return 'coordination'
        elif suffix in ['trat', 'trate', 'trated', 'trates', 'trating']:
            return 'coordinate'
        elif suffix in ['tral']:
            return 'coordination'
        else:
            return match.group(0)  # Return original if no match
    
    def _fix_camel_case(self, match) -> str:
        """Fix CamelCase words that got mangled"""
        suffix = match.group(1)
        if suffix.startswith('tor'):
            return f'Conductor{suffix[3:]}'
        elif suffix.startswith('tion'):
            return f'Coordination{suffix[4:]}'
        else:
            return match.group(0)
    
    def fix_file_content(self, file_path: Path) -> bool:
        """Fix content of a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply direct string replacements
            for old_pattern, new_pattern in self.edge_case_fixes.items():
                if old_pattern in content:
                    content = content.replace(old_pattern, new_pattern)
                    logger.info(f"  Fixed '{old_pattern}' → '{new_pattern}' in {file_path.name}")
            
            # Apply regex replacements
            for pattern, replacement in self.regex_fixes:
                if callable(replacement):
                    content = re.sub(pattern, replacement, content)
                else:
                    content = re.sub(pattern, replacement, content)
            
            # Special handling for JSON files
            if file_path.suffix == '.json':
                content = self._fix_json_content(content, file_path)
            
            if content != original_content:
                if not self.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                logger.info(f"  Updated: {file_path.relative_to(self.root_dir)}")
                return True
                
        except Exception as e:
            logger.error(f"Error fixing {file_path}: {e}")
            
        return False
    
    def _fix_json_content(self, content: str, file_path: Path) -> str:
        """Special handling for JSON files"""
        try:
            # Handle .mcp.json specifically
            if file_path.name == '.mcp.json':
                data = json.loads(content)
                
                # Fix the server name key
                if 'servers' in data and 'conductor' in data['servers']:
                    data['servers']['conductor'] = data['servers'].pop('conductor')
                    data['servers']['conductor']['args'] = ['mcp_server/servers/conductor_server.py']
                    
                    # Fix environment variables
                    if 'env' in data['servers']['conductor']:
                        env = data['servers']['conductor']['env']
                        if 'CHERRY_AI_CONDUCTOR_PORT' in env:
                            env['CHERRY_AI_CONDUCTOR_PORT'] = env.pop('CHERRY_AI_CONDUCTOR_PORT')
                
                # Fix client section
                if 'client' in data and 'mcpServers' in data['client']:
                    if 'conductor' in data['client']['mcpServers']:
                        data['client']['mcpServers']['conductor'] = data['client']['mcpServers'].pop('conductor')
                        data['client']['mcpServers']['conductor']['args'] = ['mcp_server/servers/conductor_server.py']
                
                content = json.dumps(data, indent=2)
                logger.info(f"  Fixed JSON structure in {file_path.name}")
                
        except json.JSONDecodeError:
            # If JSON parsing fails, fall back to string replacement
            pass
            
        return content
    
    def fix_all_files(self) -> None:
        """Fix all files in the codebase"""
        logger.info(f"Starting edge case fixes (dry_run={self.dry_run})")
        
        # File extensions to process
        extensions = [".py", ".json", ".yml", ".yaml", ".md", ".sh", ".env", ".txt"]
        
        # Find all files to update
        files_to_update = []
        for ext in extensions:
            files_to_update.extend(self.root_dir.rglob(f"*{ext}"))
        
        # Skip certain directories
        skip_patterns = [".git/", "venv/", "__pycache__/", "node_modules/", ".backup"]
        
        fixed_count = 0
        for file_path in files_to_update:
            if any(pattern in str(file_path) for pattern in skip_patterns):
                continue
                
            if self.fix_file_content(file_path):
                fixed_count += 1
        
        logger.info(f"✓ Fixed {fixed_count} files")
    
    def run_verification(self) -> bool:
        """Verify that edge cases were fixed"""
        logger.info("Verifying edge case fixes...")
        
        # Check for remaining problematic patterns
        problematic_patterns = [
            r'\bconductor\b',
            r'\bcoordination\b', 
            r'\bCHERRY_AI_CONDUCTOR_PORT\b',
            r'\bUnifiedWorkflowconductor\b',
            r'\bPayReadyETLconductor\b'
        ]
        
        issues = []
        python_files = list(self.root_dir.rglob("*.py"))
        config_files = list(self.root_dir.rglob("*.json"))
        
        for file_path in python_files + config_files:
            if any(pattern in str(file_path) for pattern in [".git/", "venv/", "__pycache__/"]):
                continue
                
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                for pattern in problematic_patterns:
                    if re.search(pattern, content):
                        issues.append(f"Found '{pattern}' in {file_path}")
                        
            except Exception:
                continue
        
        if issues:
            logger.warning("Verification found remaining issues:")
            for issue in issues[:10]:  # Show first 10 issues
                logger.warning(f"  - {issue}")
            return False
        else:
            logger.info("✓ Verification passed - no edge case issues found")
            return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix naming edge cases")
    parser.add_argument("--root-dir", default=".", help="Root directory of project")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--execute", action="store_true", help="Execute fixes")
    
    args = parser.parse_args()
    
    if not args.execute and not args.dry_run:
        args.dry_run = True
        logger.info("No mode specified, running in dry-run mode")
    
    fixer = NamingEdgeCaseFixer(
        root_dir=Path(args.root_dir),
        dry_run=args.dry_run
    )
    
    fixer.fix_all_files()
    
    if not args.dry_run:
        success = fixer.run_verification()
        if success:
            print("\n✅ Edge case fixes completed successfully!")
        else:
            print("\n⚠️ Edge case fixes completed with some remaining issues")
    else:
        print("\n🔍 Dry run completed - run with --execute to apply fixes")

if __name__ == "__main__":
    main() 