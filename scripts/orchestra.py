#!/usr/bin/env python3
"""
Orchestra CLI - Unified Command Interface

A simple CLI tool that consolidates common Orchestra operations:
- Configuration validation
- Health monitoring  
- Service management
- Infrastructure operations

Usage:
    python scripts/orchestra.py config validate
    python scripts/orchestra.py health check
    python scripts/orchestra.py health monitor
    python scripts/orchestra.py services start
    python scripts/orchestra.py services stop
"""

import subprocess
import sys
import argparse
import logging
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrchestaCLI:
    """Simple unified CLI for Orchestra operations."""
    
    def __init__(self):
        self.script_dir = "scripts"
        
    def run_command(self, cmd: List[str], capture_output: bool = False) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        try:
            logger.debug(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                check=False
            )
            return result
        except Exception as e:
            logger.error(f"Command failed: {e}")
            return subprocess.CompletedProcess(cmd, 1, stderr=str(e))
    
    def config_validate(self, args) -> int:
        """Validate Orchestra configuration."""
        logger.info("Validating configuration...")
        
        cmd = ["python", f"{self.script_dir}/config_validator.py"]
        if args.output:
            cmd.extend(["--output", args.output])
        if args.fail_fast:
            cmd.append("--fail-fast")
        if args.verbose:
            cmd.append("--verbose")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def health_check(self, args) -> int:
        """Check health of all services."""
        logger.info("Checking service health...")
        
        cmd = ["python", f"{self.script_dir}/health_monitor.py", "--check-services"]
        if args.verbose:
            cmd.append("--verbose")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def health_monitor(self, args) -> int:
        """Start continuous health monitoring."""
        logger.info("Starting health monitoring...")
        
        cmd = ["python", f"{self.script_dir}/health_monitor.py", "--monitor"]
        if args.interval:
            cmd.extend(["--interval", str(args.interval)])
        if args.verbose:
            cmd.append("--verbose")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def health_wait(self, args) -> int:
        """Wait for a service to become healthy."""
        if not args.service:
            logger.error("Service name required for wait command")
            return 1
        
        logger.info(f"Waiting for service: {args.service}")
        
        cmd = ["python", f"{self.script_dir}/health_monitor.py", "--wait-for", args.service]
        if args.max_wait:
            cmd.extend(["--max-wait", str(args.max_wait)])
        
        result = self.run_command(cmd)
        return result.returncode
    
    def services_status(self, args) -> int:
        """Show status of running services."""
        logger.info("Checking service status...")
        
        # Check what's running on known ports
        try:
            import socket
            services = {
                8002: "MCP Secret Manager",
                8080: "Orchestrator/Firestore",
                3000: "Admin UI"
            }
            
            status = {}
            for port, name in services.items():
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(1)
                        result = s.connect_ex(('localhost', port))
                        status[port] = {"name": name, "running": result == 0}
                except Exception:
                    status[port] = {"name": name, "running": False}
            
            print("\nService Status:")
            print("=" * 50)
            for port, info in status.items():
                status_str = "✅ RUNNING" if info["running"] else "❌ STOPPED"
                print(f"Port {port:4d}: {info['name']:<20} {status_str}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Error checking service status: {e}")
            return 1
    
    def services_start(self, args) -> int:
        """Start Orchestra services."""
        logger.info("Starting Orchestra services...")
        
        # Start services in order
        services = [
            {"name": "MCP Secret Manager", "cmd": ["python", "-m", "mcp_servers.secret_manager", "--port", "8002"]},
            {"name": "Core Orchestrator", "cmd": ["python", "core/orchestrator/src/api/app.py"]}
        ]
        
        for service in services:
            logger.info(f"Starting {service['name']}...")
            
            # Run in background
            try:
                process = subprocess.Popen(
                    service["cmd"],
                    stdout=subprocess.DEVNULL if not args.verbose else None,
                    stderr=subprocess.DEVNULL if not args.verbose else None
                )
                logger.info(f"{service['name']} started with PID {process.pid}")
            except Exception as e:
                logger.error(f"Failed to start {service['name']}: {e}")
                return 1
        
        logger.info("All services started. Use 'orchestra health check' to verify.")
        return 0
    
    def services_stop(self, args) -> int:
        """Stop Orchestra services."""
        logger.info("Stopping Orchestra services...")
        
        try:
            # Kill processes on known ports
            ports = [8002, 8080]
            for port in ports:
                cmd = ["lsof", "-ti", f":{port}"]
                result = self.run_command(cmd, capture_output=True)
                
                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid:
                            logger.info(f"Stopping process {pid} on port {port}")
                            self.run_command(["kill", pid])
            
            logger.info("Services stopped")
            return 0
            
        except Exception as e:
            logger.error(f"Error stopping services: {e}")
            return 1
    
    def infra_validate(self, args) -> int:
        """Validate infrastructure configuration."""
        logger.info("Validating infrastructure...")
        
        # Check if Pulumi files exist
        import os
        pulumi_files = ["Pulumi.yaml", "infra/__main__.py"]
        missing = [f for f in pulumi_files if not os.path.exists(f)]
        
        if missing:
            logger.warning(f"Missing Pulumi files: {missing}")
        
        # Run config validation as well
        return self.config_validate(args)
    
    def env_check(self, args) -> int:
        """Check environment setup."""
        logger.info("Checking environment...")
        
        cmd = ["python", f"{self.script_dir}/health_monitor.py", "--check-prereqs"]
        result = self.run_command(cmd)
        return result.returncode
    
    def env_setup(self, args) -> int:
        """Set up development environment."""
        logger.info("Setting up environment...")
        
        commands = [
            ["make", "venv-check"],
            ["make", "deps-check"],
            ["python", f"{self.script_dir}/config_validator.py"]
        ]
        
        for cmd in commands:
            logger.info(f"Running: {' '.join(cmd)}")
            result = self.run_command(cmd)
            if result.returncode != 0:
                logger.error(f"Setup step failed: {' '.join(cmd)}")
                return result.returncode
        
        logger.info("Environment setup complete!")
        return 0


