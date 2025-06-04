#!/usr/bin/env python3
"""
Naming Convention Refactoring Script
Resolves naming conflicts between cherry_ai/conductor/cherry-ai components
"""

import os
import re
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess
import logging
from datetime import datetime
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NamingConventionRefactor:
    """Automates the refactoring of naming conventions"""
    
    def __init__(self, root_dir: Path, dry_run: bool = True):
        self.root_dir = Path(root_dir)
        self.dry_run = dry_run
        self.backup_dir = self.root_dir / f".naming_refactor_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Naming mappings
        self.directory_mappings = {
            "core/conductor": "core/conductor",
            "ai_components/coordination": "ai_components/coordination"
        }
        
        self.file_mappings = {
            "mcp_server/servers/conductor_server.py": "mcp_server/servers/conductor_server.py",
            "mcp_server/servers/coordinator_server.py": "mcp_server/servers/coordinator_server.py",
            "ai_components/coordination/ai_conductor.py": "ai_components/coordination/ai_coordinator.py",
            "ai_components/coordination/comprehensive_conductor.py": "ai_components/coordination/cherry_ai_conductor.py"
        }
        
        self.class_mappings = {
            "CherryAIConductor": "CherryAIConductor",
            "ConductorServer": "ConductorServer", 
            "AICoordinator": "AICoordinator",
            "MCPCoordinator": "MCPCoordinator",
            "coordinator_server": "coordinator_server",
            "conductor_server": "conductor_server"
        }
        
        self.config_mappings = {
            "cherry_ai": "cherry_ai",
            "Cherry AI MCP": "Cherry AI MCP Platform",
            "conductor": "conductor",
            "CHERRY_AI_CONDUCTOR_PORT": "CHERRY_AI_CONDUCTOR_PORT",
            "DATABASE_URL.*cherry_ai": "DATABASE_URL.*cherry_ai"
        }
        
    def create_backup(self) -> None:
        """Create backup of current state"""
        if not self.dry_run:
            logger.info(f"Creating backup in {self.backup_dir}")
            self.backup_dir.mkdir(exist_ok=True)
            
            # Backup key files and directories
            backup_targets = [
                ".mcp.json",
                ".env",
                "docker-compose.yml",
                "core/conductor/",
                "ai_components/coordination/",
                "mcp_server/servers/"
            ]
            
            for target in backup_targets:
                src = self.root_dir / target
                if src.exists():
                    dst = self.backup_dir / target
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    if src.is_dir():
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)
    
    def rename_directories(self) -> None:
        """Rename directories according to mappings"""
        logger.info("Renaming directories...")
        
        for old_path, new_path in self.directory_mappings.items():
            old_full = self.root_dir / old_path
            new_full = self.root_dir / new_path
            
            if old_full.exists():
                logger.info(f"  {old_path} → {new_path}")
                if not self.dry_run:
                    new_full.parent.mkdir(parents=True, exist_ok=True)
                    subprocess.run(["git", "mv", str(old_full), str(new_full)], 
                                 cwd=self.root_dir, check=False)
    
    def rename_files(self) -> None:
        """Rename files according to mappings"""
        logger.info("Renaming files...")
        
        for old_path, new_path in self.file_mappings.items():
            old_full = self.root_dir / old_path
            new_full = self.root_dir / new_path
            
            if old_full.exists():
                logger.info(f"  {old_path} → {new_path}")
                if not self.dry_run:
                    new_full.parent.mkdir(parents=True, exist_ok=True)
                    subprocess.run(["git", "mv", str(old_full), str(new_full)], 
                                 cwd=self.root_dir, check=False)
    
    def update_file_contents(self) -> None:
        """Update file contents with new names"""
        logger.info("Updating file contents...")
        
        # File extensions to process
        extensions = [".py", ".json", ".yml", ".yaml", ".md", ".sh", ".env"]
        
        # Find all files to update
        files_to_update = []
        for ext in extensions:
            files_to_update.extend(self.root_dir.rglob(f"*{ext}"))
        
        for file_path in files_to_update:
            if self._should_skip_file(file_path):
                continue
                
            self._update_file_content(file_path)
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = [
            ".git/",
            "venv/",
            "__pycache__/",
            ".backup",
            "node_modules/"
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _update_file_content(self, file_path: Path) -> None:
        """Update content of a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply class/function mappings
            for old_name, new_name in self.class_mappings.items():
                content = re.sub(
                    rf'\b{re.escape(old_name)}\b',
                    new_name,
                    content
                )
            
            # Apply configuration mappings
            for old_config, new_config in self.config_mappings.items():
                content = re.sub(
                    rf'{re.escape(old_config)}',
                    new_config,
                    content,
                    flags=re.IGNORECASE
                )
            
            # Update import statements
            content = self._update_imports(content)
            
            # Update file paths in configs
            content = self._update_file_paths(content)
            
            if content != original_content:
                logger.info(f"  Updated: {file_path.relative_to(self.root_dir)}")
                if not self.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
        except Exception as e:
            logger.error(f"Error updating {file_path}: {e}")
    
    def _update_imports(self, content: str) -> str:
        """Update import statements"""
        # Update relative imports
        content = re.sub(
            r'from (.*\.)?coordination import',
            r'from \1coordination import',
            content
        )
        
        content = re.sub(
            r'from (.*\.)?conductor import',
            r'from \1conductor import',
            content
        )
        
        return content
    
    def _update_file_paths(self, content: str) -> str:
        """Update file paths in configuration files"""
        for old_path, new_path in self.file_mappings.items():
            content = content.replace(old_path, new_path)
            
        return content
    
    def update_configuration_files(self) -> None:
        """Update key configuration files"""
        logger.info("Updating configuration files...")
        
        # Update .mcp.json
        mcp_config_path = self.root_dir / ".mcp.json"
        if mcp_config_path.exists():
            self._update_mcp_config(mcp_config_path)
        
        # Update docker-compose.yml
        docker_compose_path = self.root_dir / "docker-compose.yml"
        if docker_compose_path.exists():
            self._update_docker_compose(docker_compose_path)
        
        # Update .env files
        for env_file in self.root_dir.glob(".env*"):
            if env_file.is_file():
                self._update_env_file(env_file)
    
    def _update_mcp_config(self, config_path: Path) -> None:
        """Update MCP configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update main config
            config["name"] = "Cherry AI MCP Platform"
            
            # Update servers section
            if "servers" in config:
                servers = config["servers"]
                
                # Rename conductor to conductor
                if "conductor" in servers:
                    servers["conductor"] = servers.pop("conductor")
                    servers["conductor"]["args"] = ["mcp_server/servers/conductor_server.py"]
                
                # Update environment variables
                for server_config in servers.values():
                    if "env" in server_config:
                        env = server_config["env"]
                        for key, value in list(env.items()):
                            if "CONDUCTOR" in key:
                                new_key = key.replace("CONDUCTOR", "CONDUCTOR")
                                env[new_key] = value
                                del env[key]
                            if "cherry_ai" in str(value).lower():
                                env[key] = str(value).replace("cherry_ai", "cherry_ai")
            
            # Update client section
            if "client" in config and "mcpServers" in config["client"]:
                client_servers = config["client"]["mcpServers"]
                if "conductor" in client_servers:
                    client_servers["conductor"] = client_servers.pop("conductor")
                    client_servers["conductor"]["args"] = ["mcp_server/servers/conductor_server.py"]
            
            if not self.dry_run:
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                    
            logger.info("  Updated .mcp.json")
            
        except Exception as e:
            logger.error(f"Error updating MCP config: {e}")
    
    def _update_docker_compose(self, compose_path: Path) -> None:
        """Update docker-compose.yml"""
        try:
            with open(compose_path, 'r') as f:
                content = f.read()
            
            # Update service names and references
            content = content.replace("cherry_ai_", "cherry_ai_")
            content = content.replace("cherry_ai:", "cherry_ai:")
            content = content.replace("/cherry_ai", "/cherry_ai")
            
            if not self.dry_run:
                with open(compose_path, 'w') as f:
                    f.write(content)
                    
            logger.info("  Updated docker-compose.yml")
            
        except Exception as e:
            logger.error(f"Error updating docker-compose: {e}")
    
    def _update_env_file(self, env_path: Path) -> None:
        """Update environment file"""
        try:
            with open(env_path, 'r') as f:
                content = f.read()
            
            # Update database references
            content = re.sub(
                r'(DATABASE_URL=.*/)cherry_ai([/?])',
                r'\1cherry_ai\2',
                content
            )
            
            content = re.sub(
                r'POSTGRES_DB=cherry_ai',
                'POSTGRES_DB=cherry_ai',
                content
            )
            
            # Update port variables
            content = content.replace("CHERRY_AI_CONDUCTOR_PORT", "CHERRY_AI_CONDUCTOR_PORT")
            
            if not self.dry_run:
                with open(env_path, 'w') as f:
                    f.write(content)
                    
            logger.info(f"  Updated {env_path.name}")
            
        except Exception as e:
            logger.error(f"Error updating {env_path}: {e}")
    
    def verify_refactoring(self) -> bool:
        """Verify the refactoring was successful"""
        logger.info("Verifying refactoring...")
        
        issues = []
        
        # Check for broken imports
        python_files = list(self.root_dir.rglob("*.py"))
        for py_file in python_files:
            if self._should_skip_file(py_file):
                continue
                
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                # Check for old naming patterns
                if re.search(r'\bconductorServer\b', content):
                    issues.append(f"Old class name found in {py_file}")
                
                if re.search(r'coordination\b.*import', content):
                    issues.append(f"Old import path found in {py_file}")
                    
            except Exception as e:
                issues.append(f"Error reading {py_file}: {e}")
        
        if issues:
            logger.warning("Verification issues found:")
            for issue in issues[:10]:  # Show first 10 issues
                logger.warning(f"  - {issue}")
            return False
        else:
            logger.info("✓ Verification passed")
            return True
    
    def run_refactoring(self) -> bool:
        """Run the complete refactoring process"""
        logger.info(f"Starting naming convention refactoring (dry_run={self.dry_run})")
        
        try:
            # Create backup
            self.create_backup()
            
            # Perform refactoring steps
            self.rename_directories()
            self.rename_files()
            self.update_file_contents()
            self.update_configuration_files()
            
            # Verify results
            if not self.dry_run:
                success = self.verify_refactoring()
                if success:
                    logger.info("✓ Refactoring completed successfully")
                else:
                    logger.warning("⚠ Refactoring completed with issues")
                return success
            else:
                logger.info("✓ Dry run completed")
                return True
                
        except Exception as e:
            logger.error(f"Refactoring failed: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Refactor naming conventions")
    parser.add_argument("--root-dir", default=".", help="Root directory of project")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--execute", action="store_true", help="Execute refactoring")
    
    args = parser.parse_args()
    
    if not args.execute and not args.dry_run:
        args.dry_run = True
        logger.info("No mode specified, running in dry-run mode")
    
    refactor = NamingConventionRefactor(
        root_dir=Path(args.root_dir),
        dry_run=args.dry_run
    )
    
    success = refactor.run_refactoring()
    
    if success:
        if args.dry_run:
            print("\n🔍 Dry run completed successfully!")
            print("Run with --execute to apply changes")
        else:
            print("\n✅ Refactoring completed successfully!")
            print("Don't forget to:")
            print("1. Update your database schema")
            print("2. Restart all services")
            print("3. Update documentation")
    else:
        print("\n❌ Refactoring failed - check logs for details")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 