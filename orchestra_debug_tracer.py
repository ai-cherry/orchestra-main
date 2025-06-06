#!/usr/bin/env python3
"""
Orchestra Debug Tracer - Infrastructure Alignment Analysis
Documents the infrastructure mismatch and provides corrected deployment strategy
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any

class OrchestraDebugTracer:
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.findings = []
        self.corrections = []
        
    def trace_infrastructure_mismatch(self):
        """Document the infrastructure mismatch between Lambda and Lambda Labs"""
        
        print("🔍 ORCHESTRA INFRASTRUCTURE DEBUG TRACE")
        print("=" * 60)
        print(f"Timestamp: {self.timestamp}")
        print()
        
        # Finding 1: Infrastructure Provider Mismatch
        finding1 = {
            "issue": "Infrastructure Provider Mismatch",
            "severity": "CRITICAL",
            "details": {
                "expected": "Lambda Labs (as per user requirement)",
                "found": "Lambda (in deployment scripts)",
                "affected_files": [
                    "deploy_orchestrator_infrastructure.py",
                    "deploy-cherry-orchestrator.sh",
                    "infrastructure/Lambda_deployment.py",
                    "infrastructure/Lambda_manager.py"
                ]
            },
            "root_cause": "Implementation mode created Lambda-specific deployment instead of Lambda Labs"
        }
        self.findings.append(finding1)
        
        # Finding 2: Existing Lambda Infrastructure
        finding2 = {
            "issue": "Lambda Labs Infrastructure Already Exists",
            "severity": "INFO",
            "details": {
                "existing_files": [
                    "lambda_infrastructure_mcp_server.py",
                    "main.py (references Lambda Labs)",
                    "fixed_main_app.py (references Lambda Labs)"
                ],
                "production_ip": "150.136.94.139",
                "server_specs": "8x A100 GPUs, 124 vCPUs, 1.8TB RAM"
            },
            "root_cause": "Project already has Lambda Labs integration"
        }
        self.findings.append(finding2)
        
        # Finding 3: Deployment Strategy Conflict
        finding3 = {
            "issue": "Deployment Strategy Conflict",
            "severity": "HIGH",
            "details": {
                "cherry_ai_orchestrator": "Frontend-only deployment (HTML/JS)",
                "orchestra_platform": "Full-stack deployment with backend services",
                "deployment_method": "Blue-green deployment configured for traditional VPS, not Lambda Labs"
            },
            "root_cause": "Mixed deployment strategies between frontend app and full platform"
        }
        self.findings.append(finding3)
        
        # Print findings
        print("📋 FINDINGS:")
        print("-" * 40)
        for i, finding in enumerate(self.findings, 1):
            print(f"\n{i}. {finding['issue']} [{finding['severity']}]")
            print(f"   Root Cause: {finding['root_cause']}")
            if 'affected_files' in finding['details']:
                print(f"   Affected Files:")
                for f in finding['details']['affected_files']:
                    print(f"     - {f}")
        
        return self.findings
    
    def generate_corrections(self):
        """Generate corrections for Lambda Labs deployment"""
        
        print("\n\n🔧 CORRECTIONS NEEDED:")
        print("-" * 40)
        
        # Correction 1: Lambda Labs Deployment Script
        correction1 = {
            "action": "Create Lambda Labs deployment script",
            "description": "Replace Lambda deployment with Lambda Labs-specific deployment",
            "new_file": "deploy_orchestra_lambda.py",
            "changes": [
                "Use Lambda Labs API instead of Lambda",
                "Deploy to existing production instance (150.136.94.139)",
                "Integrate with existing services (PostgreSQL, Redis, Weaviate)",
                "Use SSH deployment instead of cloud provisioning"
            ]
        }
        self.corrections.append(correction1)
        
        # Correction 2: Update Infrastructure Configuration
        correction2 = {
            "action": "Update infrastructure configuration",
            "description": "Align all infrastructure code with Lambda Labs",
            "files_to_update": [
                ".env.template (add LAMBDA_LABS_API_KEY)",
                "Pulumi.yaml (change provider to custom Lambda Labs)",
                "Remove Lambda-specific configurations"
            ]
        }
        self.corrections.append(correction2)
        
        # Correction 3: Integrate with Existing Services
        correction3 = {
            "action": "Integrate with existing Lambda Labs services",
            "description": "Connect to already running services on Lambda Labs",
            "services": [
                "PostgreSQL (already running)",
                "Redis (already running)",
                "Weaviate (Docker container)",
                "Nginx (reverse proxy)",
                "Cherry AI API (port 8000)"
            ]
        }
        self.corrections.append(correction3)
        
        # Print corrections
        for i, correction in enumerate(self.corrections, 1):
            print(f"\n{i}. {correction['action']}")
            print(f"   Description: {correction['description']}")
            if 'changes' in correction:
                print("   Changes:")
                for change in correction['changes']:
                    print(f"     - {change}")
        
        return self.corrections
    
    def create_lambda_deployment_strategy(self):
        """Create correct deployment strategy for Lambda Labs"""
        
        print("\n\n🚀 LAMBDA LABS DEPLOYMENT STRATEGY:")
        print("-" * 40)
        
        strategy = {
            "deployment_type": "SSH-based deployment to existing Lambda Labs instance",
            "target_server": {
                "ip": "150.136.94.139",
                "provider": "Lambda Labs",
                "specs": "8x A100 GPU instance",
                "os": "Ubuntu 22.04 LTS"
            },
            "deployment_steps": [
                {
                    "step": 1,
                    "action": "SSH Key Setup",
                    "command": "ssh-copy-id ubuntu@150.136.94.139"
                },
                {
                    "step": 2,
                    "action": "Deploy Application Code",
                    "method": "Git pull or rsync",
                    "target_dir": "/opt/orchestra"
                },
                {
                    "step": 3,
                    "action": "Configure Services",
                    "services": ["nginx", "systemd services", "SSL certificates"]
                },
                {
                    "step": 4,
                    "action": "Database Migrations",
                    "command": "python manage.py migrate"
                },
                {
                    "step": 5,
                    "action": "Restart Services",
                    "command": "systemctl restart orchestra-*"
                }
            ],
            "existing_services": {
                "postgresql": "localhost:5432",
                "redis": "localhost:6379",
                "weaviate": "localhost:8080",
                "api": "localhost:8000"
            }
        }
        
        print("\nDeployment Type:", strategy["deployment_type"])
        print(f"\nTarget Server: {strategy['target_server']['ip']} ({strategy['target_server']['provider']})")
        print("\nDeployment Steps:")
        for step in strategy["deployment_steps"]:
            print(f"  {step['step']}. {step['action']}")
            if 'command' in step:
                print(f"     Command: {step['command']}")
        
        print("\nExisting Services to Connect:")
        for service, endpoint in strategy["existing_services"].items():
            print(f"  - {service}: {endpoint}")
        
        # Save strategy to file
        with open("lambda_deployment_strategy.json", "w") as f:
            json.dump(strategy, f, indent=2)
        
        return strategy
    
    def generate_debug_report(self):
        """Generate comprehensive debug report"""
        
        report = {
            "timestamp": self.timestamp,
            "debug_type": "Infrastructure Alignment",
            "findings": self.findings,
            "corrections": self.corrections,
            "recommendation": "Use Lambda Labs deployment instead of Lambda",
            "next_steps": [
                "Create deploy_orchestra_lambda.py script",
                "Update all infrastructure references to Lambda Labs",
                "Test deployment on existing Lambda Labs instance",
                "Remove Lambda-specific code"
            ]
        }
        
        # Save report
        report_file = f"orchestra_debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n\n📄 Debug report saved to: {report_file}")
        
        return report

def main():
    """Run the debug trace"""
    tracer = OrchestraDebugTracer()
    
    # Run analysis
    tracer.trace_infrastructure_mismatch()
    tracer.generate_corrections()
    tracer.create_lambda_deployment_strategy()
    report = tracer.generate_debug_report()
    
    print("\n\n✅ DEBUG TRACE COMPLETE")
    print("=" * 60)
    print("\n🎯 IMMEDIATE ACTIONS:")
    print("1. Switch to Lambda Labs deployment strategy")
    print("2. Use existing Lambda Labs infrastructure")
    print("3. Deploy via SSH to 150.136.94.139")
    print("4. Connect to existing services (PostgreSQL, Redis, Weaviate)")
    print("\n⚠️  DO NOT create new cloud instances - use existing Lambda Labs server!")

if __name__ == "__main__":
    main()
