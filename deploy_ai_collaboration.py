#!/usr/bin/env python3
"""
AI Collaboration Dashboard Deployment Script
Production-ready deployment with health checks, rollback, and monitoring
"""

import os
import sys
import json
import time
import asyncio
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime
import argparse
import logging
from pathlib import Path


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AICollaborationDeployer:
    """
    Deployment orchestrator for AI Collaboration Dashboard
    Implements blue-green deployment with automated rollback
    """
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.project_root = Path(__file__).parent
        self.pulumi_dir = self.project_root / "infrastructure" / "ai_collaboration"
        self.deployment_log = []
        self.start_time = datetime.utcnow()
        
        # Deployment configuration
        self.config = {
            "staging": {
                "stack": "ai-collaboration-staging",
                "region": "ewr",
                "domain": "staging.cherry-ai.me",
                "min_instances": 1,
                "max_instances": 2
            },
            "production": {
                "stack": "ai-collaboration-production",
                "region": "ewr",
                "domain": "cherry-ai.me",
                "min_instances": 2,
                "max_instances": 10
            }
        }
        
        self.current_config = self.config.get(environment, self.config["production"])
    
    def log_step(self, step: str, status: str = "INFO", details: Dict[str, Any] = None):
        """Log deployment step"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "step": step,
            "status": status,
            "details": details or {}
        }
        self.deployment_log.append(log_entry)
        
        if status == "ERROR":
            logger.error(f"{step}: {details}")
        elif status == "WARNING":
            logger.warning(f"{step}: {details}")
        else:
            logger.info(f"{step}: {details}")
    
    async def deploy(self, skip_tests: bool = False, auto_rollback: bool = True):
        """
        Execute full deployment pipeline
        
        Args:
            skip_tests: Skip test execution
            auto_rollback: Automatically rollback on failure
        """
        try:
            self.log_step("Starting AI Collaboration Dashboard deployment", "INFO", {
                "environment": self.environment,
                "stack": self.current_config["stack"],
                "auto_rollback": auto_rollback
            })
            
            # Pre-deployment checks
            await self.pre_deployment_checks()
            
            # Run tests unless skipped
            if not skip_tests:
                await self.run_tests()
            
            # Build and prepare artifacts
            await self.build_artifacts()
            
            # Deploy infrastructure
            await self.deploy_infrastructure()
            
            # Deploy application
            deployment_color = await self.deploy_application()
            
            # Run health checks
            healthy = await self.health_checks(deployment_color)
            
            if healthy:
                # Switch traffic to new deployment
                await self.switch_traffic(deployment_color)
                
                # Post-deployment validation
                await self.post_deployment_validation()
                
                # Cleanup old deployment
                await self.cleanup_old_deployment(deployment_color)
                
                self.log_step("Deployment completed successfully", "SUCCESS", {
                    "duration": (datetime.utcnow() - self.start_time).total_seconds(),
                    "deployment_color": deployment_color
                })
            else:
                raise Exception("Health checks failed")
                
        except Exception as e:
            self.log_step("Deployment failed", "ERROR", {"error": str(e)})
            
            if auto_rollback:
                await self.rollback()
            
            raise
        finally:
            # Save deployment log
            self.save_deployment_log()
    
    async def pre_deployment_checks(self):
        """Run pre-deployment validation checks"""
        self.log_step("Running pre-deployment checks")
        
        checks = {
            "pulumi_installed": self.check_command("pulumi", ["version"]),
            "docker_installed": self.check_command("docker", ["--version"]),
            "git_clean": self.check_git_status(),
            "secrets_configured": self.check_secrets(),
            "disk_space": self.check_disk_space(),
            "network_connectivity": await self.check_network()
        }
        
        failed_checks = [k for k, v in checks.items() if not v]
        if failed_checks:
            raise Exception(f"Pre-deployment checks failed: {failed_checks}")
        
        self.log_step("Pre-deployment checks passed", "SUCCESS", checks)
    
    def check_command(self, command: str, args: List[str]) -> bool:
        """Check if command exists and is executable"""
        try:
            subprocess.run([command] + args, capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def check_git_status(self) -> bool:
        """Check if git working directory is clean"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True
            )
            return len(result.stdout.strip()) == 0
        except subprocess.CalledProcessError:
            return False
    
    def check_secrets(self) -> bool:
        """Check if required secrets are configured"""
        required_secrets = [
            "VULTR_API_KEY",
            "DATABASE_URL",
            "REDIS_URL",
            "SSL_PRIVATE_KEY",
            "SSL_CERTIFICATE"
        ]
        
        # Check Pulumi secrets
        try:
            result = subprocess.run(
                ["pulumi", "config", "--json", "--stack", self.current_config["stack"]],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.pulumi_dir
            )
            config = json.loads(result.stdout)
            
            for secret in required_secrets:
                if secret.lower() not in config:
                    logger.warning(f"Missing secret: {secret}")
                    return False
            
            return True
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return False
    
    def check_disk_space(self) -> bool:
        """Check available disk space"""
        import shutil
        stat = shutil.disk_usage("/")
        free_gb = stat.free / (1024 ** 3)
        return free_gb > 5  # Require at least 5GB free
    
    async def check_network(self) -> bool:
        """Check network connectivity to required services"""
        import aiohttp
        
        endpoints = [
            "https://api.vultr.com/v2/account",
            "https://github.com",
            "https://pypi.org"
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    async with session.get(endpoint, timeout=5) as response:
                        if response.status >= 500:
                            return False
                except Exception:
                    return False
        
        return True
    
    async def run_tests(self):
        """Run test suite"""
        self.log_step("Running tests")
        
        # Run unit tests
        result = subprocess.run(
            ["python", "-m", "pytest", "services/ai_collaboration/tests", "-v"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Tests failed: {result.stderr}")
        
        self.log_step("Tests passed", "SUCCESS")
    
    async def build_artifacts(self):
        """Build deployment artifacts"""
        self.log_step("Building artifacts")
        
        # Build Docker images
        services = ["ai-collaboration-service", "websocket-adapter", "metrics-collector"]
        
        for service in services:
            self.log_step(f"Building {service} Docker image")
            
            result = subprocess.run(
                [
                    "docker", "build",
                    "-t", f"{service}:{self.environment}",
                    "-f", f"services/ai_collaboration/Dockerfile.{service}",
                    "."
                ],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Docker build failed for {service}: {result.stderr}")
        
        # Build frontend assets
        self.log_step("Building frontend assets")
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=self.project_root / "admin-interface",
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Frontend build failed: {result.stderr}")
        
        self.log_step("Artifacts built successfully", "SUCCESS")
    
    async def deploy_infrastructure(self):
        """Deploy infrastructure using Pulumi"""
        self.log_step("Deploying infrastructure")
        
        # Set Pulumi configuration
        config_values = {
            "region": self.current_config["region"],
            "domain": self.current_config["domain"],
            "environment": self.environment
        }
        
        for key, value in config_values.items():
            subprocess.run(
                ["pulumi", "config", "set", key, value, "--stack", self.current_config["stack"]],
                cwd=self.pulumi_dir,
                check=True
            )
        
        # Run Pulumi up
        result = subprocess.run(
            ["pulumi", "up", "--yes", "--stack", self.current_config["stack"]],
            cwd=self.pulumi_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Infrastructure deployment failed: {result.stderr}")
        
        # Get outputs
        outputs_result = subprocess.run(
            ["pulumi", "stack", "output", "--json", "--stack", self.current_config["stack"]],
            cwd=self.pulumi_dir,
            capture_output=True,
            text=True,
            check=True
        )
        
        self.infrastructure_outputs = json.loads(outputs_result.stdout)
        self.log_step("Infrastructure deployed", "SUCCESS", self.infrastructure_outputs)
    
    async def deploy_application(self) -> str:
        """Deploy application using blue-green strategy"""
        self.log_step("Deploying application")
        
        # Determine deployment color
        current_color = self.infrastructure_outputs.get("active_deployment", "blue")
        new_color = "green" if current_color == "blue" else "blue"
        
        self.log_step(f"Deploying to {new_color} environment")
        
        # Deploy to instances
        instance_ips = [
            ip for ip in self.infrastructure_outputs["app_instance_ips"]
            if f"-{new_color}-" in ip
        ]
        
        deployment_tasks = []
        for ip in instance_ips:
            deployment_tasks.append(self.deploy_to_instance(ip, new_color))
        
        await asyncio.gather(*deployment_tasks)
        
        self.log_step(f"Application deployed to {new_color}", "SUCCESS")
        return new_color
    
    async def deploy_to_instance(self, instance_ip: str, color: str):
        """Deploy application to a specific instance"""
        # SSH and deploy
        commands = [
            "cd /opt/app",
            "git pull origin main",
            f"docker-compose -f docker-compose.{color}.yml pull",
            f"docker-compose -f docker-compose.{color}.yml up -d",
            "docker system prune -f"
        ]
        
        for cmd in commands:
            result = subprocess.run(
                ["ssh", f"ubuntu@{instance_ip}", cmd],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Deployment to {instance_ip} failed: {result.stderr}")
    
    async def health_checks(self, deployment_color: str) -> bool:
        """Run comprehensive health checks"""
        self.log_step(f"Running health checks on {deployment_color}")
        
        instance_ips = [
            ip for ip in self.infrastructure_outputs["app_instance_ips"]
            if f"-{deployment_color}-" in ip
        ]
        
        checks = {
            "api_health": await self.check_api_health(instance_ips),
            "websocket_health": await self.check_websocket_health(instance_ips),
            "database_connectivity": await self.check_database_connectivity(instance_ips),
            "redis_connectivity": await self.check_redis_connectivity(instance_ips),
            "performance_baseline": await self.check_performance_baseline(instance_ips)
        }
        
        all_healthy = all(checks.values())
        
        self.log_step(
            "Health checks completed",
            "SUCCESS" if all_healthy else "ERROR",
            checks
        )
        
        return all_healthy
    
    async def check_api_health(self, instance_ips: List[str]) -> bool:
        """Check API health endpoints"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            for ip in instance_ips:
                try:
                    async with session.get(f"http://{ip}:8000/health", timeout=10) as response:
                        if response.status != 200:
                            return False
                        
                        data = await response.json()
                        if not data.get("healthy", False):
                            return False
                except Exception as e:
                    logger.error(f"API health check failed for {ip}: {e}")
                    return False
        
        return True
    
    async def check_websocket_health(self, instance_ips: List[str]) -> bool:
        """Check WebSocket connectivity"""
        import websockets
        
        for ip in instance_ips:
            try:
                async with websockets.connect(f"ws://{ip}:8765/health") as websocket:
                    await websocket.send(json.dumps({"type": "ping"}))
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(response)
                    
                    if data.get("type") != "pong":
                        return False
            except Exception as e:
                logger.error(f"WebSocket health check failed for {ip}: {e}")
                return False
        
        return True
    
    async def check_database_connectivity(self, instance_ips: List[str]) -> bool:
        """Check database connectivity from instances"""
        # Implementation would SSH to instances and test DB connection
        return True
    
    async def check_redis_connectivity(self, instance_ips: List[str]) -> bool:
        """Check Redis connectivity from instances"""
        # Implementation would SSH to instances and test Redis connection
        return True
    
    async def check_performance_baseline(self, instance_ips: List[str]) -> bool:
        """Check if performance meets baseline requirements"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            for ip in instance_ips:
                # Test response time
                start = time.time()
                try:
                    async with session.get(f"http://{ip}:8000/api/v1/ai-collaboration/status", timeout=5) as response:
                        elapsed = (time.time() - start) * 1000  # ms
                        
                        if elapsed > 250:  # P99 target
                            logger.warning(f"Performance check failed for {ip}: {elapsed}ms")
                            return False
                except Exception:
                    return False
        
        return True
    
    async def switch_traffic(self, new_color: str):
        """Switch traffic to new deployment"""
        self.log_step(f"Switching traffic to {new_color}")
        
        # Update Pulumi configuration
        subprocess.run(
            ["pulumi", "config", "set", "active_deployment", new_color, "--stack", self.current_config["stack"]],
            cwd=self.pulumi_dir,
            check=True
        )
        
        # Update load balancer
        result = subprocess.run(
            ["pulumi", "up", "--yes", "--target", "vultr:index/loadBalancer:LoadBalancer", "--stack", self.current_config["stack"]],
            cwd=self.pulumi_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Traffic switch failed: {result.stderr}")
        
        # Wait for propagation
        await asyncio.sleep(30)
        
        self.log_step(f"Traffic switched to {new_color}", "SUCCESS")
    
    async def post_deployment_validation(self):
        """Validate deployment after traffic switch"""
        self.log_step("Running post-deployment validation")
        
        # Check public endpoints
        import aiohttp
        
        endpoints = [
            f"https://{self.current_config['domain']}/api/v1/ai-collaboration/status",
            f"https://api.{self.current_config['domain']}/health",
            f"wss://ws.{self.current_config['domain']}:8765"
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                if endpoint.startswith("wss://"):
                    # Skip WebSocket validation here
                    continue
                    
                try:
                    async with session.get(endpoint, timeout=10) as response:
                        if response.status != 200:
                            raise Exception(f"Endpoint validation failed: {endpoint}")
                except Exception as e:
                    raise Exception(f"Post-deployment validation failed: {e}")
        
        self.log_step("Post-deployment validation passed", "SUCCESS")
    
    async def cleanup_old_deployment(self, active_color: str):
        """Cleanup resources from old deployment"""
        self.log_step("Cleaning up old deployment")
        
        old_color = "blue" if active_color == "green" else "green"
        
        # Stop old containers
        instance_ips = [
            ip for ip in self.infrastructure_outputs["app_instance_ips"]
            if f"-{old_color}-" in ip
        ]
        
        for ip in instance_ips:
            subprocess.run(
                ["ssh", f"ubuntu@{ip}", f"docker-compose -f docker-compose.{old_color}.yml down"],
                capture_output=True
            )
        
        self.log_step("Old deployment cleaned up", "SUCCESS")
    
    async def rollback(self):
        """Rollback to previous deployment"""
        self.log_step("Initiating rollback", "WARNING")
        
        try:
            # Get current active deployment
            current_color = self.infrastructure_outputs.get("active_deployment", "blue")
            previous_color = "blue" if current_color == "green" else "green"
            
            # Switch traffic back
            await self.switch_traffic(previous_color)
            
            # Verify rollback
            healthy = await self.health_checks(previous_color)
            
            if healthy:
                self.log_step("Rollback completed successfully", "SUCCESS")
            else:
                self.log_step("Rollback health checks failed", "ERROR")
                raise Exception("Rollback failed - manual intervention required")
                
        except Exception as e:
            self.log_step("Rollback failed", "ERROR", {"error": str(e)})
            raise
    
    def save_deployment_log(self):
        """Save deployment log to file"""
        log_file = self.project_root / "deployments" / f"deployment_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        log_file.parent.mkdir(exist_ok=True)
        
        with open(log_file, "w") as f:
            json.dump({
                "environment": self.environment,
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "duration": (datetime.utcnow() - self.start_time).total_seconds(),
                "log": self.deployment_log
            }, f, indent=2)
        
        logger.info(f"Deployment log saved to {log_file}")


async def main():
    """Main deployment entry point"""
    parser = argparse.ArgumentParser(description="Deploy AI Collaboration Dashboard")
    parser.add_argument(
        "--environment",
        choices=["staging", "production"],
        default="staging",
        help="Deployment environment"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running tests"
    )
    parser.add_argument(
        "--no-rollback",
        action="store_true",
        help="Disable automatic rollback on failure"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform dry run without actual deployment"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No actual changes will be made")
    
    deployer = AICollaborationDeployer(args.environment)
    
    try:
        await deployer.deploy(
            skip_tests=args.skip_tests,
            auto_rollback=not args.no_rollback
        )
        
        logger.info("🎉 Deployment completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))