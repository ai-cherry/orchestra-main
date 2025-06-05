import logging
logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""
Deploy Redis Resilience Solution
Orchestrates the deployment of resilient Redis infrastructure
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.table import Table

console = Console()

class RedisResilienceDeployer:
    """Orchestrates Redis resilience deployment."""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.deployment_steps = [
            ("Check prerequisites", self.check_prerequisites),
            ("Deploy Redis infrastructure", self.deploy_redis_infrastructure),
            ("Update MCP servers", self.update_mcp_servers),
            ("Configure monitoring", self.configure_monitoring),
            ("Run integration tests", self.run_integration_tests),
            ("Validate deployment", self.validate_deployment),
        ]
    
    async def check_prerequisites(self, progress, task) -> Dict[str, Any]:
        """Check system prerequisites."""
        results = {"status": "success", "checks": {}}
        
        # Check Docker
        progress.update(task, description="Checking Docker...")
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
            results["checks"]["docker"] = "✓ Installed"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            results["checks"]["docker"] = "✗ Not found"
            results["status"] = "failed"
        
        # Check Docker Compose
        progress.update(task, description="Checking Docker Compose...")
        try:
            subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
            results["checks"]["docker_compose"] = "✓ Installed"
        except:
            results["checks"]["docker_compose"] = "✗ Not found"
            results["status"] = "failed"
        
        # Check Python packages
        progress.update(task, description="Checking Python packages...")
        required_packages = ["redis", "asyncio", "click", "rich"]
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            results["checks"]["python_packages"] = f"✗ Missing: {', '.join(missing_packages)}"
            results["status"] = "warning"
        else:
            results["checks"]["python_packages"] = "✓ All installed"
        
        # Check core Redis module
        progress.update(task, description="Checking Redis resilience module...")
        if (self.project_root / "core" / "redis" / "__init__.py").exists():
            results["checks"]["redis_module"] = "✓ Found"
        else:
            results["checks"]["redis_module"] = "✗ Not found"
            results["status"] = "failed"
        
        return results
    
    async def deploy_redis_infrastructure(self, progress, task) -> Dict[str, Any]:
        """Deploy Redis infrastructure."""
        results = {"status": "success", "services": {}}
        
        # Check which deployment to use
        if (self.project_root / "docker-compose.redis-ha.yml").exists():
            progress.update(task, description="Deploying Redis HA cluster...")
            compose_file = "docker-compose.redis-ha.yml"
            deployment_type = "High Availability"
        else:
            progress.update(task, description="Deploying single Redis instance...")
            compose_file = "docker-compose.single-user.yml"
            deployment_type = "Single Instance"
        
        try:
            # Stop existing Redis
            subprocess.run(
                ["docker-compose", "-f", compose_file, "stop", "redis"],
                capture_output=True
            )
            
            # Start Redis with new configuration
            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "up", "-d", "redis"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                results["services"]["redis"] = f"✓ {deployment_type} deployed"
                
                # Wait for Redis to be ready
                progress.update(task, description="Waiting for Redis to be ready...")
                await asyncio.sleep(5)
                
                # Check Redis health
                health_check = subprocess.run(
                    ["docker-compose", "-f", compose_file, "exec", "-T", "redis", "redis-cli", "ping"],
                    capture_output=True,
                    text=True
                )
                
                if "PONG" in health_check.stdout:
                    results["services"]["redis_health"] = "✓ Healthy"
                else:
                    results["services"]["redis_health"] = "✗ Not responding"
                    results["status"] = "warning"
            else:
                results["services"]["redis"] = f"✗ Deployment failed: {result.stderr}"
                results["status"] = "failed"
                
        except Exception as e:
            results["services"]["redis"] = f"✗ Error: {str(e)}"
            results["status"] = "failed"
        
        return results
    
    async def update_mcp_servers(self, progress, task) -> Dict[str, Any]:
        """Update MCP servers to use resilient Redis."""
        results = {"status": "success", "updates": {}}
        
        progress.update(task, description="Running Redis integration script...")
        
        try:
            # Run the integration script
            result = subprocess.run(
                [sys.executable, "scripts/integrate_redis_resilience.py"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Parse output to count updated files
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if "Updated" in line and "files" in line:
                        results["updates"]["mcp_servers"] = line.strip()
                        break
                else:
                    results["updates"]["mcp_servers"] = "✓ Integration complete"
            else:
                results["updates"]["mcp_servers"] = f"✗ Failed: {result.stderr}"
                results["status"] = "failed"
                
        except Exception as e:
            results["updates"]["mcp_servers"] = f"✗ Error: {str(e)}"
            results["status"] = "failed"
        
        return results
    
    async def configure_monitoring(self, progress, task) -> Dict[str, Any]:
        """Configure Redis monitoring."""
        results = {"status": "success", "monitoring": {}}
        
        progress.update(task, description="Setting up monitoring alerts...")
        
        # Create monitoring configuration
        monitoring_config = {
            "alerts": {
                "redis_down": {
                    "condition": "status != 'healthy'",
                    "threshold": 2,
                    "action": "webhook"
                },
                "high_memory": {
                    "condition": "memory_usage > 80",
                    "threshold": 1,
                    "action": "webhook"
                },
                "slow_response": {
                    "condition": "response_time_ms > 100",
                    "threshold": 5,
                    "action": "log"
                }
            },
            "webhooks": {
                "default": os.getenv("ALERT_WEBHOOK_URL", "http://localhost:8000/alerts")
            }
        }
        
        # Save monitoring configuration
        config_path = self.project_root / "config" / "redis_monitoring.json"
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(monitoring_config, f, indent=2)
        
        results["monitoring"]["config"] = "✓ Created monitoring configuration"
        results["monitoring"]["alerts"] = f"✓ Configured {len(monitoring_config['alerts'])} alerts"
        
        return results
    
    async def run_integration_tests(self, progress, task) -> Dict[str, Any]:
        """Run integration tests."""
        results = {"status": "success", "tests": {}}
        
        # Test resilient client
        progress.update(task, description="Testing resilient Redis client...")
        try:
            result = subprocess.run(
                [sys.executable, "scripts/test_redis_resilience.py"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse test results
                test_count = 0
                for line in result.stdout.split('\n'):
                    if "✓" in line and "test" in line.lower():
                        test_count += 1
                
                results["tests"]["resilience"] = f"✓ {test_count} tests passed"
            else:
                results["tests"]["resilience"] = "✗ Tests failed"
                results["status"] = "warning"
                
        except subprocess.TimeoutExpired:
            results["tests"]["resilience"] = "✗ Tests timed out"
            results["status"] = "warning"
        except Exception as e:
            results["tests"]["resilience"] = f"✗ Error: {str(e)}"
            results["status"] = "warning"
        
        # Test monitoring
        progress.update(task, description="Testing monitoring tools...")
        try:
            result = subprocess.run(
                [sys.executable, "scripts/redis_health_monitor.py", "health"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "healthy" in result.stdout.lower():
                results["tests"]["monitoring"] = "✓ Health check passed"
            else:
                results["tests"]["monitoring"] = "✗ Health check failed"
                results["status"] = "warning"
                
        except Exception as e:
            results["tests"]["monitoring"] = f"✗ Error: {str(e)}"
            results["status"] = "warning"
        
        return results
    
    async def validate_deployment(self, progress, task) -> Dict[str, Any]:
        """Validate the complete deployment."""
        results = {"status": "success", "validation": {}}
        
        # Check MCP smart router
        progress.update(task, description="Validating MCP smart router...")
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8010/health", timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("redis", {}).get("status") == "healthy":
                            results["validation"]["smart_router"] = "✓ Healthy with Redis"
                        else:
                            results["validation"]["smart_router"] = "⚠️ Running with fallback"
                            results["status"] = "warning"
                    else:
                        results["validation"]["smart_router"] = "✗ Not responding"
                        results["status"] = "warning"
        except:
            results["validation"]["smart_router"] = "✗ Not accessible"
            results["status"] = "warning"
        
        # Check Redis persistence
        progress.update(task, description="Checking Redis persistence...")
        if (self.project_root / "redis_data").exists() or subprocess.run(
            ["docker", "volume", "ls", "-q", "-f", "name=redis_data"],
            capture_output=True,
            text=True
        ).stdout.strip():
            results["validation"]["persistence"] = "✓ Volume configured"
        else:
            results["validation"]["persistence"] = "⚠️ No persistence volume"
        
        return results
    
    async def deploy(self):
        """Run the complete deployment process."""
        console.print(Panel.fit(
            "[bold green]Redis Resilience Deployment[/bold green]\n"
            "Deploying resilient Redis infrastructure with monitoring and fallback",
            border_style="green"
        ))
        
        all_results = {}
        overall_status = "success"
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            
            main_task = progress.add_task("Deploying Redis resilience...", total=len(self.deployment_steps))
            
            for step_name, step_func in self.deployment_steps:
                step_task = progress.add_task(f"[cyan]{step_name}...", total=100)
                
                try:
                    results = await step_func(progress, step_task)
                    all_results[step_name] = results
                    
                    if results["status"] == "failed":
                        overall_status = "failed"
                        console.print(f"\n[red]✗ {step_name} failed![/red]")
                        break
                    elif results["status"] == "warning" and overall_status != "failed":
                        overall_status = "warning"
                    
                    progress.update(step_task, completed=100)
                    
                except Exception as e:
                    console.print(f"\n[red]✗ {step_name} error: {str(e)}[/red]")
                    overall_status = "failed"
                    break
                
                progress.update(main_task, advance=1)
        
        # Display results
        self.display_results(all_results, overall_status)
        
        return overall_status == "success"
    
    def display_results(self, results: Dict[str, Any], overall_status: str):
        """Display deployment results."""
        console.print("\n")
        
        # Create results table
        table = Table(title="Deployment Results", show_header=True)
        table.add_column("Step", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")
        
        for step_name, step_results in results.items():
            status_icon = "✓" if step_results["status"] == "success" else "⚠️" if step_results["status"] == "warning" else "✗"
            status_color = "green" if step_results["status"] == "success" else "yellow" if step_results["status"] == "warning" else "red"
            
            # Collect details
            details = []
            for category, items in step_results.items():
                if category != "status":
                    if isinstance(items, dict):
                        for key, value in items.items():
                            details.append(f"{key}: {value}")
                    else:
                        details.append(str(items))
            
            table.add_row(
                step_name,
                f"[{status_color}]{status_icon} {step_results['status']}[/{status_color}]",
                "\n".join(details[:3])  # Show first 3 details
            )
        
        console.print(table)
        
        # Summary panel
        if overall_status == "success":
            console.print(Panel.fit(
                "[bold green]✓ Redis resilience deployment completed successfully![/bold green]\n\n"
                "Next steps:\n"
                "• Monitor Redis health: python scripts/redis_health_monitor.py monitor\n"
                "• Check service status: docker-compose ps\n"
                "• View logs: docker-compose logs -f redis",
                border_style="green"
            ))
        elif overall_status == "warning":
            console.print(Panel.fit(
                "[bold yellow]⚠️ Deployment completed with warnings[/bold yellow]\n\n"
                "Some components may not be fully operational.\n"
                "Check the details above and address any issues.",
                border_style="yellow"
            ))
        else:
            console.print(Panel.fit(
                "[bold red]✗ Deployment failed![/bold red]\n\n"
                "Please check the errors above and try again.\n"
                "You may need to:\n"
                "• Check Docker is running\n"
                "• Ensure all dependencies are installed\n"
                "• Review error logs",
                border_style="red"
            ))

@click.command()
@click.option('--ha', is_flag=True, help='Deploy high-availability Redis cluster')
@click.option('--skip-tests', is_flag=True, help='Skip integration tests')
def deploy(ha, skip_tests):
    """Deploy Redis resilience solution"""
    deployer = RedisResilienceDeployer()
    
    if ha:
        console.print("[yellow]Note: HA deployment requires docker-compose.redis-ha.yml[/yellow]")
    
    if skip_tests:
        # Remove test step
        deployer.deployment_steps = [s for s in deployer.deployment_steps if "tests" not in s[0]]
    
    success = asyncio.run(deployer.deploy())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    # Add required imports
    import os
    import json
    
    deploy()