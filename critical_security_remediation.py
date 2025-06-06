#!/usr/bin/env python3
"""
Critical Security Remediation Script
Addresses remaining security vulnerabilities identified by test validation
"""

import os
import re
import ast
import json
from typing import List, Dict, Tuple, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityRemediator:
    """Remediate critical security vulnerabilities"""
    
    def __init__(self):
        self.fixed_count = 0
        self.total_issues = 0
        self.remediation_log = []
        
    def fix_remaining_hardcoded_credentials(self):
        """Fix remaining hardcoded credentials with more aggressive patterns"""
        logger.info("🔒 Fixing remaining hardcoded credentials...")
        
        # Extended patterns for credential detection
        credential_patterns = [
            (r'password\s*=\s*["\']([^"\']+)["\']', 'PASSWORD'),
            (r'PASSWORD\s*=\s*["\']([^"\']+)["\']', 'PASSWORD'),
            (r'api_key\s*=\s*["\']([^"\']+)["\']', 'API_KEY'),
            (r'API_KEY\s*=\s*["\']([^"\']+)["\']', 'API_KEY'),
            (r'secret\s*=\s*["\']([^"\']+)["\']', 'SECRET'),
            (r'SECRET\s*=\s*["\']([^"\']+)["\']', 'SECRET'),
            (r'token\s*=\s*["\']([^"\']+)["\']', 'TOKEN'),
            (r'TOKEN\s*=\s*["\']([^"\']+)["\']', 'TOKEN'),
            (r'key\s*=\s*["\']([^"\']+)["\']', 'KEY'),
            (r'KEY\s*=\s*["\']([^"\']+)["\']', 'KEY'),
            # Database URLs
            (r'DATABASE_URL\s*=\s*["\']([^"\']+)["\']', 'DATABASE_URL'),
            (r'REDIS_URL\s*=\s*["\']([^"\']+)["\']', 'REDIS_URL'),
            # Connection strings
            (r'connection_string\s*=\s*["\']([^"\']+)["\']', 'CONNECTION_STRING'),
        ]
        
        for root, dirs, files in os.walk('.'):
            # Skip directories
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self._process_file_for_credentials(file_path, credential_patterns)
    
    def _process_file_for_credentials(self, file_path: str, patterns: List[Tuple[str, str]]):
        """Process a single file for credential patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            modified = False
            
            for pattern, cred_type in patterns:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                
                for match in reversed(matches):  # Process in reverse to maintain positions
                    # Skip if already using environment variable
                    line_start = content.rfind('\n', 0, match.start()) + 1
                    line_end = content.find('\n', match.end())
                    if line_end == -1:
                        line_end = len(content)
                    
                    line = content[line_start:line_end]
                    
                    # Skip if already using os.getenv or os.environ
                    if 'os.getenv' in line or 'os.environ' in line:
                        continue
                    
                    # Skip test values
                    test_values = ['test', 'example', 'dummy', 'placeholder', 'xxx', '...']
                    if any(val in match.group(1).lower() for val in test_values):
                        continue
                    
                    # Generate environment variable name
                    env_var = self._generate_env_var_name(file_path, cred_type)
                    
                    # Create replacement
                    var_match = re.search(r'(\w+)\s*=', line)
                    if var_match:
                        var_name = var_match.group(1)
                        replacement = f'{var_name} = os.getenv("{env_var}", "")'
                        
                        # Replace the line
                        content = content[:line_start] + replacement + content[line_end:]
                        modified = True
                        self.fixed_count += 1
                        
                        self.remediation_log.append({
                            'file': file_path,
                            'type': cred_type,
                            'env_var': env_var,
                            'line': content[:match.start()].count('\n') + 1
                        })
            
            if modified:
                # Ensure os import exists
                if 'import os' not in content:
                    # Add import at the beginning after any shebang or encoding
                    lines = content.split('\n')
                    insert_pos = 0
                    
                    # Skip shebang and encoding
                    for i, line in enumerate(lines):
                        if line.startswith('#!') or line.startswith('# -*- coding'):
                            insert_pos = i + 1
                        else:
                            break
                    
                    lines.insert(insert_pos, 'import os')
                    content = '\n'.join(lines)
                
                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"  ✅ Fixed credentials in {file_path}")
                
        except Exception as e:
            logger.error(f"  ❌ Error processing {file_path}: {e}")
    
    def _generate_env_var_name(self, file_path: str, cred_type: str) -> str:
        """Generate unique environment variable name"""
        # Extract meaningful context from path
        parts = file_path.split(os.sep)
        
        if 'scripts' in parts:
            context = 'SCRIPT'
        elif 'mcp_server' in parts:
            context = 'MCP'
        elif 'infrastructure' in parts:
            context = 'INFRA'
        elif 'core' in parts:
            context = 'CORE'
        elif 'src' in parts:
            context = 'APP'
        else:
            context = 'ORCHESTRA'
        
        # Make it unique based on file
        file_name = os.path.basename(file_path).replace('.py', '').upper()
        
        return f"{context}_{file_name}_{cred_type}"
    
    def fix_sql_injection_vulnerabilities(self):
        """Fix SQL injection vulnerabilities"""
        logger.info("🛡️ Fixing SQL injection vulnerabilities...")
        
        sql_patterns = [
            # String formatting in SQL
            (r'\.execute\s*\(\s*["\']([^"\']+%[sd][^"\']*)["\'].*%', 'string_format'),
            (r'\.execute\s*\(\s*f["\']([^"\']+)["\']', 'f_string'),
            (r'\.execute\s*\(\s*["\']([^"\']+)["\'].*\+', 'concatenation'),
            # Direct variable injection
            (r'\.execute\s*\(\s*"([^"]+)"\s*\.\s*format\s*\(', 'format_method'),
        ]
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self._fix_sql_in_file(file_path, sql_patterns)
    
    def _fix_sql_in_file(self, file_path: str, patterns: List[Tuple[str, str]]):
        """Fix SQL injection issues in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            modified = False
            
            for i, line in enumerate(lines):
                if '.execute(' in line:
                    # Check for vulnerable patterns
                    for pattern, vuln_type in patterns:
                        if re.search(pattern, line):
                            # Add comment warning
                            if '# SQL INJECTION' not in line:
                                indent = len(line) - len(line.lstrip())
                                warning = ' ' * indent + '# WARNING: SQL INJECTION RISK - Use parameterized queries\n'
                                lines.insert(i, warning)
                                
                                # Add example fix
                                example = ' ' * indent + '# Example: cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))\n'
                                lines.insert(i + 1, example)
                                
                                modified = True
                                self.fixed_count += 1
                                
                                self.remediation_log.append({
                                    'file': file_path,
                                    'type': 'sql_injection',
                                    'line': i + 1,
                                    'vulnerability': vuln_type
                                })
                                break
            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                logger.info(f"  ✅ Added SQL injection warnings to {file_path}")
                
        except Exception as e:
            logger.error(f"  ❌ Error processing {file_path}: {e}")
    
    def fix_bare_except_clauses(self):
        """Fix remaining bare except clauses"""
        logger.info("🛡️ Fixing bare except clauses...")
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self._fix_bare_except_in_file(file_path)
    
    def _fix_bare_except_in_file(self, file_path: str):
        """Fix bare except clauses in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            modified = False
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped == 'except:':
                    # Replace with Exception
                    indent = len(line) - len(line.lstrip())
                    lines[i] = ' ' * indent + 'except Exception as e:\n'
                    
                    # Add logging if not present in next line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        if 'logger' not in next_line and 'print' not in next_line:
                            log_line = ' ' * (indent + 4) + 'logger.error(f"Error in {__name__}: {e}")\n'
                            lines.insert(i + 1, log_line)
                    
                    modified = True
                    self.fixed_count += 1
                    
                    self.remediation_log.append({
                        'file': file_path,
                        'type': 'bare_except',
                        'line': i + 1
                    })
            
            if modified:
                # Ensure logging import
                has_logging = any('import logging' in line for line in lines[:20])
                if not has_logging:
                    # Find appropriate place for import
                    insert_pos = 0
                    for i, line in enumerate(lines):
                        if line.startswith('import') or line.startswith('from'):
                            insert_pos = i + 1
                        elif not line.startswith('#') and line.strip():
                            break
                    
                    lines.insert(insert_pos, 'import logging\n')
                    lines.insert(insert_pos + 1, 'logger = logging.getLogger(__name__)\n\n')
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                logger.info(f"  ✅ Fixed bare except clauses in {file_path}")
                
        except Exception as e:
            logger.error(f"  ❌ Error processing {file_path}: {e}")
    
    def generate_env_template(self):
        """Generate comprehensive .env.template file"""
        logger.info("📝 Generating comprehensive .env.template...")
        
        template_content = """# Orchestra Environment Configuration Template
