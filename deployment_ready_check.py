#!/usr/bin/env python3
"""
Final deployment readiness check and summary
"""

import os
import json
import subprocess
import sys
from datetime import datetime

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment configuration...")
    
    env_file_exists = os.path.exists('.env')
    env_example_exists = os.path.exists('.env.example')
    
    if not env_file_exists and env_example_exists:
        print("⚠️  .env file not found. Copy .env.example to .env and update values")
        print("   Run: cp .env.example .env")
        return False
    elif not env_file_exists:
        print("❌ No .env file found")
        return False
    else:
        print("✅ Environment file exists")
        return True

def check_dependencies():
    """Check if all dependencies are installed"""
    print("\n🔍 Checking dependencies...")
    
    try:
        import asyncpg
        import bs4
        import sentence_transformers
        import torch
        import transformers
        print("✅ All critical dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def check_services():
    """Check if required services are available"""
    print("\n🔍 Checking services...")
    
    services = {
        "PostgreSQL": "psql --version",
        "Redis": "redis-cli --version",
        "Docker": "docker --version"
    }
    
    all_good = True
    for service, cmd in services.items():
        try:
            subprocess.run(cmd.split(), capture_output=True, check=True)
            print(f"✅ {service} is available")
        except:
            print(f"⚠️  {service} not found or not running")
            all_good = False
            
    return all_good

def get_deployment_summary():
    """Get deployment summary from validation report"""
    if os.path.exists('deployment_validation_report.json'):
        with open('deployment_validation_report.json', 'r') as f:
            report = json.load(f)
            
        return {
            "total_checks": report['summary']['total_checks'],
            "passed": report['summary']['passed'],
            "issues": report['summary']['issues'],
            "critical_issues": report['summary']['critical_issues'],
            "warnings": report['summary']['warnings']
        }
    return None

def print_deployment_instructions():
    """Print deployment instructions"""
    print("\n" + "="*60)
    print("🚀 DEPLOYMENT INSTRUCTIONS")
    print("="*60)
    
    print("\n1️⃣  ENVIRONMENT SETUP:")
    print("   cp .env.example .env")
    print("   # Edit .env and add your actual API keys and database URLs")
    
    print("\n2️⃣  DATABASE SETUP:")
    print("   # Ensure PostgreSQL is running")
    print("   # Create database: createdb orchestra_db")
    print("   # Update DATABASE_URL in .env")
    
    print("\n3️⃣  REDIS SETUP:")
    print("   # Ensure Redis is running")
    print("   # Update REDIS_URL in .env")
    
    print("\n4️⃣  WEAVIATE SETUP:")
    print("   # For development:")
    print("   docker run -d --name weaviate \\")
    print("     -p 8080:8080 \\")
    print("     -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \\")
    print("     semitechnologies/weaviate:latest")
    
    print("\n5️⃣  DEPLOY TO STAGING:")
    print("   ./deploy_production.sh staging")
    
    print("\n6️⃣  VERIFY DEPLOYMENT:")
    print("   # Check health: curl http://localhost:8000/health")
    print("   # View metrics: curl http://localhost:8000/metrics")
    
    print("\n7️⃣  RUN TESTS:")
    print("   pytest tests/test_ai_orchestration_integration.py -v")
    
    print("\n8️⃣  PRODUCTION DEPLOYMENT:")
    print("   # After staging validation:")
    print("   ./deploy_production.sh production")

def main():
    print("🎯 AI ORCHESTRATION DEPLOYMENT READINESS CHECK")
    print("="*60)
    
    # Get validation summary
    summary = get_deployment_summary()
    if summary:
        print(f"\n📊 VALIDATION SUMMARY:")
        print(f"   Total Checks: {summary['total_checks']}")
        print(f"   ✅ Passed: {summary['passed']}")
        print(f"   ❌ Issues: {summary['issues']} ({summary['critical_issues']} critical)")
        print(f"   ⚠️  Warnings: {summary['warnings']}")
        
        readiness = (summary['passed'] / summary['total_checks']) * 100
        print(f"\n   🎯 Deployment Readiness: {readiness:.1f}%")
    
    # Run checks
    env_ok = check_environment()
    deps_ok = check_dependencies()
    services_ok = check_services()
    
    # Overall status
    print("\n" + "="*60)
    if env_ok and deps_ok and services_ok:
        print("✅ SYSTEM IS READY FOR DEPLOYMENT!")
        print_deployment_instructions()
    else:
        print("❌ SYSTEM NOT READY - Please fix the issues above")
        print("\nQuick fixes:")
        if not env_ok:
            print("  - Create .env file: cp .env.example .env")
        if not deps_ok:
            print("  - Install dependencies: pip install -r requirements_ai_orchestration.txt")
        if not services_ok:
            print("  - Ensure PostgreSQL, Redis, and Docker are installed and running")
    
    print("\n📄 For detailed report: cat remediation_report.json")
    print("📋 For validation details: cat deployment_validation_report.json")

if __name__ == "__main__":
    main()