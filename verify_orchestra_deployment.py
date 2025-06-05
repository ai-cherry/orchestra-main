#!/usr/bin/env python3
"""
Orchestra Deployment Verification Script
Comprehensive checks for Lambda Labs deployment
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'deployment_verification_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


class OrchestraDeploymentVerifier:
    """Verify Orchestra deployment on Lambda Labs."""
    
    def __init__(self):
        self.server_ip = "150.136.94.139"
        self.verification_results = {
            "timestamp": datetime.now().isoformat(),
            "server": {
                "ip": self.server_ip,
                "provider": "Lambda Labs",
                "type": "8x A100 GPU instance"
            },
            "checks": {},
            "issues": [],
            "recommendations": []
        }
    
    def check_local_services(self) -> Dict[str, bool]:
        """Check locally running services."""
        logger.info("🔍 Checking local services...")
        
        local_services = {}
        
        # Check if local test server is running
        try:
            result = subprocess.run(
                "lsof -i:8080",
                shell=True,
                capture_output=True,
                text=True
            )
            local_services["test_server_8080"] = result.returncode == 0
            if local_services["test_server_8080"]:
                logger.info("✅ Local test server running on port 8080")
            else:
                logger.info("❌ No local test server on port 8080")
        except Exception as e:
            logger.error(f"Error checking local services: {e}")
            local_services["test_server_8080"] = False
        
        return local_services
    
    def check_remote_services(self) -> Dict[str, Dict[str, any]]:
        """Check remote Lambda Labs services."""
        logger.info(f"🌐 Checking remote services on {self.server_ip}...")
        
        services = {
            "cherry_ai": {
                "url": f"http://{self.server_ip}:8000",
                "name": "Cherry AI Interface",
                "critical": True
            },
            "weaviate": {
                "url": f"http://{self.server_ip}:8080/v1/.well-known/ready",
                "name": "Weaviate Vector DB",
                "critical": True
            },
            "nginx": {
                "url": f"http://{self.server_ip}",
                "name": "Nginx Web Server",
                "critical": False
            }
        }
        
        results = {}
        for service_id, service_info in services.items():
            try:
                cmd = f"curl -s -o /dev/null -w '%{{http_code}}' {service_info['url']} --connect-timeout 5"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                http_code = result.stdout.strip()
                
                is_healthy = http_code in ["200", "301", "302", "404"]  # 404 might be OK for root
                
                results[service_id] = {
                    "name": service_info["name"],
                    "url": service_info["url"],
                    "http_code": http_code,
                    "status": "healthy" if is_healthy else "unhealthy",
                    "critical": service_info["critical"]
                }
                
                status_icon = "✅" if is_healthy else "❌"
                logger.info(f"{status_icon} {service_info['name']}: HTTP {http_code}")
                
                if not is_healthy and service_info["critical"]:
                    self.verification_results["issues"].append(
                        f"Critical service {service_info['name']} is not responding properly"
                    )
                    
            except Exception as e:
                logger.error(f"Error checking {service_info['name']}: {e}")
                results[service_id] = {
                    "name": service_info["name"],
                    "url": service_info["url"],
                    "status": "error",
                    "error": str(e),
                    "critical": service_info["critical"]
                }
                
                if service_info["critical"]:
                    self.verification_results["issues"].append(
                        f"Cannot reach critical service {service_info['name']}: {e}"
                    )
        
        return results
    
    def check_deployment_files(self) -> Dict[str, bool]:
        """Check if deployment files exist locally."""
        logger.info("📁 Checking deployment files...")
        
        required_files = {
            "cherry-ai-orchestrator-final.html": "Frontend HTML",
            "cherry-ai-orchestrator.js": "Frontend JavaScript",
            "deploy_orchestra_lambda.py": "Lambda deployment script",
            "lambda_deployment_strategy.json": "Deployment strategy",
            ".env.template": "Environment template"
        }
        
        file_status = {}
        for filename, description in required_files.items():
            exists = Path(filename).exists()
            file_status[filename] = exists
            
            icon = "✅" if exists else "❌"
            logger.info(f"{icon} {description}: {filename}")
            
            if not exists:
                self.verification_results["issues"].append(
                    f"Missing deployment file: {filename}"
                )
        
        return file_status
    
    def check_infrastructure_alignment(self) -> Dict[str, any]:
        """Check if infrastructure is properly aligned with Lambda Labs."""
        logger.info("🏗️ Checking infrastructure alignment...")
        
        alignment = {
            "correct_files": [],
            "incorrect_files": [],
            "recommendations": []
        }
        
        # Check for Lambda-specific files
        lambda_files = [
            "lambda_infrastructure_mcp_server.py",
            "deploy_orchestra_lambda.py",
            "lambda_deployment_strategy.json"
        ]
        
        for file in lambda_files:
            if Path(file).exists():
                alignment["correct_files"].append(file)
                logger.info(f"✅ Lambda file exists: {file}")
        
        # Check for Vultr files that shouldn't be used
        vultr_files = [
            "deploy_orchestrator_infrastructure.py",
            "infrastructure/vultr_deployment.py",
            "infrastructure/vultr_manager.py"
        ]
        
        for file in vultr_files:
            if Path(file).exists():
                alignment["incorrect_files"].append(file)
                logger.warning(f"⚠️  Vultr file found (should not be used): {file}")
                self.verification_results["recommendations"].append(
                    f"Remove or archive Vultr-specific file: {file}"
                )
        
        return alignment
    
    def generate_deployment_summary(self) -> str:
        """Generate a comprehensive deployment summary."""
        summary = []
        summary.append("🚀 ORCHESTRA DEPLOYMENT VERIFICATION SUMMARY")
        summary.append("=" * 60)
        summary.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(f"Target: Lambda Labs ({self.server_ip})")
        summary.append("")
        
        # Overall status
        critical_issues = [
            issue for issue in self.verification_results["issues"]
            if "critical" in issue.lower()
        ]
        
        if not critical_issues:
            summary.append("✅ DEPLOYMENT STATUS: OPERATIONAL")
        else:
            summary.append("❌ DEPLOYMENT STATUS: ISSUES DETECTED")
        
        summary.append("")
        
        # Service status
        if "remote_services" in self.verification_results["checks"]:
            summary.append("📊 Service Status:")
            for service_id, info in self.verification_results["checks"]["remote_services"].items():
                status_icon = "✅" if info["status"] == "healthy" else "❌"
                summary.append(f"  {status_icon} {info['name']}: {info['status']}")
        
        summary.append("")
        
        # Issues
        if self.verification_results["issues"]:
            summary.append("⚠️  Issues Found:")
            for issue in self.verification_results["issues"]:
                summary.append(f"  - {issue}")
            summary.append("")
        
        # Recommendations
        if self.verification_results["recommendations"]:
            summary.append("💡 Recommendations:")
            for rec in self.verification_results["recommendations"]:
                summary.append(f"  - {rec}")
            summary.append("")
        
        # Access information
        summary.append("🌐 Access Points:")
        summary.append(f"  - Cherry AI Interface: http://{self.server_ip}:8000")
        summary.append(f"  - Weaviate API: http://{self.server_ip}:8080")
        summary.append(f"  - Local Test UI: http://localhost:8080")
        summary.append("")
        
        # Next steps
        summary.append("📋 Next Steps:")
        summary.append("  1. Configure SSL/HTTPS for production")
        summary.append("  2. Set up domain name (e.g., orchestra.yourdomain.com)")
        summary.append("  3. Configure monitoring and alerts")
        summary.append("  4. Set up automated backups")
        summary.append("  5. Review security settings")
        
        return "\n".join(summary)
    
    def run_verification(self) -> bool:
        """Run complete deployment verification."""
        logger.info("Starting Orchestra deployment verification...")
        
        try:
            # Check local services
            self.verification_results["checks"]["local_services"] = self.check_local_services()
            
            # Check remote services
            self.verification_results["checks"]["remote_services"] = self.check_remote_services()
            
            # Check deployment files
            self.verification_results["checks"]["deployment_files"] = self.check_deployment_files()
            
            # Check infrastructure alignment
            self.verification_results["checks"]["infrastructure_alignment"] = self.check_infrastructure_alignment()
            
            # Generate summary
            summary = self.generate_deployment_summary()
            print("\n" + summary)
            
            # Save results
            report_file = f"orchestra_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, "w") as f:
                json.dump(self.verification_results, f, indent=2)
            
            logger.info(f"\n📄 Detailed report saved to: {report_file}")
            
            # Return success if no critical issues
            critical_issues = [
                issue for issue in self.verification_results["issues"]
                if "critical" in issue.lower()
            ]
            return len(critical_issues) == 0
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False


def main() -> int:
    """Main entry point."""
    verifier = OrchestraDeploymentVerifier()
    success = verifier.run_verification()
    
    if success:
        logger.info("\n✅ Deployment verification completed successfully!")
        return 0
    else:
        logger.error("\n❌ Deployment verification found issues!")
        return 1


if __name__ == "__main__":
    sys.exit(main())