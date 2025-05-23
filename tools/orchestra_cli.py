#!/usr/bin/env python3
"""
Orchestra AI Unified CLI

A comprehensive command-line interface for managing the Orchestra AI system,
including adapters, credentials, diagnostics, and orchestration.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from google.cloud import secretmanager
from google.api_core import exceptions as gcp_exceptions
from dotenv import load_dotenv, set_key

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
        "VERTEX_API_KEY",
    ],
}

class SecretManager:
    """Handles GCP Secret Manager operations."""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.client = secretmanager.SecretManagerServiceClient()
        self.parent = f"projects/{project_id}"
    
    def list_secrets(self) -> List[str]:
        """List all secret IDs in the project."""
        secrets = []
        try:
            for secret in self.client.list_secrets(request={"parent": self.parent}):
                secret_id = secret.name.split("/")[-1]
                secrets.append(secret_id)
        except Exception as e:
            console.print(f"[red]Error listing secrets: {e}[/red]")
        return secrets
    
    def get_secret(self, secret_id: str) -> Optional[str]:
        """Get the latest version of a secret."""
        try:
            name = f"{self.parent}/secrets/{secret_id}/versions/latest"
            response = self.client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except gcp_exceptions.NotFound:
            return None
        except Exception as e:
            console.print(f"[red]Error accessing secret {secret_id}: {e}[/red]")
            return None
    
    def create_secret(self, secret_id: str, value: str) -> bool:
        """Create a new secret."""
        try:
            # Create the secret
            secret = self.client.create_secret(
                request={
                    "parent": self.parent,
                    "secret_id": secret_id,
                    "secret": {"replication": {"automatic": {}}},
                }
            )
            
            # Add secret version
            self.client.add_secret_version(
                request={
                    "parent": secret.name,
                    "payload": {"data": value.encode("UTF-8")},
                }
            )
            return True
        except Exception as e:
            console.print(f"[red]Error creating secret {secret_id}: {e}[/red]")
            return False
    
    def update_secret(self, secret_id: str, value: str) -> bool:
        """Update an existing secret by adding a new version."""
        try:
            secret_name = f"{self.parent}/secrets/{secret_id}"
            self.client.add_secret_version(
                request={
                    "parent": secret_name,
                    "payload": {"data": value.encode("UTF-8")},
                }
            )
            return True
        except Exception as e:
            console.print(f"[red]Error updating secret {secret_id}: {e}[/red]")
            return False

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
                "required_secrets": ["SALESFORCE_CLIENT_ID", "SALESFORCE_CLIENT_SECRET"],
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
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """Orchestra AI Unified CLI - Manage all aspects of the Orchestra AI system."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    # Load environment
    load_dotenv()

@cli.group()
def secrets():
    """Manage secrets and credentials."""

@secrets.command()
@click.option('--env-file', default='.env', help='Path to .env file')
@click.option('--dry-run', is_flag=True, help='Show what would be synced without making changes')
@click.pass_context
def sync(ctx, env_file, dry_run):
    """Sync secrets from GCP Secret Manager to local environment."""
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'cherry-ai-project')
    
    console.print(Panel(f"[bold blue]Syncing secrets from GCP project: {project_id}[/bold blue]"))
    
    secret_manager = SecretManager(project_id)
    
    # Get all secrets from GCP
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching secrets from GCP...", total=None)
        gcp_secrets = secret_manager.list_secrets()
        progress.update(task, completed=True)
    
    console.print(f"[green]Found {len(gcp_secrets)} secrets in GCP[/green]")
    
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
            
            if secret_id in gcp_secrets:
                value = secret_manager.get_secret(secret_id)
                if value:
                    if not dry_run:
                        # Update .env file
                        set_key(env_file, secret_id, value)
                        # Also set in current environment
                        os.environ[secret_id] = value
                    synced.append(secret_id)
                else:
                    errors.append(f"{secret_id}: Failed to fetch value")
            else:
                missing.append(secret_id)
            
            progress.advance(task)
    
    # Display results
    if synced:
        console.print(f"\n[green]✓ Synced {len(synced)} secrets[/green]")
        if ctx.obj.get('verbose'):
            for s in synced:
                console.print(f"  - {s}")
    
    if missing:
        console.print(f"\n[yellow]⚠ Missing {len(missing)} secrets in GCP:[/yellow]")
        for m in missing:
            console.print(f"  - {m}")
    
    if errors:
        console.print(f"\n[red]✗ Errors syncing {len(errors)} secrets:[/red]")
        for e in errors:
            console.print(f"  - {e}")
    
    if dry_run:
        console.print("\n[yellow]DRY RUN - No changes were made[/yellow]")
    else:
        console.print(f"\n[green]Secrets written to {env_file}[/green]")

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
        console.print("[yellow]Run 'orchestra secrets sync' to fetch from GCP[/yellow]")
        sys.exit(1)

