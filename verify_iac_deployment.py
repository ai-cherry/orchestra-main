#!/usr/bin/env python3
"""
Orchestra AI Infrastructure as Code Deployment Verification
Uses Pulumi to verify and manage infrastructure deployment status
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class InfrastructureVerifier:
    """Comprehensive IaC deployment verification using Pulumi"""
    
    def __init__(self):
        self.console = console
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "infrastructure": {},
            "services": {},
            "deployments": {},
            "health_checks": {}
        }
    
    def verify_pulumi_status(self) -> Dict:
        """Verify Pulumi stack and resource status"""
        self.console.print("[bold blue]🏗️ Checking Pulumi Infrastructure Status...[/bold blue]")
        
        try:
            # Check Pulumi stack
            stack_output = subprocess.run(
                ["pulumi", "stack", "--json"],
                capture_output=True,
                text=True
            )
            
            if stack_output.returncode == 0:
                stack_info = json.loads(stack_output.stdout)
                
                # Get stack outputs
                outputs_cmd = subprocess.run(
                    ["pulumi", "stack", "output", "--json"],
                    capture_output=True,
                    text=True
                )
                
                outputs = {}
                if outputs_cmd.returncode == 0:
                    outputs = json.loads(outputs_cmd.stdout)
                
                return {
                    "status": "configured",
                    "stack_name": stack_info.get("name", "unknown"),
                    "last_update": stack_info.get("lastUpdate", "never"),
                    "resource_count": stack_info.get("resourceCount", 0),
                    "outputs": outputs,
                    "infrastructure_ready": outputs.get("infrastructure_status", {}).get("ready_for_deployment", False)
                }
            else:
                return {
                    "status": "error",
                    "error": "Failed to get Pulumi stack info"
                }
                
        except Exception as e:
            return {
                "status": "not_configured",
                "error": str(e)
            }
    
    def verify_vercel_deployments(self) -> Dict:
        """Verify Vercel frontend deployments"""
        self.console.print("[bold green]🌐 Checking Vercel Deployments...[/bold green]")
        
        vercel_status = {
            "admin_interface": {},
            "dashboard": {}
        }
        
        # Check admin interface
        try:
            # Check local Vercel project
            if subprocess.run(["which", "vercel"], capture_output=True).returncode == 0:
                # Get deployment list
                vercel_list = subprocess.run(
                    ["vercel", "ls", "--json"],
                    cwd="admin-interface",
                    capture_output=True,
                    text=True
                )
                
                if vercel_list.returncode == 0:
                    deployments = json.loads(vercel_list.stdout)
                    if deployments:
                        latest = deployments[0] if isinstance(deployments, list) else deployments
                        vercel_status["admin_interface"] = {
                            "status": "deployed",
                            "url": latest.get("url", "unknown"),
                            "created": latest.get("created", "unknown"),
                            "state": latest.get("state", "unknown")
                        }
                    else:
                        vercel_status["admin_interface"] = {
                            "status": "no_deployments",
                            "message": "Project linked but no deployments found"
                        }
                else:
                    vercel_status["admin_interface"] = {
                        "status": "not_linked",
                        "message": "Vercel project not linked"
                    }
        except Exception as e:
            vercel_status["admin_interface"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check production URLs
        production_urls = [
            ("orchestra-admin-interface.vercel.app", "Primary Frontend"),
            ("ai-cherry.vercel.app", "Secondary Frontend")
        ]
        
        for url, name in production_urls:
            try:
                response = requests.get(f"https://{url}", timeout=5)
                vercel_status[url] = {
                    "name": name,
                    "status": "live" if response.status_code in [200, 401] else "not_deployed",
                    "http_code": response.status_code
                }
            except Exception as e:
                vercel_status[url] = {
                    "name": name,
                    "status": "error",
                    "error": str(e)
                }
        
        return vercel_status
    
    def verify_docker_services(self) -> Dict:
        """Verify Docker service deployments"""
        self.console.print("[bold cyan]🐳 Checking Docker Services...[/bold cyan]")
        
        docker_status = {}
        
        try:
            # Check if Docker is running
            docker_check = subprocess.run(
                ["docker", "ps", "--format", "json"],
                capture_output=True,
                text=True
            )
            
            if docker_check.returncode == 0:
                containers = docker_check.stdout.strip().split('\n')
                for container_json in containers:
                    if container_json:
                        container = json.loads(container_json)
                        if 'orchestra' in container.get('Names', '').lower() or \
                           'cherry' in container.get('Names', '').lower():
                            docker_status[container['Names']] = {
                                "status": container.get('Status', 'unknown'),
                                "ports": container.get('Ports', 'none'),
                                "state": "running" if "Up" in container.get('Status', '') else "stopped"
                            }
            else:
                docker_status["docker"] = {
                    "status": "error",
                    "message": "Docker daemon not accessible"
                }
                
        except Exception as e:
            docker_status["docker"] = {
                "status": "error",
                "error": str(e)
            }
        
        return docker_status
    
    def verify_api_endpoints(self) -> Dict:
        """Verify API endpoint health"""
        self.console.print("[bold magenta]🔌 Checking API Endpoints...[/bold magenta]")
        
        endpoints = [
            ("http://localhost:8000/health", "Local API Port 8000"),
            ("http://localhost:8010/docs", "Local API Port 8010"),
            ("http://192.9.142.8:8000/health", "Remote Lambda Labs API"),
            ("http://192.9.142.8/health", "Remote Zapier MCP Server")
        ]
        
        api_status = {}
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(endpoint, timeout=3)
                api_status[endpoint] = {
                    "name": name,
                    "status": "healthy" if response.status_code in [200, 401] else "unhealthy",
                    "http_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                }
            except requests.exceptions.RequestException as e:
                api_status[endpoint] = {
                    "name": name,
                    "status": "unreachable",
                    "error": str(e)
                }
        
        return api_status
    
    def generate_deployment_plan(self) -> List[Dict]:
        """Generate deployment plan based on current status"""
        plan = []
        
        # Check Pulumi infrastructure
        if self.results["infrastructure"].get("status") == "configured":
            if self.results["infrastructure"].get("resource_count", 0) == 0:
                plan.append({
                    "action": "Deploy Pulumi Infrastructure",
                    "command": "pulumi up --yes",
                    "priority": "high",
                    "reason": "No resources deployed in Pulumi stack"
                })
        
        # Check Vercel deployments
        vercel = self.results["deployments"]
        if vercel.get("admin_interface", {}).get("status") == "no_deployments":
            plan.append({
                "action": "Deploy Admin Interface to Vercel",
                "command": "cd admin-interface && vercel --prod --yes",
                "priority": "high",
                "reason": "Admin interface not deployed to Vercel"
            })
        
        # Check Docker services
        docker_running = any(
            "running" in str(service.get("state", ""))
            for service in self.results["services"].values()
        )
        
        if not docker_running:
            plan.append({
                "action": "Start Docker Services",
                "command": "./deploy_production_complete.sh",
                "priority": "medium",
                "reason": "Docker services not running"
            })
        
        # Check API health
        api_healthy = any(
            endpoint.get("status") == "healthy"
            for endpoint in self.results["health_checks"].values()
        )
        
        if not api_healthy:
            plan.append({
                "action": "Restart API Services",
                "command": "docker-compose -f docker-compose.production.yml restart",
                "priority": "medium",
                "reason": "No healthy API endpoints found"
            })
        
        return plan
    
    def display_results(self):
        """Display comprehensive verification results"""
        # Infrastructure Status
        infra_table = Table(title="🏗️ Infrastructure Status (Pulumi)")
        infra_table.add_column("Property", style="cyan")
        infra_table.add_column("Value", style="green")
        
        infra = self.results["infrastructure"]
        infra_table.add_row("Status", infra.get("status", "unknown"))
        infra_table.add_row("Stack Name", str(infra.get("stack_name", "N/A")))
        infra_table.add_row("Resources", str(infra.get("resource_count", 0)))
        infra_table.add_row("Ready for Deployment", 
                           "✅ Yes" if infra.get("infrastructure_ready") else "❌ No")
        
        self.console.print(infra_table)
        
        # Vercel Deployments
        vercel_table = Table(title="🌐 Vercel Deployments")
        vercel_table.add_column("Deployment", style="cyan")
        vercel_table.add_column("Status", style="green")
        vercel_table.add_column("URL/Details", style="blue")
        
        for key, value in self.results["deployments"].items():
            if isinstance(value, dict) and "status" in value:
                status_emoji = "✅" if value.get("status") in ["deployed", "live"] else "❌"
                vercel_table.add_row(
                    value.get("name", key),
                    f"{status_emoji} {value.get('status', 'unknown')}",
                    value.get("url", value.get("message", "N/A"))
                )
        
        self.console.print(vercel_table)
        
        # Docker Services
        if self.results["services"]:
            docker_table = Table(title="🐳 Docker Services")
            docker_table.add_column("Service", style="cyan")
            docker_table.add_column("Status", style="green")
            docker_table.add_column("Ports", style="yellow")
            
            for name, service in self.results["services"].items():
                if "docker" not in name:  # Skip docker daemon status
                    docker_table.add_row(
                        name,
                        service.get("status", "unknown"),
                        service.get("ports", "none")
                    )
            
            self.console.print(docker_table)
        
        # API Health
        api_table = Table(title="🔌 API Endpoints")
        api_table.add_column("Endpoint", style="cyan")
        api_table.add_column("Status", style="green")
        api_table.add_column("Response", style="yellow")
        
        for endpoint, health in self.results["health_checks"].items():
            status_emoji = "✅" if health.get("status") == "healthy" else "❌"
            response = f"HTTP {health.get('http_code', 'N/A')}" if "http_code" in health else health.get("error", "Error")
            api_table.add_row(
                health.get("name", endpoint),
                f"{status_emoji} {health.get('status', 'unknown')}",
                response
            )
        
        self.console.print(api_table)
        
        # Deployment Plan
        plan = self.generate_deployment_plan()
        if plan:
            plan_table = Table(title="🎯 Recommended Deployment Actions")
            plan_table.add_column("Priority", style="red")
            plan_table.add_column("Action", style="cyan")
            plan_table.add_column("Command", style="green")
            plan_table.add_column("Reason", style="yellow")
            
            for action in sorted(plan, key=lambda x: x["priority"]):
                plan_table.add_row(
                    action["priority"].upper(),
                    action["action"],
                    action["command"],
                    action["reason"]
                )
            
            self.console.print(plan_table)
        else:
            self.console.print(Panel("✅ All systems deployed and operational!", 
                                   title="Status", style="bold green"))
    
    def run_verification(self):
        """Run complete infrastructure verification"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            # Verify Pulumi
            task = progress.add_task("[cyan]Verifying Pulumi infrastructure...", total=1)
            self.results["infrastructure"] = self.verify_pulumi_status()
            progress.update(task, advance=1)
            
            # Verify Vercel
            task = progress.add_task("[green]Checking Vercel deployments...", total=1)
            self.results["deployments"] = self.verify_vercel_deployments()
            progress.update(task, advance=1)
            
            # Verify Docker
            task = progress.add_task("[blue]Checking Docker services...", total=1)
            self.results["services"] = self.verify_docker_services()
            progress.update(task, advance=1)
            
            # Verify APIs
            task = progress.add_task("[magenta]Testing API endpoints...", total=1)
            self.results["health_checks"] = self.verify_api_endpoints()
            progress.update(task, advance=1)
        
        # Display results
        self.console.print("\n[bold]🚀 Orchestra AI Infrastructure Verification Report[/bold]\n")
        self.display_results()
        
        # Save results
        with open("deployment_verification_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        self.console.print(f"\n[dim]Results saved to deployment_verification_results.json[/dim]")

def main():
    """Main entry point"""
    verifier = InfrastructureVerifier()
    verifier.run_verification()

if __name__ == "__main__":
    main() 