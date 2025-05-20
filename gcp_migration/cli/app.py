"""
CLI application for the GCP Migration toolkit.

This module provides the main entry point for the CLI application,
defining commands for migration, benchmarking, and other operations.
"""

import asyncio
import json
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from gcp_migration.application.benchmark import BenchmarkService
from gcp_migration.config.settings import settings
from gcp_migration.domain.exceptions import MigrationError
from gcp_migration.domain.interfaces import IBenchmarkService
from gcp_migration.utils.errors import extract_error_details, format_error_for_user
from gcp_migration.utils.logging import get_logger


# Create logger
logger = get_logger(__name__)

# Create typer app
app = typer.Typer(
    name="gcp-migrate",
    help="Migration toolkit for GitHub Codespaces to GCP Workstations",
    add_completion=False,
)

# Create rich console
console = Console()


@app.callback()
def callback():
    """
    Migration toolkit for GitHub Codespaces to GCP Workstations.

    This tool provides commands for benchmarking, migrating, and validating
    the migration from GitHub Codespaces to GCP Workstations.
    """
    # Display the banner on every command
    console.print(
        Panel.fit(
            "[bold blue]GCP Migration Toolkit[/bold blue]\n"
            "[blue]GitHub Codespaces to GCP Workstations[/blue]",
            border_style="blue",
        )
    )


@app.command()
def info():
    """
    Display information about the current configuration.
    """
    # Configuration information
    config_table = Table(title="Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")

    # Add basic settings
    config_table.add_row("Project ID", settings.gcp_project_id)
    config_table.add_row("Region", settings.gcp_region)
    config_table.add_row("Zone", settings.gcp_zone)
    config_table.add_row("Docker Registry", settings.docker_registry)
    config_table.add_row("Environment", settings.env)
    config_table.add_row("Terraform Path", str(settings.terraform_path))
    config_table.add_row("Performance Optimized", str(settings.performance_optimized))
    config_table.add_row("GPU Enabled", str(settings.workstation_use_gpu))

    # Compute resources
    config_table.add_row(
        "Standard Machine Type",
        settings.workstation_machine_types.get("standard", "N/A"),
    )
    config_table.add_row(
        "ML Machine Type", settings.workstation_machine_types.get("ml", "N/A")
    )

    console.print(config_table)

    # Print GitHub repositories if configured
    if settings.github_repositories:
        repo_table = Table(title="GitHub Repositories")
        repo_table.add_column("Repository", style="cyan")

        for repo in settings.github_repositories:
            repo_table.add_row(repo)

        console.print(repo_table)

    # Print GitHub token status
    console.print(
        f"GitHub Token: [{'green' if settings.github_token else 'red'}]"
        f"{'Configured' if settings.github_token else 'Not Configured'}[/]"
    )

    # Print GCP credentials status
    console.print(
        f"GCP Credentials: [{'green' if settings.gcp_credentials_file else 'yellow'}]"
        f"{'File: ' + str(settings.gcp_credentials_file) if settings.gcp_credentials_file else 'Using Application Default Credentials'}[/]"
    )


