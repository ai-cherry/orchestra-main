#!/usr/bin/env python3
"""
Redis Health Monitor and Management Tool
Monitors Redis health, performance, and provides management capabilities
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, Any, List
import click
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add parent directory to path for imports
sys.path.append('.')
from core.redis import ResilientRedisClient, RedisConfig, RedisHealthMonitor

console = Console()

class RedisMonitoringDashboard:
    """Real-time Redis monitoring dashboard."""
    
    def __init__(self):
        self.config = RedisConfig.from_env()
        self.client = ResilientRedisClient(self.config)
        self.monitor = RedisHealthMonitor(self.client)
        self.running = False
    
    async def get_redis_info(self) -> Dict[str, Any]:
        """Get comprehensive Redis information."""
        info = {}
        
        try:
            # Get basic info
            redis_info = await self.client._execute_with_fallback('info')
            if redis_info and isinstance(redis_info, str):
                for line in redis_info.split('\n'):
                    if ':' in line and not line.startswith('#'):
                        key, value = line.strip().split(':', 1)
                        info[key] = value
            
            # Get memory stats
            memory_info = await self.client._execute_with_fallback('info', 'memory')
            if memory_info and isinstance(memory_info, str):
                for line in memory_info.split('\n'):
                    if ':' in line and not line.startswith('#'):
                        key, value = line.strip().split(':', 1)
                        info[f"memory_{key}"] = value
            
            # Get client list
            clients = await self.client._execute_with_fallback('client', 'list')
            if clients:
                info['connected_clients_details'] = len(clients.split('\n')) if isinstance(clients, str) else 0
            
            # Get key statistics
            dbsize = await self.client._execute_with_fallback('dbsize')
            info['total_keys'] = dbsize if dbsize else 0
            
        except Exception as e:
            console.print(f"[red]Error getting Redis info: {e}[/red]")
        
        return info
    
    def create_dashboard_layout(self) -> Layout:
        """Create the dashboard layout."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        return layout
    
    def render_header(self, health_status: Dict[str, Any]) -> Panel:
        """Render the header panel."""
        status_color = "green" if health_status.get("status") == "healthy" else "red"
        fallback_status = "🔄 Fallback Active" if self.client.is_fallback_active() else "✅ Redis Connected"
        
        header_text = f"""[bold {status_color}]Redis Health Monitor[/bold {status_color}]
Mode: {self.config.mode} | Status: {health_status.get("status", "unknown")} | {fallback_status}
Last Check: {health_status.get("last_check", "never")}"""
        
        return Panel(header_text, style=f"{status_color}")
    
    def render_metrics_table(self, info: Dict[str, Any]) -> Table:
        """Render the metrics table."""
        table = Table(title="Redis Metrics", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        # Key metrics to display
        metrics = [
            ("Uptime (days)", f"{int(info.get('uptime_in_seconds', 0)) / 86400:.1f}"),
            ("Connected Clients", info.get('connected_clients', 'N/A')),
            ("Total Keys", info.get('total_keys', 'N/A')),
            ("Used Memory", info.get('memory_used_memory_human', 'N/A')),
            ("Memory Usage", f"{float(info.get('memory_used_memory_percentage', '0').rstrip('%')):.1f}%"),
            ("Peak Memory", info.get('memory_used_memory_peak_human', 'N/A')),
            ("Total Commands", info.get('total_commands_processed', 'N/A')),
            ("Ops/sec", info.get('instantaneous_ops_per_sec', 'N/A')),
            ("Hit Rate", f"{float(info.get('keyspace_hit_rate', '0')):.1f}%"),
            ("Evicted Keys", info.get('evicted_keys', '0')),
        ]
        
        for metric, value in metrics:
            table.add_row(metric, str(value))
        
        return table
    
    def render_health_metrics(self, health_status: Dict[str, Any]) -> Table:
        """Render health metrics table."""
        table = Table(title="Health Metrics", show_header=True)
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="green")
        
        metrics = health_status.get("metrics", {})
        
        # Health checks
        checks = [
            ("Response Time", f"{metrics.get('response_time_ms', 'N/A')} ms"),
            ("Circuit Breaker", health_status.get('circuit_breaker_state', 'unknown')),
            ("Fallback Active", "Yes" if self.client.is_fallback_active() else "No"),
            ("Connection Pool", f"{metrics.get('active_connections', 0)}/{metrics.get('max_connections', 'N/A')}"),
            ("Failed Requests", str(metrics.get('failed_requests', 0))),
            ("Success Rate", f"{metrics.get('success_rate', 0):.1f}%"),
        ]
        
        for check, status in checks:
            color = "green" if "Yes" not in status and "failed" not in check.lower() else "yellow"
            table.add_row(check, f"[{color}]{status}[/{color}]")
        
        return table
    
    async def run_dashboard(self):
        """Run the monitoring dashboard."""
        self.running = True
        layout = self.create_dashboard_layout()
        
        with Live(layout, refresh_per_second=1, console=console) as live:
            while self.running:
                try:
                    # Get current data
                    health_status = await self.monitor.get_health_status()
                    redis_info = await self.get_redis_info()
                    
                    # Update layout
                    layout["header"].update(self.render_header(health_status))
                    layout["left"].update(Panel(self.render_metrics_table(redis_info), title="Performance"))
                    layout["right"].update(Panel(self.render_health_metrics(health_status), title="Health"))
                    layout["footer"].update(Panel(
                        "[bold]Commands:[/bold] [q]uit | [r]efresh | [f]lush | [t]est",
                        style="blue"
                    ))
                    
                    await asyncio.sleep(1)
                    
                except KeyboardInterrupt:
                    self.running = False
                except Exception as e:
                    console.print(f"[red]Dashboard error: {e}[/red]")
                    await asyncio.sleep(5)

