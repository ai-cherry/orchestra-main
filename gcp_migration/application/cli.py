"""
Command-line interface for the GCP migration toolkit.

This module provides a CLI for executing migrations from the command line,
making the toolkit accessible in various environments.
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import click
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..domain.exceptions_fixed import MigrationError, ValidationError
from ..domain.models import (
    GCPConfig,
    GithubConfig,
    MigrationContext,
    MigrationPlan,
    MigrationResult,
    MigrationStatus,
    MigrationType,
    ResourceType,
    MigrationResource,
)
from .migration_service import MigrationService, MigrationOptions

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("gcp_migration")

# Create console for rich output
console = Console()


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Loaded configuration

    Raises:
        click.FileError: If the file cannot be loaded
    """
    path = Path(config_path)

    if not path.exists():
        raise click.FileError(
            config_path, hint=f"The configuration file {config_path} does not exist."
        )

    try:
        if path.suffix == ".json":
            with open(path, "r") as f:
                return json.load(f)
        elif path.suffix in (".yaml", ".yml"):
            with open(path, "r") as f:
                return yaml.safe_load(f)
        else:
            raise click.FileError(
                config_path, hint="Configuration file must be JSON or YAML."
            )
    except Exception as e:
        raise click.FileError(config_path, hint=f"Failed to load configuration: {e}")


def save_result(result_path: str, result: MigrationResult) -> None:
    """
    Save migration result to a file.

    Args:
        result_path: Path to save the result
        result: Migration result to save
    """
    path = Path(result_path)

    # Create directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert result to dictionary
    result_dict = result.dict()

    # Save the result
    if path.suffix == ".json":
        with open(path, "w") as f:
            json.dump(result_dict, f, default=str, indent=2)
    elif path.suffix in (".yaml", ".yml"):
        with open(path, "w") as f:
            yaml.dump(result_dict, f)
    else:
        # Default to JSON
        with open(f"{path}.json", "w") as f:
            json.dump(result_dict, f, default=str, indent=2)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """GCP Migration Toolkit - Command-line interface for migrating to Google Cloud Platform."""
    pass


