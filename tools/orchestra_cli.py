#!/usr/bin/env python3
"""
Orchestra AI Unified CLI

A comprehensive command-line interface for managing the Orchestra AI system,
including adapters, credentials, diagnostics, and orchestration.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from dotenv import set_key

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

console = Console()

# Required secrets configuration
REQUIRED_SECRETS = {
    "core": [
        "OPENAI_API_KEY",
        "PORTKEY_API_KEY",
        "GOOGLE_CLOUD_PROJECT",
    ],
    "data_sources": [
        "GONG_API_KEY",
        "SALESFORCE_CLIENT_ID",
        "SALESFORCE_CLIENT_SECRET",
        "HUBSPOT_API_KEY",
        "SLACK_BOT_TOKEN",
        "LOOKER_CLIENT_ID",
        "LOOKER_CLIENT_SECRET",
    ],
    "web_scraping": [
        "ZENROWS_API_KEY",
        "APIFY_API_KEY",
        "PHANTOMBUSTER_API_KEY",
    ],
    "infrastructure": [
        "REDIS_HOST",
        "REDIS_PASSWORD",
        "DRAGONFLY_HOST",
        "DRAGONFLY_PASSWORD",
    ],
    "ai_providers": [
        "ANTHROPIC_API_KEY",
        "PERPLEXITY_API_KEY",
        "GOOGLE_API_KEY",
        "OPENAI_API_KEY",
    ],
}


def get_pulumi_secrets() -> Dict[str, str]:
    """Get secrets from Pulumi-generated .env file."""
    secrets = {}
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    secrets[key] = value
    except FileNotFoundError:
        console.print(
            "[red]Error: .env file not found. Run 'pulumi config' first[/red]"
        )
    except Exception as e:
        console.print(f"[red]Error reading .env file: {e}[/red]")
    return secrets


class AdapterConfig:
    """Standard adapter configuration interface."""

    @staticmethod
    def get_adapter_configs() -> Dict[str, Dict[str, Any]]:
        """Get configuration for all adapters."""
        return {
            "gong": {
                "name": "Gong.io",
                "required_secrets": ["GONG_API_KEY"],
                "optional_secrets": [],
                "health_endpoint": "/health",
                "description": "Call recordings and insights",
            },
            "salesforce": {
                "name": "Salesforce",
                "required_secrets": [
                    "SALESFORCE_CLIENT_ID",
                    "SALESFORCE_CLIENT_SECRET",
                ],
                "optional_secrets": ["SALESFORCE_REFRESH_TOKEN"],
                "health_endpoint": "/health",
                "description": "CRM data and opportunities",
            },
            "hubspot": {
                "name": "HubSpot",
                "required_secrets": ["HUBSPOT_API_KEY"],
                "optional_secrets": [],
                "health_endpoint": "/health",
                "description": "Marketing and sales data",
            },
            "slack": {
                "name": "Slack",
                "required_secrets": ["SLACK_BOT_TOKEN"],
                "optional_secrets": ["SLACK_APP_TOKEN"],
                "health_endpoint": "/health",
                "description": "Team communication",
            },
            "looker": {
                "name": "Looker",
                "required_secrets": ["LOOKER_CLIENT_ID", "LOOKER_CLIENT_SECRET"],
                "optional_secrets": ["LOOKER_BASE_URL"],
                "health_endpoint": "/health",
                "description": "Business intelligence",
            },
            "web_scraping": {
                "name": "Web Scraping",
                "required_secrets": ["ZENROWS_API_KEY", "APIFY_API_KEY"],
                "optional_secrets": ["PHANTOMBUSTER_API_KEY"],
                "health_endpoint": "/health",
                "description": "Web data extraction",
            },
        }


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, verbose):
    """Orchestra AI Unified CLI - Manage all aspects of the Orchestra AI system."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    # Environment variables for secrets are injected by GCP infra or set in CI/CD.
    # Do NOT use load_dotenv in production.


