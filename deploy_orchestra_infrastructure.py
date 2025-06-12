#!/usr/bin/env python3
"""
Orchestra AI Infrastructure Deployment Script
Handles complete infrastructure setup with Pulumi Cloud
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

# ANSI color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_status(message: str, status: str = "INFO"):
    """Print colored status messages"""
    colors = {
        "INFO": BLUE,
        "SUCCESS": GREEN,
        "WARNING": YELLOW,
        "ERROR": RED
    }
    color = colors.get(status, BLUE)
    print(f"{color}[{status}]{RESET} {message}")

def run_command(cmd: List[str], cwd: str = None, capture_output: bool = True) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr"""
    try:
        if capture_output:
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, cwd=cwd)
            return result.returncode, "", ""
    except Exception as e:
        return 1, "", str(e)

def check_prerequisites():
    """Check if all required tools are installed"""
    print_status("Checking prerequisites...", "INFO")
    
    required_tools = {
        "pulumi": "Pulumi CLI",
        "python3": "Python 3",
        "npm": "Node.js/npm",
        "docker": "Docker"
    }
    
    missing = []
    for tool, name in required_tools.items():
        code, _, _ = run_command(["which", tool])
        if code != 0:
            missing.append(name)
        else:
            print_status(f"✓ {name} found", "SUCCESS")
    
    if missing:
        print_status(f"Missing tools: {', '.join(missing)}", "ERROR")
        print_status("Please install missing tools before continuing", "ERROR")
        return False
    
    return True

def setup_pulumi_secrets():
    """Set all API keys as Pulumi secrets"""
    print_status("Setting up Pulumi secrets...", "INFO")
    
    # Core secrets (these would be provided by the user)
    secrets = {
        "github_pat": os.getenv("GITHUB_PAT", ""),
        "pulumi_access_token": os.getenv("PULUMI_ACCESS_TOKEN", ""),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "notion_api_key": os.getenv("NOTION_API_KEY", ""),
        "vercel_api_token": os.getenv("VERCEL_API_TOKEN", ""),
        "pinecone_api_key": os.getenv("PINECONE_API_KEY", ""),
        "weaviate_api_key": os.getenv("WEAVIATE_API_KEY", ""),
        "slack_bot_token": os.getenv("SLACK_BOT_TOKEN", ""),
        "neo4j_password": os.getenv("NEO4J_PASSWORD", "neo4j_orchestra_secure_2024"),
    }
    
    # Additional secrets
    additional_secrets = {
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY", ""),
        "perplexity_api_key": os.getenv("PERPLEXITY_API_KEY", ""),
        "groq_api_key": os.getenv("GROQ_API_KEY", ""),
        "elevenlabs_api_key": os.getenv("ELEVENLABS_API_KEY", ""),
        "deepgram_api_key": os.getenv("DEEPGRAM_API_KEY", ""),
        "replicate_api_token": os.getenv("REPLICATE_API_TOKEN", ""),
        "huggingface_api_token": os.getenv("HUGGINGFACE_API_TOKEN", ""),
        "postgres_password": os.getenv("POSTGRES_PASSWORD", "orchestra_secure_2024"),
        "redis_password": os.getenv("REDIS_PASSWORD", "redis_orchestra_2024"),
    }
    
    # Set each secret
    set_count = 0
    for key, value in {**secrets, **additional_secrets}.items():
        if value:
            code, _, _ = run_command(["pulumi", "config", "set", "--secret", key, value])
            if code == 0:
                set_count += 1
                print_status(f"✓ Set secret: {key}", "SUCCESS")
            else:
                print_status(f"✗ Failed to set secret: {key}", "WARNING")
    
    print_status(f"Set {set_count} secrets in Pulumi", "SUCCESS")
    return set_count > 0

def deploy_infrastructure():
    """Deploy infrastructure using Pulumi"""
    print_status("Deploying infrastructure with Pulumi...", "INFO")
    
    # Run Pulumi up
    print_status("Running 'pulumi up --yes'...", "INFO")
    code, stdout, stderr = run_command(["pulumi", "up", "--yes"], capture_output=False)
    
    if code == 0:
        print_status("Infrastructure deployed successfully!", "SUCCESS")
        return True
    else:
        print_status("Infrastructure deployment failed", "ERROR")
        return False