@click.group()
def cli():
    """Redis Health Monitor and Management Tool"""
    pass

@cli.command()
def monitor():
    """Run real-time monitoring dashboard"""
    dashboard = RedisMonitoringDashboard()
    console.print("[bold green]Starting Redis Monitor Dashboard...[/bold green]")
    console.print("[dim]Press Ctrl+C to exit[/dim]\n")
    
    try:
        asyncio.run(dashboard.run_dashboard())
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped[/yellow]")

@cli.command()
@click.option('--detailed', is_flag=True, help='Show detailed health information')
def health(detailed):
    """Check Redis health status"""
    async def check_health():
        config = RedisConfig.from_env()
        client = ResilientRedisClient(config)
        monitor = RedisHealthMonitor(client)
        
        console.print("[bold]Checking Redis Health...[/bold]\n")
        
        health_status = await monitor.get_health_status()
        
        # Basic status
        status_color = "green" if health_status["status"] == "healthy" else "red"
        console.print(f"Status: [{status_color}]{health_status['status']}[/{status_color}]")
        console.print(f"Mode: {config.mode}")
        console.print(f"Fallback Active: {'Yes' if client.is_fallback_active() else 'No'}")
        
        if detailed:
            console.print("\n[bold]Detailed Metrics:[/bold]")
            metrics = health_status.get("metrics", {})
            for key, value in metrics.items():
                console.print(f"  {key}: {value}")
            
            console.print("\n[bold]Recent Checks:[/bold]")
            history = health_status.get("history", [])
            for check in history[-5:]:
                console.print(f"  {check['timestamp']}: {check['status']}")
        
        await client.close()
    
    asyncio.run(check_health())

@cli.command()
@click.argument('key')
@click.argument('value')
@click.option('--ttl', type=int, help='TTL in seconds')
def set(key, value, ttl):
    """Set a key-value pair in Redis"""
    async def set_value():
        config = RedisConfig.from_env()
        client = ResilientRedisClient(config)
        
        try:
            if ttl:
                await client.set(key, value, ex=ttl)
                console.print(f"[green]✓ Set {key} = {value} (TTL: {ttl}s)[/green]")
            else:
                await client.set(key, value)
                console.print(f"[green]✓ Set {key} = {value}[/green]")
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
        finally:
            await client.close()
    
    asyncio.run(set_value())

@cli.command()
@click.argument('key')
def get(key):
    """Get a value from Redis"""
    async def get_value():
        config = RedisConfig.from_env()
        client = ResilientRedisClient(config)
        
        try:
            value = await client.get(key)
            if value:
                console.print(f"[green]{key} = {value}[/green]")
            else:
                console.print(f"[yellow]Key '{key}' not found[/yellow]")
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
        finally:
            await client.close()
    
    asyncio.run(get_value())

@cli.command()
@click.option('--pattern', default='*', help='Key pattern to match')
def keys(pattern):
    """List keys matching pattern"""
    async def list_keys():
        config = RedisConfig.from_env()
        client = ResilientRedisClient(config)
        
        try:
            keys = await client.keys(pattern)
            if keys:
                console.print(f"[bold]Found {len(keys)} keys:[/bold]")
                for key in sorted(keys):
                    if isinstance(key, bytes):
                        key = key.decode('utf-8')
                    console.print(f"  • {key}")
            else:
                console.print(f"[yellow]No keys found matching '{pattern}'[/yellow]")
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
        finally:
            await client.close()
    
    asyncio.run(list_keys())

@cli.command()
@click.confirmation_option(prompt='Are you sure you want to flush all data?')
def flush():
    """Flush all data from Redis (DANGEROUS!)"""
    async def flush_db():
        config = RedisConfig.from_env()
        client = ResilientRedisClient(config)
        
        try:
            await client._execute_with_fallback('flushdb')
            console.print("[green]✓ Database flushed successfully[/green]")
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
        finally:
            await client.close()
    
    asyncio.run(flush_db())

@cli.command()
def test():
    """Run Redis connection and performance tests"""
    async def run_tests():
        config = RedisConfig.from_env()
        client = ResilientRedisClient(config)
        
        console.print("[bold]Running Redis Tests...[/bold]\n")
        
        # Connection test
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Testing connection...", total=None)
            
            try:
                await client.set("test:connection", "ok", ex=10)
                value = await client.get("test:connection")
                if value == "ok":
                    console.print("[green]✓ Connection test passed[/green]")
                else:
                    console.print("[red]✗ Connection test failed[/red]")
            except Exception as e:
                console.print(f"[red]✗ Connection test failed: {e}[/red]")
            
            progress.update(task, completed=True)
        
        # Performance test
        console.print("\n[bold]Performance Test:[/bold]")
        iterations = 1000
        
        import time
        start_time = time.time()
        
        for i in range(iterations):
            await client.set(f"test:perf:{i}", f"value_{i}", ex=60)
        
        write_time = time.time() - start_time
        write_ops = iterations / write_time
        
        start_time = time.time()
        
        for i in range(iterations):
            await client.get(f"test:perf:{i}")
        
        read_time = time.time() - start_time
        read_ops = iterations / read_time
        
        console.print(f"  Write: {write_ops:.0f} ops/sec ({write_time:.2f}s for {iterations} ops)")
        console.print(f"  Read:  {read_ops:.0f} ops/sec ({read_time:.2f}s for {iterations} ops)")
        
        # Cleanup
        for i in range(iterations):
            await client.delete(f"test:perf:{i}")
        
        await client.close()
        console.print("\n[green]✓ All tests completed[/green]")
    
    asyncio.run(run_tests())

if __name__ == "__main__":
    cli()