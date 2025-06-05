#!/usr/bin/env python3
"""
Cherry AI Orchestrator Deployment Root Cause Analysis
Investigates why mock data persists and deployment fails
"""

import os
import sys
import json
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'cherry_diagnosis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class CherryDeploymentDiagnostics:
    """Diagnose Cherry AI deployment issues"""
    
    def __init__(self):
        self.lambda_ip = "150.136.94.139"
        self.cherry_domain = "cherry-ai.me"
        self.username = "ubuntu"
        self.issues_found = []
        self.diagnosis_results = {}
        
    def execute_ssh_command(self, host: str, command: str, user: str = None) -> Tuple[int, str, str]:
        """Execute SSH command and return exit code, stdout, stderr"""
        user = user or self.username
        ssh_cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 {user}@{host} '{command}'"
        
        logger.debug(f"Executing on {host}: {command}")
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
        
        return result.returncode, result.stdout, result.stderr
    
    def diagnose_file_locations(self):
        """Check where files are actually deployed"""
        logger.info("\n🔍 DIAGNOSING FILE LOCATIONS")
        logger.info("=" * 60)
        
        locations_to_check = [
            "/opt/orchestra",
            "/var/www/html",
            "/var/www/cherry-ai-orchestrator",
            "/home/ubuntu/orchestra",
            "/usr/share/nginx/html"
        ]
        
        file_locations = {}
        
        for location in locations_to_check:
            logger.info(f"\nChecking {location}...")
            
            # Check if directory exists
            exit_code, stdout, _ = self.execute_ssh_command(
                self.lambda_ip,
                f"test -d {location} && echo 'EXISTS' || echo 'NOT_FOUND'"
            )
            
            if "EXISTS" in stdout:
                # List orchestrator files
                exit_code, stdout, _ = self.execute_ssh_command(
                    self.lambda_ip,
                    f"find {location} -name '*orchestrator*.html' -o -name '*orchestrator*.js' -o -name '*cherry*.html' | head -20"
                )
                
                if stdout.strip():
                    file_locations[location] = stdout.strip().split('\n')
                    logger.info(f"  ✅ Found files:")
                    for file in file_locations[location]:
                        logger.info(f"     - {file}")
                        
                        # Check file modification time
                        exit_code, mtime, _ = self.execute_ssh_command(
                            self.lambda_ip,
                            f"stat -c '%y' '{file}' 2>/dev/null"
                        )
                        if mtime:
                            logger.info(f"       Modified: {mtime.strip()}")
                else:
                    logger.info(f"  ⚠️  Directory exists but no orchestrator files found")
            else:
                logger.info(f"  ❌ Directory does not exist")
        
        self.diagnosis_results['file_locations'] = file_locations
        
        if not file_locations:
            self.issues_found.append("No orchestrator files found in any expected location")
    
    def check_nginx_configuration(self):
        """Analyze nginx configuration for issues"""
        logger.info("\n🔧 CHECKING NGINX CONFIGURATION")
        logger.info("=" * 60)
        
        nginx_issues = []
        
        # Check nginx sites-enabled
        logger.info("\nChecking nginx sites-enabled...")
        exit_code, stdout, _ = self.execute_ssh_command(
            self.lambda_ip,
            "ls -la /etc/nginx/sites-enabled/"
        )
        logger.info(f"Sites enabled:\n{stdout}")
        
        # Check for orchestra-specific config
        exit_code, stdout, _ = self.execute_ssh_command(
            self.lambda_ip,
            "grep -r 'orchestrator\\|cherry' /etc/nginx/sites-enabled/ | head -20"
        )
        
        if stdout:
            logger.info(f"\nOrchestra-related nginx config found:")
            logger.info(stdout)
            
            # Get full config
            exit_code, config, _ = self.execute_ssh_command(
                self.lambda_ip,
                "cat /etc/nginx/sites-enabled/orchestra 2>/dev/null || cat /etc/nginx/sites-enabled/default"
            )
            
            # Check for caching directives
            if "proxy_cache" in config or "expires" in config:
                nginx_issues.append("Nginx caching is enabled - this could cause stale content")
                logger.warning("  ⚠️  Found caching directives in nginx config")
            
            # Check root directory
            import re
            root_match = re.search(r'root\s+([^;]+);', config)
            if root_match:
                root_dir = root_match.group(1).strip()
                logger.info(f"\nNginx root directory: {root_dir}")
                self.diagnosis_results['nginx_root'] = root_dir
            
            # Check location blocks
            location_matches = re.findall(r'location\s+([^\s{]+)\s*{([^}]+)}', config, re.DOTALL)
            for location, block in location_matches:
                if 'orchestrator' in location or 'api' in location:
                    logger.info(f"\nLocation block for {location}:")
                    logger.info(f"  {block.strip()}")
        else:
            nginx_issues.append("No orchestra/cherry configuration found in nginx")
            logger.error("  ❌ No orchestra-specific nginx configuration found")
        
        # Check nginx error logs
        logger.info("\nChecking recent nginx errors...")
        exit_code, errors, _ = self.execute_ssh_command(
            self.lambda_ip,
            "sudo tail -50 /var/log/nginx/error.log | grep -i 'orchestrator\\|cherry' || echo 'No relevant errors'"
        )
        if errors and "No relevant errors" not in errors:
            logger.warning(f"Nginx errors found:\n{errors}")
            nginx_issues.append("Nginx errors detected in logs")
        
        self.diagnosis_results['nginx_issues'] = nginx_issues
        self.issues_found.extend(nginx_issues)
    
    def verify_javascript_files(self):
        """Check which JavaScript files are actually being served"""
        logger.info("\n📜 VERIFYING JAVASCRIPT FILES")
        logger.info("=" * 60)
        
        js_analysis = {}
        
        # Find all orchestrator JS files
        exit_code, js_files, _ = self.execute_ssh_command(
            self.lambda_ip,
            "find /opt/orchestra /var/www -name '*orchestrator*.js' 2>/dev/null | grep -v node_modules"
        )
        
        if js_files:
            for js_file in js_files.strip().split('\n'):
                if not js_file:
                    continue
                    
                logger.info(f"\nAnalyzing: {js_file}")
                
                # Check if it has mock data
                exit_code, content, _ = self.execute_ssh_command(
                    self.lambda_ip,
                    f"grep -c 'alert\\|mock\\|Mock\\|MOCK\\|dummy\\|Dummy' '{js_file}' || echo '0'"
                )
                
                mock_count = int(content.strip())
                
                # Check if it has real API calls
                exit_code, api_content, _ = self.execute_ssh_command(
                    self.lambda_ip,
                    f"grep -c 'fetch\\|axios\\|/api/' '{js_file}' || echo '0'"
                )
                
                api_count = int(api_content.strip())
                
                # Get file size and first few lines
                exit_code, file_info, _ = self.execute_ssh_command(
                    self.lambda_ip,
                    f"wc -l '{js_file}' && head -5 '{js_file}'"
                )
                
                js_analysis[js_file] = {
                    'mock_references': mock_count,
                    'api_references': api_count,
                    'file_info': file_info.strip()
                }
                
                logger.info(f"  Mock references: {mock_count}")
                logger.info(f"  API references: {api_count}")
                
                if mock_count > 0 and api_count == 0:
                    self.issues_found.append(f"JavaScript file {js_file} contains mock data but no API calls")
        
        self.diagnosis_results['javascript_analysis'] = js_analysis
    
    def check_html_javascript_references(self):
        """Verify which JS files the HTML is actually loading"""
        logger.info("\n🔗 CHECKING HTML JAVASCRIPT REFERENCES")
        logger.info("=" * 60)
        
        # Find all orchestrator HTML files
        exit_code, html_files, _ = self.execute_ssh_command(
            self.lambda_ip,
            "find /opt/orchestra /var/www -name '*orchestrator*.html' -o -name '*cherry*.html' 2>/dev/null | grep -v node_modules"
        )
        
        html_js_refs = {}
        
        if html_files:
            for html_file in html_files.strip().split('\n'):
                if not html_file:
                    continue
                    
                logger.info(f"\nChecking: {html_file}")
                
                # Extract script references
                exit_code, scripts, _ = self.execute_ssh_command(
                    self.lambda_ip,
                    f"grep -o '<script[^>]*src=[^>]*>' '{html_file}' || echo 'No external scripts'"
                )
                
                html_js_refs[html_file] = scripts.strip()
                logger.info(f"  Script references:\n{scripts}")
                
                # Check for inline scripts with mock data
                exit_code, inline_mocks, _ = self.execute_ssh_command(
                    self.lambda_ip,
                    f"grep -c 'alert\\|mock\\|Mock' '{html_file}' || echo '0'"
                )
                
                if int(inline_mocks.strip()) > 0:
                    self.issues_found.append(f"HTML file {html_file} contains inline mock references")
                    logger.warning(f"  ⚠️  Found inline mock references")
        
        self.diagnosis_results['html_js_references'] = html_js_refs
    
    def test_domain_connectivity(self):
        """Test cherry-ai.me domain and DNS"""
        logger.info("\n🌐 TESTING DOMAIN CONNECTIVITY")
        logger.info("=" * 60)
        
        domain_issues = []
        
        # DNS lookup
        logger.info(f"\nDNS lookup for {self.cherry_domain}...")
        dns_result = subprocess.run(
            f"nslookup {self.cherry_domain}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        logger.info(dns_result.stdout)
        
        if self.lambda_ip not in dns_result.stdout:
            domain_issues.append(f"DNS not pointing to Lambda server {self.lambda_ip}")
            logger.error(f"  ❌ Domain not pointing to expected IP")
        
        # Try SSH to domain
        logger.info(f"\nTesting SSH to {self.cherry_domain}...")
        exit_code, _, stderr = self.execute_ssh_command(
            self.cherry_domain,
            "echo 'SSH connection successful'",
            user="root"
        )
        
        if exit_code != 0:
            domain_issues.append(f"Cannot SSH to {self.cherry_domain}: {stderr}")
            logger.error(f"  ❌ SSH connection failed: {stderr}")
            
            # Try with ubuntu user
            exit_code, _, stderr = self.execute_ssh_command(
                self.cherry_domain,
                "echo 'SSH connection successful'",
                user="ubuntu"
            )
            
            if exit_code == 0:
                logger.info("  ✅ SSH works with ubuntu user")
            else:
                logger.error("  ❌ SSH also fails with ubuntu user")
        else:
            logger.info("  ✅ SSH connection successful")
        
        # HTTP test
        logger.info(f"\nTesting HTTP access to {self.cherry_domain}...")
        http_result = subprocess.run(
            f"curl -s -I http://{self.cherry_domain}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if "200 OK" in http_result.stdout or "301" in http_result.stdout:
            logger.info("  ✅ HTTP access working")
        else:
            domain_issues.append("HTTP access to domain not working properly")
            logger.error(f"  ❌ HTTP access issue:\n{http_result.stdout}")
        
        self.diagnosis_results['domain_issues'] = domain_issues
        self.issues_found.extend(domain_issues)
    
    def check_browser_caching(self):
        """Generate browser cache-busting recommendations"""
        logger.info("\n🌐 BROWSER CACHING ANALYSIS")
        logger.info("=" * 60)
        
        cache_solutions = []
        
        # Check current cache headers
        exit_code, headers, _ = self.execute_ssh_command(
            self.lambda_ip,
            "curl -s -I http://localhost/orchestrator/ | grep -i 'cache\\|expires\\|etag'"
        )
        
        logger.info(f"Current cache headers:\n{headers}")
        
        if not headers or "no-cache" not in headers.lower():
            cache_solutions.append("Add no-cache headers to nginx configuration")
            cache_solutions.append("Implement cache busting with version query parameters")
        
        self.diagnosis_results['cache_solutions'] = cache_solutions
    
    def check_api_connectivity(self):
        """Verify API is accessible from frontend"""
        logger.info("\n🔌 CHECKING API CONNECTIVITY")
        logger.info("=" * 60)
        
        api_issues = []
        
        # Test local API
        logger.info("\nTesting API on Lambda server...")
        endpoints = [
            ("http://localhost:8000/health", "Health check"),
            ("http://localhost:8000/api/health", "API health"),
            ("http://localhost/api/health", "Nginx proxied API")
        ]
        
        for endpoint, description in endpoints:
            exit_code, response, _ = self.execute_ssh_command(
                self.lambda_ip,
                f"curl -s {endpoint} | head -100"
            )
            
            logger.info(f"\n{description} ({endpoint}):")
            if exit_code == 0 and response:
                logger.info(f"  ✅ Response: {response[:200]}")
            else:
                api_issues.append(f"{description} endpoint not accessible")
                logger.error(f"  ❌ No response")
        
        self.diagnosis_results['api_issues'] = api_issues
        self.issues_found.extend(api_issues)
    
    def generate_diagnosis_report(self):
        """Generate comprehensive diagnosis report"""
        logger.info("\n📊 DIAGNOSIS SUMMARY")
        logger.info("=" * 60)
        
        report = {
            "diagnosis_timestamp": datetime.now().isoformat(),
            "servers_checked": {
                "lambda_labs": self.lambda_ip,
                "cherry_domain": self.cherry_domain
            },
            "issues_found": self.issues_found,
            "detailed_results": self.diagnosis_results,
            "root_causes": self._identify_root_causes(),
            "recommended_fixes": self._generate_fixes()
        }
        
        # Save report
        report_file = f"cherry_diagnosis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n📄 Full diagnosis report saved to: {report_file}")
        
        # Print summary
        logger.info("\n🔴 ROOT CAUSES IDENTIFIED:")
        for i, cause in enumerate(report['root_causes'], 1):
            logger.info(f"{i}. {cause}")
        
        logger.info("\n💡 RECOMMENDED FIXES:")
        for i, fix in enumerate(report['recommended_fixes'], 1):
            logger.info(f"{i}. {fix}")
        
        return report
    
    def _identify_root_causes(self) -> List[str]:
        """Identify root causes based on diagnosis"""
        root_causes = []
        
        if 'file_locations' in self.diagnosis_results:
            if not self.diagnosis_results['file_locations']:
                root_causes.append("Orchestrator files are not deployed to any expected location")
            elif len(self.diagnosis_results['file_locations']) > 1:
                root_causes.append("Files are scattered across multiple locations causing confusion")
        
        if 'javascript_analysis' in self.diagnosis_results:
            for file, analysis in self.diagnosis_results['javascript_analysis'].items():
                if analysis['mock_references'] > 0 and analysis['api_references'] == 0:
                    root_causes.append(f"JavaScript file {file} contains only mock data, no real API integration")
        
        if 'nginx_issues' in self.diagnosis_results:
            for issue in self.diagnosis_results['nginx_issues']:
                if 'caching' in issue:
                    root_causes.append("Nginx caching is preventing updated files from being served")
        
        if 'domain_issues' in self.diagnosis_results:
            for issue in self.diagnosis_results['domain_issues']:
                if 'DNS' in issue:
                    root_causes.append("DNS configuration prevents deployment to cherry-ai.me")
                elif 'SSH' in issue:
                    root_causes.append("SSH access misconfiguration blocks cherry-ai.me deployment")
        
        return root_causes
    
    def _generate_fixes(self) -> List[str]:
        """Generate specific fixes based on diagnosis"""
        fixes = []
        
        # File location fixes
        if not self.diagnosis_results.get('file_locations'):
            fixes.append("Deploy all orchestrator files to /opt/orchestra using rsync")
        
        # JavaScript fixes
        js_issues = self.diagnosis_results.get('javascript_analysis', {})
        for file, analysis in js_issues.items():
            if analysis['mock_references'] > 0:
                fixes.append(f"Replace {file} with enhanced version that uses real API calls")
        
        # Nginx fixes
        if 'nginx_issues' in self.diagnosis_results:
            fixes.append("Add 'expires -1' and 'add_header Cache-Control no-cache' to nginx config")
            fixes.append("Restart nginx with 'sudo systemctl restart nginx'")
        
        # Domain fixes
        if 'domain_issues' in self.diagnosis_results:
            fixes.append("Update DNS A record for cherry-ai.me to point to 150.136.94.139")
            fixes.append("Configure SSH access: 'ssh-copy-id ubuntu@cherry-ai.me'")
        
        # General fixes
        fixes.append("Clear browser cache and test with incognito/private mode")
        fixes.append("Use versioned URLs for JS files (e.g., script.js?v=2)")
        
        return fixes
    
    def run_diagnosis(self):
        """Run complete diagnosis"""
        logger.info("🏥 CHERRY AI ORCHESTRATOR DEPLOYMENT DIAGNOSIS")
        logger.info("=" * 60)
        logger.info(f"Started at: {datetime.now()}")
        
        # Run all diagnostic checks
        self.diagnose_file_locations()
        self.check_nginx_configuration()
        self.verify_javascript_files()
        self.check_html_javascript_references()
        self.test_domain_connectivity()
        self.check_browser_caching()
        self.check_api_connectivity()
        
        # Generate report
        report = self.generate_diagnosis_report()
        
        logger.info("\n✅ Diagnosis complete!")
        return report


def main():
    """Run the diagnosis"""
    diagnostics = CherryDeploymentDiagnostics()
    report = diagnostics.run_diagnosis()
    
    # Return non-zero exit code if issues found
    sys.exit(1 if diagnostics.issues_found else 0)


if __name__ == "__main__":
    main()