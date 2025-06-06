#!/usr/bin/env python3
"""
Orchestra Debug Status Report
Comprehensive status check of all components and deployment readiness
"""

import os
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Any

def check_security_remediation_status():
    """Check if security remediation is complete"""
    print("🔒 Security Remediation Status:")
    print("-" * 40)
    
    # Check if process is still running
    result = subprocess.run("ps aux | grep critical_security_remediation | grep -v grep", 
                          shell=True, capture_output=True, text=True)
    
    if result.returncode == 0 and result.stdout:
        print("⏳ Security remediation is STILL RUNNING")
        print(f"   Process info: {result.stdout.strip()}")
        print("   This is taking longer than expected (25+ minutes)")
        print("   Consider stopping it and using the fixed deployment script instead")
    else:
        print("✅ Security remediation process completed or not running")
    
    # Check for output files
    if os.path.exists('.env.template'):
        print("✅ .env.template exists")
    else:
        print("❌ .env.template not found")
    
    # Check for security reports
    security_reports = [f for f in os.listdir('.') if f.startswith('security_remediation_report_')]
    if security_reports:
        latest = sorted(security_reports)[-1]
        print(f"✅ Security report found: {latest}")
    else:
        print("⚠️  No security remediation report found yet")
    
    print()

def check_deployment_readiness():
    """Check Lambda Labs deployment readiness"""
    print("🚀 Lambda Labs Deployment Readiness:")
    print("-" * 40)
    
    # Check for deployment scripts
    deployment_scripts = {
        'deploy_orchestra_lambda.py': 'Lambda deployment script (original)',
        'deploy_orchestra_lambda_fixed.py': 'Lambda deployment script (fixed)',
        'lambda_deployment_strategy.json': 'Deployment strategy',
        'orchestra_debug_report_*.json': 'Debug reports'
    }
    
    for script, description in deployment_scripts.items():
        if '*' in script:
            files = [f for f in os.listdir('.') if f.startswith(script.replace('*', ''))]
            if files:
                print(f"✅ {description}: {len(files)} found")
            else:
                print(f"❌ {description}: Not found")
        else:
            if os.path.exists(script):
                print(f"✅ {description}: Found")
            else:
                print(f"❌ {description}: Not found")
    
    print()

def check_critical_files():
    """Check for critical Orchestra files"""
    print("📁 Critical Files Status:")
    print("-" * 40)
    
    critical_files = {
        'architecture_blueprint.json': 'Architecture blueprint',
        'test_validation_framework.py': 'Test validation framework',
        'orchestra_implementation_validator.py': 'Implementation validator',
        'implementation_checklist.py': 'Implementation checklist',
        'orchestra_deployment_framework.py': 'Deployment framework (Lambda)',
        '.env.template': 'Environment template',
        'docker-compose.yml': 'Docker compose config',
        'Pulumi.yaml': 'Pulumi configuration'
    }
    
    for file, description in critical_files.items():
        if os.path.exists(file):
            print(f"✅ {description}: Found")
        else:
            print(f"❌ {description}: Missing")
    
    print()

def check_test_results():
    """Check latest test results"""
    print("🧪 Test Results:")
    print("-" * 40)
    
    # Check for test reports
    test_reports = [f for f in os.listdir('.') if f.startswith('test_validation_report_')]
    if test_reports:
        latest = sorted(test_reports)[-1]
        with open(latest, 'r') as f:
            report = json.load(f)
        
        summary = report['summary']
        print(f"Latest test report: {latest}")
        print(f"  Total tests: {summary['total_tests']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Pass rate: {summary['pass_rate']:.1%}")
        
        if report['failed_tests']:
            print("\nFailed tests:")
            for test in report['failed_tests']:
                print(f"  ❌ {test['test']}")
    else:
        print("❌ No test validation reports found")
    
    print()

def generate_action_plan():
    """Generate immediate action plan"""
    print("📋 IMMEDIATE ACTION PLAN:")
    print("=" * 60)
    
    print("1. STOP THE HANGING SECURITY REMEDIATION:")
    print("   kill -9 66244  # Kill the stuck process")
    print()
    
    print("2. USE THE FIXED LAMBDA DEPLOYMENT SCRIPT:")
    print("   python3 deploy_orchestra_lambda_fixed.py")
    print()
    
    print("3. DEPLOYMENT PREREQUISITES:")
    print("   - Ensure SSH access to 150.136.94.139")
    print("   - Run: ssh-copy-id ubuntu@150.136.94.139")
    print("   - Or export LAMBDA_SSH_PASSWORD=your_password")
    print()
    
    print("4. MANUAL SECURITY FIXES (if needed):")
    print("   - Create .env from .env.template")
    print("   - Update all hardcoded credentials manually")
    print("   - Use environment variables for all secrets")
    print()
    
    print("5. VERIFY DEPLOYMENT:")
    print("   - SSH to Lambda Labs: ssh ubuntu@150.136.94.139")
    print("   - Check services: systemctl status orchestra-api")
    print("   - Test API: curl http://150.136.94.139:8000/health")
    print()

def main():
    """Main execution"""
    print("🔍 ORCHESTRA DEBUG STATUS REPORT")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all checks
    check_security_remediation_status()
    check_deployment_readiness()
    check_critical_files()
    check_test_results()
    generate_action_plan()
    
    print("⚠️  CRITICAL FINDING:")
    print("-" * 40)
    print("The infrastructure was mistakenly configured for Lambda instead of Lambda Labs.")
    print("Use deploy_orchestra_lambda_fixed.py for correct Lambda Labs deployment.")
    print("Do NOT use the Lambda deployment scripts!")
    print()
    
    print("✅ Debug status report complete!")

if __name__ == "__main__":
    main()