def main():
    """Main entry point for Orchestra CLI."""
    parser = argparse.ArgumentParser(
        description="Orchestra CLI - Unified command interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    orchestra.py config validate              # Validate all configuration
    orchestra.py health check                 # Check service health once  
    orchestra.py health monitor               # Monitor continuously
    orchestra.py health wait --service=mcp_firestore  # Wait for service
    orchestra.py services status              # Show service status
    orchestra.py services start               # Start all services
    orchestra.py services stop                # Stop all services
    orchestra.py infra validate               # Validate infrastructure
    orchestra.py env check                    # Check environment
    orchestra.py env setup                    # Set up environment
        """
    )
    
    # Global options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Config commands
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_subparsers = config_parser.add_subparsers(dest="config_action")
    
    validate_parser = config_subparsers.add_parser("validate", help="Validate configuration")
    validate_parser.add_argument("--output", help="Output file for results")
    validate_parser.add_argument("--fail-fast", action="store_true", help="Exit on first error")
    
    # Health commands
    health_parser = subparsers.add_parser("health", help="Health monitoring")
    health_subparsers = health_parser.add_subparsers(dest="health_action")
    
    health_subparsers.add_parser("check", help="Check service health once")
    
    monitor_parser = health_subparsers.add_parser("monitor", help="Monitor continuously")
    monitor_parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds")
    
    wait_parser = health_subparsers.add_parser("wait", help="Wait for service to be healthy")
    wait_parser.add_argument("--service", required=True, help="Service name to wait for")
    wait_parser.add_argument("--max-wait", type=int, default=120, help="Maximum wait time")
    
    # Services commands
    services_parser = subparsers.add_parser("services", help="Service management")
    services_subparsers = services_parser.add_subparsers(dest="services_action")
    
    services_subparsers.add_parser("status", help="Show service status")
    services_subparsers.add_parser("start", help="Start all services")
    services_subparsers.add_parser("stop", help="Stop all services")
    
    # Infrastructure commands
    infra_parser = subparsers.add_parser("infra", help="Infrastructure management")
    infra_subparsers = infra_parser.add_subparsers(dest="infra_action")
    
    infra_subparsers.add_parser("validate", help="Validate infrastructure configuration")
    
    # Environment commands
    env_parser = subparsers.add_parser("env", help="Environment management")
    env_subparsers = env_parser.add_subparsers(dest="env_action")
    
    env_subparsers.add_parser("check", help="Check environment setup")
    env_subparsers.add_parser("setup", help="Set up development environment")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = OrchestaCLI()
    
    # Route to appropriate handler
    try:
        if args.command == "config":
            if args.config_action == "validate":
                return cli.config_validate(args)
        elif args.command == "health":
            if args.health_action == "check":
                return cli.health_check(args)
            elif args.health_action == "monitor":
                return cli.health_monitor(args)
            elif args.health_action == "wait":
                return cli.health_wait(args)
        elif args.command == "services":
            if args.services_action == "status":
                return cli.services_status(args)
            elif args.services_action == "start":
                return cli.services_start(args)
            elif args.services_action == "stop":
                return cli.services_stop(args)
        elif args.command == "infra":
            if args.infra_action == "validate":
                return cli.infra_validate(args)
        elif args.command == "env":
            if args.env_action == "check":
                return cli.env_check(args)
            elif args.env_action == "setup":
                return cli.env_setup(args)
        
        # If we get here, invalid subcommand
        parser.print_help()
        return 1
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 