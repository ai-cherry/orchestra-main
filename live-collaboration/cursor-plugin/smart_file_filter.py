#!/usr/bin/env python3
"""
Smart File Filter for Live Collaboration
Handles large projects by intelligently filtering relevant files
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime, timedelta

class SmartCollaborationFilter:
    """Intelligent file filtering for live collaboration"""
    
    def __init__(self):
        self.priority_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', 
            '.md', '.json', '.yaml', '.yml', '.sql', '.sh'
        }
        
        self.ignore_patterns = {
            # Build artifacts
            'node_modules', '__pycache__', '.pyc', 'dist', 'build',
            '.next', '.nuxt', 'target', 'out',
            
            # Version control
            '.git', '.svn', '.hg',
            
            # IDE files
            '.vscode', '.idea', '*.swp', '*.swo',
            
            # Dependencies
            'venv', 'env', '.env', 'vendor',
            
            # Large files
            '*.log', '*.dump', '*.sql.gz', '*.tar.gz'
        }
        
        self.recent_files: Dict[str, datetime] = {}
        self.collaboration_zones = {
            'active': [],    # Real-time sync
            'passive': [],   # Periodic sync
            'ignore': []     # Never sync
        }
    
    def should_sync_file(self, file_path: str) -> bool:
        """Determine if file should be synced to AI"""
        path = Path(file_path)
        
        # Skip ignored patterns
        if self._is_ignored(path):
            return False
            
        # Always sync priority extensions
        if path.suffix.lower() in self.priority_extensions:
            return True
            
        # Skip very large files (>1MB)
        try:
            if path.stat().st_size > 1024 * 1024:
                return False
        except (OSError, FileNotFoundError):
            return False
            
        # Skip binary files
        if self._is_binary(path):
            return False
            
        return True
    
    def _is_ignored(self, path: Path) -> bool:
        """Check if path matches ignore patterns"""
        path_str = str(path).lower()
        
        for pattern in self.ignore_patterns:
            if pattern in path_str:
                return True
                
        return False
    
    def _is_binary(self, path: Path) -> bool:
        """Simple binary file detection"""
        try:
            with open(path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except (OSError, FileNotFoundError):
            return True
    
    def get_project_context(self, project_root: str) -> Dict:
        """Get intelligent project context for AI"""
        context = {
            'recent_files': self._get_recent_files(project_root),
            'project_structure': self._get_project_structure(project_root),
            'active_files': self._get_active_files(project_root),
            'file_count': self._count_relevant_files(project_root)
        }
        return context
    
    def _get_recent_files(self, project_root: str, hours: int = 24) -> List[str]:
        """Get files modified in last N hours"""
        recent = []
        cutoff = datetime.now() - timedelta(hours=hours)
        
        for root, dirs, files in os.walk(project_root):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not any(pattern in d.lower() for pattern in self.ignore_patterns)]
            
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if mtime > cutoff and self.should_sync_file(file_path):
                        recent.append(file_path)
                except (OSError, FileNotFoundError):
                    continue
                    
        return sorted(recent, key=lambda x: os.path.getmtime(x), reverse=True)[:50]  # Limit to 50 most recent
    
    def _get_project_structure(self, project_root: str) -> Dict:
        """Get high-level project structure"""
        structure = {}
        
        for item in os.listdir(project_root):
            item_path = os.path.join(project_root, item)
            if os.path.isdir(item_path) and not self._is_ignored(Path(item_path)):
                file_count = self._count_files_in_dir(item_path)
                structure[item] = {
                    'type': 'directory',
                    'file_count': file_count,
                    'relevant': file_count > 0
                }
            elif self.should_sync_file(item_path):
                structure[item] = {
                    'type': 'file',
                    'extension': Path(item_path).suffix,
                    'relevant': True
                }
                
        return structure
    
    def _get_active_files(self, project_root: str) -> List[str]:
        """Get files likely being actively worked on"""
        # Look for recently modified files in key directories
        active_dirs = ['src', 'lib', 'app', 'components', 'pages', 'api']
        active_files = []
        
        for dir_name in active_dirs:
            dir_path = os.path.join(project_root, dir_name)
            if os.path.exists(dir_path):
                active_files.extend(self._get_recent_files(dir_path, hours=6))
                
        return active_files[:20]  # Limit to 20 most active
    
    def _count_relevant_files(self, project_root: str) -> int:
        """Count files that would be synced"""
        count = 0
        for root, dirs, files in os.walk(project_root):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not any(pattern in d.lower() for pattern in self.ignore_patterns)]
            
            for file in files:
                file_path = os.path.join(root, file)
                if self.should_sync_file(file_path):
                    count += 1
                    
        return count
    
    def _count_files_in_dir(self, dir_path: str) -> int:
        """Count relevant files in directory"""
        count = 0
        try:
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                if os.path.isfile(item_path) and self.should_sync_file(item_path):
                    count += 1
        except (OSError, PermissionError):
            pass
        return count

def filter_files_for_collaboration(project_root: str, max_files: int = 100) -> List[str]:
    """Get the most relevant files for AI collaboration"""
    filter = SmartCollaborationFilter()
    
    # Get project context
    context = filter.get_project_context(project_root)
    
    # Start with recently modified files
    files_to_sync = context['recent_files'][:max_files//2]
    
    # Add active files if we have room
    remaining_slots = max_files - len(files_to_sync)
    if remaining_slots > 0:
        active_files = [f for f in context['active_files'] if f not in files_to_sync]
        files_to_sync.extend(active_files[:remaining_slots])
    
    return files_to_sync

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python smart_file_filter.py <project_root>")
        sys.exit(1)
        
    project_root = sys.argv[1]
    filter = SmartCollaborationFilter()
    
    print(f"📊 Project Analysis: {project_root}")
    context = filter.get_project_context(project_root)
    
    print(f"📁 Total relevant files: {context['file_count']}")
    print(f"🔥 Recent files (24h): {len(context['recent_files'])}")
    print(f"⚡ Active files (6h): {len(context['active_files'])}")
    
    if context['file_count'] > 1000:
        print("⚠️  Large project detected - using smart filtering")
        filtered_files = filter_files_for_collaboration(project_root)
        print(f"✅ Filtered to {len(filtered_files)} most relevant files")
    else:
        print("✅ Project size manageable for full sync") 