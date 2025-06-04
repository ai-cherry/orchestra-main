#!/usr/bin/env python3
"""
Fix critical backend issues identified in the audit
This script addresses:
1. Security vulnerabilities (hardcoded credentials, weak hashing)
2. Syntax errors (indentation issues)
3. Error handling improvements
4. Performance optimizations
"""

import os
import re
import json
import shutil
from pathlib import Path
from datetime import datetime
import subprocess
import ast

class BackendIssueFixer:
    def __init__(self):
        self.project_root = Path("/root/cherry_ai-main")
        self.fixes_applied = []
        self.backup_dir = self.project_root / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def backup_file(self, file_path: Path) -> None:
        """Create backup of file before modifying"""
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)
            
        relative_path = file_path.relative_to(self.project_root)
        backup_path = self.backup_dir / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        if file_path.exists():
            shutil.copy2(file_path, backup_path)
            
    def fix_syntax_errors(self) -> None:
        """Fix Python syntax errors, especially indentation"""
        print("🔧 Fixing syntax errors...")
        
        # Files with known syntax issues
        problem_files = [
            "scripts/comprehensive_backend_audit.py",
            "mcp_server/demo_memory_sync.py",
            "mcp_server/servers/memory_mcp_server.py",
            "scripts/maintain_uiux_design_system.py",
            "scripts/comprehensive_codebase_audit.py",
            "core/conductor/src/core/main.py",
            "core/conductor/src/api/endpoints/interaction.py",
            "core/conductor/src/api/endpoints/monitoring.py",
            "core/conductor/src/api/endpoints/llm_interaction.py"
        ]
        
        for file_path in problem_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.fix_python_file_syntax(full_path)
                
    def fix_python_file_syntax(self, file_path: Path) -> None:
        """Fix syntax issues in a Python file"""
        try:
            self.backup_file(file_path)
            
            # Try to auto-format with black
            result = subprocess.run(
                ["python3", "-m", "black", "--quiet", str(file_path)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.fixes_applied.append({
                    "file": str(file_path),
                    "fix": "Auto-formatted with black",
                    "type": "syntax"
                })
            else:
                # If black fails, try autopep8
                result = subprocess.run(
                    ["python3", "-m", "autopep8", "--in-place", "--aggressive", str(file_path)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self.fixes_applied.append({
                        "file": str(file_path),
                        "fix": "Auto-formatted with autopep8",
                        "type": "syntax"
                    })
                    
        except Exception as e:
            print(f"  ⚠️  Failed to fix {file_path}: {e}")
            
    def fix_hardcoded_credentials(self) -> None:
        """Replace hardcoded credentials with environment variables"""
        print("🔐 Fixing hardcoded credentials...")
        
        # Pattern to find hardcoded credentials
        credential_patterns = [
            (r'password\s*=\s*["\']([^"\']+)["\']', 'PASSWORD'),
            (r'secret\s*=\s*["\']([^"\']+)["\']', 'SECRET'),
            (r'api_key\s*=\s*["\']([^"\']+)["\']', 'API_KEY'),
            (r'token\s*=\s*["\']([^"\']+)["\']', 'TOKEN'),
        ]
        
        python_files = list(self.project_root.glob("**/*.py"))
        
        for py_file in python_files:
            if any(skip in str(py_file) for skip in ['venv', '__pycache__', 'node_modules']):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                modified = False
                original_content = content
                
                for pattern, env_var in credential_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Replace with environment variable
                        old_text = match.group(0)
                        new_text = f"{match.group(0).split('=')[0]}= os.getenv('{env_var}')"
                        content = content.replace(old_text, new_text)
                        modified = True
                        
                if modified:
                    self.backup_file(py_file)
                    
                    # Add import if needed
                    if 'import os' not in content:
                        content = 'import os\n' + content
                        
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
                    self.fixes_applied.append({
                        "file": str(py_file),
                        "fix": "Replaced hardcoded credentials with environment variables",
                        "type": "security"
                    })
                    
            except Exception as e:
                continue
                
    def fix_weak_hashing(self) -> None:
        """Replace weak hashing algorithms with bcrypt"""
        print("🔒 Fixing weak password hashing...")
        
        weak_hash_patterns = [
            (r'hashlib\.md5\(', 'bcrypt.hashpw('),
            (r'hashlib\.sha1\(', 'bcrypt.hashpw('),
            (r'\.hexdigest\(\)', '.decode("utf-8")'),
        ]
        
        python_files = list(self.project_root.glob("**/*.py"))
        
        for py_file in python_files:
            if any(skip in str(py_file) for skip in ['venv', '__pycache__', 'node_modules']):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if any(pattern in content for pattern, _ in weak_hash_patterns):
                    self.backup_file(py_file)
                    
                    # Replace weak hashing
                    for pattern, replacement in weak_hash_patterns:
                        content = re.sub(pattern, replacement, content)
                        
                    # Add bcrypt import if needed
                    if 'bcrypt' in content and 'import bcrypt' not in content:
                        content = 'import bcrypt\n' + content
                        
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
                    self.fixes_applied.append({
                        "file": str(py_file),
                        "fix": "Replaced weak hashing with bcrypt",
                        "type": "security"
                    })
                    
            except Exception as e:
                continue
                
    def fix_dangerous_functions(self) -> None:
        """Replace dangerous functions like eval() and exec()"""
        print("⚠️  Fixing dangerous function usage...")
        
        dangerous_patterns = [
            (r'eval\s*\(([^)]+)\)', r'ast.literal_ast.literal_eval(\1)'),
            (r'exec\s*\(([^)]+)\)', r'# SECURITY: exec() removed - \1'),
            (r'pickle\.loads?\s*\(', 'json.loads('),
            (r'os\.system\s*\(([^)]+)\)', r'subprocess.run(\1, shell=False)'),
        ]
        
        python_files = list(self.project_root.glob("**/*.py"))
        
        for py_file in python_files:
            if any(skip in str(py_file) for skip in ['venv', '__pycache__', 'node_modules']):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                modified = False
                for pattern, replacement in dangerous_patterns:
                    if re.search(pattern, content):
                        content = re.sub(pattern, replacement, content)
                        modified = True
                        
                if modified:
                    self.backup_file(py_file)
                    
                    # Add necessary imports
                    if 'ast.literal_eval' in content and 'import ast' not in content:
                        content = 'import ast\n' + content
                    if 'subprocess.run' in content and 'import subprocess' not in content:
                        content = 'import subprocess\n' + content
                    if 'json.loads' in content and 'import json' not in content:
                        content = 'import json\n' + content
                        
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
                    self.fixes_applied.append({
                        "file": str(py_file),
                        "fix": "Replaced dangerous functions",
                        "type": "security"
                    })
                    
            except Exception as e:
                continue
                
    def fix_error_handling(self) -> None:
        """Fix bare except clauses"""
        print("🛡️  Fixing error handling...")
        
        python_files = list(self.project_root.glob("**/*.py"))
        
        for py_file in python_files:
            if any(skip in str(py_file) for skip in ['venv', '__pycache__', 'node_modules']):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Replace bare except with specific exception
                if re.search(r'except\s*:', content):
                    self.backup_file(py_file)
                    content = re.sub(r'except\s*:', 'except Exception:', content)
                    
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
                    self.fixes_applied.append({
                        "file": str(py_file),
                        "fix": "Fixed bare except clauses",
                        "type": "error_handling"
                    })
                    
            except Exception as e:
                continue
                
    def create_env_template(self) -> None:
        """Create .env.template with all required environment variables"""
        print("📝 Creating environment template...")
        
        env_template = """# Cherry AI Environment Configuration
# Copy this file to .env and fill in the values

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
ENCRYPTION_KEY=your-encryption-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/cherry_ai
REDIS_URL=redis://localhost:6379/0

# API Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
PORTKEY_API_KEY=your-portkey-key

# Authentication
PASSWORD_SALT=your-password-salt
SESSION_SECRET=your-session-secret
COOKIE_SECRET=your-cookie-secret

# Services
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your-weaviate-key

# Security Settings
CORS_ORIGINS=http://localhost:3000,https://cherry-ai.me
SECURE_COOKIES=true
SESSION_TIMEOUT=3600

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO
"""
        
        env_template_path = self.project_root / ".env.template"
        with open(env_template_path, 'w') as f:
            f.write(env_template)
            
        self.fixes_applied.append({
            "file": str(env_template_path),
            "fix": "Created environment template",
            "type": "configuration"
        })
        
    def fix_cors_configuration(self) -> None:
        """Add proper CORS configuration to API files"""
        print("🌐 Fixing CORS configuration...")
        
        cors_config = '''
from fastapi.middleware.cors import CORSMiddleware

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
'''
        
        api_files = list(self.project_root.glob("**/main.py")) + \
                   list(self.project_root.glob("**/app.py"))
                   
        for api_file in api_files:
            if 'api' in str(api_file) or 'server' in str(api_file):
                try:
                    with open(api_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    if 'FastAPI' in content and 'CORSMiddleware' not in content:
                        self.backup_file(api_file)
                        
                        # Find where to insert CORS config
                        app_pattern = r'app\s*=\s*FastAPI\([^)]*\)'
                        match = re.search(app_pattern, content)
                        
                        if match:
                            insert_pos = match.end()
                            content = content[:insert_pos] + cors_config + content[insert_pos:]
                            
                            with open(api_file, 'w', encoding='utf-8') as f:
                                f.write(content)
                                
                            self.fixes_applied.append({
                                "file": str(api_file),
                                "fix": "Added CORS configuration",
                                "type": "security"
                            })
                            
                except Exception as e:
                    continue
                    
    def install_security_dependencies(self) -> None:
        """Install required security dependencies"""
        print("📦 Installing security dependencies...")
        
        dependencies = [
            "bcrypt",
            "python-jose[cryptography]",
            "passlib[bcrypt]",
            "python-multipart",
            "email-validator",
            "python-dotenv"
        ]
        
        requirements_file = self.project_root / "requirements" / "security.txt"
        requirements_file.parent.mkdir(exist_ok=True)
        
        with open(requirements_file, 'w') as f:
            f.write("# Security dependencies\n")
            for dep in dependencies:
                f.write(f"{dep}\n")
                
        self.fixes_applied.append({
            "file": str(requirements_file),
            "fix": "Created security requirements file",
            "type": "dependencies"
        })
        
    def generate_report(self) -> None:
        """Generate a report of all fixes applied"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "backup_directory": str(self.backup_dir),
            "fixes_applied": self.fixes_applied,
            "summary": {
                "total_fixes": len(self.fixes_applied),
                "by_type": {}
            }
        }
        
        # Count fixes by type
        for fix in self.fixes_applied:
            fix_type = fix["type"]
            if fix_type not in report["summary"]["by_type"]:
                report["summary"]["by_type"][fix_type] = 0
            report["summary"]["by_type"][fix_type] += 1
            
        report_file = f"backend_fixes_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📊 Fix report saved to: {report_file}")
        print(f"🗂️  Backups saved to: {self.backup_dir}")
        
    def run_fixes(self) -> None:
        """Run all fixes"""
        print("🚀 Starting backend fixes...")
        print(f"📁 Project root: {self.project_root}")
        
        # Install formatters if needed
        print("\n📦 Installing code formatters...")
        subprocess.run(["pip", "install", "-q", "black", "autopep8"], capture_output=True)
        
        # Run fixes in order of priority
        self.fix_syntax_errors()
        self.fix_hardcoded_credentials()
        self.fix_weak_hashing()
        self.fix_dangerous_functions()
        self.fix_error_handling()
        self.fix_cors_configuration()
        self.create_env_template()
        self.install_security_dependencies()
        
        # Generate report
        self.generate_report()
        
        print(f"\n✅ Applied {len(self.fixes_applied)} fixes!")
        print("\n⚠️  IMPORTANT NEXT STEPS:")
        print("1. Review the changes in the backup directory")
        print("2. Copy .env.template to .env and fill in values")
        print("3. Install security dependencies: pip install -r requirements/security.txt")
        print("4. Run tests to ensure nothing is broken")
        print("5. Commit the changes after review")

def main():
    fixer = BackendIssueFixer()
    fixer.run_fixes()

if __name__ == "__main__":
    main()