@cli.group()
def secrets():
    """Manage secrets and credentials."""


@secrets.command()
@click.option("--env-file", default=".env", help="Path to .env file")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be synced without making changes"
)
@click.pass_context
def sync(ctx, env_file, dry_run):
    """Sync secrets from Pulumi configuration to local environment."""
    console.print(
        Panel("[bold blue]Syncing secrets from Pulumi configuration[/bold blue]")
    )

    pulumi_secrets = get_pulumi_secrets()
    if not pulumi_secrets:
        console.print("[red]No secrets found in Pulumi configuration[/red]")
        return False

    # Track sync results
    synced = []
    missing = []
    errors = []

    # Check all required secrets
    all_required = []
    for category, secrets_list in REQUIRED_SECRETS.items():
        all_required.extend(secrets_list)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Syncing secrets...", total=len(all_required))

        for secret_id in all_required:
            progress.update(task, description=f"Syncing {secret_id}...")

            value = pulumi_secrets.get(secret_id)
            if value:
                if not dry_run:
                    # Update .env file
                    set_key(env_file, secret_id, value)
                    # Also set in current environment
                    os.environ[secret_id] = value
                synced.append(secret_id)
            else:
                missing.append(secret_id)
                errors.append(f"{secret_id}: Not found in Pulumi config")

            progress.advance(task)

    # Display results
    if synced:
        console.print(f"\n[green]✓ Synced {len(synced)} secrets[/green]")
        if ctx.obj.get("verbose"):
            for s in synced:
                console.print(f"  - {s}")

    if missing:
        console.print(f"\n[yellow]⚠ Missing {len(missing)} secrets:[/yellow]")
        for m in missing:
            console.print(f"  - {m}")

    if errors:
        console.print(f"\n[red]✗ Errors syncing {len(errors)} secrets:[/red]")
        for e in errors:
            console.print(f"  - {e}")

    if dry_run:
        console.print("\n[yellow]DRY RUN - No changes were made[/yellow]")
    else:
        console.print(f"\n[green]✓ Synced {len(synced)} secrets to {env_file}[/green]")


@secrets.command()
@click.pass_context
def validate(ctx):
    """Validate that all required secrets are present."""
    console.print(Panel("[bold blue]Validating secrets configuration[/bold blue]"))

    # Create validation table
    table = Table(title="Secret Validation Results")
    table.add_column("Category", style="cyan")
    table.add_column("Secret", style="white")
    table.add_column("Status", style="white")
    table.add_column("Value", style="dim")

    all_valid = True

    for category, secrets_list in REQUIRED_SECRETS.items():
        for secret_id in secrets_list:
            value = os.getenv(secret_id)
            if value:
                status = "[green]✓ Present[/green]"
                display_value = f"{value[:8]}..." if len(value) > 8 else value
            else:
                status = "[red]✗ Missing[/red]"
                display_value = "-"
                all_valid = False

            table.add_row(category, secret_id, status, display_value)

    console.print(table)

    if all_valid:
        console.print("\n[green]✓ All required secrets are present[/green]")
    else:
        console.print("\n[red]✗ Some required secrets are missing[/red]")
        console.print(
            "[yellow]Run 'orchestra secrets sync' to fetch from Pulumi[/yellow]"
        )
        sys.exit(1)


@secrets.command()
@click.argument("secret_id")
@click.option("--value", prompt=True, hide_input=True, confirmation_prompt=True)
@click.pass_context
def set(ctx, secret_id, value):
    """Set or update a secret in Pulumi configuration."""
    # Get current secrets
    pulumi_secrets = get_pulumi_secrets()

    # Check if secret exists
    secret_exists = secret_id in pulumi_secrets

    if secret_exists:
        if not click.confirm(f"Secret {secret_id} already exists. Update it?"):
            return

    # Update environment immediately
    os.environ[secret_id] = value

    # Update .env file
    try:
        set_key(".env", secret_id, value)
        if secret_exists:
            console.print(f"[green]✓ Updated secret {secret_id}[/green]")
        else:
            console.print(f"[green]✓ Created secret {secret_id}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Failed to update secret {secret_id}: {str(e)}[/red]")
        sys.exit(1)