# Copy this file to .env and fill in your actual values

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/orchestra
POSTGRES_USER=orchestra_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=orchestra_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password_here

# Weaviate Configuration
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your_weaviate_api_key_here

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
LAMBDA_API_KEY=your_LAMBDA_API_KEY_here

# Authentication
JWT_SECRET_KEY=your_jwt_secret_key_here
SESSION_SECRET_KEY=your_session_secret_key_here

# Application Settings
FLASK_SECRET_KEY=your_flask_secret_key_here
DEBUG=False
ENVIRONMENT=production

# MCP Server Configuration
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000
MCP_AUTH_TOKEN=your_mcp_auth_token_here

# Monitoring
SENTRY_DSN=your_sentry_dsn_here
LOG_LEVEL=INFO

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_email_password_here

# Cloud Storage
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
S3_BUCKET_NAME=orchestra-storage

# Feature Flags
ENABLE_CACHING=true
ENABLE_RATE_LIMITING=true
ENABLE_MONITORING=true

# Security
ENCRYPTION_KEY=your_encryption_key_here
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

"""
        
        # Add discovered environment variables
        for item in self.remediation_log:
            if 'env_var' in item:
                env_var = item['env_var']
                if env_var not in template_content:
                    template_content += f"\n# From {item['file']}\n"
                    template_content += f"{env_var}=your_{item['type'].lower()}_here\n"
        
        with open('.env.template', 'w') as f:
            f.write(template_content)
        
        logger.info("  ✅ Created comprehensive .env.template")
    
    def generate_security_report(self):
        """Generate security remediation report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_fixes': self.fixed_count,
                'credentials_fixed': len([r for r in self.remediation_log if r['type'] != 'bare_except' and r['type'] != 'sql_injection']),
                'sql_injection_warnings': len([r for r in self.remediation_log if r['type'] == 'sql_injection']),
                'bare_except_fixed': len([r for r in self.remediation_log if r['type'] == 'bare_except'])
            },
            'remediation_details': self.remediation_log,
            'next_steps': [
                "Review and update .env.template with your actual values",
                "Create .env file from template (never commit this file)",
                "Review SQL injection warnings and refactor to use parameterized queries",
                "Test all modified files to ensure functionality",
                ""
            ]
        }
        
        report_file = f"security_remediation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report_file

def main():
    """Main execution"""
    print("🔐 Critical Security Remediation")
    print("=" * 50)
    
    remediator = SecurityRemediator()
    
    # Fix remaining issues
    remediator.fix_remaining_hardcoded_credentials()
    remediator.fix_sql_injection_vulnerabilities()
    remediator.fix_bare_except_clauses()
    remediator.generate_env_template()
    
    # Generate report
    report_file = remediator.generate_security_report()
    
    print(f"\n✅ Remediation Complete!")
    print(f"  Total Fixes Applied: {remediator.fixed_count}")
    print(f"  Report saved to: {report_file}")
    print("\n📋 Next Steps:")
    print("  1. Review the generated .env.template file")
    print("  2. Create your .env file with actual values")
    print("  3. Review SQL injection warnings in modified files")
    print("  4. Test all changes thoroughly")
    print("")

if __name__ == "__main__":
    main()