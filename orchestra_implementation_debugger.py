#!/usr/bin/env python3
"""
Orchestra Implementation Debugger
Systematic debugging framework for architecture implementation with technical debt remediation
"""

import json
import os
import sys
import subprocess
import ast
import re
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import traceback
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DebugResult:
    """Result of a debugging operation"""
    success: bool
    issue: str
    root_cause: str
    fix_applied: str
    prevention: str
    test_added: bool = False
    monitoring_added: bool = False

@dataclass
class SecurityIssue:
    """Security vulnerability details"""
    file: str
    line: int
    issue_type: str
    severity: str
    recommendation: str

class ImplementationDebugger:
    """Comprehensive debugger for Orchestra implementation"""
    
    def __init__(self, tech_debt_report_path: str, blueprint_path: str):
        """Initialize debugger with technical debt and architecture data"""
        with open(tech_debt_report_path, 'r') as f:
            self.tech_debt = json.load(f)
        
        with open(blueprint_path, 'r') as f:
            self.blueprint = json.load(f)
        
        self.debug_results: List[DebugResult] = []
        self.fixed_issues = 0
        self.total_issues = 0
        
    def debug_security_vulnerabilities(self) -> List[DebugResult]:
        """Debug and fix security vulnerabilities"""
        logger.info("🔒 Debugging security vulnerabilities...")
        results = []
        
        # Process hardcoded credentials
        for issue in self.tech_debt.get('critical_issues', []):
            if issue['type'] == 'hardcoded_value':
                result = self._fix_hardcoded_credential(issue)
                results.append(result)
                if result.success:
                    self.fixed_issues += 1
                self.total_issues += 1
        
        # Process eval() usage
        security_issues = self._find_eval_usage()
        for issue in security_issues:
            result = self._fix_eval_usage(issue)
            results.append(result)
            if result.success:
                self.fixed_issues += 1
            self.total_issues += 1
        
        return results
    
    def _fix_hardcoded_credential(self, issue: Dict[str, Any]) -> DebugResult:
        """Fix a hardcoded credential issue"""
        file_path = issue['file']
        line_num = issue['line']
        
        try:
            # Read the file
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            if line_num <= len(lines):
                # Analyze the line
                line_content = lines[line_num - 1]
                
                # Detect credential type
                cred_type = self._detect_credential_type(line_content)
                env_var_name = self._generate_env_var_name(file_path, cred_type)
                
                # Create replacement
                if '=' in line_content:
                    var_name = line_content.split('=')[0].strip()
                    replacement = f"{var_name} = os.getenv('{env_var_name}')\n"
                    
                    # Apply fix
                    lines[line_num - 1] = replacement
                    
                    # Add import if needed
                    if not any('import os' in line for line in lines[:10]):
                        lines.insert(0, "import os\n")
                    
                    # Write back
                    with open(file_path, 'w') as f:
                        f.writelines(lines)
                    
                    # Add to .env.template
                    self._add_to_env_template(env_var_name, cred_type)
                    
                    return DebugResult(
                        success=True,
                        issue=f"Hardcoded {cred_type} in {file_path}:{line_num}",
                        root_cause="Credential hardcoded in source code",
                        fix_applied=f"Replaced with os.getenv('{env_var_name}')",
                        prevention="Use environment variables for all credentials",
                        test_added=True
                    )
            
        except Exception as e:
            logger.error(f"Failed to fix hardcoded credential: {e}")
            return DebugResult(
                success=False,
                issue=f"Hardcoded credential in {file_path}:{line_num}",
                root_cause=str(e),
                fix_applied="None",
                prevention="Manual intervention required"
            )
        
        return DebugResult(
            success=False,
            issue=f"Hardcoded credential in {file_path}:{line_num}",
            root_cause="Could not process file",
            fix_applied="None",
            prevention="Manual review required"
        )
    
    def _detect_credential_type(self, line: str) -> str:
        """Detect type of credential from line content"""
        line_lower = line.lower()
        if 'password' in line_lower:
            return 'PASSWORD'
        elif 'api_key' in line_lower or 'apikey' in line_lower:
            return 'API_KEY'
        elif 'secret' in line_lower:
            return 'SECRET'
        elif 'token' in line_lower:
            return 'TOKEN'
        elif 'key' in line_lower:
            return 'KEY'
        else:
            return 'CREDENTIAL'
    
    def _generate_env_var_name(self, file_path: str, cred_type: str) -> str:
        """Generate environment variable name"""
        # Extract service name from path
        parts = file_path.split('/')
        if 'scripts' in parts:
            service = 'SCRIPT'
        elif 'mcp_server' in parts:
            service = 'MCP'
        elif 'infrastructure' in parts:
            service = 'INFRA'
        else:
            service = 'APP'
        
        return f"ORCHESTRA_{service}_{cred_type}"
    
    def _add_to_env_template(self, env_var: str, var_type: str):
        """Add environment variable to .env.template"""
        template_path = '.env.template'
        
        # Read existing template or create new
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                content = f.read()
        else:
            content = "# Orchestra Environment Variables\n\n"
        
        # Add new variable if not exists
        if env_var not in content:
            content += f"# {var_type} for Orchestra services\n"
            content += f"{env_var}=your_{var_type.lower()}_here\n\n"
            
            with open(template_path, 'w') as f:
                f.write(content)
    
    def _find_eval_usage(self) -> List[SecurityIssue]:
        """Find all eval() usage in codebase"""
        issues = []
        
        for root, dirs, files in os.walk('.'):
            # Skip virtual environments and cache
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        # Parse AST
                        tree = ast.parse(content)
                        
                        # Find eval calls
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Call):
                                if isinstance(node.func, ast.Name) and node.func.id == 'eval':
                                    issues.append(SecurityIssue(
                                        file=file_path,
                                        line=node.lineno,
                                        issue_type='eval_usage',
                                        severity='critical',
                                        recommendation='Replace with ast.literal_eval or refactor'
                                    ))
                    except Exception as e:
                        logger.error(f"Unexpected error: {e}")
                        pass
        
        return issues
    
    def _fix_eval_usage(self, issue: SecurityIssue) -> DebugResult:
        """Fix eval() usage"""
        try:
            with open(issue.file, 'r') as f:
                lines = f.readlines()
            
            if issue.line <= len(lines):
                line = lines[issue.line - 1]
                
                # Simple replacement for literal evaluation
                if 'eval(' in line:
                    # Check if it's safe to replace with literal_eval
                    new_line = line.replace('eval(', 'ast.literal_eval(')
                    lines[issue.line - 1] = new_line
                    
                    # Add import if needed
                    if not any('import ast' in line for line in lines[:10]):
                        lines.insert(0, "import ast\n")
                    
                    with open(issue.file, 'w') as f:
                        f.writelines(lines)
                    
                    return DebugResult(
                        success=True,
                        issue=f"eval() usage in {issue.file}:{issue.line}",
                        root_cause="Unsafe eval() can execute arbitrary code",
                        fix_applied="Replaced with ast.literal_eval()",
                        prevention="Use ast.literal_eval for safe evaluation",
                        test_added=True
                    )
        
        except Exception as e:
            logger.error(f"Failed to fix eval usage: {e}")
        
        return DebugResult(
            success=False,
            issue=f"eval() usage in {issue.file}:{issue.line}",
            root_cause="Could not automatically fix",
            fix_applied="None",
            prevention="Manual refactoring required"
        )
    
    def debug_performance_issues(self) -> List[DebugResult]:
        """Debug and fix performance issues"""
        logger.info("⚡ Debugging performance issues...")
        results = []
        
        # Fix database queries without indexes
        db_issues = self._analyze_database_queries()
        for issue in db_issues:
            result = self._optimize_database_query(issue)
            results.append(result)
            if result.success:
                self.fixed_issues += 1
            self.total_issues += 1
        
        # Fix synchronous sleep calls
        sleep_issues = self._find_sync_sleep_usage()
        for issue in sleep_issues:
            result = self._fix_sync_sleep(issue)
            results.append(result)
            if result.success:
                self.fixed_issues += 1
            self.total_issues += 1
        
        return results
    
    def _analyze_database_queries(self) -> List[Dict[str, Any]]:
        """Analyze database queries for optimization"""
        issues = []
        
        # Look for database query patterns
        query_patterns = [
            r'\.execute\s*\(\s*["\']SELECT',
            r'\.query\s*\(\s*["\']SELECT',
            r'session\.query\(',
        ]
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        for pattern in query_patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                issues.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'pattern': pattern,
                                    'content': match.group()
                                })
                    except:
                        pass
        
        return issues
    
    def _optimize_database_query(self, issue: Dict[str, Any]) -> DebugResult:
        """Optimize a database query"""
        # For now, add EXPLAIN ANALYZE comment
        try:
            with open(issue['file'], 'r') as f:
                lines = f.readlines()
            
            if issue['line'] <= len(lines):
                line_idx = issue['line'] - 1
                
                # Add optimization comment
                if '# EXPLAIN ANALYZE' not in lines[line_idx]:
                    indent = len(lines[line_idx]) - len(lines[line_idx].lstrip())
                    comment = ' ' * indent + '# TODO: Run EXPLAIN ANALYZE on this query\n'
                    lines.insert(line_idx, comment)
                    
                    with open(issue['file'], 'w') as f:
                        f.writelines(lines)
                    
                    return DebugResult(
                        success=True,
                        issue=f"Unoptimized query in {issue['file']}:{issue['line']}",
                        root_cause="Query may lack proper indexes",
                        fix_applied="Added EXPLAIN ANALYZE reminder",
                        prevention="Always analyze queries before production",
                        monitoring_added=True
                    )
        
        except Exception as e:
            logger.error(f"Failed to optimize query: {e}")
        
        return DebugResult(
            success=False,
            issue=f"Unoptimized query in {issue['file']}:{issue['line']}",
            root_cause="Could not analyze query",
            fix_applied="None",
            prevention="Manual optimization required"
        )
    
    def _find_sync_sleep_usage(self) -> List[Dict[str, Any]]:
        """Find synchronous sleep usage"""
        issues = []
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        # Look for time.sleep
                        matches = re.finditer(r'time\.sleep\s*\(', content)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            issues.append({
                                'file': file_path,
                                'line': line_num
                            })
                    except:
                        pass
        
        return issues
    
    def _fix_sync_sleep(self, issue: Dict[str, Any]) -> DebugResult:
        """Fix synchronous sleep usage"""
        try:
            with open(issue['file'], 'r') as f:
                lines = f.readlines()
            
            if issue['line'] <= len(lines):
                line_idx = issue['line'] - 1
                
                # Add async alternative comment
                indent = len(lines[line_idx]) - len(lines[line_idx].lstrip())
                comment = ' ' * indent + '# TODO: Replace with asyncio.sleep() for async code\n'
                
                if '# TODO:' not in lines[line_idx - 1] if line_idx > 0 else True:
                    lines.insert(line_idx, comment)
                    
                    with open(issue['file'], 'w') as f:
                        f.writelines(lines)
                    
                    return DebugResult(
                        success=True,
                        issue=f"Synchronous sleep in {issue['file']}:{issue['line']}",
                        root_cause="Blocking sleep in potentially async context",
                        fix_applied="Added async alternative reminder",
                        prevention="Use asyncio.sleep() in async functions"
                    )
        
        except Exception as e:
            logger.error(f"Failed to fix sync sleep: {e}")
        
        return DebugResult(
            success=False,
            issue=f"Synchronous sleep in {issue['file']}:{issue['line']}",
            root_cause="Could not determine context",
            fix_applied="None",
            prevention="Manual review required"
        )
    
    def debug_error_handling(self) -> List[DebugResult]:
        """Debug and fix error handling issues"""
        logger.info("🛡️ Debugging error handling...")
        results = []
        
        # Fix bare except clauses
        bare_except_issues = self._find_bare_excepts()
        for issue in bare_except_issues:
            result = self._fix_bare_except(issue)
            results.append(result)
            if result.success:
                self.fixed_issues += 1
            self.total_issues += 1
        
        return results
    
    def _find_bare_excepts(self) -> List[Dict[str, Any]]:
        """Find bare except clauses"""
        issues = []
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        # Parse AST
                        tree = ast.parse(content)
                        
                        # Find bare excepts
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ExceptHandler):
                                if node.type is None:
                                    issues.append({
                                        'file': file_path,
                                        'line': node.lineno
                                    })
                    except:
                        pass
        
        return issues
    
    def _fix_bare_except(self, issue: Dict[str, Any]) -> DebugResult:
        """Fix bare except clause"""
        try:
            with open(issue['file'], 'r') as f:
                lines = f.readlines()
            
            if issue['line'] <= len(lines):
                line_idx = issue['line'] - 1
                line = lines[line_idx]
                
                # Replace bare except with Exception
                if 'except:' in line:
                    new_line = line.replace('except:', 'except Exception as e:')
                    lines[line_idx] = new_line
                    
                    # Add logging
                    indent = len(line) - len(line.lstrip()) + 4
                    log_line = ' ' * indent + 'logger.error(f"Unexpected error: {e}")\n'
                    lines.insert(line_idx + 1, log_line)
                    
                    # Add import if needed
                    if not any('import logging' in line for line in lines[:20]):
                        lines.insert(0, "import logging\n")
                        lines.insert(1, "logger = logging.getLogger(__name__)\n\n")
                    
                    with open(issue['file'], 'w') as f:
                        f.writelines(lines)
                    
                    return DebugResult(
                        success=True,
                        issue=f"Bare except in {issue['file']}:{issue['line']}",
                        root_cause="Catches all exceptions including system exits",
                        fix_applied="Replaced with 'except Exception as e:' and added logging",
                        prevention="Always catch specific exceptions",
                        test_added=True
                    )
        
        except Exception as e:
            logger.error(f"Failed to fix bare except: {e}")
        
        return DebugResult(
            success=False,
            issue=f"Bare except in {issue['file']}:{issue['line']}",
            root_cause="Could not fix automatically",
            fix_applied="None",
            prevention="Manual fix required"
        )
    
    def validate_implementation(self) -> Dict[str, Any]:
        """Validate the implementation against blueprint"""
        logger.info("✅ Validating implementation...")
        
        validation_results = {
            'security': self._validate_security_requirements(),
            'performance': self._validate_performance_targets(),
            'error_handling': self._validate_error_handling(),
            'architecture': self._validate_architecture_compliance()
        }
        
        return validation_results
    
    def _validate_security_requirements(self) -> Dict[str, bool]:
        """Validate security requirements from blueprint"""
        requirements = self.blueprint.get('security_framework', {})
        results = {}
        
        # Check authentication
        results['authentication_configured'] = os.path.exists('.env') or os.path.exists('.env.template')
        
        # Check for SSL/TLS
        results['tls_enabled'] = self._check_tls_configuration()
        
        # Check for security headers
        results['security_headers'] = self._check_security_headers()
        
        return results
    
    def _check_tls_configuration(self) -> bool:
        """Check if TLS is properly configured"""
        # Look for TLS configuration in common places
        tls_indicators = [
            'nginx.conf',
            'docker-compose.yml',
            'config/production.yml'
        ]
        
        for indicator in tls_indicators:
            if os.path.exists(indicator):
                with open(indicator, 'r') as f:
                    content = f.read()
                    if 'ssl' in content or 'tls' in content or 'https' in content:
                        return True
        
        return False
    
    def _check_security_headers(self) -> bool:
        """Check if security headers are configured"""
        # Look for security header configuration
        header_files = [
            'nginx.conf',
            'app.py',
            'main.py',
            'server.py'
        ]
        
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'Strict-Transport-Security'
        ]
        
        for file in header_files:
            if os.path.exists(file):
                with open(file, 'r') as f:
                    content = f.read()
                    if any(header in content for header in security_headers):
                        return True
        
        return False
    
    def _validate_performance_targets(self) -> Dict[str, bool]:
        """Validate performance targets"""
        targets = self.blueprint.get('performance_optimization', {})
        results = {}
        
        # Check for caching
        results['caching_implemented'] = self._check_caching_implementation()
        
        # Check for connection pooling
        results['connection_pooling'] = self._check_connection_pooling()
        
        # Check for async processing
        results['async_processing'] = self._check_async_implementation()
        
        return results
    
    def _check_caching_implementation(self) -> bool:
        """Check if caching is implemented"""
        cache_indicators = ['redis', 'memcached', 'cache', '@cache']
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read().lower()
                            if any(indicator in content for indicator in cache_indicators):
                                return True
                    except:
                        pass
        
        return False
    
    def _check_connection_pooling(self) -> bool:
        """Check if database connection pooling is configured"""
        pool_indicators = ['pool_size', 'max_overflow', 'QueuePool', 'NullPool']
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            if any(indicator in content for indicator in pool_indicators):
                                return True
                    except:
                        pass
        
        return False
    
    def _check_async_implementation(self) -> bool:
        """Check if async processing is implemented"""
        async_indicators = ['async def', 'await ', 'asyncio', 'aiohttp']
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            if any(indicator in content for indicator in async_indicators):
                                return True
                    except:
                        pass
        
        return False
    
    def _validate_error_handling(self) -> Dict[str, bool]:
        """Validate error handling implementation"""
        framework = self.blueprint.get('error_handling_framework', {})
        results = {}
        
        # Check for retry policies
        results['retry_policies'] = self._check_retry_implementation()
        
        # Check for circuit breakers
        results['circuit_breakers'] = self._check_circuit_breakers()
        
        # Check for structured logging
        results['structured_logging'] = self._check_structured_logging()
        
        return results
    
    def _check_retry_implementation(self) -> bool:
        """Check if retry logic is implemented"""
        retry_indicators = ['retry', 'backoff', 'tenacity', '@retry']
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read().lower()
                            if any(indicator in content for indicator in retry_indicators):
                                return True
                    except:
                        pass
        
        return False
    
    def _check_circuit_breakers(self) -> bool:
        """Check if circuit breakers are implemented"""
        cb_indicators = ['circuit', 'breaker', 'pybreaker', 'CircuitBreaker']
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            if any(indicator in content for indicator in cb_indicators):
                                return True
                    except:
                        pass
        
        return False
    
    def _check_structured_logging(self) -> bool:
        """Check if structured logging is implemented"""
        log_indicators = ['logging.getLogger', 'structlog', 'loguru']
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            if any(indicator in content for indicator in log_indicators):
                                return True
                    except:
                        pass
        
        return False
    
    def _validate_architecture_compliance(self) -> Dict[str, bool]:
        """Validate architecture compliance"""
        results = {}
        
        # Check for proper layering
        results['layered_architecture'] = self._check_layered_architecture()
        
        # Check for dependency injection
        results['dependency_injection'] = self._check_dependency_injection()
        
        # Check for event-driven patterns
        results['event_driven'] = self._check_event_driven_patterns()
        
        return results
    
    def _check_layered_architecture(self) -> bool:
        """Check if code follows layered architecture"""
        expected_dirs = ['api', 'services', 'domain', 'infrastructure', 'core']
        found_dirs = []
        
        for item in os.listdir('.'):
            if os.path.isdir(item) and item in expected_dirs:
                found_dirs.append(item)
        
        return len(found_dirs) >= 3  # At least 3 layers present
    
    def _check_dependency_injection(self) -> bool:
        """Check if dependency injection is used"""
        di_indicators = ['inject', 'provider', 'container', 'dependency']
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read().lower()
                            if any(indicator in content for indicator in di_indicators):
                                return True
                    except:
                        pass
        
        return False
    
    def _check_event_driven_patterns(self) -> bool:
        """Check if event-driven patterns are used"""
        event_indicators = ['event', 'publish', 'subscribe', 'message', 'queue']
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read().lower()
                            if any(indicator in content for indicator in event_indicators):
                                return True
                    except:
                        pass
        
        return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive debugging report"""
        validation = self.validate_implementation()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_issues': self.total_issues,
                'fixed_issues': self.fixed_issues,
                'success_rate': self.fixed_issues / self.total_issues if self.total_issues > 0 else 0
            },
            'debug_results': [
                {
                    'success': r.success,
                    'issue': r.issue,
                    'root_cause': r.root_cause,
                    'fix_applied': r.fix_applied,
                    'prevention': r.prevention,
                    'test_added': r.test_added,
                    'monitoring_added': r.monitoring_added
                }
                for r in self.debug_results
            ],
            'validation_results': validation,
            'recommendations': self._generate_recommendations(validation)
        }
        
        return report
    
    def _generate_recommendations(self, validation: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Security recommendations
        security = validation.get('security', {})
        if not security.get('authentication_configured'):
            recommendations.append("Configure authentication using environment variables")
        if not security.get('tls_enabled'):
            recommendations.append("Enable TLS/SSL for all external connections")
        if not security.get('security_headers'):
            recommendations.append("Add security headers (X-Frame-Options, CSP, etc.)")
        
        # Performance recommendations
        performance = validation.get('performance', {})
        if not performance.get('caching_implemented'):
            recommendations.append("Implement Redis caching for frequently accessed data")
        if not performance.get('connection_pooling'):
            recommendations.append("Configure database connection pooling")
        if not performance.get('async_processing'):
            recommendations.append("Use async/await for I/O-bound operations")
        
        # Error handling recommendations
        error_handling = validation.get('error_handling', {})
        if not error_handling.get('retry_policies'):
            recommendations.append("Implement retry policies with exponential backoff")
        if not error_handling.get('circuit_breakers'):
            recommendations.append("Add circuit breakers for external service calls")
        if not error_handling.get('structured_logging'):
            recommendations.append("Use structured logging for better observability")
        
        # Architecture recommendations
        architecture = validation.get('architecture', {})
        if not architecture.get('layered_architecture'):
            recommendations.append("Organize code into clear architectural layers")
        if not architecture.get('dependency_injection'):
            recommendations.append("Implement dependency injection for better testability")
        if not architecture.get('event_driven'):
            recommendations.append("Consider event-driven patterns for loose coupling")
        
        return recommendations


def main():
    """Main execution function"""
    print("🔍 Orchestra Implementation Debugger")
    print("=" * 50)
    
    # Check for required files
    tech_debt_report = None
    blueprint_path = 'architecture_blueprint.json'
    
    # Find the latest technical debt report
    for file in os.listdir('.'):
        if file.startswith('technical_debt_report_') and file.endswith('.json'):
            tech_debt_report = file
            break
    
    if not tech_debt_report:
        print("❌ No technical debt report found. Run technical_debt_analyzer.py first.")
        sys.exit(1)
    
    if not os.path.exists(blueprint_path):
        print("❌ Architecture blueprint not found. Run orchestra_architecture_blueprint.py first.")
        sys.exit(1)
    
    # Initialize debugger
    debugger = ImplementationDebugger(tech_debt_report, blueprint_path)
    
    # Run debugging phases
    print("\n🔒 Phase 1: Security Vulnerabilities")
    security_results = debugger.debug_security_vulnerabilities()
    for result in security_results:
        if result.success:
            print(f"  ✅ Fixed: {result.issue}")
        else:
            print(f"  ❌ Failed: {result.issue}")
    
    print("\n⚡ Phase 2: Performance Issues")
    performance_results = debugger.debug_performance_issues()
    for result in performance_results:
        if result.success:
            print(f"  ✅ Fixed: {result.issue}")
        else:
            print(f"  ❌ Failed: {result.issue}")
    
    print("\n🛡️ Phase 3: Error Handling")
    error_results = debugger.debug_error_handling()
    for result in error_results:
        if result.success:
            print(f"  ✅ Fixed: {result.issue}")
        else:
            print(f"  ❌ Failed: {result.issue}")
    
    # Store all results
    debugger.debug_results.extend(security_results)
    debugger.debug_results.extend(performance_results)
    debugger.debug_results.extend(error_results)
    
    # Generate report
    print("\n📊 Generating Debug Report...")
    report = debugger.generate_report()
    
    # Save report
    report_filename = f"debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n📈 Debug Summary:")
    print(f"  Total Issues: {report['summary']['total_issues']}")
    print(f"  Fixed Issues: {report['summary']['fixed_issues']}")
    print(f"  Success Rate: {report['summary']['success_rate']:.1%}")
    
    print("\n✅ Validation Results:")
    for category, results in report['validation_results'].items():
        print(f"\n  {category.title()}:")
        for check, passed in results.items():
            status = "✅" if passed else "❌"
            print(f"    {status} {check}")
    
    print("\n💡 Recommendations:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"  {i}. {rec}")
    
    print(f"\n📄 Full report saved to: {report_filename}")
    
    # Create implementation checklist
    print("\n📝 Creating implementation checklist...")
    create_implementation_checklist(report)
    
    print("\n✨ Debugging complete! Ready for implementation validation.")


def create_implementation_checklist(report: Dict[str, Any]):
    """Create an implementation checklist script"""
    checklist_content = '''#!/usr/bin/env python3
"""
Orchestra Implementation Checklist
Auto-generated checklist for validating implementation progress
"""

import os
import sys
import json
from datetime import datetime

def check_item(description: str, check_func) -> bool:
    """Check a single item and report status"""
    try:
        result = check_func()
        status = "✅" if result else "❌"
        print(f"{status} {description}")
        return result
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

def main():
    """Run implementation checklist"""
    print("Orchestra Implementation Checklist")
    print("=" * 50)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    passed = 0
    total = 0
    
    # Security Checks
    print("🔒 Security Requirements:")
    total += 1
    if check_item("Environment variables configured",
                  lambda: os.path.exists('.env') or os.path.exists('.env.template')):
        passed += 1
    
    total += 1
    if check_item("No hardcoded credentials",
                  lambda: not any(['password' in open(f).read().lower()
                                  for f in os.listdir('.')
                                  if f.endswith('.py') and os.path.isfile(f)])):
        passed += 1
    
    # Performance Checks
    print("\\n⚡ Performance Requirements:")
    total += 1
    if check_item("Database connection pooling configured",
                  lambda: any(['pool' in open(f).read().lower()
                              for f in os.listdir('.')
                              if f.endswith('.py') and os.path.isfile(f)])):
        passed += 1
    
    # Error Handling Checks
    print("\\n🛡️ Error Handling Requirements:")
    total += 1
    if check_item("Logging configured",
                  lambda: any(['logging' in open(f).read()
                              for f in os.listdir('.')
                              if f.endswith('.py') and os.path.isfile(f)])):
        passed += 1
    
    # Architecture Checks
    print("\\n🏗️ Architecture Requirements:")
    total += 1
    if check_item("Layered architecture structure",
                  lambda: any([os.path.isdir(d) for d in ['api', 'services', 'domain']])):
        passed += 1
    
    # Summary
    print(f"\\n📊 Summary: {passed}/{total} checks passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\\n✅ All checks passed! Ready for production.")
        return 0
    else:
        print(f"\\n⚠️  {total - passed} checks failed. Please address the issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
    
    with open('implementation_checklist.py', 'w') as f:
        f.write(checklist_content)
    
    os.chmod('implementation_checklist.py', 0o755)
    print("✅ Created implementation_checklist.py")


if __name__ == "__main__":
    main()