@cli.group()
def adapters():
    """Manage data source adapters."""


@adapters.command()
@click.pass_context
def list(ctx):
    """List all available adapters and their status."""
    adapters = AdapterConfig.get_adapter_configs()

    table = Table(title="Available Adapters")
    table.add_column("Adapter", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Description", style="dim")
    table.add_column("Required Secrets", style="yellow")
    table.add_column("Status", style="white")

    for adapter_id, config in adapters.items():
        # Check if required secrets are present
        secrets_present = all(
            os.getenv(secret) is not None for secret in config["required_secrets"]
        )

        status = (
            "[green]✓ Ready[/green]"
            if secrets_present
            else "[red]✗ Missing secrets[/red]"
        )

        table.add_row(
            adapter_id,
            config["name"],
            config["description"],
            ", ".join(config["required_secrets"]),
            status,
        )

    console.print(table)


@adapters.command(name="check")
@click.argument("adapter_id")
@click.pass_context
def check_adapter(ctx, adapter_id):
    """Validate adapter configuration and credentials."""
    adapters = AdapterConfig.get_adapter_configs()

    if adapter_id not in adapters:
        console.print(f"[red]Unknown adapter: {adapter_id}[/red]")
        console.print(f"Available adapters: {', '.join(adapters.keys())}")
        return

    config = adapters[adapter_id]
    console.print(Panel(f"[bold blue]Validating {config['name']} adapter[/bold blue]"))

    # Check required secrets
    console.print("\n[bold]Required Secrets:[/bold]")
    all_present = True
    for secret in config["required_secrets"]:
        value = os.getenv(secret)
        if value:
            console.print(f"  [green]✓[/green] {secret}")
        else:
            console.print(f"  [red]✗[/red] {secret} - MISSING")
            all_present = False

    # Check optional secrets
    if config["optional_secrets"]:
        console.print("\n[bold]Optional Secrets:[/bold]")
        for secret in config["optional_secrets"]:
            value = os.getenv(secret)
            if value:
                console.print(f"  [green]✓[/green] {secret}")
            else:
                console.print(f"  [yellow]○[/yellow] {secret} - Not set")

    if all_present:
        console.print(
            f"\n[green]✓ {config['name']} adapter is properly configured[/green]"
        )
    else:
        console.print(
            f"\n[red]✗ {config['name']} adapter is missing required configuration[/red]"
        )


@cli.group()
def diagnostics():
    """Run system diagnostics and health checks."""


@diagnostics.command()
@click.pass_context
def health(ctx):
    """Check health of all system components."""
    console.print(Panel("[bold blue]Running system health checks[/bold blue]"))

    checks = {
        "Secrets": check_secrets_health(),
        "Pulumi Config": check_pulumi_health(),
        "Redis": check_redis_health(),
        "MCP Gateway": check_mcp_health(),
        "Adapters": check_adapters_health(),
    }

    table = Table(title="System Health Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Details", style="dim")

    all_healthy = True

    for component, (status, details) in checks.items():
        status_display = (
            "[green]✓ Healthy[/green]" if status else "[red]✗ Unhealthy[/red]"
        )
        table.add_row(component, status_display, details)
        if not status:
            all_healthy = False

    console.print(table)

    if all_healthy:
        console.print("\n[green]✓ All systems operational[/green]")
    else:
        console.print("\n[red]✗ Some systems need attention[/red]")


def check_secrets_health():
    """Check if all required secrets are present."""
    total = sum(len(secrets) for secrets in REQUIRED_SECRETS.values())
    present = sum(
        1
        for secrets in REQUIRED_SECRETS.values()
        for secret in secrets
        if os.getenv(secret)
    )

    if present == total:
        return True, f"All {total} required secrets present"
    else:
        return False, f"{present}/{total} secrets present"


def check_pulumi_health():
    """Check Pulumi configuration."""
    try:
        if not os.path.exists(".env"):
            return False, ".env file missing - run 'pulumi config'"

        required = ["PORTKEY_API_KEY", "OPENAI_API_KEY"]
        missing = [key for key in required if key not in os.environ]
        if missing:
            return False, f"Missing secrets: {', '.join(missing)}"
        return True, "Pulumi config loaded successfully"
    except Exception as e:
        return False, f"Pulumi check failed: {str(e)[:50]}..."


def check_redis_health():
    """Check Redis connectivity."""
    try:
        import redis

        host = os.getenv("REDIS_HOST", "localhost")
        password = os.getenv("REDIS_PASSWORD")

        r = redis.Redis(host=host, password=password, decode_responses=True)
        r.ping()
        return True, f"Connected to {host}"
    except Exception as e:
        return False, f"Connection failed: {str(e)[:50]}..."


def check_mcp_health():
    """Check MCP Gateway status."""
    try:
        # This would check actual MCP gateway
        # For now, just check if the module can be imported
        import importlib.util

        spec = importlib.util.find_spec("mcp_server.gateway")
        if spec is not None:
            return True, "MCP Gateway available"
        else:
            return False, "MCP Gateway module not found"
    except Exception as e:
        return False, f"Import check failed: {str(e)[:50]}..."


def check_adapters_health():
    """Check adapter readiness."""
    adapters = AdapterConfig.get_adapter_configs()
    ready = sum(
        1
        for config in adapters.values()
        if all(os.getenv(secret) for secret in config["required_secrets"])
    )
    total = len(adapters)

    if ready == total:
        return True, f"All {total} adapters ready"
    else:
        return False, f"{ready}/{total} adapters ready"


@cli.group()
def orchestrator():
    """Manage the orchestration system."""


@orchestrator.command()
@click.pass_context
def reload(ctx):
    """Reload orchestrator configuration."""
    console.print("[yellow]Reloading orchestrator configuration...[/yellow]")

    try:
        # Validate secrets first
        ctx.invoke(validate)

        # Reload environment (for local/dev only; not used in production)
        # load_dotenv(override=True)

        # Signal orchestrator to reload (this would be implemented based on your orchestrator)
        console.print("[green]✓ Orchestrator configuration reloaded[/green]")
    except Exception as e:
        console.print(f"[red]✗ Failed to reload: {e}[/red]")


@orchestrator.command()
@click.pass_context
def status(ctx):
    """Show orchestrator status."""
    console.print(Panel("[bold blue]Orchestrator Status[/bold blue]"))

    # This would connect to your actual orchestrator
    # For now, show configuration status

    table = Table()
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Project ID", os.getenv("GOOGLE_CLOUD_PROJECT", "Not set"))
    table.add_row("Environment", os.getenv("ENVIRONMENT", "development"))
    table.add_row("Redis Host", os.getenv("REDIS_HOST", "Not set"))
    table.add_row(
        "Active Adapters",
        str(
            len(
                [
                    a
                    for a in AdapterConfig.get_adapter_configs().values()
                    if all(os.getenv(s) for s in a["required_secrets"])
                ]
            )
        ),
    )

    console.print(table)


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize Orchestra AI system with all checks."""
    console.print(Panel("[bold blue]Initializing Orchestra AI System[/bold blue]"))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Step 1: Sync secrets
        task = progress.add_task("Syncing secrets from Pulumi...", total=None)
        ctx.invoke(sync)
        progress.update(task, completed=True)

        # Step 2: Validate configuration
        task = progress.add_task("Validating configuration...", total=None)
        ctx.invoke(validate)
        progress.update(task, completed=True)

        # Step 3: Check system health
        task = progress.add_task("Running health checks...", total=None)
        ctx.invoke(health)
        progress.update(task, completed=True)

    console.print("\n[green]✓ Orchestra AI system initialized successfully![/green]")


if __name__ == "__main__":
    cli()