@secrets.command()
@click.argument('secret_id')
@click.option('--value', prompt=True, hide_input=True, confirmation_prompt=True)
@click.pass_context
def set(ctx, secret_id, value):
    """Set or update a secret in GCP Secret Manager."""
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'cherry-ai-project')
    secret_manager = SecretManager(project_id)
    
    # Check if secret exists
    existing_secrets = secret_manager.list_secrets()
    
    if secret_id in existing_secrets:
        if click.confirm(f"Secret {secret_id} already exists. Update it?"):
            if secret_manager.update_secret(secret_id, value):
                console.print(f"[green]✓ Updated secret {secret_id}[/green]")
            else:
                console.print(f"[red]✗ Failed to update secret {secret_id}[/red]")
    else:
        if secret_manager.create_secret(secret_id, value):
            console.print(f"[green]✓ Created secret {secret_id}[/green]")
        else:
            console.print(f"[red]✗ Failed to create secret {secret_id}[/red]")

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
            os.getenv(secret) is not None 
            for secret in config['required_secrets']
        )
        
        status = "[green]✓ Ready[/green]" if secrets_present else "[red]✗ Missing secrets[/red]"
        
        table.add_row(
            adapter_id,
            config['name'],
            config['description'],
            ", ".join(config['required_secrets']),
            status
        )
    
    console.print(table)

@adapters.command(name='check')
@click.argument('adapter_id')
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
    for secret in config['required_secrets']:
        value = os.getenv(secret)
        if value:
            console.print(f"  [green]✓[/green] {secret}")
        else:
            console.print(f"  [red]✗[/red] {secret} - MISSING")
            all_present = False
    
    # Check optional secrets
    if config['optional_secrets']:
        console.print("\n[bold]Optional Secrets:[/bold]")
        for secret in config['optional_secrets']:
            value = os.getenv(secret)
            if value:
                console.print(f"  [green]✓[/green] {secret}")
            else:
                console.print(f"  [yellow]○[/yellow] {secret} - Not set")
    
    if all_present:
        console.print(f"\n[green]✓ {config['name']} adapter is properly configured[/green]")
    else:
        console.print(f"\n[red]✗ {config['name']} adapter is missing required configuration[/red]")

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
        "GCP Connection": check_gcp_health(),
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
        status_display = "[green]✓ Healthy[/green]" if status else "[red]✗ Unhealthy[/red]"
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
        1 for secrets in REQUIRED_SECRETS.values() 
        for secret in secrets 
        if os.getenv(secret)
    )
    
    if present == total:
        return True, f"All {total} required secrets present"
    else:
        return False, f"{present}/{total} secrets present"

def check_gcp_health():
    """Check GCP connectivity."""
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return False, "GOOGLE_CLOUD_PROJECT not set"
        
        # Try to access secret manager
        client = secretmanager.SecretManagerServiceClient()
        parent = f"projects/{project_id}"
        list(client.list_secrets(request={"parent": parent}, page_size=1))
        return True, f"Connected to project {project_id}"
    except Exception as e:
        return False, f"Connection failed: {str(e)[:50]}..."

def check_redis_health():
    """Check Redis connectivity."""
    try:
        import redis
        host = os.getenv('REDIS_HOST', 'localhost')
        password = os.getenv('REDIS_PASSWORD')
        
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
        1 for config in adapters.values()
        if all(os.getenv(secret) for secret in config['required_secrets'])
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
        
        # Reload environment
        load_dotenv(override=True)
        
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
    
    table.add_row("Project ID", os.getenv('GOOGLE_CLOUD_PROJECT', 'Not set'))
    table.add_row("Environment", os.getenv('ENVIRONMENT', 'development'))
    table.add_row("Redis Host", os.getenv('REDIS_HOST', 'Not set'))
    table.add_row("Active Adapters", str(len([
        a for a in AdapterConfig.get_adapter_configs().values()
        if all(os.getenv(s) for s in a['required_secrets'])
    ])))
    
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
        task = progress.add_task("Syncing secrets from GCP...", total=None)
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

if __name__ == '__main__':
    cli()