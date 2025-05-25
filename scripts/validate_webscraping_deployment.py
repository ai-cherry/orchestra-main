#!/usr/bin/env python3
"""
Web Scraping AI Agent System Deployment Validation Script
Validates infrastructure alignment and deployment readiness.

This project uses pip and requirements files only. See requirements/webscraping.txt for web scraping dependencies.
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Optional

import aiohttp


class WebScrapingDeploymentValidator:
    """Validates web scraping system deployment and alignment."""

    def __init__(self):
        self.project_id = "cherry-ai-project"
        self.region = "us-central1"
        self.service_name = "web-scraping-agents"
        self.validation_results = []

    def log_result(self, check: str, status: str, message: str):
        """Log validation result."""
        result = {
            "timestamp": datetime.now().isoformat(),
            "check": check,
            "status": status,
            "message": message,
        }
        self.validation_results.append(result)

        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {check}: {message}")

    def validate_files_exist(self):
        """Validate required files exist."""
        required_files = [
            "web_scraping_ai_agents.py",
            "webscraping_app.py",
            "Dockerfile.webscraping",
            "requirements-webscraping.txt",
            "mcp_server/servers/web_scraping_mcp_server.py",
            "infra/pulumi_gcp/__main__.py",
            "cloudbuild.yaml",
        ]

        for file_path in required_files:
            if os.path.exists(file_path):
                self.log_result("File Existence", "PASS", f"{file_path} exists")
            else:
                self.log_result("File Existence", "FAIL", f"{file_path} missing")

    def validate_pulumi_config(self):
        """Validate Pulumi configuration includes web scraping service."""
        try:
            with open("infra/pulumi_gcp/__main__.py", "r") as f:
                content = f.read()

            if "web_scraping_service" in content:
                self.log_result("Pulumi Config", "PASS", "Web scraping service defined")
            else:
                self.log_result(
                    "Pulumi Config", "FAIL", "Web scraping service not found"
                )

            if "zenrows_secret" in content:
                self.log_result("Pulumi Config", "PASS", "Zenrows secret configured")
            else:
                self.log_result(
                    "Pulumi Config", "WARN", "Zenrows secret not configured"
                )

            if "apify_secret" in content:
                self.log_result("Pulumi Config", "PASS", "Apify secret configured")
            else:
                self.log_result("Pulumi Config", "WARN", "Apify secret not configured")

        except Exception as e:
            self.log_result(
                "Pulumi Config", "FAIL", f"Error reading Pulumi config: {e}"
            )

    def validate_cloudbuild_config(self):
        """Validate Cloud Build configuration."""
        try:
            with open("cloudbuild.yaml", "r") as f:
                content = f.read()

            if "Build-WebScraping" in content:
                self.log_result(
                    "Cloud Build", "PASS", "Web scraping build step configured"
                )
            else:
                self.log_result(
                    "Cloud Build", "FAIL", "Web scraping build step missing"
                )

            if "Deploy-WebScraping" in content:
                self.log_result(
                    "Cloud Build", "PASS", "Web scraping deploy step configured"
                )
            else:
                self.log_result(
                    "Cloud Build", "FAIL", "Web scraping deploy step missing"
                )

            if "Dockerfile.webscraping" in content:
                self.log_result("Cloud Build", "PASS", "Custom Dockerfile referenced")
            else:
                self.log_result(
                    "Cloud Build", "FAIL", "Custom Dockerfile not referenced"
                )

        except Exception as e:
            self.log_result(
                "Cloud Build", "FAIL", f"Error reading Cloud Build config: {e}"
            )

    def validate_docker_config(self):
        """Validate Docker configuration."""
        try:
            with open("Dockerfile.webscraping", "r") as f:
                content = f.read()

            if "playwright install chromium" in content:
                self.log_result(
                    "Docker Config",
                    "PASS",
                    "Playwright browser installation configured",
                )
            else:
                self.log_result(
                    "Docker Config", "WARN", "Playwright browser installation missing"
                )

            if "webscraping_app.py" in content:
                self.log_result(
                    "Docker Config", "PASS", "Application entry point configured"
                )
            else:
                self.log_result(
                    "Docker Config", "FAIL", "Application entry point missing"
                )

            if "USER webscraper" in content:
                self.log_result("Docker Config", "PASS", "Non-root user configured")
            else:
                self.log_result("Docker Config", "WARN", "Non-root user not configured")

        except Exception as e:
            self.log_result(
                "Docker Config", "FAIL", f"Error reading Docker config: {e}"
            )

    def validate_dependencies(self):
        """Validate Python dependencies."""
        try:
            with open("requirements-webscraping.txt", "r") as f:
                content = f.read()

            required_deps = [
                "playwright",
                "beautifulsoup4",
                "aiohttp",
                "openai",
                "sentence-transformers",
                "redis",
                "fastapi",
                "uvicorn",
            ]

            for dep in required_deps:
                if dep in content:
                    self.log_result("Dependencies", "PASS", f"{dep} included")
                else:
                    self.log_result("Dependencies", "WARN", f"{dep} missing")

        except Exception as e:
            self.log_result("Dependencies", "FAIL", f"Error reading requirements: {e}")

    def validate_environment_variables(self):
        """Validate environment variables configuration."""
        required_env_vars = [
            "REDIS_HOST",
            "ZENROWS_API_KEY",
            "APIFY_API_KEY",
            "OPENAI_API_KEY",
            "GOOGLE_CLOUD_PROJECT",
        ]

        # Check if environment variables are mentioned in config files
        config_files = [
            "cloudbuild.yaml",
            "infra/pulumi_gcp/__main__.py",
            "webscraping_app.py",
        ]

        for env_var in required_env_vars:
            found = False
            for config_file in config_files:
                try:
                    with open(config_file, "r") as f:
                        if env_var in f.read():
                            found = True
                            break
                except FileNotFoundError:
                    continue

            if found:
                self.log_result(
                    "Environment Variables", "PASS", f"{env_var} configured"
                )
            else:
                self.log_result(
                    "Environment Variables", "WARN", f"{env_var} not found in configs"
                )

    def run_gcp_checks(self):
        """Run GCP-specific validation checks."""
        try:
            # Check if gcloud is configured
            result = subprocess.run(
                ["gcloud", "config", "get-value", "project"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                project = result.stdout.strip()
                if project == self.project_id:
                    self.log_result(
                        "GCP Setup", "PASS", f"gcloud configured for project {project}"
                    )
                else:
                    self.log_result(
                        "GCP Setup",
                        "WARN",
                        f"gcloud configured for project {project}, expected {self.project_id}",
                    )
            else:
                self.log_result(
                    "GCP Setup", "FAIL", "gcloud not configured or not authenticated"
                )

        except subprocess.TimeoutExpired:
            self.log_result("GCP Setup", "FAIL", "gcloud command timed out")
        except FileNotFoundError:
            self.log_result("GCP Setup", "FAIL", "gcloud CLI not installed")
        except Exception as e:
            self.log_result("GCP Setup", "FAIL", f"Error checking gcloud: {e}")

    async def validate_service_health(self, service_url: Optional[str] = None):
        """Validate deployed service health."""
        if not service_url:
            # Try to get service URL from gcloud
            try:
                result = subprocess.run(
                    [
                        "gcloud",
                        "run",
                        "services",
                        "describe",
                        self.service_name,
                        "--region",
                        self.region,
                        "--format",
                        "value(status.url)",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    service_url = result.stdout.strip()
                else:
                    self.log_result(
                        "Service Health", "WARN", "Service not deployed yet"
                    )
                    return

            except Exception as e:
                self.log_result(
                    "Service Health", "WARN", f"Could not get service URL: {e}"
                )
                return

        # Test health endpoint
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(f"{service_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "healthy":
                            self.log_result(
                                "Service Health",
                                "PASS",
                                "Health endpoint responding correctly",
                            )
                        else:
                            self.log_result(
                                "Service Health",
                                "WARN",
                                f"Health endpoint status: {data.get('status')}",
                            )
                    else:
                        self.log_result(
                            "Service Health",
                            "FAIL",
                            f"Health endpoint returned {response.status}",
                        )

        except Exception as e:
            self.log_result(
                "Service Health", "WARN", f"Could not reach health endpoint: {e}"
            )

    async def validate_mcp_integration(self, service_url: Optional[str] = None):
        """Validate MCP integration."""
        if not service_url:
            return

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(f"{service_url}/mcp/tools") as response:
                    if response.status == 200:
                        data = await response.json()
                        tools = data.get("tools", [])
                        if (
                            len(tools) >= 5
                        ):  # Expected tools: web_search, scrape_website, analyze_content, bulk_scrape, get_task_status
                            self.log_result(
                                "MCP Integration",
                                "PASS",
                                f"MCP tools available: {len(tools)} tools",
                            )
                        else:
                            self.log_result(
                                "MCP Integration",
                                "WARN",
                                f"Only {len(tools)} MCP tools available",
                            )
                    else:
                        self.log_result(
                            "MCP Integration",
                            "FAIL",
                            f"MCP tools endpoint returned {response.status}",
                        )

        except Exception as e:
            self.log_result(
                "MCP Integration", "WARN", f"Could not test MCP integration: {e}"
            )

    def generate_report(self):
        """Generate validation report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "project": self.project_id,
            "region": self.region,
            "service": self.service_name,
            "results": self.validation_results,
            "summary": {
                "total_checks": len(self.validation_results),
                "passed": len(
                    [r for r in self.validation_results if r["status"] == "PASS"]
                ),
                "failed": len(
                    [r for r in self.validation_results if r["status"] == "FAIL"]
                ),
                "warnings": len(
                    [r for r in self.validation_results if r["status"] == "WARN"]
                ),
            },
        }

        # Save report
        report_file = f"webscraping_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, indent=2, fp=f)

        print(f"\n📊 Validation Report Saved: {report_file}")
        print(f"✅ Passed: {report['summary']['passed']}")
        print(f"❌ Failed: {report['summary']['failed']}")
        print(f"⚠️  Warnings: {report['summary']['warnings']}")

        return report

    async def run_all_validations(self, service_url: Optional[str] = None):
        """Run all validation checks."""
        print("🔍 Starting Web Scraping AI Agent System Validation...")
        print("=" * 60)

        # File and configuration validations
        self.validate_files_exist()
        self.validate_pulumi_config()
        self.validate_cloudbuild_config()
        self.validate_docker_config()
        self.validate_dependencies()
        self.validate_environment_variables()

        # GCP validations
        self.run_gcp_checks()

        # Service validations (if deployed)
        await self.validate_service_health(service_url)
        await self.validate_mcp_integration(service_url)

        print("=" * 60)

        # Generate report
        report = self.generate_report()

        # Return overall status
        failed_checks = report["summary"]["failed"]
        if failed_checks == 0:
            print("🎉 All critical validations passed! System is ready for deployment.")
            return True
        else:
            print(
                f"⚠️  {failed_checks} critical issues found. Please address before deployment."
            )
            return False


async def main():
    """Main validation function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate Web Scraping AI Agent System deployment"
    )
    parser.add_argument(
        "--service-url", help="URL of deployed service for live testing"
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")

    args = parser.parse_args()

    validator = WebScrapingDeploymentValidator()
    success = await validator.run_all_validations(args.service_url)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
