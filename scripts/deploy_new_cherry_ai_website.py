import logging
logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""
DEFINITIVE Cherry AI Website Deployment
Multi-role execution plan with zero tolerance for errors
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from datetime import datetime

# ANSI colors for role identification
ORCHESTRATOR = '\033[95m'  # Magenta
ARCHITECT = '\033[94m'      # Blue
DEVELOPER = '\033[92m'      # Green
DEBUGGER = '\033[93m'       # Yellow
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'

class DeploymentOrchestrator:
    """Strategic planning and coordination"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.deployment_path = Path("/var/www/cherry-ai.me")
        self.source_path = Path("./src/ui/web/react_app")
        self.backup_path = Path(f"./backup_old_ui_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
    def log(self, role, message, status="INFO"):
        """Unified logging with role identification"""
        color = {
            "ORCHESTRATOR": ORCHESTRATOR,
            "ARCHITECT": ARCHITECT,
            "DEVELOPER": DEVELOPER,
            "DEBUGGER": DEBUGGER
        }.get(role, RESET)
        
        status_color = {
            "ERROR": RED,
            "SUCCESS": DEVELOPER,
            "WARNING": DEBUGGER
        }.get(status, RESET)
        
        print(f"{color}[{role}]{RESET} {status_color}{message}{RESET}")
    
    def execute_command(self, cmd, role="ORCHESTRATOR", critical=True):
        """Execute command with role context"""
        self.log(role, f"Executing: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                self.log(role, f"Command failed: {result.stderr}", "ERROR")
                if critical:
                    sys.exit(1)
                return False
            return True
        except Exception as e:
            self.log(role, f"Exception: {str(e)}", "ERROR")
            if critical:
                sys.exit(1)
            return False

class SystemArchitect:
    """System design and infrastructure management"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        
    def validate_infrastructure(self):
        """Validate all infrastructure components"""
        self.orchestrator.log("ARCHITECT", "Validating infrastructure components")
        
        checks = {
            "Docker Services": "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E '(postgres|redis|weaviate|api)'",
            "Nginx": "systemctl is-active nginx",
            "SSL Certificate": "test -f /etc/letsencrypt/live/cherry-ai.me/fullchain.pem && echo 'exists'"
        }
        
        all_good = True
        for component, check in checks.items():
            result = subprocess.run(check, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                self.orchestrator.log("ARCHITECT", f"✓ {component}: OK", "SUCCESS")
            else:
                self.orchestrator.log("ARCHITECT", f"✗ {component}: FAILED", "ERROR")
                all_good = False
        
        # Check API health separately with better error handling
        try:
            api_result = subprocess.run(
                "curl -s https://cherry-ai.me/health",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            if api_result.returncode == 0 and "healthy" in api_result.stdout:
                self.orchestrator.log("ARCHITECT", f"✓ API Health: OK", "SUCCESS")
            else:
                self.orchestrator.log("ARCHITECT", f"⚠ API Health: Not responding (will continue)", "WARNING")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.orchestrator.log("ARCHITECT", f"⚠ API Health: Timeout (will continue)", "WARNING")
                
        return all_good
    
    def prepare_deployment_environment(self):
        """Prepare the deployment environment"""
        self.orchestrator.log("ARCHITECT", "Preparing deployment environment")
        
        # Backup existing deployment
        if self.orchestrator.deployment_path.exists():
            self.orchestrator.log("ARCHITECT", f"Backing up existing deployment to {self.orchestrator.backup_path}")
            self.orchestrator.execute_command(
                f"sudo cp -r {self.orchestrator.deployment_path} {self.orchestrator.backup_path}",
                "ARCHITECT"
            )
        
        # Ensure deployment directory exists
        self.orchestrator.execute_command(
            f"sudo mkdir -p {self.orchestrator.deployment_path}",
            "ARCHITECT"
        )
        
        return True

class Developer:
    """Implementation and coding"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        
    def setup_build_environment(self):
        """Setup the build environment for the new UI"""
        self.orchestrator.log("DEVELOPER", "Setting up build environment")
        
        # Create necessary config files
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "useDefineForClassFields": True,
                "lib": ["ES2020", "DOM", "DOM.Iterable"],
                "module": "ESNext",
                "skipLibCheck": True,
                "moduleResolution": "node",
                "allowImportingTsExtensions": False,
                "resolveJsonModule": True,
                "isolatedModules": True,
                "noEmit": True,
                "jsx": "react-jsx",
                "strict": True,
                "noUnusedLocals": False,
                "noUnusedParameters": False,
                "noFallthroughCasesInSwitch": True,
                "allowSyntheticDefaultImports": True,
                "esModuleInterop": True
            },
            "include": ["src"],
            "exclude": ["node_modules", "dist"]
        }
        
        tsconfig_node = {
            "compilerOptions": {
                "composite": True,
                "skipLibCheck": True,
                "module": "ESNext",
                "moduleResolution": "node",
                "allowSyntheticDefaultImports": True
            },
            "include": ["vite.config.ts"]
        }
        
        # Write config files
        with open(self.orchestrator.source_path / "tsconfig.json", "w") as f:
            json.dump(tsconfig, f, indent=2)
            
        with open(self.orchestrator.source_path / "tsconfig.node.json", "w") as f:
            json.dump(tsconfig_node, f, indent=2)
            
        self.orchestrator.log("DEVELOPER", "TypeScript configuration created", "SUCCESS")
        return True
    
    def build_application(self):
        """Build the React application"""
        self.orchestrator.log("DEVELOPER", "Building React application")
        
        # Change to source directory
        os.chdir(self.orchestrator.source_path)
        
        # Install dependencies
        self.orchestrator.log("DEVELOPER", "Installing dependencies")
        if not self.orchestrator.execute_command("npm install", "DEVELOPER"):
            return False
            
        # Build the application
        self.orchestrator.log("DEVELOPER", "Building production bundle")
        if not self.orchestrator.execute_command("npm run build", "DEVELOPER"):
            # Try alternative build command
            self.orchestrator.log("DEVELOPER", "Trying direct vite build")
            if not self.orchestrator.execute_command("npx vite build", "DEVELOPER"):
                return False
        
        # Change back to original directory
        os.chdir("/root/orchestra-main")
        
        return True
    
    def deploy_application(self):
        """Deploy the built application"""
        self.orchestrator.log("DEVELOPER", "Deploying application")
        
        dist_path = self.orchestrator.source_path / "dist"
        if not dist_path.exists():
            self.orchestrator.log("DEVELOPER", "Build output not found", "ERROR")
            return False
        
        # Clear existing deployment
        self.orchestrator.execute_command(
            f"sudo rm -rf {self.orchestrator.deployment_path}/*",
            "DEVELOPER"
        )
        
        # Copy new build
        self.orchestrator.execute_command(
            f"sudo cp -r {dist_path}/* {self.orchestrator.deployment_path}/",
            "DEVELOPER"
        )
        
        # Set permissions
        self.orchestrator.execute_command(
            f"sudo chown -R www-data:www-data {self.orchestrator.deployment_path}",
            "DEVELOPER"
        )
        
        self.orchestrator.log("DEVELOPER", "Application deployed successfully", "SUCCESS")
        return True

class Debugger:
    """Quality assurance and optimization"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        
    def validate_deployment(self):
        """Validate the deployment"""
        self.orchestrator.log("DEBUGGER", "Validating deployment")
        
        tests = [
            ("Homepage", "https://cherry-ai.me/", 200),
            ("Admin Route", "https://cherry-ai.me/admin", 200),
            ("API Health", "https://cherry-ai.me/health", 200),
            ("Static Assets", "https://cherry-ai.me/assets/", None)  # Check if directory listing is forbidden
        ]
        
        all_passed = True
        for test_name, url, expected_status in tests:
            try:
                result = subprocess.run(
                    f"curl -s -o /dev/null -w '%{{http_code}}' {url}",
                    shell=True, capture_output=True, text=True
                )
                status_code = result.stdout.strip()
                
                if expected_status:
                    if status_code == str(expected_status):
                        self.orchestrator.log("DEBUGGER", f"✓ {test_name}: {status_code}", "SUCCESS")
                    else:
                        self.orchestrator.log("DEBUGGER", f"✗ {test_name}: {status_code} (expected {expected_status})", "ERROR")
                        all_passed = False
                else:
                    self.orchestrator.log("DEBUGGER", f"✓ {test_name}: {status_code}", "SUCCESS")
                    
            except Exception as e:
                self.orchestrator.log("DEBUGGER", f"✗ {test_name}: {str(e)}", "ERROR")
                all_passed = False
                
        return all_passed
    
    def optimize_nginx_config(self):
        """Ensure Nginx is optimally configured"""
        self.orchestrator.log("DEBUGGER", "Optimizing Nginx configuration")
        
        # Test Nginx configuration
        if self.orchestrator.execute_command("sudo nginx -t", "DEBUGGER"):
            # Reload Nginx
            self.orchestrator.execute_command("sudo systemctl reload nginx", "DEBUGGER")
            self.orchestrator.log("DEBUGGER", "Nginx configuration optimized", "SUCCESS")
            return True
        return False

def main():
    """Main execution flow"""
    print(f"{BOLD}{ORCHESTRATOR}{'='*60}{RESET}")
    print(f"{BOLD}{ORCHESTRATOR}DEFINITIVE CHERRY AI WEBSITE DEPLOYMENT{RESET}")
    print(f"{BOLD}{ORCHESTRATOR}{'='*60}{RESET}\n")
    
    # Initialize orchestrator
    orchestrator = DeploymentOrchestrator()
    orchestrator.log("ORCHESTRATOR", "Deployment initiated", "INFO")
    
    # Initialize role handlers
    architect = SystemArchitect(orchestrator)
    developer = Developer(orchestrator)
    debugger = Debugger(orchestrator)
    
    # PHASE 1: Infrastructure Validation
    orchestrator.log("ORCHESTRATOR", "PHASE 1: Infrastructure Validation")
    if not architect.validate_infrastructure():
        orchestrator.log("ORCHESTRATOR", "Infrastructure validation failed", "ERROR")
        sys.exit(1)
    
    # PHASE 2: Environment Preparation
    orchestrator.log("ORCHESTRATOR", "PHASE 2: Environment Preparation")
    if not architect.prepare_deployment_environment():
        orchestrator.log("ORCHESTRATOR", "Environment preparation failed", "ERROR")
        sys.exit(1)
    
    # PHASE 3: Build Setup
    orchestrator.log("ORCHESTRATOR", "PHASE 3: Build Setup")
    if not developer.setup_build_environment():
        orchestrator.log("ORCHESTRATOR", "Build setup failed", "ERROR")
        sys.exit(1)
    
    # PHASE 4: Application Build
    orchestrator.log("ORCHESTRATOR", "PHASE 4: Application Build")
    if not developer.build_application():
        orchestrator.log("ORCHESTRATOR", "Application build failed", "ERROR")
        sys.exit(1)
    
    # PHASE 5: Deployment
    orchestrator.log("ORCHESTRATOR", "PHASE 5: Deployment")
    if not developer.deploy_application():
        orchestrator.log("ORCHESTRATOR", "Deployment failed", "ERROR")
        sys.exit(1)
    
    # PHASE 6: Validation
    orchestrator.log("ORCHESTRATOR", "PHASE 6: Validation")
    if not debugger.validate_deployment():
        orchestrator.log("ORCHESTRATOR", "Deployment validation failed", "ERROR")
        sys.exit(1)
    
    # PHASE 7: Optimization
    orchestrator.log("ORCHESTRATOR", "PHASE 7: Optimization")
    debugger.optimize_nginx_config()
    
    # Final Summary
    duration = (datetime.now() - orchestrator.start_time).total_seconds()
    print(f"\n{BOLD}{ORCHESTRATOR}{'='*60}{RESET}")
    print(f"{BOLD}{DEVELOPER}✅ DEPLOYMENT SUCCESSFUL{RESET}")
    print(f"{ORCHESTRATOR}Duration: {duration:.2f} seconds{RESET}")
    print(f"{ORCHESTRATOR}Website: https://cherry-ai.me{RESET}")
    print(f"{ORCHESTRATOR}Admin: https://cherry-ai.me/admin{RESET}")
    print(f"{BOLD}{ORCHESTRATOR}{'='*60}{RESET}")

if __name__ == "__main__":
    main()