# TODO: Consider adding connection pooling configuration
import asyncio
#!/usr/bin/env python3
"""
"""
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class HealthMonitor:
    """Simple health monitoring for cherry_ai services."""
    def __init__(self, admin_ui_url: str = "http://localhost:3000") -> None:
        self.admin_ui_url = admin_ui_url
        self.services: dict[str, dict[str, Any]] = {
            "mcp_os.environ": {"port": 8002, "name": "MCP Secret Manager"},
            "mcp_firestore": {"port": 8080, "name": "MCP mongodb"},
            "conductor": {"port": 8080, "name": "Core conductor"},
        }

    def check_port(self, port: int, timeout: float = 2.0) -> bool:
        """Check if a port is responding."""
                result = sock.connect_ex(("localhost", port))
                return result == 0
        except Exception:

            pass
            return False

    def check_service_health(self, service_name: str, config: dict[str, Any]) -> dict[str, Any]:
        """Check health of a specific service."""
        port = config["port"]
        name = config["name"]

        result = {
            "service": service_name,
            "name": name,
            "port": port,
            "status": "unknown",
            "response_time": None,
            "timestamp": datetime.now().isoformat(),
            "details": {},
        }

        # Check port connectivity
        start_time = time.time()
        port_up = self.check_port(port)
        response_time = time.time() - start_time

        result["response_time"] = round(response_time, 3)

        if port_up:
            result["status"] = "healthy"
            result["details"]["port_accessible"] = True

            # Try HTTP health check if possible
            try:

                pass
                health_url = f"http://localhost:{port}/health"
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    result["details"]["http_health"] = "ok"
                    result["details"]["http_response"] = response.json()
                else:
                    result["details"]["http_health"] = f"status_{response.status_code}"
            except Exception:

                pass
                result["details"]["http_health"] = f"error: {str(e)}"
        else:
            result["status"] = "unhealthy"
            result["details"]["port_accessible"] = False

        return result

    def check_all_services(self) -> dict[str, Any]:
        """Check health of all configured services."""
        logger.info("Checking health of all services...")

        results: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "services": {},
            "summary": {"total": len(self.services), "healthy": 0, "unhealthy": 0},
        }

        for service_name, config in self.services.items():
            service_result = self.check_service_health(service_name, config)
            results["services"][service_name] = service_result

            if service_result["status"] == "healthy":
                results["summary"]["healthy"] += 1
            else:
                results["summary"]["unhealthy"] += 1
                results["overall_status"] = "degraded"

        if results["summary"]["unhealthy"] == len(self.services):
            results["overall_status"] = "critical"

        return results

    def send_notification(self, message: str, level: str = "info", data: dict[str, Any] | None = None) -> bool:
        """Send notification to admin UI."""
                "message": message,
                "level": level,
                "timestamp": datetime.now().isoformat(),
                "source": "health_monitor",
                "data": data or {},
            }

            # Try to send to admin UI notification endpoint
            response = requests.post(
                f"{self.admin_ui_url}/api/notifications",
                json=notification_payload,
                timeout=5,
            )

            if response.status_code in [200, 201]:
                logger.info(f"Notification sent successfully: {message}")
                return True
            else:
                logger.warning(f"Notification failed with status {response.status_code}")
                return False

        except Exception:


            pass
            logger.error(f"Failed to send notification: {e}")
            # Fall back to console logging
            logger.warning(f"NOTIFICATION: [{level.upper()}] {message}")
            return False

    def wait_for_service(self, service_name: str, max_wait: int = 120, check_interval: int = 5) -> bool:
        """
        """
            logger.error(f"Unknown service: {service_name}")
            return False

        config = self.services[service_name]
        logger.info(f"Waiting for {config['name']} to become healthy (max {max_wait}s)...")

        start_time = time.time()
        while time.time() - start_time < max_wait:
            result = self.check_service_health(service_name, config)

            if result["status"] == "healthy":
                elapsed = round(time.time() - start_time, 1)
                logger.info(f"{config['name']} is healthy after {elapsed}s")
                self.send_notification(
                    f"Service {config['name']} is now healthy",
                    level="success",
                    data={"service": service_name, "wait_time": elapsed},
                )
                return True

            await asyncio.sleep(check_interval)

        # Service didn't come up in time
        elapsed = round(time.time() - start_time, 1)
        logger.error(f"{config['name']} failed to become healthy after {elapsed}s")
        self.send_notification(
            f"Service {config['name']} failed to start within {max_wait}s",
            level="error",
            data={"service": service_name, "wait_time": elapsed},
        )
        return False

    async def monitor_continuously(self, interval: int = 30) -> None:
        """Monitor services continuously and alert on changes."""
        logger.info(f"Starting continuous monitoring (interval: {interval}s)")

        previous_status: dict[str, Any] | None = None
        consecutive_failures: dict[str, int] = {}

        while True:
            try:

                pass
                current_status = self.check_all_services()

                # Check for status changes
                if previous_status:
                    for service_name, current in current_status["services"].items():
                        previous = previous_status["services"].get(service_name, {})

                        if previous.get("status") != current["status"]:
                            if current["status"] == "healthy":
                                self.send_notification(
                                    f"Service {current['name']} recovered",
                                    level="success",
                                    data=current,
                                )
                                consecutive_failures.pop(service_name, None)
                            else:
                                consecutive_failures[service_name] = consecutive_failures.get(service_name, 0) + 1
                                failure_count = consecutive_failures[service_name]

                                self.send_notification(
                                    f"Service {current['name']} unhealthy (failure #{failure_count})",
                                    level="warning" if failure_count < 3 else "error",
                                    data=current,
                                )

                # Log current status
                healthy_count = current_status["summary"]["healthy"]
                total_count = current_status["summary"]["total"]
                logger.info(f"Health check: {healthy_count}/{total_count} services healthy")

                previous_status = current_status
                await asyncio.sleep(interval)

            except Exception:


                pass
                logger.info("Monitoring stopped by user")
                break
            except Exception:

                pass
                logger.error(f"Error during monitoring: {e}")
                await asyncio.sleep(interval)

    def check_prerequisites(self) -> dict[str, Any]:
        """Check system prerequisites and dependencies."""
            "timestamp": datetime.now().isoformat(),
            "status": "ok",
            "checks": {},
        }

        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        python_ok = sys.version_info >= (3, 11)
        results["checks"]["python_version"] = {
            "status": "ok" if python_ok else "error",
            "value": python_version,
            "required": "3.11+",
        }
        if not python_ok:
            results["status"] = "error"

        # Check virtual environment
        in_venv = hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
        results["checks"]["virtual_environment"] = {
            "status": "ok" if in_venv else "warning",
            "active": in_venv,
        }

        # Check required files
        required_files = [
            "requirements/base.txt",
            "scripts/check_venv.py",
            "core/conductor/src/api/app.py",
        ]

        missing_files: list[str] = []
        for file_path in required_files:
            import os

            if not os.path.exists(file_path):
                missing_files.append(file_path)

        results["checks"]["required_files"] = {
            "status": "ok" if not missing_files else "error",
            "missing": missing_files,
        }
        if missing_files:
            results["status"] = "error"

        return results

