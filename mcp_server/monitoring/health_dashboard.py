#!/usr/bin/env python3
"""
MCP Health Monitoring Dashboard
Real-time monitoring of all MCP servers
"""

import asyncio
import json
from datetime import datetime

import click
import httpx
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

console = Console()

# MCP server endpoints
SERVERS = {
    "Gateway": "http://localhost:8000/health",
    "Cloud Run": "http://localhost:8001/health",
    "Secrets": "http://localhost:8002/health",
    "Memory": "http://localhost:8003/health",
    "Orchestrator": "http://localhost:8004/health",
}

# Metrics endpoint
METRICS_URL = "http://localhost:8000/metrics"


async def check_health(name: str, url: str) -> dict:
    """Check health of a single server"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start = datetime.now()
            response = await client.get(url)
            latency = (datetime.now() - start).total_seconds() * 1000

            if response.status_code == 200:
                data = response.json()
                return {"name": name, "status": "✅ Healthy", "latency": f"{latency:.0f}ms", "details": data}
            else:
                return {
                    "name": name,
                    "status": f"⚠️  Error ({response.status_code})",
                    "latency": f"{latency:.0f}ms",
                    "details": {},
                }
    except Exception as e:
        return {"name": name, "status": "❌ Down", "latency": "N/A", "details": {"error": str(e)}}


def create_health_table(health_data: list) -> Table:
    """Create health status table"""
    table = Table(title="MCP Server Health Status", show_header=True, header_style="bold magenta")
    table.add_column("Server", style="cyan", width=15)
    table.add_column("Status", width=15)
    table.add_column("Latency", justify="right", width=10)
    table.add_column("Details", width=50)

    for server in health_data:
        details = ""
        if server["details"]:
            if "error" in server["details"]:
                details = f"[red]{server['details']['error']}[/red]"
            else:
                # Format details based on server type
                if server["name"] == "Memory":
                    backends = server["details"].get("backends", {})
                    details = f"Redis: {backends.get('redis', '❌')}, Firestore: {backends.get('firestore', '❌')}, Qdrant: {backends.get('qdrant', '❌')}"
                elif server["name"] == "Orchestrator":
                    details = f"Mode: {server['details'].get('current_mode', 'N/A')}, Workflows: {server['details'].get('active_workflows', 0)}"
                elif server["name"] == "Gateway":
                    details = f"Servers: {server['details'].get('healthy_servers', 0)}/{server['details'].get('total_servers', 0)}"
                else:
                    details = f"Service: {server['details'].get('service', 'N/A')}"

        table.add_row(server["name"], server["status"], server["latency"], details)

    return table


async def get_metrics() -> dict:
    """Get Prometheus metrics"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(METRICS_URL)
            if response.status_code == 200:
                # Parse Prometheus metrics
                metrics = {}
                for line in response.text.split("\n"):
                    if line.startswith("#") or not line:
                        continue
                    if "mcp_gateway_requests_total" in line:
                        metrics["requests"] = metrics.get("requests", 0) + 1
                    elif "mcp_gateway_errors_total" in line:
                        metrics["errors"] = metrics.get("errors", 0) + 1
                return metrics
            return {}
    except:
        return {}


def create_metrics_panel(metrics: dict) -> Panel:
    """Create metrics panel"""
    if not metrics:
        return Panel("No metrics available", title="Metrics")

    content = f"""
Total Requests: {metrics.get('requests', 0)}
Total Errors: {metrics.get('errors', 0)}
Error Rate: {metrics.get('errors', 0) / max(metrics.get('requests', 1), 1) * 100:.1f}%
    """

    return Panel(content.strip(), title="System Metrics")


async def monitor_health(interval: int = 5):
    """Monitor health continuously"""
    with Live(console=console, refresh_per_second=1) as live:
        while True:
            # Check health of all servers
            health_tasks = [check_health(name, url) for name, url in SERVERS.items()]
            health_data = await asyncio.gather(*health_tasks)

            # Get metrics
            metrics = await get_metrics()

            # Create layout
            layout = Layout()
            layout.split_column(
                Layout(create_health_table(health_data), name="health"),
                Layout(create_metrics_panel(metrics), name="metrics", size=6),
            )

            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            layout["health"].update(Panel(create_health_table(health_data), title=f"MCP System Health - {timestamp}"))

            live.update(layout)
            await asyncio.sleep(interval)


@click.command()
@click.option("--interval", "-i", default=5, help="Update interval in seconds")
@click.option("--once", "-o", is_flag=True, help="Run once and exit")
def main(interval: int, once: bool):
    """MCP Health Monitoring Dashboard"""
    console.print("[bold blue]MCP Health Monitoring Dashboard[/bold blue]")
    console.print(f"Monitoring {len(SERVERS)} servers...")

    if once:
        # Run once
        async def run_once():
            health_tasks = [check_health(name, url) for name, url in SERVERS.items()]
            health_data = await asyncio.gather(*health_tasks)
            console.print(create_health_table(health_data))

            # Print detailed JSON for debugging
            for server in health_data:
                console.print(f"\n[bold]{server['name']}[/bold]")
                console.print(json.dumps(server["details"], indent=2))

        asyncio.run(run_once())
    else:
        # Continuous monitoring
        try:
            asyncio.run(monitor_health(interval))
        except KeyboardInterrupt:
            console.print("\n[yellow]Monitoring stopped[/yellow]")


if __name__ == "__main__":
    main()