def start_local_services():
    """Start local development services"""
    print_status("Starting local services...", "INFO")
    
    services = [
        {
            "name": "API Service",
            "cmd": ["python3", "main_app.py"],
            "port": 8010,
            "background": True
        },
        {
            "name": "Admin Interface",
            "cmd": ["npm", "run", "dev"],
            "cwd": "admin-interface",
            "port": 5174,
            "background": True
        },
        {
            "name": "MCP Unified Server",
            "cmd": ["python3", "mcp_unified_server.py"],
            "port": 3000,
            "background": True
        }
    ]
    
    for service in services:
        print_status(f"Starting {service['name']}...", "INFO")
        cwd = service.get("cwd", ".")
        
        if service.get("background"):
            # Start in background
            subprocess.Popen(service["cmd"], cwd=cwd)
            time.sleep(2)  # Give service time to start
            print_status(f"✓ {service['name']} started on port {service.get('port', 'N/A')}", "SUCCESS")
        else:
            run_command(service["cmd"], cwd=cwd, capture_output=False)

def verify_deployment():
    """Verify that all services are running correctly"""
    print_status("Verifying deployment...", "INFO")
    
    checks = [
        {
            "name": "API Health Check",
            "url": "http://localhost:8010/health",
            "expected": 200
        },
        {
            "name": "Admin Interface",
            "url": "http://localhost:5174",
            "expected": 200
        },
        {
            "name": "MCP Server",
            "url": "http://localhost:3000/health",
            "expected": 200
        }
    ]
    
    import requests
    
    all_passed = True
    for check in checks:
        try:
            response = requests.get(check["url"], timeout=5)
            if response.status_code == check["expected"]:
                print_status(f"✓ {check['name']} - OK", "SUCCESS")
            else:
                print_status(f"✗ {check['name']} - Status {response.status_code}", "ERROR")
                all_passed = False
        except Exception as e:
            print_status(f"✗ {check['name']} - {str(e)}", "ERROR")
            all_passed = False
    
    return all_passed

def main():
    """Main deployment function"""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Orchestra AI Infrastructure Deployment{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Check if we're in the right directory
    if not Path("Pulumi.yaml").exists():
        print_status("Pulumi.yaml not found. Are you in the orchestra-dev directory?", "ERROR")
        sys.exit(1)
    
    # Login to Pulumi (if not already logged in)
    print_status("Checking Pulumi login status...", "INFO")
    code, stdout, _ = run_command(["pulumi", "whoami"])
    if code != 0:
        print_status("Not logged into Pulumi. Please run 'pulumi login' first", "ERROR")
        sys.exit(1)
    else:
        print_status(f"✓ Logged in as: {stdout.strip()}", "SUCCESS")
    
    # Select stack
    print_status("Selecting 'dev' stack...", "INFO")
    run_command(["pulumi", "stack", "select", "dev"])
    
    # Setup Python virtual environment
    if not Path("venv").exists():
        print_status("Creating Python virtual environment...", "INFO")
        run_command(["python3", "-m", "venv", "venv"])
        run_command(["./venv/bin/pip", "install", "pulumi", "pulumi-aws", "pulumi-gcp", "requests"])
    
    # Set up secrets
    if not setup_pulumi_secrets():
        print_status("No secrets were set. Please set environment variables for API keys", "WARNING")
        print_status("Example: export OPENAI_API_KEY='your-key-here'", "INFO")
    
    # Deploy infrastructure
    print_status("\nReady to deploy infrastructure?", "INFO")
    response = input("Deploy now? (y/n): ")
    if response.lower() == 'y':
        if deploy_infrastructure():
            print_status("\n✅ Infrastructure deployment complete!", "SUCCESS")
            
            # Start local services
            print_status("\nStart local services?", "INFO")
            response = input("Start services? (y/n): ")
            if response.lower() == 'y':
                start_local_services()
                time.sleep(5)  # Give services time to fully start
                
                # Verify deployment
                if verify_deployment():
                    print_status("\n🎉 All services are running successfully!", "SUCCESS")
                    print_status("\nAccess points:", "INFO")
                    print(f"  • API: http://localhost:8010")
                    print(f"  • Admin Interface: http://localhost:5174")
                    print(f"  • MCP Server: http://localhost:3000")
                else:
                    print_status("\n⚠️  Some services failed verification", "WARNING")
        else:
            print_status("\n❌ Infrastructure deployment failed", "ERROR")
    else:
        print_status("Deployment cancelled", "INFO")
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    print_status("Deployment script complete", "INFO")

if __name__ == "__main__":
    main() 