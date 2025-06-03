import asyncio
#!/usr/bin/env python3
"""
"""
    """Metrics for a single server"""
    status: str = "unknown"
    response_time: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0
    request_count: int = 0
    error_count: int = 0
    error_rate: float = 0.0
    uptime_seconds: float = 0.0
    last_check: Optional[datetime] = None
    health_details: Dict[str, Any] = field(default_factory=dict)
    response_times: deque = field(default_factory=lambda: deque(maxlen=60))
    error_history: deque = field(default_factory=lambda: deque(maxlen=100))

class MCPHealthDashboard:
    """Real-time health monitoring dashboard for MCP servers"""
            "orchestrator": ServerMetrics(name="Orchestrator", url="http://localhost:8002/health", port=8002),
            "memory": ServerMetrics(name="Memory", url="http://localhost:8003/health", port=8003),
            "tools": ServerMetrics(name="Tools", url="http://localhost:8006/health", port=8006),
            "weaviate": ServerMetrics(
                name="Weaviate Direct", url="http://localhost:8001/mcp/weaviate_direct/health", port=8001
            ),
        }

        # Performance tracking
        self.start_time = time.time()
        self.total_checks = 0
        self.failed_checks = defaultdict(int)

        # Alert thresholds
        self.thresholds = {
            "response_time_ms": 1000,
            "error_rate_percent": 10,
            "memory_usage_mb": 500,
            "cpu_percent": 80,
        }

        # Alert history
        self.alerts = deque(maxlen=50)

    async def check_server_health(self, server_key: str, server: ServerMetrics) -> None:
        """Check health of a single server"""
                        server.status = data.get("status", "healthy")
                        server.health_details = data

                        if "metrics" in data:
                            metrics = data["metrics"]
                            server.memory_usage_mb = metrics.get("memory_usage_mb", 0)
                            server.cpu_percent = metrics.get("cpu_percent", 0)
                            server.request_count = metrics.get("request_count", 0)
                            server.error_count = metrics.get("error_count", 0)
                            server.error_rate = metrics.get("error_rate", 0)
                            server.uptime_seconds = metrics.get("uptime_seconds", 0)

                        # Check for alerts
                        self._check_alerts(server_key, server)
                    else:
                        server.status = "unhealthy"
                        server.error_history.append({"time": datetime.now(), "error": f"HTTP {response.status}"})
                        self.failed_checks[server_key] += 1

        except Exception:


            pass
            server.status = "timeout"
            server.response_time = 5000  # 5s timeout
            server.error_history.append({"time": datetime.now(), "error": "Timeout"})
            self.failed_checks[server_key] += 1

        except Exception:


            pass
            server.status = "error"
            server.error_history.append({"time": datetime.now(), "error": str(e)})
            self.failed_checks[server_key] += 1

        server.last_check = datetime.now()
        self.total_checks += 1

    def _check_alerts(self, server_key: str, server: ServerMetrics) -> None:
        """Check if any metrics exceed thresholds"""
        if server.response_time > self.thresholds["response_time_ms"]:
            alerts.append(f"High response time: {server.response_time:.0f}ms")

        if server.error_rate > self.thresholds["error_rate_percent"]:
            alerts.append(f"High error rate: {server.error_rate:.1f}%")

        if server.memory_usage_mb > self.thresholds["memory_usage_mb"]:
            alerts.append(f"High memory usage: {server.memory_usage_mb:.0f}MB")

        if server.cpu_percent > self.thresholds["cpu_percent"]:
            alerts.append(f"High CPU usage: {server.cpu_percent:.1f}%")

        for alert in alerts:
            self.alerts.append({"time": datetime.now(), "server": server.name, "alert": alert})

    async def check_all_servers(self) -> None:
        """Check health of all servers concurrently"""
        """Get overall system metrics"""
        disk = psutil.disk_usage("/")

        return {
            "uptime": uptime,
            "total_checks": self.total_checks,
            "success_rate": success_rate,
            "system_cpu": cpu_percent,
            "system_memory": memory.percent,
            "system_disk": disk.percent,
            "active_servers": sum(1 for s in self.servers.values() if s.status == "healthy"),
            "total_servers": len(self.servers),
        }

    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.0f}m {seconds%60:.0f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h {minutes:.0f}m"

    def draw_dashboard(self, stdscr) -> None:
        """Draw the dashboard using curses"""
                header = "MCP Health Monitoring Dashboard"
                stdscr.addstr(0, (width - len(header)) // 2, header, curses.A_BOLD)
                stdscr.addstr(1, 0, "=" * width)

                # System metrics
                system_metrics = self.get_system_metrics()
                row = 3

                stdscr.addstr(row, 0, "System Overview:", curses.A_BOLD)
                row += 1

                status_line = (
                    f"Uptime: {self.format_duration(system_metrics['uptime'])} | "
                    f"Checks: {system_metrics['total_checks']} | "
                    f"Success Rate: {system_metrics['success_rate']:.1f}% | "
                    f"Active: {system_metrics['active_servers']}/{system_metrics['total_servers']}"
                )
                stdscr.addstr(row, 2, status_line)
                row += 1

                resource_line = (
                    f"System - CPU: {system_metrics['system_cpu']:.1f}% | "
                    f"Memory: {system_metrics['system_memory']:.1f}% | "
                    f"Disk: {system_metrics['system_disk']:.1f}%"
                )
                stdscr.addstr(row, 2, resource_line)
                row += 2

                # Server status table
                stdscr.addstr(row, 0, "Server Status:", curses.A_BOLD)
                row += 1
                stdscr.addstr(row, 0, "-" * width)
                row += 1

                # Table headers
                headers = ["Server", "Status", "Response", "Memory", "CPU", "Requests", "Errors", "Uptime"]
                col_widths = [15, 10, 10, 10, 8, 10, 10, 12]

                col = 0
                for i, header in enumerate(headers):
                    stdscr.addstr(row, col, header, curses.A_BOLD)
                    col += col_widths[i]
                row += 1
                stdscr.addstr(row, 0, "-" * width)
                row += 1

                # Server rows
                for server_key, server in self.servers.items():
                    col = 0

                    # Server name
                    stdscr.addstr(row, col, server.name[: col_widths[0] - 1])
                    col += col_widths[0]

                    # Status with color
                    status_color = curses.color_pair(1)  # Green
                    if server.status == "unhealthy":
                        status_color = curses.color_pair(3)  # Yellow
                    elif server.status in ["error", "timeout"]:
                        status_color = curses.color_pair(2)  # Red
                    elif server.status == "unknown":
                        status_color = curses.color_pair(5)  # White

                    stdscr.addstr(row, col, server.status[: col_widths[1] - 1], status_color)
                    col += col_widths[1]

                    # Response time
                    resp_time = f"{server.response_time:.0f}ms"
                    resp_color = curses.color_pair(5)
                    if server.response_time > self.thresholds["response_time_ms"]:
                        resp_color = curses.color_pair(2)
                    stdscr.addstr(row, col, resp_time[: col_widths[2] - 1], resp_color)
                    col += col_widths[2]

                    # Memory
                    mem_str = f"{server.memory_usage_mb:.0f}MB"
                    mem_color = curses.color_pair(5)
                    if server.memory_usage_mb > self.thresholds["memory_usage_mb"]:
                        mem_color = curses.color_pair(2)
                    stdscr.addstr(row, col, mem_str[: col_widths[3] - 1], mem_color)
                    col += col_widths[3]

                    # CPU
                    cpu_str = f"{server.cpu_percent:.1f}%"
                    cpu_color = curses.color_pair(5)
                    if server.cpu_percent > self.thresholds["cpu_percent"]:
                        cpu_color = curses.color_pair(2)
                    stdscr.addstr(row, col, cpu_str[: col_widths[4] - 1], cpu_color)
                    col += col_widths[4]

                    # Requests
                    stdscr.addstr(row, col, str(server.request_count)[: col_widths[5] - 1])
                    col += col_widths[5]

                    # Errors
                    error_str = f"{server.error_count}"
                    if server.error_rate > 0:
                        error_str += f" ({server.error_rate:.1f}%)"
                    error_color = curses.color_pair(5)
                    if server.error_rate > self.thresholds["error_rate_percent"]:
                        error_color = curses.color_pair(2)
                    stdscr.addstr(row, col, error_str[: col_widths[6] - 1], error_color)
                    col += col_widths[6]

                    # Uptime
                    uptime_str = self.format_duration(server.uptime_seconds)
                    stdscr.addstr(row, col, uptime_str[: col_widths[7] - 1])

                    row += 1

                row += 1

                # Recent alerts
                if self.alerts and row < height - 5:
                    stdscr.addstr(row, 0, "Recent Alerts:", curses.A_BOLD)
                    row += 1

                    alert_count = min(5, len(self.alerts), height - row - 2)
                    for i in range(alert_count):
                        alert = self.alerts[-(i + 1)]
                        alert_time = alert["time"].strftime("%H:%M:%S")
                        alert_msg = f"[{alert_time}] {alert['server']}: {alert['alert']}"
                        stdscr.addstr(row, 2, alert_msg[: width - 3], curses.color_pair(3))
                        row += 1

                # Footer
                footer = f"Press 'q' to quit | Refresh: {self.refresh_interval}s | Last update: {datetime.now().strftime('%H:%M:%S')}"
                stdscr.addstr(height - 1, 0, footer, curses.A_DIM)

                # Refresh
                stdscr.refresh()

                # Check for quit
                key = stdscr.getch()
                if key == ord("q") or key == ord("Q"):
                    break

                # Wait before next update
                await asyncio.sleep(0.1)

            except Exception:


                pass
                break
            except Exception:

                pass
                # Handle resize or other curses errors
                pass

    async def run_monitoring_loop(self, stdscr) -> None:
        """Run the monitoring loop"""
        """Run a single health check and return results"""
        results = {"timestamp": datetime.now().isoformat(), "system": self.get_system_metrics(), "servers": {}}

        for key, server in self.servers.items():
            results["servers"][key] = {
                "name": server.name,
                "status": server.status,
                "response_time_ms": server.response_time,
                "memory_usage_mb": server.memory_usage_mb,
                "cpu_percent": server.cpu_percent,
                "request_count": server.request_count,
                "error_count": server.error_count,
                "error_rate": server.error_rate,
                "uptime_seconds": server.uptime_seconds,
                "last_check": server.last_check.isoformat() if server.last_check else None,
            }

        return results

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="MCP Health Monitoring Dashboard")
    parser.add_argument("--once", action="store_true", help="Run once and output JSON results")
    parser.add_argument("--interval", type=int, default=5, help="Refresh interval in seconds (default: 5)")
    parser.add_argument("--output", type=str, help="Output file for JSON results (with --once)")

    args = parser.parse_args()

    dashboard = MCPHealthDashboard(refresh_interval=args.interval)

    if args.once:
        # Run once and output results
        results = dashboard.run_once()

        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"Results written to {args.output}")
        else:
            print(json.dumps(results, indent=2))
    else:
        # Run interactive dashboard
        try:

            pass
            curses.wrapper(lambda stdscr: asyncio.run(dashboard.run_monitoring_loop(stdscr)))
        except Exception:

            pass
            print("\nDashboard stopped.")

if __name__ == "__main__":
    main()
