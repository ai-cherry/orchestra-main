#!/usr/bin/env python3
"""
Orchestra AI Deployment Validation Script

Comprehensive validation of the entire Orchestra AI system including:
- Infrastructure components
- Service health
- Secret configuration
- Integration points
- Security settings
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Tuple

import requests
from google.api_core import exceptions as gcp_exceptions
from google.cloud import monitoring_v3, pubsub_v1, secretmanager, servicedirectory_v1
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "cherry-ai-project")
REGION = "us-central1"

# Services to validate
SERVICES = {
    "ai-orchestra-minimal": {
        "type": "orchestrator",
        "health_endpoint": "/health",
        "required": True,
    },
    "web-scraping-agents": {
        "type": "webscraping",
        "health_endpoint": "/health",
        "required": True,
    },
    "admin-interface": {"type": "admin", "health_endpoint": "/", "required": False},
}

# Required secrets by service type
REQUIRED_SECRETS = {
    "orchestrator": [
        "OPENAI_API_KEY",
        "PORTKEY_API_KEY",
        "REDIS_HOST",
        "REDIS_PASSWORD",
    ],
    "webscraping": [
        "ZENROWS_API_KEY",
        "APIFY_API_KEY",
        "OPENAI_API_KEY",
        "REDIS_HOST",
    ],
    "admin": [],
}

# Pub/Sub topics to validate
PUBSUB_TOPICS = ["mcp-events", "web-scraping-events", "mcp-dead-letter"]

console = Console()


class ValidationResult:
    """Result of a validation check."""

    def __init__(self, component: str, check: str, passed: bool, details: str = ""):
        self.component = component
        self.check = check
        self.passed = passed
        self.details = details
        self.timestamp = datetime.utcnow()


class OrchestraValidator:
    """Validates Orchestra AI deployment."""

    def __init__(self):
        self.results: List[ValidationResult] = []
        self.secret_client = secretmanager.SecretManagerServiceClient()
        self.pubsub_client = pubsub_v1.PublisherClient()
        self.sd_client = servicedirectory_v1.RegistrationServiceClient()
        self.monitoring_client = monitoring_v3.MetricServiceClient()

    async def validate_all(self) -> Tuple[int, int]:
        """Run all validation checks."""
        console.print(
            Panel(
                "[bold blue]Orchestra AI Deployment Validation[/bold blue]\n"
                f"Project: {PROJECT_ID}\n"
                f"Region: {REGION}",
                title="Starting Validation",
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Infrastructure checks
            task = progress.add_task("Validating infrastructure...", total=None)
            await self.validate_infrastructure()
            progress.update(task, completed=True)

            # Service checks
            task = progress.add_task("Validating services...", total=None)
            await self.validate_services()
            progress.update(task, completed=True)

            # Secret checks
            task = progress.add_task("Validating secrets...", total=None)
            await self.validate_secrets()
            progress.update(task, completed=True)

            # Integration checks
            task = progress.add_task("Validating integrations...", total=None)
            await self.validate_integrations()
            progress.update(task, completed=True)

            # Security checks
            task = progress.add_task("Validating security...", total=None)
            await self.validate_security()
            progress.update(task, completed=True)

        # Display results
        self.display_results()

        # Return pass/fail counts
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)

        return passed, failed

    async def validate_infrastructure(self):
        """Validate GCP infrastructure components."""
        # Check VPC
        try:
            result = subprocess.run(
                [
                    "gcloud",
                    "compute",
                    "networks",
                    "describe",
                    "orchestra-vpc",
                    "--project",
                    PROJECT_ID,
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            _ = json.loads(result.stdout)  # Validate JSON but don't need the data
            self.results.append(
                ValidationResult(
                    "Infrastructure", "VPC Network", True, "VPC 'orchestra-vpc' exists"
                )
            )
        except subprocess.CalledProcessError:
            self.results.append(
                ValidationResult(
                    "Infrastructure",
                    "VPC Network",
                    False,
                    "VPC 'orchestra-vpc' not found",
                )
            )

        # Check Redis
        try:
            result = subprocess.run(
                [
                    "gcloud",
                    "redis",
                    "instances",
                    "describe",
                    "orchestra-redis",
                    "--region",
                    REGION,
                    "--project",
                    PROJECT_ID,
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            redis_data = json.loads(result.stdout)
            status = redis_data.get("state", "UNKNOWN")
            self.results.append(
                ValidationResult(
                    "Infrastructure",
                    "Redis Instance",
                    status == "READY",
                    f"Redis status: {status}",
                )
            )
        except subprocess.CalledProcessError:
            self.results.append(
                ValidationResult(
                    "Infrastructure",
                    "Redis Instance",
                    False,
                    "Redis instance not found",
                )
            )

        # Check Artifact Registry
        try:
            result = subprocess.run(
                [
                    "gcloud",
                    "artifacts",
                    "repositories",
                    "describe",
                    "orchestra-repo",
                    "--location",
                    REGION,
                    "--project",
                    PROJECT_ID,
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            self.results.append(
                ValidationResult(
                    "Infrastructure",
                    "Artifact Registry",
                    True,
                    "Repository 'orchestra-repo' exists",
                )
            )
        except subprocess.CalledProcessError:
            self.results.append(
                ValidationResult(
                    "Infrastructure", "Artifact Registry", False, "Repository not found"
                )
            )

        # Check Service Directory namespace
        try:
            namespace_path = (
                f"projects/{PROJECT_ID}/locations/{REGION}/namespaces/orchestra-ai"
            )
            _ = self.sd_client.get_namespace(
                name=namespace_path
            )  # Just checking existence
            self.results.append(
                ValidationResult(
                    "Infrastructure",
                    "Service Directory",
                    True,
                    "Namespace 'orchestra-ai' exists",
                )
            )
        except gcp_exceptions.NotFound:
            self.results.append(
                ValidationResult(
                    "Infrastructure",
                    "Service Directory",
                    False,
                    "Namespace 'orchestra-ai' not found",
                )
            )

        # Check Pub/Sub topics
        for topic_id in PUBSUB_TOPICS:
            try:
                _ = self.pubsub_client.topic_path(PROJECT_ID, topic_id)  # Build path
                # Try to get the topic
                subprocess.run(
                    [
                        "gcloud",
                        "pubsub",
                        "topics",
                        "describe",
                        topic_id,
                        "--project",
                        PROJECT_ID,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self.results.append(
                    ValidationResult(
                        "Infrastructure",
                        f"Pub/Sub Topic '{topic_id}'",
                        True,
                        "Topic exists",
                    )
                )
            except subprocess.CalledProcessError:
                self.results.append(
                    ValidationResult(
                        "Infrastructure",
                        f"Pub/Sub Topic '{topic_id}'",
                        False,
                        "Topic not found",
                    )
                )

    async def validate_services(self):
        """Validate Cloud Run services."""
        for service_name, config in SERVICES.items():
            # Check if service exists
            try:
                result = subprocess.run(
                    [
                        "gcloud",
                        "run",
                        "services",
                        "describe",
                        service_name,
                        "--region",
                        REGION,
                        "--project",
                        PROJECT_ID,
                        "--format",
                        "json",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                service_data = json.loads(result.stdout)

                # Get service URL
                service_url = service_data.get("status", {}).get("url")
                if not service_url:
                    self.results.append(
                        ValidationResult(
                            "Services",
                            f"{service_name} deployment",
                            False,
                            "No URL found",
                        )
                    )
                    continue

                self.results.append(
                    ValidationResult(
                        "Services",
                        f"{service_name} deployment",
                        True,
                        f"Deployed at {service_url}",
                    )
                )

                # Check health endpoint
                health_url = f"{service_url}{config['health_endpoint']}"
                try:
                    # Get identity token for authenticated request
                    token_result = subprocess.run(
                        ["gcloud", "auth", "print-identity-token"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    token = token_result.stdout.strip()

                    response = requests.get(
                        health_url,
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=30,
                    )

                    if response.status_code == 200:
                        self.results.append(
                            ValidationResult(
                                "Services",
                                f"{service_name} health",
                                True,
                                "Service is healthy",
                            )
                        )
                    else:
                        self.results.append(
                            ValidationResult(
                                "Services",
                                f"{service_name} health",
                                False,
                                f"Health check returned {response.status_code}",
                            )
                        )
                except Exception as e:
                    self.results.append(
                        ValidationResult(
                            "Services",
                            f"{service_name} health",
                            False,
                            f"Health check failed: {str(e)}",
                        )
                    )

                # Check service account
                sa_email = (
                    service_data.get("spec", {})
                    .get("template", {})
                    .get("spec", {})
                    .get("serviceAccountName")
                )
                if sa_email:
                    expected_sa = f"orchestra-{config['type']}-sa@{PROJECT_ID}.iam.gserviceaccount.com"
                    self.results.append(
                        ValidationResult(
                            "Services",
                            f"{service_name} service account",
                            sa_email == expected_sa,
                            f"Using: {sa_email}",
                        )
                    )

            except subprocess.CalledProcessError:
                if config["required"]:
                    self.results.append(
                        ValidationResult(
                            "Services",
                            f"{service_name} deployment",
                            False,
                            "Service not found (required)",
                        )
                    )
                else:
                    self.results.append(
                        ValidationResult(
                            "Services",
                            f"{service_name} deployment",
                            True,
                            "Service not deployed (optional)",
                        )
                    )

    async def validate_secrets(self):
        """Validate required secrets exist."""
        all_secrets = set()
        for service_type, secrets in REQUIRED_SECRETS.items():
            all_secrets.update(secrets)

        for secret_id in all_secrets:
            try:
                secret_path = (
                    f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
                )
                self.secret_client.access_secret_version(request={"name": secret_path})
                self.results.append(
                    ValidationResult(
                        "Secrets",
                        f"Secret '{secret_id}'",
                        True,
                        "Secret exists and accessible",
                    )
                )
            except gcp_exceptions.NotFound:
                self.results.append(
                    ValidationResult(
                        "Secrets", f"Secret '{secret_id}'", False, "Secret not found"
                    )
                )
            except Exception as e:
                self.results.append(
                    ValidationResult(
                        "Secrets",
                        f"Secret '{secret_id}'",
                        False,
                        f"Error accessing secret: {str(e)}",
                    )
                )

    async def validate_integrations(self):
        """Validate service integrations."""
        # Check Service Directory registrations
        try:
            namespace_path = (
                f"projects/{PROJECT_ID}/locations/{REGION}/namespaces/orchestra-ai"
            )
            services = self.sd_client.list_services(parent=namespace_path)

            registered_services = []
            for service in services:
                service_name = service.name.split("/")[-1]
                registered_services.append(service_name)

            self.results.append(
                ValidationResult(
                    "Integrations",
                    "Service Directory registrations",
                    len(registered_services) > 0,
                    f"Found {len(registered_services)} registered services",
                )
            )
        except Exception as e:
            self.results.append(
                ValidationResult(
                    "Integrations",
                    "Service Directory registrations",
                    False,
                    f"Failed to check: {str(e)}",
                )
            )

        # Check monitoring dashboard
        try:
            result = subprocess.run(
                [
                    "gcloud",
                    "monitoring",
                    "dashboards",
                    "list",
                    "--project",
                    PROJECT_ID,
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            dashboards = json.loads(result.stdout)
            orchestra_dashboard = any(
                d.get("displayName") == "Orchestra AI Dashboard" for d in dashboards
            )
            self.results.append(
                ValidationResult(
                    "Integrations",
                    "Monitoring Dashboard",
                    orchestra_dashboard,
                    (
                        "Dashboard exists"
                        if orchestra_dashboard
                        else "Dashboard not found"
                    ),
                )
            )
        except Exception:
            self.results.append(
                ValidationResult(
                    "Integrations",
                    "Monitoring Dashboard",
                    False,
                    "Failed to check dashboards",
                )
            )

        # Check alert policies
        try:
            result = subprocess.run(
                [
                    "gcloud",
                    "alpha",
                    "monitoring",
                    "policies",
                    "list",
                    "--project",
                    PROJECT_ID,
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            policies = json.loads(result.stdout)
            policy_names = [p.get("displayName", "") for p in policies]

            expected_policies = ["High Error Rate Alert", "High Memory Usage Alert"]
            found_policies = [p for p in expected_policies if p in policy_names]

            self.results.append(
                ValidationResult(
                    "Integrations",
                    "Alert Policies",
                    len(found_policies) == len(expected_policies),
                    f"Found {len(found_policies)}/{len(expected_policies)} policies",
                )
            )
        except Exception:
            self.results.append(
                ValidationResult(
                    "Integrations",
                    "Alert Policies",
                    False,
                    "Failed to check alert policies",
                )
            )

    async def validate_security(self):
        """Validate security configurations."""
        # Check service accounts exist
        service_accounts = [
            "orchestra-orchestrator-sa",
            "orchestra-webscraping-sa",
            "orchestra-admin-sa",
            "cicd-sa",
        ]

        for sa_name in service_accounts:
            sa_email = f"{sa_name}@{PROJECT_ID}.iam.gserviceaccount.com"
            try:
                result = subprocess.run(
                    [
                        "gcloud",
                        "iam",
                        "service-accounts",
                        "describe",
                        sa_email,
                        "--project",
                        PROJECT_ID,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self.results.append(
                    ValidationResult(
                        "Security",
                        f"Service Account '{sa_name}'",
                        True,
                        "Service account exists",
                    )
                )
            except subprocess.CalledProcessError:
                self.results.append(
                    ValidationResult(
                        "Security",
                        f"Service Account '{sa_name}'",
                        False,
                        "Service account not found",
                    )
                )

        # Check Workload Identity Federation
        try:
            result = subprocess.run(
                [
                    "gcloud",
                    "iam",
                    "workload-identity-pools",
                    "describe",
                    "github-wif-pool",
                    "--location",
                    "global",
                    "--project",
                    PROJECT_ID,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            self.results.append(
                ValidationResult(
                    "Security",
                    "Workload Identity Pool",
                    True,
                    "GitHub WIF pool configured",
                )
            )
        except subprocess.CalledProcessError:
            self.results.append(
                ValidationResult(
                    "Security",
                    "Workload Identity Pool",
                    False,
                    "GitHub WIF pool not found",
                )
            )

        # Check Redis encryption
        try:
            result = subprocess.run(
                [
                    "gcloud",
                    "redis",
                    "instances",
                    "describe",
                    "orchestra-redis",
                    "--region",
                    REGION,
                    "--project",
                    PROJECT_ID,
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            redis_data = json.loads(result.stdout)
            encryption_mode = redis_data.get("transitEncryptionMode", "DISABLED")
            self.results.append(
                ValidationResult(
                    "Security",
                    "Redis Encryption",
                    encryption_mode == "SERVER_AUTHENTICATION",
                    f"Transit encryption: {encryption_mode}",
                )
            )
        except Exception:
            self.results.append(
                ValidationResult(
                    "Security",
                    "Redis Encryption",
                    False,
                    "Failed to check Redis encryption",
                )
            )

    def display_results(self):
        """Display validation results in a table."""
        # Group results by component
        components: Dict[str, List[ValidationResult]] = {}
        for result in self.results:
            if result.component not in components:
                components[result.component] = []
            components[result.component].append(result)

        # Create summary table
        summary_table = Table(title="Validation Summary")
        summary_table.add_column("Component", style="cyan")
        summary_table.add_column("Passed", style="green")
        summary_table.add_column("Failed", style="red")
        summary_table.add_column("Total", style="white")

        total_passed = 0
        total_failed = 0

        for component, results in components.items():
            passed = sum(1 for r in results if r.passed)
            failed = sum(1 for r in results if not r.passed)
            total = len(results)

            summary_table.add_row(component, str(passed), str(failed), str(total))

            total_passed += passed
            total_failed += failed

        summary_table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold]{total_passed}[/bold]",
            f"[bold]{total_failed}[/bold]",
            f"[bold]{total_passed + total_failed}[/bold]",
        )

        console.print("\n")
        console.print(summary_table)

        # Show failed checks
        if total_failed > 0:
            console.print("\n[red]Failed Checks:[/red]")
            failed_table = Table()
            failed_table.add_column("Component", style="cyan")
            failed_table.add_column("Check", style="white")
            failed_table.add_column("Details", style="yellow")

            for result in self.results:
                if not result.passed:
                    failed_table.add_row(result.component, result.check, result.details)

            console.print(failed_table)

        # Overall status
        console.print("\n")
        if total_failed == 0:
            console.print(
                Panel(
                    "[bold green]✓ All validation checks passed![/bold green]\n"
                    "Orchestra AI system is properly deployed and configured.",
                    title="Validation Success",
                )
            )
        else:
            console.print(
                Panel(
                    f"[bold red]✗ {total_failed} validation checks failed[/bold red]\n"
                    "Please address the issues above before proceeding.",
                    title="Validation Failed",
                )
            )


async def main():
    """Main entry point."""
    validator = OrchestraValidator()

    try:
        passed, failed = await validator.validate_all()

        # Exit with appropriate code
        sys.exit(0 if failed == 0 else 1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Validation interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Validation error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    # Check if running in GCP environment
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and not os.getenv(
        "GOOGLE_CLOUD_PROJECT"
    ):
        console.print(
            "[yellow]Warning: No GCP credentials detected. Ensure you're authenticated with gcloud.[/yellow]"
        )

    asyncio.run(main())
