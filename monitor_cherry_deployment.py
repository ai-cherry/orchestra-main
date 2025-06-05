#!/usr/bin/env python3
"""
Cherry AI Deployment Monitor
Real-time monitoring of deployment progress and health
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Tuple

class DeploymentMonitor:
    """Monitor Cherry AI deployment in real-time"""
    
    def __init__(self):
        self.lambda_ip = "150.136.94.139"
        self.cherry_domain = "cherry-ai.me"
        self.username = "ubuntu"
        self.metrics = {
            'start_time': datetime.now(),
            'checks_performed': 0,
            'issues_detected': [],
            'services_status': {},
            'api_health': 'unknown',
            'frontend_status': 'unknown'
        }
    
    def execute_ssh_command(self, command: str) -> Tuple[int, str, str]:
        """Execute SSH command silently"""
        ssh_cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {self.username}@{self.lambda_ip} '{command}'"
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    
    def check_api_health(self) -> str:
        """Check API health status"""
        exit_code, stdout, _ = self.execute_ssh_command(
            "curl -s http://localhost:8000/api/health | jq -r '.status' 2>/dev/null || echo 'offline'"
        )
        return stdout.strip() if exit_code == 0 else 'offline'
    
    def check_frontend_status(self) -> Dict[str, Any]:
        """Check frontend deployment status"""
        status = {'deployed': False, 'using_enhanced_js': False, 'cache_disabled': False}
        
        # Check if orchestrator HTML exists
        exit_code, stdout, _ = self.execute_ssh_command(
            "test -f /opt/orchestra/cherry-ai-orchestrator-final.html && echo 'exists'"
        )
        status['deployed'] = 'exists' in stdout
        
        # Check if using enhanced JS
        if status['deployed']:
            exit_code, stdout, _ = self.execute_ssh_command(
                "grep -q 'cherry-ai-orchestrator-enhanced.js' /opt/orchestra/cherry-ai-orchestrator-final.html && echo 'yes'"
            )
            status['using_enhanced_js'] = 'yes' in stdout
        
        # Check nginx cache settings
        exit_code, stdout, _ = self.execute_ssh_command(
            "grep -q 'no-cache' /etc/nginx/sites-enabled/* && echo 'disabled'"
        )
        status['cache_disabled'] = 'disabled' in stdout
        
        return status
    
    def check_services(self) -> Dict[str, bool]:
        """Check all required services"""
        services = {
            'nginx': "systemctl is-active nginx",
            'postgresql': "systemctl is-active postgresql",
            'redis': "redis-cli ping 2>/dev/null | grep -q PONG",
            'weaviate': "curl -s http://localhost:8080/v1/.well-known/ready | grep -q '\"status\":\"ok\"'",
            'orchestra-api': "systemctl is-active orchestra-api"
        }
        
        status = {}
        for service, check_cmd in services.items():
            exit_code, _, _ = self.execute_ssh_command(check_cmd)
            status[service] = exit_code == 0
        
        return status
    
    def check_dns_status(self) -> Dict[str, Any]:
        """Check DNS configuration"""
        dns_result = subprocess.run(
            f"nslookup {self.cherry_domain} | grep -A2 'answer:' | grep 'Address'",
            shell=True,
            capture_output=True,
            text=True
        )
        
        return {
            'resolves': dns_result.returncode == 0,
            'points_to_lambda': self.lambda_ip in dns_result.stdout,
            'output': dns_result.stdout.strip()
        }
    
    def display_status(self):
        """Display current deployment status"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🍒 CHERRY AI DEPLOYMENT MONITOR")
        print("=" * 60)
        print(f"Started: {self.metrics['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Runtime: {datetime.now() - self.metrics['start_time']}")
        print(f"Checks: {self.metrics['checks_performed']}")
        print()
        
        # API Health
        api_status = self.metrics['api_health']
        api_icon = "🟢" if api_status == "healthy" else "🔴"
        print(f"API Health: {api_icon} {api_status}")
        
        # Frontend Status
        frontend = self.metrics.get('frontend_status', {})
        if isinstance(frontend, dict):
            print(f"\nFrontend Status:")
            print(f"  Deployed: {'✅' if frontend.get('deployed') else '❌'}")
            print(f"  Enhanced JS: {'✅' if frontend.get('using_enhanced_js') else '❌'}")
            print(f"  Cache Disabled: {'✅' if frontend.get('cache_disabled') else '❌'}")
        
        # Services
        print(f"\nServices:")
        for service, running in self.metrics.get('services_status', {}).items():
            icon = "🟢" if running else "🔴"
            print(f"  {service}: {icon}")
        
        # DNS Status
        dns = self.metrics.get('dns_status', {})
        if dns:
            print(f"\nDNS Status:")
            print(f"  Resolves: {'✅' if dns.get('resolves') else '❌'}")
            print(f"  Points to Lambda: {'✅' if dns.get('points_to_lambda') else '❌'}")
        
        # Issues
        if self.metrics['issues_detected']:
            print(f"\n⚠️  Issues Detected:")
            for issue in self.metrics['issues_detected'][-5:]:  # Show last 5 issues
                print(f"  - {issue}")
        
        print("\n" + "=" * 60)
        print("Press Ctrl+C to exit")
    
    def detect_issues(self):
        """Detect and log issues"""
        issues = []
        
        # Check API
        if self.metrics['api_health'] != 'healthy':
            issues.append(f"API is {self.metrics['api_health']}")
        
        # Check frontend
        frontend = self.metrics.get('frontend_status', {})
        if isinstance(frontend, dict):
            if not frontend.get('deployed'):
                issues.append("Frontend not deployed to /opt/orchestra")
            elif not frontend.get('using_enhanced_js'):
                issues.append("Frontend using old mock JS, not enhanced version")
            if not frontend.get('cache_disabled'):
                issues.append("Nginx caching not disabled - may serve stale content")
        
        # Check services
        for service, running in self.metrics.get('services_status', {}).items():
            if not running:
                issues.append(f"{service} service is down")
        
        # Check DNS
        dns = self.metrics.get('dns_status', {})
        if dns and not dns.get('points_to_lambda'):
            issues.append(f"DNS not pointing to Lambda server {self.lambda_ip}")
        
        # Update metrics
        for issue in issues:
            if issue not in self.metrics['issues_detected']:
                self.metrics['issues_detected'].append(f"{datetime.now().strftime('%H:%M:%S')} - {issue}")
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        self.metrics['checks_performed'] += 1
        
        # Perform all checks
        self.metrics['api_health'] = self.check_api_health()
        self.metrics['frontend_status'] = self.check_frontend_status()
        self.metrics['services_status'] = self.check_services()
        self.metrics['dns_status'] = self.check_dns_status()
        
        # Detect issues
        self.detect_issues()
        
        # Display status
        self.display_status()
    
    def monitor(self, interval: int = 5):
        """Start continuous monitoring"""
        print("Starting deployment monitoring...")
        print(f"Checking every {interval} seconds")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.run_monitoring_cycle()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")
            self.save_report()
    
    def save_report(self):
        """Save monitoring report"""
        report = {
            'monitoring_session': {
                'start_time': self.metrics['start_time'].isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration': str(datetime.now() - self.metrics['start_time']),
                'checks_performed': self.metrics['checks_performed']
            },
            'final_status': {
                'api_health': self.metrics['api_health'],
                'frontend_status': self.metrics.get('frontend_status', {}),
                'services_status': self.metrics.get('services_status', {}),
                'dns_status': self.metrics.get('dns_status', {})
            },
            'issues_timeline': self.metrics['issues_detected']
        }
        
        filename = f"deployment_monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReport saved to: {filename}")


def main():
    """Run the deployment monitor"""
    monitor = DeploymentMonitor()
    
    # Check if we can connect
    print("Testing connection to Lambda server...")
    exit_code, _, _ = monitor.execute_ssh_command("echo 'Connected'")
    
    if exit_code != 0:
        print("❌ Cannot connect to Lambda server")
        print("Please ensure SSH access is configured")
        sys.exit(1)
    
    print("✅ Connected to Lambda server")
    print()
    
    # Start monitoring
    monitor.monitor(interval=5)


if __name__ == "__main__":
    main()