# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    "Gateway": "http://localhost:8000/health",
    "Cloud Run": "http://localhost:8001/health",
    "Secrets": "http://localhost:8002/health",
    "Memory": "http://localhost:8003/health",
    "conductor": "http://localhost:8004/health",
}

# Metrics endpoint
METRICS_URL = "http://localhost:8000/metrics"

async def check_health(name: str, url: str) -> dict:
    """Check health of a single server"""
                    "name": name,
                    "status": "✅ Healthy",
                    "latency": f"{latency:.0f}ms",
                    "details": data,
                }
            else:
                return {
                    "name": name,
                    "status": f"⚠️  Error ({response.status_code})",
                    "latency": f"{latency:.0f}ms",
                    "details": {},
                }
    except Exception:

        pass
        return {
            "name": name,
            "status": "❌ Down",
            "latency": "N/A",
            "details": {"error": str(e)},
        }

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
                elif server["name"] == "conductor":
                    details = f"Mode: {server['details'].get('current_mode', 'N/A')}, Workflows: {server['details'].get('active_workflows', 0)}"
                elif server["name"] == "Gateway":
                    details = f"Servers: {server['details'].get('healthy_servers', 0)}/{server['details'].get('total_servers', 0)}"
                else:
                    details = f"Service: {server['details'].get('service', 'N/A')}"

        table.add_row(server["name"], server["status"], server["latency"], details)

    return table

async def get_metrics() -> dict:
    """Get Prometheus metrics"""
                for line in response.text.split("\n"):
                    if line.startswith("#") or not line:
                        continue
                    if "mcp_gateway_requests_total" in line:
                        metrics["requests"] = metrics.get("requests", 0) + 1
                    elif "mcp_gateway_errors_total" in line:
                        metrics["errors"] = metrics.get("errors", 0) + 1
                return metrics
            return {}
    except Exception:

        pass
        console.print(f"Error fetching metrics: {e}", style="red")
        return {}