@cli.command()
@click.option(
    "--config",
    "-c",
    required=True,
    help="Path to migration configuration file (JSON or YAML)",
)
@click.option(
    "--output",
    "-o",
    default="migration_result.json",
    help="Path to save migration result",
)
@click.option(
    "--validate-only",
    is_flag=True,
    help="Validate the migration plan without executing it",
)
@click.option(
    "--dry-run", is_flag=True, help="Perform a dry run without making changes"
)
@click.option(
    "--skip-validation", is_flag=True, help="Skip validation before execution"
)
@click.option(
    "--parallel/--sequential",
    default=True,
    help="Execute resource migrations in parallel or sequentially",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def migrate(
    config: str,
    output: str,
    validate_only: bool,
    dry_run: bool,
    skip_validation: bool,
    parallel: bool,
    verbose: bool,
):
    """Execute a migration based on a configuration file."""
    try:
        # Set log level based on verbose flag
        if verbose:
            logger.setLevel(logging.DEBUG)

        # Load configuration
        console.print(f"Loading configuration from [bold]{config}[/bold]...")
        config_data = load_config(config)

        # Run the migration
        result = asyncio.run(
            run_migration(
                config_data,
                validate_only=validate_only,
                dry_run=dry_run,
                skip_validation=skip_validation,
                parallel=parallel,
            )
        )

        # Save result if not None
        if result:
            console.print(f"Saving migration result to [bold]{output}[/bold]...")
            save_result(output, result)

            # Print summary
            console.print("\n[bold green]Migration Summary:[/bold green]")
            console.print(f"Status: {'Successful' if result.success else 'Failed'}")
            console.print(f"Resources: {len(result.context.resources)}")
            console.print(f"Duration: {result.duration_seconds:.2f} seconds")

            if not result.success:
                console.print(f"Errors: {len(result.errors)}")
                for error in result.errors:
                    console.print(f"  - {error['message']}")

    except click.FileError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--config",
    "-c",
    required=True,
    help="Path to migration configuration file (JSON or YAML)",
)
@click.option(
    "--output",
    "-o",
    default="validation_result.json",
    help="Path to save validation result",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def validate(config: str, output: str, verbose: bool):
    """Validate a migration configuration without executing it."""
    try:
        # Set log level based on verbose flag
        if verbose:
            logger.setLevel(logging.DEBUG)

        # Load configuration
        console.print(f"Loading configuration from [bold]{config}[/bold]...")
        config_data = load_config(config)

        # Run validation
        result = asyncio.run(validate_migration(config_data))

        # Save result if not None
        if result:
            # Convert to dictionary
            result_dict = {
                "valid": result.valid,
                "checks": result.checks,
                "errors": result.errors,
                "warnings": result.warnings,
            }

            # Save the result
            path = Path(output)
            if path.suffix == ".json":
                with open(path, "w") as f:
                    json.dump(result_dict, f, default=str, indent=2)
            elif path.suffix in (".yaml", ".yml"):
                with open(path, "w") as f:
                    yaml.dump(result_dict, f)
            else:
                # Default to JSON
                with open(f"{path}.json", "w") as f:
                    json.dump(result_dict, f, default=str, indent=2)

            # Print summary
            console.print("\n[bold green]Validation Summary:[/bold green]")
            console.print(f"Valid: {result.valid}")
            console.print(f"Checks: {len(result.checks)}")
            console.print(f"Errors: {len(result.errors)}")
            console.print(f"Warnings: {len(result.warnings)}")

            if not result.valid:
                console.print("\n[bold red]Validation Errors:[/bold red]")
                for error in result.errors:
                    console.print(f"  - {error['message']}")

    except click.FileError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command(name="init")
@click.option(
    "--output",
    "-o",
    default="migration_config.yaml",
    help="Path to save the configuration template",
)
@click.option("--github-repo", help="GitHub repository name (owner/repo)")
@click.option("--gcp-project", help="GCP project ID")
@click.option(
    "--type",
    "migration_type",
    type=click.Choice(["github-to-gcp", "local-to-gcp", "gcp-to-gcp"]),
    default="github-to-gcp",
    help="Type of migration to generate a template for",
)
def init_config(
    output: str,
    github_repo: Optional[str],
    gcp_project: Optional[str],
    migration_type: str,
):
    """Generate a configuration template for migration."""
    # Create config based on type
    config = {
        "migration_type": migration_type,
        "source": {},
        "destination": {},
        "options": {
            "parallel_resources": True,
            "validate_only": False,
            "dry_run": False,
            "skip_validation": False,
        },
        "resources": [],
    }

    # Set source based on type
    if migration_type == "github-to-gcp":
        config["source"] = {
            "type": "github",
            "repository": github_repo or "owner/repo",
            "branch": "main",
            "use_oauth": False,
            "auth_method": "personal_access_token",
        }
    elif migration_type == "local-to-gcp":
        config["source"] = {"type": "local", "directory": "/path/to/local/directory"}
    elif migration_type == "gcp-to-gcp":
        config["source"] = {
            "type": "gcp",
            "project_id": "source-project-id",
            "location": "us-central1",
        }

    # Set destination
    config["destination"] = {
        "type": "gcp",
        "project_id": gcp_project or "destination-project-id",
        "location": "us-central1",
        "use_application_default": True,
    }

    # Add sample resources based on type
    if migration_type == "github-to-gcp":
        config["resources"] = [
            {
                "id": "secret1",
                "name": "github-token",
                "type": "SECRET",
                "source_path": "GITHUB_TOKEN",
            },
            {
                "id": "config1",
                "name": "app-config",
                "type": "CONFIGURATION",
                "source_path": ".devcontainer/devcontainer.json",
                "destination_path": "gs://bucket-name/configs/devcontainer.json",
            },
        ]

    # Save the config
    path = Path(output)
    if path.suffix == ".json":
        with open(path, "w") as f:
            json.dump(config, f, indent=2)
    elif path.suffix in (".yaml", ".yml"):
        with open(path, "w") as f:
            yaml.dump(config, f)
    else:
        # Default to YAML
        with open(f"{path}.yaml", "w") as f:
            yaml.dump(config, f)

    console.print(f"[bold green]Configuration template generated:[/bold green] {path}")
    console.print("Edit this file to customize your migration configuration.")


@cli.command()
@click.option("--project", "-p", help="GCP project ID")
@click.option("--location", "-l", default="us-central1", help="GCP location")
@click.option("--name", "-n", required=True, help="Name for the workstation cluster")
@click.option(
    "--output",
    "-o",
    default="workstation_cluster.yaml",
    help="Path to save the Terraform configuration",
)
def generate_workstation_config(
    project: Optional[str], location: str, name: str, output: str
):
    """Generate Terraform configuration for a GCP Cloud Workstation cluster."""
    # Get project ID from environment if not provided
    if not project:
        project = os.environ.get("GCP_PROJECT")
        if not project:
            console.print("[bold red]Error:[/bold red] No GCP project ID provided")
            console.print(
                "Either specify --project or set GCP_PROJECT environment variable"
            )
            sys.exit(1)

    # Create Terraform configuration
    terraform_config = {
        "variable": {
            "project_id": {"default": project},
            "region": {"default": location},
            "cluster_name": {"default": name},
        },
        "provider": {
            "google": {"project": "${var.project_id}", "region": "${var.region}"}
        },
        "resource": {
            "google_workstations_workstation_cluster": {
                "main": {
                    "workstation_cluster_id": "${var.cluster_name}",
                    "network": "default",
                    "subnetwork": "default",
                    "location": "${var.region}",
                    "private_cluster_config": {"enable_private_endpoint": False},
                }
            },
            "google_workstations_workstation_config": {
                "default": {
                    "workstation_config_id": "default-config",
                    "workstation_cluster_id": "${google_workstations_workstation_cluster.main.workstation_cluster_id}",
                    "location": "${var.region}",
                    "host": {
                        "gce_instance": {
                            "machine_type": "e2-standard-4",
                            "boot_disk_size_gb": 35,
                            "tags": ["workstation"],
                        }
                    },
                    "persistent_directories": {
                        "gcePd": {
                            "size_gb": 200,
                            "fs_type": "ext4",
                            "mount_path": "/home",
                        }
                    },
                }
            },
        },
    }

    # Save the config
    path = Path(output)
    if path.suffix == ".json":
        with open(path, "w") as f:
            json.dump(terraform_config, f, indent=2)
    elif path.suffix in (".yaml", ".yml"):
        with open(path, "w") as f:
            yaml.dump(terraform_config, f)
    else:
        # Save as Terraform HCL
        with open(f"{path}.tf", "w") as f:
            # Very basic HCL formatting - in a real implementation, use a proper HCL generator
            f.write('variable "project_id" {\n  default = "' + project + '"\n}\n\n')
            f.write('variable "region" {\n  default = "' + location + '"\n}\n\n')
            f.write('variable "cluster_name" {\n  default = "' + name + '"\n}\n\n')
            f.write(
                'provider "google" {\n  project = var.project_id\n  region  = var.region\n}\n\n'
            )
            f.write('resource "google_workstations_workstation_cluster" "main" {\n')
            f.write("  workstation_cluster_id = var.cluster_name\n")
            f.write('  network               = "default"\n')
            f.write('  subnetwork            = "default"\n')
            f.write("  location              = var.region\n")
            f.write("  private_cluster_config {\n")
            f.write("    enable_private_endpoint = false\n")
            f.write("  }\n")
            f.write("}\n\n")
            f.write('resource "google_workstations_workstation_config" "default" {\n')
            f.write('  workstation_config_id   = "default-config"\n')
            f.write(
                "  workstation_cluster_id  = google_workstations_workstation_cluster.main.workstation_cluster_id\n"
            )
            f.write("  location               = var.region\n")
            f.write("  host {\n")
            f.write("    gce_instance {\n")
            f.write('      machine_type      = "e2-standard-4"\n')
            f.write("      boot_disk_size_gb = 35\n")
            f.write('      tags              = ["workstation"]\n')
            f.write("    }\n")
            f.write("  }\n")
            f.write("  persistent_directories {\n")
            f.write("    gcePd {\n")
            f.write("      size_gb           = 200\n")
            f.write('      fs_type           = "ext4"\n')
            f.write('      mount_path        = "/home"\n')
            f.write("    }\n")
            f.write("  }\n")
            f.write("}\n")

    console.print(
        f"[bold green]Workstation configuration generated:[/bold green] {path}"
    )
    console.print(
        "Use this configuration with Terraform to create a Cloud Workstation cluster."
    )


async def run_migration(
    config_data: Dict[str, Any],
    validate_only: bool = False,
    dry_run: bool = False,
    skip_validation: bool = False,
    parallel: bool = True,
) -> MigrationResult:
    """
    Run a migration based on the provided configuration.

    Args:
        config_data: Migration configuration
        validate_only: Whether to validate only without executing
        dry_run: Whether to perform a dry run
        skip_validation: Whether to skip validation
        parallel: Whether to execute resource migrations in parallel

    Returns:
        Migration result
    """
    # Create migration service
    service = MigrationService(
        default_project_id=os.environ.get("GCP_PROJECT"),
        default_location=os.environ.get("GCP_LOCATION", "us-central1"),
        default_credentials_path=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
    )

    try:
        # Initialize the service
        console.print("Initializing migration service...")
        await service.initialize()

        # Create migration plan based on configuration
        console.print("Creating migration plan...")
        plan = await create_plan_from_config(service, config_data)

        # Set migration options
        options = MigrationOptions(
            validate_only=validate_only,
            dry_run=dry_run,
            skip_validation=skip_validation,
            parallel_resources=parallel,
        )

        # Execute the plan with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Create progress task
            task = progress.add_task("Executing migration...", total=None)

            # Execute the plan
            result = await service.execute_plan(plan, options)

            # Mark task as completed
            progress.update(task, completed=True)

        return result
    finally:
        # Close the service
        await service.close()


async def validate_migration(config_data: Dict[str, Any]) -> Any:
    """
    Validate a migration configuration.

    Args:
        config_data: Migration configuration

    Returns:
        Validation result
    """
    # Create migration service
    service = MigrationService(
        default_project_id=os.environ.get("GCP_PROJECT"),
        default_location=os.environ.get("GCP_LOCATION", "us-central1"),
        default_credentials_path=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
    )

    try:
        # Initialize the service
        console.print("Initializing migration service...")
        await service.initialize()

        # Create migration plan based on configuration
        console.print("Creating migration plan...")
        plan = await create_plan_from_config(service, config_data)

        # Validate the plan
        console.print("Validating migration plan...")
        return await service.validate_plan(plan)
    finally:
        # Close the service
        await service.close()


async def create_plan_from_config(
    service: MigrationService, config_data: Dict[str, Any]
) -> MigrationPlan:
    """
    Create a migration plan from configuration.

    Args:
        service: Migration service
        config_data: Migration configuration

    Returns:
        Migration plan

    Raises:
        ValidationError: If the configuration is invalid
    """
    # Get migration type
    migration_type_str = config_data.get("migration_type", "github-to-gcp")

    if migration_type_str == "github-to-gcp":
        # Get GitHub configuration
        source_config = config_data.get("source", {})
        github_config = GithubConfig(
            repository=source_config.get("repository", ""),
            branch=source_config.get("branch", "main"),
            access_token=source_config.get("access_token"),
            use_oauth=source_config.get("use_oauth", False),
        )

        # Get GCP configuration
        dest_config = config_data.get("destination", {})
        gcp_config = GCPConfig(
            project_id=dest_config.get("project_id", ""),
            location=dest_config.get("location", "us-central1"),
            credentials_path=dest_config.get("credentials_path"),
            use_application_default=dest_config.get("use_application_default", True),
            storage_bucket=dest_config.get("storage_bucket"),
        )

        # Get resources
        resources = []
        for res_data in config_data.get("resources", []):
            try:
                res_type = ResourceType[res_data.get("type", "OTHER")]
            except KeyError:
                res_type = ResourceType.OTHER

            resources.append(
                MigrationResource(
                    id=res_data.get("id", str(len(resources) + 1)),
                    name=res_data.get("name", f"Resource {len(resources) + 1}"),
                    type=res_type,
                    source_path=res_data.get("source_path"),
                    destination_path=res_data.get("destination_path"),
                    metadata=res_data.get("metadata", {}),
                    dependencies=res_data.get("dependencies", []),
                )
            )

        # Create migration plan
        return await service.create_github_to_gcp_plan(
            github_config=github_config,
            gcp_config=gcp_config,
            resources=resources,
            options=config_data.get("options", {}),
        )
    else:
        raise ValidationError(
            f"Unsupported migration type: {migration_type_str}",
            details={"supported_types": ["github-to-gcp"]},
        )


if __name__ == "__main__":
    cli()