@app.command()
def benchmark(
    environment: str = typer.Option(
        "github",
        help="Environment to benchmark (github, gcp, or both)",
        case_sensitive=False,
    ),
    workstation_name: Optional[str] = typer.Option(
        None,
        help="Name of the GCP Workstation to benchmark (required for gcp environment)",
    ),
    output_dir: Path = typer.Option(
        Path("benchmark_results"),
        help="Directory to save benchmark results",
        file_okay=False,
    ),
):
    """
    Benchmark GitHub Codespaces and/or GCP Workstations environments.
    """
    # Validate arguments
    if environment.lower() in ["gcp", "both"] and not workstation_name:
        console.print(
            "[bold red]Error:[/bold red] Workstation name is required for GCP benchmarking"
        )
        raise typer.Exit(1)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create benchmark service
    benchmark_service = BenchmarkService()

    try:
        # Run appropriate benchmarks
        if environment.lower() in ["github", "both"]:
            console.print("[bold]Benchmarking GitHub Codespaces environment...[/bold]")

            # Run in a progress spinner context
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                # Start a benchmarking task
                task = progress.add_task("Running benchmarks...", total=None)

                # Run the benchmark
                github_results = asyncio.run(
                    benchmark_service.benchmark_github_codespaces()
                )

                # Mark the task as completed
                progress.update(task, completed=True)

            # Save results
            github_output = (
                output_dir
                / f"github_benchmark_{github_results.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            )
            benchmark_service.save_results(github_results, github_output)

            # Display results summary
            console.print(
                f"[green]GitHub benchmarks completed and saved to {github_output}[/green]"
            )
            _display_benchmark_summary(github_results)

        if environment.lower() in ["gcp", "both"]:
            # We know workstation_name is not None here due to the validation check above
            assert (
                workstation_name is not None
            ), "Workstation name is required for GCP benchmarking"
            console.print(
                f"[bold]Benchmarking GCP Workstation: {workstation_name}...[/bold]"
            )

            # Run in a progress spinner context
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                # Start a benchmarking task
                task = progress.add_task("Running benchmarks...", total=None)

                # Run the benchmark with the validated workstation name
                gcp_results = asyncio.run(
                    benchmark_service.benchmark_gcp_workstation(workstation_name)
                )

                # Mark the task as completed
                progress.update(task, completed=True)

            # Save results
            gcp_output = (
                output_dir
                / f"gcp_benchmark_{gcp_results.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            )
            benchmark_service.save_results(gcp_results, gcp_output)

            # Display results summary
            console.print(
                f"[green]GCP benchmarks completed and saved to {gcp_output}[/green]"
            )
            _display_benchmark_summary(gcp_results)

        # If both environments were benchmarked, show comparison
        if environment.lower() == "both":
            comparison = asyncio.run(
                benchmark_service.compare_environments(github_results, gcp_results)
            )
            _display_comparison(comparison)

            # Save comparison
            comparison_output = (
                output_dir
                / f"benchmark_comparison_{github_results.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(comparison_output, "w") as f:
                json.dump(comparison, f, indent=2)

            console.print(f"[green]Comparison saved to {comparison_output}[/green]")

    except MigrationError as e:
        error_details = extract_error_details(e)
        error_message = format_error_for_user(e)

        # Create a detailed error panel with suggestions
        error_panel = Panel(
            f"[bold red]Error:[/bold red] {error_message}\n\n"
            f"[yellow]Root Cause:[/yellow] {error_details.get('root_cause', 'Unknown')}\n"
            f"[yellow]Suggestion:[/yellow] {error_details.get('suggestion', 'Try again or check logs for more details.')}",
            title="Benchmark Failed",
            border_style="red",
        )
        console.print(error_panel)

        # Log the detailed error
        logger.error("Benchmark failed", exc_info=True, extra=error_details)
        raise typer.Exit(1)

    except Exception as e:
        # For unexpected errors, provide a more generic message
        error_panel = Panel(
            f"[bold red]Unexpected error:[/bold red] {str(e)}\n\n"
            f"[yellow]Suggestion:[/yellow] This is an unhandled error. Please report this issue "
            f"with the complete error message and steps to reproduce.",
            title="Unexpected Error",
            border_style="red",
        )
        console.print(error_panel)

        # Log the full error details
        logger.error("Benchmark failed with unexpected error", exc_info=True)
        raise typer.Exit(1)


@app.command()
def migrate(
    project_id: str = typer.Option(
        None, help="GCP Project ID (uses configured value if not provided)"
    ),
    repositories: Optional[List[str]] = typer.Option(
        None,
        help="GitHub repositories to migrate (uses configured values if not provided)",
    ),
    skip_benchmark: bool = typer.Option(False, help="Skip benchmarking"),
    skip_terraform: bool = typer.Option(
        False, help="Skip Terraform infrastructure deployment"
    ),
    skip_container: bool = typer.Option(False, help="Skip container image building"),
    skip_secrets: bool = typer.Option(False, help="Skip secret migration"),
    auto_approve: bool = typer.Option(False, help="Skip confirmation prompts"),
):
    """
    Execute the complete migration process.
    """
    # Use configured project ID if not provided
    project_id = project_id or settings.gcp_project_id

    # Use configured repositories if not provided
    repositories = repositories or settings.github_repositories

    # Validate required parameters
    if not project_id:
        console.print("[bold red]Error:[/bold red] Project ID is required")
        raise typer.Exit(1)

    if not repositories:
        console.print("[bold red]Error:[/bold red] At least one repository is required")
        raise typer.Exit(1)

    # TODO: Implement migration logic
    console.print("[bold yellow]Migration not yet implemented[/bold yellow]")
    raise typer.Exit(1)


@app.command()
def validate(
    workstation_name: str = typer.Argument(
        ..., help="Name of the GCP Workstation to validate"
    ),
):
    """
    Validate a migrated GCP Workstation.
    """
    # TODO: Implement validation logic
    console.print("[bold yellow]Validation not yet implemented[/bold yellow]")
    raise typer.Exit(1)


def _display_benchmark_summary(results):
    """
    Display a summary of benchmark results.

    Args:
        results: The benchmark results to display
    """
    # Create a table
    table = Table(title=f"{results.environment_type.title()} Benchmark Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Unit", style="blue")

    # Add system info
    console.print("[bold]System Information:[/bold]")
    sys_table = Table(show_header=False)
    sys_table.add_column("Key", style="cyan")
    sys_table.add_column("Value", style="green")

    for key, value in results.system_info.items():
        sys_table.add_row(key, str(value))

    console.print(sys_table)

    # Add metrics
    console.print("[bold]Performance Metrics:[/bold]")
    metrics_table = Table()
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="green")
    metrics_table.add_column("Unit", style="blue")

    for metric in sorted(results.metrics, key=lambda m: m.name):
        # Format the value nicely
        if metric.value > 1000:
            formatted_value = f"{metric.value:.2f}"
        elif metric.value > 100:
            formatted_value = f"{metric.value:.2f}"
        elif metric.value > 10:
            formatted_value = f"{metric.value:.3f}"
        elif metric.value > 1:
            formatted_value = f"{metric.value:.4f}"
        else:
            formatted_value = f"{metric.value:.6f}"

        metrics_table.add_row(metric.name, formatted_value, metric.unit)

    console.print(metrics_table)


def _display_comparison(comparison):
    """
    Display a comparison of benchmark results.

    Args:
        comparison: The comparison results to display
    """
    # Create a table
    table = Table(title="Benchmark Comparison (GCP vs GitHub)")
    table.add_column("Metric", style="cyan")
    table.add_column("Improvement", style="green")
    table.add_column("Ratio", style="blue")

    # Add metrics
    for name in sorted(comparison.keys()):
        ratio = comparison[name]

        # Format based on whether higher or lower is better
        if ratio > 1.0:
            improvement = f"{ratio:.2f}x better"
            style = "green"
        elif ratio == 1.0:
            improvement = "Same"
            style = "yellow"
        else:
            improvement = f"{1/ratio:.2f}x worse"
            style = "red"

        table.add_row(name, f"[{style}]{improvement}[/{style}]", f"{ratio:.2f}")

    console.print(table)


if __name__ == "__main__":
    app()
