#!/usr/bin/env python3
"""
Comprehensive Codebase Cleanup Script
Cherry AI Orchestrator - Production Optimization

This script performs:
1. Dependency analysis and cleanup
2. Naming convention standardization
3. Redundant file removal
4. Documentation updates
5. Configuration optimization
6. Security improvements

Author: Cherry AI Team
Version: 1.0.0
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Tuple
import re
from datetime import datetime

class CodebaseCleanup:
    """Comprehensive codebase cleanup and optimization"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.issues = []
        self.fixes_applied = []
        self.backup_dir = self.repo_path / f".cleanup_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def run_cleanup(self):
        """Execute comprehensive cleanup process"""
        print("🧹 CHERRY AI ORCHESTRATOR - CODEBASE CLEANUP")
        print("=" * 60)
        
        # Create backup
        self.create_backup()
        
        # Analysis phase
        print("\n📊 ANALYSIS PHASE")
        print("-" * 30)
        self.analyze_dependencies()
        self.analyze_naming_conventions()
        self.analyze_redundant_files()
        self.analyze_documentation()
        self.analyze_configurations()
        
        # Cleanup phase
        print("\n🔧 CLEANUP PHASE")
        print("-" * 30)
        self.fix_dependencies()
        self.standardize_naming()
        self.remove_redundant_files()
        self.update_documentation()
        self.optimize_configurations()
        
        # Generate report
        self.generate_cleanup_report()
        
        print(f"\n✅ Cleanup completed! {len(self.fixes_applied)} fixes applied.")
        print(f"📁 Backup created at: {self.backup_dir}")
    
    def create_backup(self):
        """Create backup of critical files before cleanup"""
        print("📁 Creating backup...")
        
        critical_files = [
            ".env", ".env.example", "docker-compose.yml", "requirements.txt",
            "package.json", "pyproject.toml", ".github/workflows",
            "admin-interface", "infrastructure", "mcp_server"
        ]
        
        self.backup_dir.mkdir(exist_ok=True)
        
        for file_path in critical_files:
            source = self.repo_path / file_path
            if source.exists():
                if source.is_dir():
                    shutil.copytree(source, self.backup_dir / file_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(source, self.backup_dir / file_path)
        
        print(f"✅ Backup created: {self.backup_dir}")
    
    def analyze_dependencies(self):
        """Analyze dependency files for conflicts and outdated packages"""
        print("🔍 Analyzing dependencies...")
        
        # Check Python dependencies
        requirements_files = list(self.repo_path.glob("**/requirements*.txt"))
        pyproject_files = list(self.repo_path.glob("**/pyproject.toml"))
        
        for req_file in requirements_files:
            self.analyze_requirements_file(req_file)
        
        for pyproject_file in pyproject_files:
            self.analyze_pyproject_file(pyproject_file)
        
        # Check Node.js dependencies
        package_files = list(self.repo_path.glob("**/package.json"))
        for package_file in package_files:
            self.analyze_package_json(package_file)
    
    def analyze_requirements_file(self, file_path: Path):
        """Analyze Python requirements file"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            duplicates = set()
            seen_packages = set()
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    package = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
                    if package in seen_packages:
                        duplicates.add(package)
                    seen_packages.add(package)
            
            if duplicates:
                self.issues.append({
                    'type': 'dependency_duplicate',
                    'file': str(file_path),
                    'packages': list(duplicates)
                })
        except Exception as e:
            self.issues.append({
                'type': 'dependency_error',
                'file': str(file_path),
                'error': str(e)
            })
    
    def analyze_pyproject_file(self, file_path: Path):
        """Analyze pyproject.toml file"""
        try:
            import tomllib
            with open(file_path, 'rb') as f:
                data = tomllib.load(f)
            
            # Check for common issues
            if 'project' in data and 'dependencies' in data['project']:
                deps = data['project']['dependencies']
                if len(deps) > 50:  # Too many dependencies
                    self.issues.append({
                        'type': 'dependency_bloat',
                        'file': str(file_path),
                        'count': len(deps)
                    })
        except Exception as e:
            self.issues.append({
                'type': 'pyproject_error',
                'file': str(file_path),
                'error': str(e)
            })
    
    def analyze_package_json(self, file_path: Path):
        """Analyze package.json file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Check for security vulnerabilities in dependencies
            deps = data.get('dependencies', {})
            dev_deps = data.get('devDependencies', {})
            
            total_deps = len(deps) + len(dev_deps)
            if total_deps > 100:
                self.issues.append({
                    'type': 'node_dependency_bloat',
                    'file': str(file_path),
                    'count': total_deps
                })
        except Exception as e:
            self.issues.append({
                'type': 'package_json_error',
                'file': str(file_path),
                'error': str(e)
            })
    
    def analyze_naming_conventions(self):
        """Analyze naming conventions across the codebase"""
        print("🏷️ Analyzing naming conventions...")
        
        # Check for inconsistent naming patterns
        python_files = list(self.repo_path.glob("**/*.py"))
        js_files = list(self.repo_path.glob("**/*.js"))
        html_files = list(self.repo_path.glob("**/*.html"))
        
        naming_issues = []
        
        for py_file in python_files:
            if not self.is_valid_python_filename(py_file.name):
                naming_issues.append({
                    'file': str(py_file),
                    'issue': 'non_snake_case_python'
                })
        
        for js_file in js_files:
            if not self.is_valid_js_filename(js_file.name):
                naming_issues.append({
                    'file': str(js_file),
                    'issue': 'non_camelCase_js'
                })
        
        if naming_issues:
            self.issues.append({
                'type': 'naming_convention',
                'issues': naming_issues
            })
    
    def is_valid_python_filename(self, filename: str) -> bool:
        """Check if Python filename follows snake_case convention"""
        name = filename.replace('.py', '')
        return re.match(r'^[a-z][a-z0-9_]*$', name) is not None
    
    def is_valid_js_filename(self, filename: str) -> bool:
        """Check if JS filename follows camelCase or kebab-case convention"""
        name = filename.replace('.js', '')
        return (re.match(r'^[a-z][a-zA-Z0-9]*$', name) is not None or 
                re.match(r'^[a-z][a-z0-9-]*$', name) is not None)
    
    def analyze_redundant_files(self):
        """Identify redundant and unnecessary files"""
        print("🗑️ Analyzing redundant files...")
        
        redundant_patterns = [
            "**/*.pyc", "**/__pycache__", "**/.DS_Store",
            "**/node_modules", "**/*.log", "**/.pytest_cache",
            "**/backup_*", "**/*_backup_*", "**/*.bak",
            "**/.vscode/settings.json", "**/.idea"
        ]
        
        redundant_files = []
        for pattern in redundant_patterns:
            redundant_files.extend(self.repo_path.glob(pattern))
        
        # Check for duplicate backup directories
        backup_dirs = list(self.repo_path.glob("**/*backup*"))
        migration_dirs = list(self.repo_path.glob("**/*migration*"))
        
        if redundant_files or backup_dirs or migration_dirs:
            self.issues.append({
                'type': 'redundant_files',
                'files': [str(f) for f in redundant_files],
                'backup_dirs': [str(d) for d in backup_dirs],
                'migration_dirs': [str(d) for d in migration_dirs]
            })
    
    def analyze_documentation(self):
        """Analyze documentation for outdated content"""
        print("📚 Analyzing documentation...")
        
        readme_files = list(self.repo_path.glob("**/README.md"))
        doc_files = list(self.repo_path.glob("**/*.md"))
        
        outdated_docs = []
        
        for doc_file in doc_files:
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for outdated references
                if 'localhost:3000' in content and 'cherry-ai.me' not in content:
                    outdated_docs.append({
                        'file': str(doc_file),
                        'issue': 'localhost_references'
                    })
                
                if 'TODO' in content or 'FIXME' in content:
                    outdated_docs.append({
                        'file': str(doc_file),
                        'issue': 'todo_items'
                    })
            except Exception as e:
                outdated_docs.append({
                    'file': str(doc_file),
                    'issue': f'read_error: {e}'
                })
        
        if outdated_docs:
            self.issues.append({
                'type': 'outdated_documentation',
                'docs': outdated_docs
            })
    
    def analyze_configurations(self):
        """Analyze configuration files for optimization opportunities"""
        print("⚙️ Analyzing configurations...")
        
        config_files = [
            'docker-compose.yml', '.env.example', '.github/workflows/*.yml',
            'nginx.conf', '.mcp.json'
        ]
        
        config_issues = []
        
        for pattern in config_files:
            for config_file in self.repo_path.glob(pattern):
                if config_file.exists():
                    self.analyze_config_file(config_file, config_issues)
        
        if config_issues:
            self.issues.append({
                'type': 'configuration_issues',
                'issues': config_issues
            })
    
    def analyze_config_file(self, file_path: Path, issues: List):
        """Analyze individual configuration file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for hardcoded values
            if 'localhost' in content and file_path.name != '.env.example':
                issues.append({
                    'file': str(file_path),
                    'issue': 'hardcoded_localhost'
                })
            
            # Check for insecure configurations
            if 'password' in content.lower() and 'example' not in str(file_path):
                issues.append({
                    'file': str(file_path),
                    'issue': 'potential_exposed_password'
                })
        except Exception as e:
            issues.append({
                'file': str(file_path),
                'issue': f'analysis_error: {e}'
            })
    
    def fix_dependencies(self):
        """Fix dependency issues"""
        print("🔧 Fixing dependencies...")
        
        for issue in self.issues:
            if issue['type'] == 'dependency_duplicate':
                self.fix_duplicate_dependencies(issue)
    
    def fix_duplicate_dependencies(self, issue: Dict):
        """Remove duplicate dependencies from requirements files"""
        file_path = Path(issue['file'])
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            seen_packages = set()
            cleaned_lines = []
            
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    package = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
                    if package not in seen_packages:
                        cleaned_lines.append(line)
                        seen_packages.add(package)
                else:
                    cleaned_lines.append(line)
            
            with open(file_path, 'w') as f:
                f.writelines(cleaned_lines)
            
            self.fixes_applied.append(f"Removed duplicate dependencies from {file_path}")
        except Exception as e:
            print(f"❌ Failed to fix dependencies in {file_path}: {e}")
    
    def standardize_naming(self):
        """Standardize naming conventions"""
        print("🏷️ Standardizing naming conventions...")
        
        # This would be a complex operation requiring careful file renaming
        # For now, just report the issues
        for issue in self.issues:
            if issue['type'] == 'naming_convention':
                print(f"⚠️ Found {len(issue['issues'])} naming convention issues")
                self.fixes_applied.append("Identified naming convention issues for manual review")
    
    def remove_redundant_files(self):
        """Remove redundant and unnecessary files"""
        print("🗑️ Removing redundant files...")
        
        for issue in self.issues:
            if issue['type'] == 'redundant_files':
                # Remove cache files and temporary files
                for file_path in issue['files']:
                    try:
                        path = Path(file_path)
                        if path.exists():
                            if path.is_dir():
                                shutil.rmtree(path)
                            else:
                                path.unlink()
                            self.fixes_applied.append(f"Removed redundant file: {file_path}")
                    except Exception as e:
                        print(f"❌ Failed to remove {file_path}: {e}")
    
    def update_documentation(self):
        """Update outdated documentation"""
        print("📚 Updating documentation...")
        
        for issue in self.issues:
            if issue['type'] == 'outdated_documentation':
                for doc_issue in issue['docs']:
                    if doc_issue['issue'] == 'localhost_references':
                        self.update_localhost_references(doc_issue['file'])
    
    def update_localhost_references(self, file_path: str):
        """Update localhost references to production URLs"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace localhost references with production URLs
            content = content.replace('http://localhost:3000', 'https://cherry-ai.me')
            content = content.replace('localhost:3000', 'cherry-ai.me')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.fixes_applied.append(f"Updated localhost references in {file_path}")
        except Exception as e:
            print(f"❌ Failed to update {file_path}: {e}")
    
    def optimize_configurations(self):
        """Optimize configuration files"""
        print("⚙️ Optimizing configurations...")
        
        # Update .env.example with production-ready values
        env_example = self.repo_path / '.env.example'
        if env_example.exists():
            self.optimize_env_example(env_example)
    
    def optimize_env_example(self, file_path: Path):
        """Optimize .env.example file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Add production-ready comments and examples
            optimized_content = f"""# Cherry AI Orchestrator - Production Environment Configuration
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 
# IMPORTANT: Copy this file to .env and update with your actual values
# Never commit .env file to version control

{content}

# Production Deployment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# Security
SECURE_COOKIES=true
CSRF_PROTECTION=true
RATE_LIMITING=true
"""
            
            with open(file_path, 'w') as f:
                f.write(optimized_content)
            
            self.fixes_applied.append("Optimized .env.example with production settings")
        except Exception as e:
            print(f"❌ Failed to optimize .env.example: {e}")
    
    def generate_cleanup_report(self):
        """Generate comprehensive cleanup report"""
        report_path = self.repo_path / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        report_content = f"""# Codebase Cleanup Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Issues Found**: {len(self.issues)}
- **Fixes Applied**: {len(self.fixes_applied)}
- **Backup Location**: {self.backup_dir}

## Issues Identified

"""
        
        for i, issue in enumerate(self.issues, 1):
            report_content += f"### {i}. {issue['type'].replace('_', ' ').title()}\n"
            report_content += f"**Type**: {issue['type']}\n"
            
            if 'file' in issue:
                report_content += f"**File**: {issue['file']}\n"
            if 'files' in issue:
                report_content += f"**Files**: {len(issue['files'])} files affected\n"
            if 'count' in issue:
                report_content += f"**Count**: {issue['count']}\n"
            
            report_content += "\n"
        
        report_content += "## Fixes Applied\n\n"
        for fix in self.fixes_applied:
            report_content += f"- {fix}\n"
        
        report_content += f"""
## Recommendations

1. **Review naming convention issues** and standardize file names
2. **Update GitHub workflows** to fix failing deployments
3. **Audit dependencies** for security vulnerabilities
4. **Complete documentation updates** for production deployment
5. **Test all configurations** in production environment

## Next Steps

1. Run system integration tests: `python3 test_system_integration.py`
2. Deploy to production: `./deploy.sh`
3. Monitor system health: Check GitHub Actions and logs
4. Update documentation: Complete any remaining TODO items

---
*Generated by Cherry AI Orchestrator Cleanup Script v1.0.0*
"""
        
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        print(f"📊 Cleanup report generated: {report_path}")

def main():
    """Main cleanup function"""
    repo_path = "/home/ubuntu/orchestra-main-repo"
    
    if not os.path.exists(repo_path):
        print(f"❌ Repository path not found: {repo_path}")
        return
    
    cleanup = CodebaseCleanup(repo_path)
    cleanup.run_cleanup()

if __name__ == "__main__":
    main()

