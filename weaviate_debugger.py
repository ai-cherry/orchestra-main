#!/usr/bin/env python3
"""
Weaviate Debugger - Comprehensive diagnostics and resolution
Identifies root causes of connectivity, authentication, and data retrieval issues
"""

import os
import sys
import json
import time
import subprocess
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import socket
import traceback

class WeaviateDebugger:
    def __init__(self):
        self.timestamp = datetime.now()
        self.issues_found = []
        self.resolutions = []
        self.logs = []
        
        # Weaviate configuration
        self.weaviate_url = os.getenv('WEAVIATE_URL', 'http://localhost:8080')
        self.weaviate_host = 'localhost'
        self.weaviate_port = 8080
        
    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp"""
        entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {message}"
        print(entry)
        self.logs.append(entry)
    
    def run_full_diagnostics(self):
        """Run comprehensive Weaviate diagnostics"""
        self.log("Starting Weaviate comprehensive diagnostics", "INFO")
        
        # 1. Check service status
        self.log("\n=== CHECKING SERVICE STATUS ===")
        service_status = self.check_service_status()
        
        # 2. Check network connectivity
        self.log("\n=== CHECKING NETWORK CONNECTIVITY ===")
        network_status = self.check_network_connectivity()
        
        # 3. Check process and ports
        self.log("\n=== CHECKING PROCESSES AND PORTS ===")
        process_status = self.check_processes_and_ports()
        
        # 4. Check logs for errors
        self.log("\n=== ANALYZING WEAVIATE LOGS ===")
        log_analysis = self.analyze_logs()
        
        # 5. Check configuration
        self.log("\n=== CHECKING CONFIGURATION ===")
        config_status = self.check_configuration()
        
        # 6. Test API connectivity
        self.log("\n=== TESTING API CONNECTIVITY ===")
        api_status = self.test_api_connectivity()
        
        # 7. Check authentication
        self.log("\n=== CHECKING AUTHENTICATION ===")
        auth_status = self.check_authentication()
        
        # 8. Check schema and data
        self.log("\n=== CHECKING SCHEMA AND DATA ===")
        schema_status = self.check_schema_and_data()
        
        # 9. Performance diagnostics
        self.log("\n=== PERFORMANCE DIAGNOSTICS ===")
        perf_status = self.check_performance()
        
        # Generate report
        return self.generate_report()
    
    def check_service_status(self) -> Dict:
        """Check if Weaviate service is running"""
        try:
            # Check systemctl status
            result = subprocess.run(
                ['systemctl', 'status', 'weaviate'],
                capture_output=True,
                text=True
            )
            
            is_active = 'active (running)' in result.stdout
            
            if not is_active:
                self.log("Weaviate service is NOT running", "ERROR")
                self.issues_found.append({
                    'type': 'SERVICE_DOWN',
                    'severity': 'CRITICAL',
                    'details': 'Weaviate systemd service is not active',
                    'output': result.stdout + result.stderr
                })
                
                # Check for common error patterns
                if 'code=exited' in result.stdout:
                    exit_code = result.stdout.split('code=exited, status=')[1].split(')')[0]
                    self.log(f"Service exited with code: {exit_code}", "ERROR")
                    
                    # Check why it failed
                    journal_result = subprocess.run(
                        ['journalctl', '-u', 'weaviate', '-n', '50', '--no-pager'],
                        capture_output=True,
                        text=True
                    )
                    
                    self.issues_found.append({
                        'type': 'SERVICE_CRASH',
                        'severity': 'CRITICAL',
                        'details': f'Service crashed with exit code {exit_code}',
                        'logs': journal_result.stdout
                    })
            else:
                self.log("Weaviate service is running", "SUCCESS")
            
            return {
                'active': is_active,
                'status': result.stdout
            }
            
        except Exception as e:
            self.log(f"Error checking service status: {str(e)}", "ERROR")
            return {'active': False, 'error': str(e)}
    
    def check_network_connectivity(self) -> Dict:
        """Check network connectivity to Weaviate"""
        results = {}
        
        # Test port connectivity
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.weaviate_host, self.weaviate_port))
            sock.close()
            
            if result == 0:
                self.log(f"Port {self.weaviate_port} is open", "SUCCESS")
                results['port_open'] = True
            else:
                self.log(f"Port {self.weaviate_port} is CLOSED", "ERROR")
                results['port_open'] = False
                self.issues_found.append({
                    'type': 'PORT_CLOSED',
                    'severity': 'CRITICAL',
                    'details': f'Cannot connect to port {self.weaviate_port}'
                })
                
        except Exception as e:
            self.log(f"Network connectivity error: {str(e)}", "ERROR")
            results['port_open'] = False
            
        # Check firewall rules
        try:
            iptables_result = subprocess.run(
                ['sudo', 'iptables', '-L', '-n'],
                capture_output=True,
                text=True
            )
            
            if f'{self.weaviate_port}' in iptables_result.stdout:
                self.log("Found firewall rules for Weaviate port", "WARNING")
                results['firewall_rules'] = True
                
        except:
            pass
            
        return results
    
    def check_processes_and_ports(self) -> Dict:
        """Check running processes and port bindings"""
        results = {}
        
        # Check if Weaviate process is running
        try:
            ps_result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True
            )
            
            weaviate_processes = [line for line in ps_result.stdout.split('\n') if 'weaviate' in line.lower()]
            
            if weaviate_processes:
                self.log(f"Found {len(weaviate_processes)} Weaviate process(es)", "INFO")
                results['processes'] = weaviate_processes
            else:
                self.log("No Weaviate processes found", "ERROR")
                self.issues_found.append({
                    'type': 'NO_PROCESS',
                    'severity': 'CRITICAL',
                    'details': 'Weaviate process is not running'
                })
                
        except Exception as e:
            self.log(f"Error checking processes: {str(e)}", "ERROR")
            
        # Check port bindings
        try:
            netstat_result = subprocess.run(
                ['netstat', '-tlnp'],
                capture_output=True,
                text=True
            )
            
            port_bindings = [line for line in netstat_result.stdout.split('\n') if str(self.weaviate_port) in line]
            
            if port_bindings:
                self.log(f"Port {self.weaviate_port} is bound", "SUCCESS")
                results['port_bound'] = True
            else:
                self.log(f"Port {self.weaviate_port} is NOT bound", "ERROR")
                results['port_bound'] = False
                
        except:
            # Try ss if netstat not available
            try:
                ss_result = subprocess.run(
                    ['ss', '-tlnp'],
                    capture_output=True,
                    text=True
                )
                if str(self.weaviate_port) in ss_result.stdout:
                    results['port_bound'] = True
            except:
                pass
                
        return results
    
    def analyze_logs(self) -> Dict:
        """Analyze Weaviate logs for errors"""
        log_analysis = {
            'errors': [],
            'warnings': [],
            'recent_events': []
        }
        
        # Check systemd logs
        try:
            journal_result = subprocess.run(
                ['journalctl', '-u', 'weaviate', '-n', '100', '--no-pager'],
                capture_output=True,
                text=True
            )
            
            logs = journal_result.stdout.split('\n')
            
            for line in logs:
                if 'error' in line.lower():
                    log_analysis['errors'].append(line)
                    
                    # Check for specific error patterns
                    if 'syntax error' in line.lower():
                        self.issues_found.append({
                            'type': 'SYNTAX_ERROR',
                            'severity': 'CRITICAL',
                            'details': 'Python syntax error preventing startup',
                            'log_line': line
                        })
                    elif 'import error' in line.lower():
                        self.issues_found.append({
                            'type': 'IMPORT_ERROR',
                            'severity': 'CRITICAL',
                            'details': 'Missing dependency or import error',
                            'log_line': line
                        })
                    elif 'connection refused' in line.lower():
                        self.issues_found.append({
                            'type': 'CONNECTION_ERROR',
                            'severity': 'HIGH',
                            'details': 'Connection refused - possible dependency issue',
                            'log_line': line
                        })
                        
                elif 'warning' in line.lower():
                    log_analysis['warnings'].append(line)
                    
            # Get recent events
            log_analysis['recent_events'] = logs[-10:]
            
        except Exception as e:
            self.log(f"Error analyzing logs: {str(e)}", "ERROR")
            
        # Check Weaviate specific logs
        weaviate_log_paths = [
            '/var/log/weaviate/weaviate.log',
            './weaviate.log',
            '/opt/weaviate/logs/weaviate.log'
        ]
        
        for log_path in weaviate_log_paths:
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r') as f:
                        recent_logs = f.readlines()[-50:]
                        log_analysis['weaviate_logs'] = recent_logs
                        
                        for line in recent_logs:
                            if 'panic:' in line:
                                self.issues_found.append({
                                    'type': 'PANIC',
                                    'severity': 'CRITICAL',
                                    'details': 'Weaviate panic detected',
                                    'log_line': line
                                })
                                
                except Exception as e:
                    self.log(f"Error reading {log_path}: {str(e)}", "WARNING")
                    
        return log_analysis
    
    def check_configuration(self) -> Dict:
        """Check Weaviate configuration"""
        config_status = {}
        
        # Common config locations
        config_paths = [
            '/etc/weaviate/weaviate.conf',
            './weaviate.conf',
            '/opt/weaviate/config/weaviate.conf',
            '.env'
        ]
        
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        content = f.read()
                        
                    config_status[config_path] = {
                        'exists': True,
                        'readable': True
                    }
                    
                    # Check for common misconfigurations
                    if 'WEAVIATE_HOST' in content and 'localhost' not in content:
                        self.log("Non-localhost host configured", "WARNING")
                        
                    if 'AUTHENTICATION' in content:
                        self.log("Authentication is configured", "INFO")
                        
                except Exception as e:
                    config_status[config_path] = {
                        'exists': True,
                        'readable': False,
                        'error': str(e)
                    }
                    
        # Check environment variables
        env_vars = {
            'WEAVIATE_URL': os.getenv('WEAVIATE_URL'),
            'WEAVIATE_HOST': os.getenv('WEAVIATE_HOST'),
            'WEAVIATE_PORT': os.getenv('WEAVIATE_PORT'),
            'WEAVIATE_SCHEME': os.getenv('WEAVIATE_SCHEME')
        }
        
        config_status['environment'] = env_vars
        
        return config_status
    
    def test_api_connectivity(self) -> Dict:
        """Test Weaviate API endpoints"""
        api_tests = {}
        
        endpoints = [
            ('/', 'Root endpoint'),
            ('/v1/meta', 'Meta endpoint'),
            ('/v1/schema', 'Schema endpoint'),
            ('/v1/.well-known/ready', 'Readiness endpoint'),
            ('/v1/.well-known/live', 'Liveness endpoint')
        ]
        
        for endpoint, description in endpoints:
            url = f"{self.weaviate_url}{endpoint}"
            
            try:
                response = requests.get(url, timeout=5)
                
                api_tests[endpoint] = {
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'response_time': response.elapsed.total_seconds(),
                    'description': description
                }
                
                if response.status_code == 200:
                    self.log(f"{description} OK ({response.elapsed.total_seconds():.2f}s)", "SUCCESS")
                else:
                    self.log(f"{description} returned {response.status_code}", "WARNING")
                    
                    if response.status_code == 401:
                        self.issues_found.append({
                            'type': 'AUTH_REQUIRED',
                            'severity': 'HIGH',
                            'details': f'Authentication required for {endpoint}'
                        })
                    elif response.status_code == 404:
                        self.issues_found.append({
                            'type': 'ENDPOINT_NOT_FOUND',
                            'severity': 'MEDIUM',
                            'details': f'Endpoint {endpoint} not found'
                        })
                        
            except requests.exceptions.ConnectionError:
                self.log(f"{description} - Connection refused", "ERROR")
                api_tests[endpoint] = {
                    'success': False,
                    'error': 'Connection refused'
                }
                self.issues_found.append({
                    'type': 'API_UNREACHABLE',
                    'severity': 'CRITICAL',
                    'details': f'Cannot connect to {url}'
                })
                
            except requests.exceptions.Timeout:
                self.log(f"{description} - Timeout", "ERROR")
                api_tests[endpoint] = {
                    'success': False,
                    'error': 'Timeout'
                }
                
            except Exception as e:
                self.log(f"{description} - Error: {str(e)}", "ERROR")
                api_tests[endpoint] = {
                    'success': False,
                    'error': str(e)
                }
                
        return api_tests
    
    def check_authentication(self) -> Dict:
        """Check authentication configuration"""
        auth_status = {}
        
        # Test with different auth methods
        auth_methods = [
            ('none', None),
            ('api_key', {'X-API-KEY': 'test-key'}),
            ('oidc', {'Authorization': 'Bearer test-token'})
        ]
        
        for method, headers in auth_methods:
            try:
                response = requests.get(
                    f"{self.weaviate_url}/v1/meta",
                    headers=headers,
                    timeout=5
                )
                
                auth_status[method] = {
                    'status_code': response.status_code,
                    'success': response.status_code == 200
                }
                
                if response.status_code == 200 and method == 'none':
                    self.log("No authentication required", "WARNING")
                    self.issues_found.append({
                        'type': 'NO_AUTH',
                        'severity': 'MEDIUM',
                        'details': 'Weaviate is accessible without authentication'
                    })
                    
            except Exception as e:
                auth_status[method] = {
                    'success': False,
                    'error': str(e)
                }
                
        return auth_status
    
    def check_schema_and_data(self) -> Dict:
        """Check schema integrity and data access"""
        schema_status = {}
        
        try:
            # Get schema
            response = requests.get(f"{self.weaviate_url}/v1/schema", timeout=5)
            
            if response.status_code == 200:
                schema = response.json()
                schema_status['schema_accessible'] = True
                schema_status['classes'] = len(schema.get('classes', []))
                
                self.log(f"Schema accessible, {len(schema.get('classes', []))} classes found", "SUCCESS")
                
                # Check each class
                for class_def in schema.get('classes', []):
                    class_name = class_def.get('class')
                    
                    # Try to query the class
                    try:
                        query_response = requests.get(
                            f"{self.weaviate_url}/v1/objects?class={class_name}&limit=1",
                            timeout=5
                        )
                        
                        if query_response.status_code == 200:
                            schema_status[f'class_{class_name}'] = 'accessible'
                        else:
                            schema_status[f'class_{class_name}'] = f'error_{query_response.status_code}'
                            
                    except Exception as e:
                        schema_status[f'class_{class_name}'] = f'error: {str(e)}'
                        
            else:
                schema_status['schema_accessible'] = False
                self.issues_found.append({
                    'type': 'SCHEMA_INACCESSIBLE',
                    'severity': 'HIGH',
                    'details': f'Cannot access schema, status: {response.status_code}'
                })
                
        except Exception as e:
            schema_status['error'] = str(e)
            self.issues_found.append({
                'type': 'SCHEMA_ERROR',
                'severity': 'HIGH',
                'details': f'Error accessing schema: {str(e)}'
            })
            
        return schema_status
    
    def check_performance(self) -> Dict:
        """Check performance metrics"""
        perf_status = {}
        
        # Check system resources
        try:
            # Memory usage
            mem_result = subprocess.run(
                ['free', '-m'],
                capture_output=True,
                text=True
            )
            
            mem_lines = mem_result.stdout.split('\n')
            if len(mem_lines) > 1:
                mem_parts = mem_lines[1].split()
                if len(mem_parts) > 3:
                    total_mem = int(mem_parts[1])
                    used_mem = int(mem_parts[2])
                    mem_percent = (used_mem / total_mem) * 100
                    
                    perf_status['memory'] = {
                        'total_mb': total_mem,
                        'used_mb': used_mem,
                        'percent': mem_percent
                    }
                    
                    if mem_percent > 90:
                        self.issues_found.append({
                            'type': 'HIGH_MEMORY',
                            'severity': 'HIGH',
                            'details': f'Memory usage at {mem_percent:.1f}%'
                        })
                        
            # CPU usage
            cpu_result = subprocess.run(
                ['top', '-bn1'],
                capture_output=True,
                text=True
            )
            
            for line in cpu_result.stdout.split('\n'):
                if 'weaviate' in line.lower():
                    parts = line.split()
                    if len(parts) > 8:
                        cpu_percent = float(parts[8].replace(',', '.'))
                        perf_status['weaviate_cpu'] = cpu_percent
                        
                        if cpu_percent > 80:
                            self.issues_found.append({
                                'type': 'HIGH_CPU',
                                'severity': 'MEDIUM',
                                'details': f'Weaviate CPU usage at {cpu_percent}%'
                            })
                            
        except Exception as e:
            self.log(f"Error checking performance: {str(e)}", "WARNING")
            
        return perf_status
    
    def generate_resolutions(self):
        """Generate resolutions for found issues"""
        for issue in self.issues_found:
            if issue['type'] == 'SERVICE_DOWN':
                self.resolutions.append({
                    'issue': 'Weaviate service is down',
                    'steps': [
                        'Check Python syntax errors: grep -r "SyntaxError" /var/log/weaviate/',
                        'Fix any Python files with indentation errors',
                        'Restart service: sudo systemctl restart weaviate',
                        'Check status: sudo systemctl status weaviate'
                    ],
                    'script': 'fix_weaviate_service.sh'
                })
                
            elif issue['type'] == 'SYNTAX_ERROR':
                self.resolutions.append({
                    'issue': 'Python syntax errors preventing startup',
                    'steps': [
                        'Run syntax fixer: python3 automated_syntax_fixer.py',
                        'Check specific files mentioned in logs',
                        'Validate Python files: python3 -m py_compile <file>',
                        'Restart service after fixes'
                    ],
                    'priority': 'CRITICAL'
                })
                
            elif issue['type'] == 'PORT_CLOSED':
                self.resolutions.append({
                    'issue': f'Port {self.weaviate_port} is closed',
                    'steps': [
                        'Check if service is running: ps aux | grep weaviate',
                        'Check firewall: sudo iptables -L -n',
                        'Open port if needed: sudo ufw allow 8080',
                        'Verify binding: netstat -tlnp | grep 8080'
                    ]
                })
                
            elif issue['type'] == 'API_UNREACHABLE':
                self.resolutions.append({
                    'issue': 'API endpoints unreachable',
                    'steps': [
                        'Verify service is running',
                        'Check network connectivity',
                        'Review Weaviate configuration',
                        'Check for proxy/firewall issues'
                    ]
                })
    
    def generate_report(self) -> Dict:
        """Generate comprehensive debug report"""
        self.generate_resolutions()
        
        report = {
            'timestamp': self.timestamp.isoformat(),
            'summary': {
                'total_issues': len(self.issues_found),
                'critical_issues': len([i for i in self.issues_found if i['severity'] == 'CRITICAL']),
                'high_issues': len([i for i in self.issues_found if i['severity'] == 'HIGH']),
                'resolutions_provided': len(self.resolutions)
            },
            'issues': self.issues_found,
            'resolutions': self.resolutions,
            'logs': self.logs[-100:]  # Last 100 log entries
        }
        
        # Save report
        report_path = f"weaviate_debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.log(f"\nDebug report saved to: {report_path}", "INFO")
        
        return report
    
    def create_fix_script(self):
        """Create automated fix script"""
        script_content = '''#!/bin/bash
# Weaviate Fix Script - Generated by debugger

echo "Fixing Weaviate issues..."

# 1. Fix Python syntax errors
echo "Checking for Python syntax errors..."
find /opt/weaviate -name "*.py" -exec python3 -m py_compile {} \; 2>&1 | grep -E "SyntaxError|IndentationError"

# 2. Restart Weaviate service
echo "Restarting Weaviate service..."
sudo systemctl stop weaviate
sleep 2
sudo systemctl start weaviate

# 3. Wait for service to start
echo "Waiting for service to start..."
sleep 10

# 4. Check service status
sudo systemctl status weaviate

# 5. Test API connectivity
echo "Testing API connectivity..."
curl -s http://localhost:8080/v1/.well-known/ready || echo "API not ready"

echo "Fix script completed"
'''
        
        with open('fix_weaviate.sh', 'w') as f:
            f.write(script_content)
            
        os.chmod('fix_weaviate.sh', 0o755)
        self.log("Created fix script: fix_weaviate.sh", "INFO")


def main():
    """Run Weaviate debugger"""
    debugger = WeaviateDebugger()
    
    print("="*80)
    print("WEAVIATE DEBUGGER - Comprehensive Diagnostics")
    print("="*80)
    
    # Run diagnostics
    report = debugger.run_full_diagnostics()
    
    # Print summary
    print("\n" + "="*80)
    print("DIAGNOSTIC SUMMARY")
    print("="*80)
    print(f"Total issues found: {report['summary']['total_issues']}")
    print(f"Critical issues: {report['summary']['critical_issues']}")
    print(f"High priority issues: {report['summary']['high_issues']}")
    
    if report['issues']:
        print("\nTOP ISSUES:")
        for issue in report['issues'][:5]:
            print(f"- [{issue['severity']}] {issue['type']}: {issue['details']}")
    
    if report['resolutions']:
        print("\nRECOMMENDED ACTIONS:")
        for i, resolution in enumerate(report['resolutions'][:3], 1):
            print(f"\n{i}. {resolution['issue']}")
            for step in resolution['steps']:
                print(f"   - {step}")
    
    # Create fix script
    debugger.create_fix_script()
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("1. Review the detailed report")
    print("2. Run: ./fix_weaviate.sh")
    print("3. Monitor: python3 monitor_cherry_deployment.py")
    print("="*80)


if __name__ == "__main__":
    main()