def main() -> int:
    """Main entry point for the health monitor."""
    parser = argparse.ArgumentParser(description="AI cherry_ai Health Monitor")
    parser.add_argument("--check-services", action="store_true", help="Check all services once")
    parser.add_argument("--monitor", action="store_true", help="Monitor continuously")
    parser.add_argument("--wait-for", help="Wait for specific service to be healthy")
    parser.add_argument("--interval", type=int, default=30, help="Monitoring interval in seconds")
    parser.add_argument("--max-wait", type=int, default=120, help="Maximum wait time for service")
    parser.add_argument(
        "--admin-ui-url",
        default="http://localhost:3000",
        help="Admin UI URL for notifications",
    )
    parser.add_argument("--check-prereqs", action="store_true", help="Check system prerequisites")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    monitor = HealthMonitor(admin_ui_url=args.admin_ui_url)

    if args.check_prereqs:
        results = monitor.check_prerequisites()
        logger.info(json.dumps(results, indent=2))
        return 0 if results["status"] == "ok" else 1

    if args.check_services:
        results = monitor.check_all_services()
        logger.info(json.dumps(results, indent=2))
        return 0 if results["overall_status"] == "healthy" else 1

    if args.wait_for:
        success = monitor.wait_for_service(args.wait_for, max_wait=args.max_wait)
        return 0 if success else 1

    if args.monitor:
        try:

            pass
            asyncio.run(monitor.monitor_continuously(interval=args.interval))
        except Exception:

            pass
            logger.info("Monitoring stopped")
        return 0

    # Default: show help
    parser.print_help()
    return 1

if __name__ == "__main__":
    sys.exit(main())
