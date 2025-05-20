#!/usr/bin/env python3
"""
Migration Error Resolution Tool for AI Orchestra

This script identifies and resolves critical errors encountered during
the GCP migration process. It focuses on fixing MCP server issues and
other common migration problems.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("migration_error_resolution.log"),
    ],
)
logger = logging.getLogger("error-resolution")

# Add parent directory to the Python path
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Constants
MIGRATION_LOG_DIR = "/var/log/mcp"
INCIDENT_REPORT_DIR = "incidents"
DEFAULT_MCP_SERVICE = "mcp-server"


class MigrationErrorResolver:
    """Identifies and resolves migration errors."""

    def __init__(
        self,
        log_dir: Optional[str] = None,
        report_dir: Optional[str] = None,
        mcp_service: str = DEFAULT_MCP_SERVICE,
        verbose: bool = False,
    ):
        """Initialize migration error resolver.

        Args:
            log_dir: Log directory
            report_dir: Incident report directory
            mcp_service: MCP service name
            verbose: Enable verbose logging
        """
        self.log_dir = Path(log_dir or MIGRATION_LOG_DIR)
        self.report_dir = Path(report_dir or INCIDENT_REPORT_DIR)
        self.mcp_service = mcp_service

        # Create report directory if it doesn't exist
        self.report_dir.mkdir(parents=True, exist_ok=True)

        # Set log level
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        # Import diagnostics
        try:
            from gcp_migration.mcp_server_diagnostics import MCPDiagnostics

            self.diagnostics = MCPDiagnostics(service_name=mcp_service)
            self.has_diagnostics = True
        except ImportError:
            logger.warning("MCP server diagnostics not available")
            self.has_diagnostics = False

        logger.info(f"Migration error resolver initialized")

    def parse_error_logs(self, log_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Parse error logs for critical issues.

        Args:
            log_path: Optional specific log path to check

        Returns:
            List of critical errors found
        """
        critical_errors = []

        if log_path:
            log_paths = [Path(log_path)]
        else:
            # Default to migration.log in log directory
            log_paths = [self.log_dir / "migration.log"]

            # Also check for any other log files
            if self.log_dir.exists():
                log_paths.extend(list(self.log_dir.glob("*.log")))

        logger.info(f"Checking {len(log_paths)} log files for errors")

        for log_file in log_paths:
            if not log_file.exists():
                logger.warning(f"Log file not found: {log_file}")
                continue

            logger.info(f"Scanning log file: {log_file}")

            # Look for critical error patterns
            try:
                with open(log_file, "r") as f:
                    for i, line in enumerate(f, 1):
                        # Check for error indicators
                        if any(
                            pattern in line.lower()
                            for pattern in [
                                "critical error",
                                "migration failed",
                                "failed with exit code",
                                "terminated unexpectedly",
                                "connection refused",
                                "cannot connect",
                                "access denied",
                                "permission denied",
                                "out of memory",
                                "disk full",
                                "no space left",
                                "timeout exceeded",
                            ]
                        ):
                            # Extract timestamp
                            timestamp = self._extract_timestamp(line)

                            # Classify error
                            error_type = self._classify_error(line)

                            critical_errors.append(
                                {
                                    "file": str(log_file),
                                    "line": i,
                                    "message": line.strip(),
                                    "timestamp": timestamp,
                                    "type": error_type,
                                }
                            )
            except Exception as e:
                logger.error(f"Error processing log file {log_file}: {e}")

        logger.info(f"Found {len(critical_errors)} critical errors")
        return critical_errors

    def _extract_timestamp(self, log_line: str) -> Optional[str]:
        """Extract timestamp from log line.

        Args:
            log_line: Log line text

        Returns:
            Timestamp string or None
        """
        # Try common timestamp formats
        try:
            # Most common format: 2025-05-13 03:14:39,706
            parts = log_line.split(" ", 2)
            if len(parts) >= 2:
                date_part = parts[0]
                time_part = parts[1].split(",")[0] if "," in parts[1] else parts[1]
                return f"{date_part} {time_part}"
        except:
            pass

        return None

    def _classify_error(self, log_line: str) -> str:
        """Classify error type from log line.

        Args:
            log_line: Log line text

        Returns:
            Error classification
        """
        log_lower = log_line.lower()

        if any(
            pattern in log_lower
            for pattern in ["connection refused", "cannot connect", "timeout"]
        ):
            return "connectivity"
        elif any(
            pattern in log_lower for pattern in ["permission denied", "access denied"]
        ):
            return "permission"
        elif any(
            pattern in log_lower for pattern in ["out of memory", "memory allocation"]
        ):
            return "memory"
        elif any(pattern in log_lower for pattern in ["disk full", "no space left"]):
            return "disk"
        elif any(pattern in log_lower for pattern in ["database", "sql", "query"]):
            return "database"
        elif any(
            pattern in log_lower
            for pattern in ["configuration", "config", "invalid setting"]
        ):
            return "config"
        elif any(
            pattern in log_lower
            for pattern in ["authentication", "unauthorized", "auth"]
        ):
            return "auth"
        else:
            return "unknown"

    def check_mcp_server(self) -> Dict[str, Any]:
        """Check MCP server status.

        Returns:
            Server status information
        """
        logger.info(f"Checking MCP server status")

        status = {
            "service": self.mcp_service,
            "running": False,
            "port_available": False,
            "timestamp": datetime.now().isoformat(),
        }

        # Use systemctl to check if service is running
        try:
            result = subprocess.run(
                ["systemctl", "status", self.mcp_service],
                capture_output=True,
                text=True,
                check=False,
            )

            status["running"] = "active (running)" in result.stdout
            status["systemctl_output"] = result.stdout

            if status["running"]:
                logger.info(f"MCP server service is running")
            else:
                logger.warning(f"MCP server service is not running")
        except Exception as e:
            logger.error(f"Error checking MCP server service: {e}")
            status["error"] = str(e)

        # Check if port 8080 is in use
        try:
            result = subprocess.run(
                ["lsof", "-i", ":8080"],
                capture_output=True,
                text=True,
                check=False,
            )

            status["port_in_use"] = bool(result.stdout.strip())

            if status["port_in_use"]:
                logger.info(f"Port 8080 is in use")
                status["port_available"] = status["running"]
            else:
                logger.warning(f"Port 8080 is not in use")
                status["port_available"] = False
        except Exception as e:
            logger.error(f"Error checking port status: {e}")

        # If diagnostics module is available, use it for detailed status
        if self.has_diagnostics:
            try:
                diag_results = self.diagnostics.run_full_diagnostics()
                status["diagnostics"] = diag_results
            except Exception as e:
                logger.error(f"Error running diagnostics: {e}")

        return status

    def repair_mcp_server(self) -> Dict[str, Any]:
        """Attempt to repair MCP server.

        Returns:
            Repair results
        """
        logger.info(f"Attempting to repair MCP server")

        results = {
            "timestamp": datetime.now().isoformat(),
            "service": self.mcp_service,
            "actions": [],
            "success": False,
        }

        # Check current status
        status = self.check_mcp_server()

        if status.get("running", False):
            logger.info(f"MCP server is already running")
            results["actions"].append(
                {"action": "check_status", "result": "Service already running"}
            )
            results["success"] = True
            return results

        # If diagnostics module is available, use it for repairs
        if self.has_diagnostics:
            try:
                repairs = self.diagnostics.repair_common_issues()
                results["diagnostics_repair"] = repairs

                # Check if repairs were successful
                status_after = self.check_mcp_server()
                if status_after.get("running", False):
                    logger.info(f"MCP server repaired successfully via diagnostics")
                    results["actions"].append(
                        {"action": "diagnostic_repair", "result": "Successful"}
                    )
                    results["success"] = True
                    return results
            except Exception as e:
                logger.error(f"Error running diagnostics repairs: {e}")

        # Attempt manual repairs if diagnostics failed or isn't available

        # 1. Try restarting the service
        try:
            logger.info(f"Attempting to restart service: {self.mcp_service}")
            result = subprocess.run(
                ["sudo", "systemctl", "restart", self.mcp_service],
                capture_output=True,
                text=True,
                check=False,
            )

            results["actions"].append(
                {
                    "action": "restart_service",
                    "command": f"sudo systemctl restart {self.mcp_service}",
                    "exit_code": result.returncode,
                    "output": result.stdout,
                    "error": result.stderr,
                    "success": result.returncode == 0,
                }
            )

            if result.returncode == 0:
                logger.info(f"Successfully restarted MCP server service")

                # Check if service is now running
                time.sleep(2)  # Give it a moment to start
                status_after = self.check_mcp_server()
                if status_after.get("running", False):
                    logger.info(f"MCP server is now running")
                    results["success"] = True
                    return results
            else:
                logger.error(f"Failed to restart service: {result.stderr}")
        except Exception as e:
            logger.error(f"Error restarting service: {e}")
            results["actions"].append(
                {"action": "restart_service", "success": False, "error": str(e)}
            )

        # 2. Check if port is in use by another process
        if status.get("port_in_use", False) and not status.get("running", False):
            try:
                logger.info("Checking what's using port 8080")
                result = subprocess.run(
                    ["sudo", "lsof", "-i", ":8080"],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                results["actions"].append(
                    {
                        "action": "check_port",
                        "command": "sudo lsof -i :8080",
                        "output": result.stdout,
                        "success": result.returncode == 0,
                    }
                )

                # Extract PID if possible
                pid = None
                if result.stdout:
                    lines = result.stdout.strip().split("\n")
                    if len(lines) > 1:  # Header + at least one process
                        parts = lines[1].split()
                        if len(parts) > 1:
                            try:
                                pid = int(parts[1])
                            except:
                                pass

                # If we found a PID, try to terminate it
                if pid:
                    logger.info(
                        f"Attempting to terminate process using port 8080 (PID {pid})"
                    )
                    term_result = subprocess.run(
                        ["sudo", "kill", str(pid)],
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    results["actions"].append(
                        {
                            "action": "terminate_process",
                            "command": f"sudo kill {pid}",
                            "exit_code": term_result.returncode,
                            "success": term_result.returncode == 0,
                        }
                    )

                    if term_result.returncode == 0:
                        logger.info(f"Successfully terminated process using port 8080")

                        # Try starting the service again
                        time.sleep(1)
                        restart_result = subprocess.run(
                            ["sudo", "systemctl", "start", self.mcp_service],
                            capture_output=True,
                            text=True,
                            check=False,
                        )

                        results["actions"].append(
                            {
                                "action": "start_service_after_port_clear",
                                "command": f"sudo systemctl start {self.mcp_service}",
                                "exit_code": restart_result.returncode,
                                "success": restart_result.returncode == 0,
                            }
                        )

                        if restart_result.returncode == 0:
                            logger.info(
                                f"Successfully started service after clearing port"
                            )
                            results["success"] = True
                            return results
            except Exception as e:
                logger.error(f"Error handling port conflict: {e}")
                results["actions"].append(
                    {
                        "action": "handle_port_conflict",
                        "success": False,
                        "error": str(e),
                    }
                )

        # 3. Check logs for specific errors
        try:
            service_logs = subprocess.run(
                [
                    "sudo",
                    "journalctl",
                    "-u",
                    self.mcp_service,
                    "--no-pager",
                    "-n",
                    "50",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            log_output = service_logs.stdout
            results["actions"].append(
                {
                    "action": "check_service_logs",
                    "command": f"sudo journalctl -u {self.mcp_service} --no-pager -n 50",
                    "success": service_logs.returncode == 0,
                }
            )

            # Look for specific issues in the logs
            if "no space left on device" in log_output.lower():
                logger.error("Disk space issue detected")
                results["actions"].append(
                    {
                        "action": "detect_issue",
                        "issue": "disk_space",
                        "suggestion": "Free up disk space: sudo du -sh /* | sort -hr",
                    }
                )
            elif "permission denied" in log_output.lower():
                logger.error("Permission issue detected")
                results["actions"].append(
                    {
                        "action": "detect_issue",
                        "issue": "permissions",
                        "suggestion": f"Check directory permissions: sudo ls -la /var/lib/mcp",
                    }
                )
            elif "cannot bind to address" in log_output.lower():
                logger.error("Address binding issue detected")
                results["actions"].append(
                    {
                        "action": "detect_issue",
                        "issue": "address_binding",
                        "suggestion": "Check network interfaces: ip addr show",
                    }
                )
            elif (
                "configuration file" in log_output.lower()
                and "error" in log_output.lower()
            ):
                logger.error("Configuration file issue detected")
                results["actions"].append(
                    {
                        "action": "detect_issue",
                        "issue": "config_file",
                        "suggestion": f"Check configuration files: sudo cat /etc/mcp/config.json",
                    }
                )
        except Exception as e:
            logger.error(f"Error checking service logs: {e}")
            results["actions"].append(
                {"action": "check_service_logs", "success": False, "error": str(e)}
            )

        return results

    def verify_data_integrity(self) -> Dict[str, Any]:
        """Verify data integrity after migration.

        Returns:
            Data integrity status
        """
        logger.info("Verifying data integrity")

        results = {
            "timestamp": datetime.now().isoformat(),
            "checks": [],
            "all_passed": True,
        }

        # Check MCP data directory
        data_dir = Path("/var/lib/mcp")
        if data_dir.exists():
            results["checks"].append(
                {"check": "data_dir_exists", "path": str(data_dir), "passed": True}
            )

            # Check for data files
            data_files = list(data_dir.glob("*.json"))
            data_files.extend(list(data_dir.glob("*.db")))

            results["checks"].append(
                {
                    "check": "data_files_exist",
                    "path": str(data_dir),
                    "file_count": len(data_files),
                    "passed": len(data_files) > 0,
                }
            )

            if len(data_files) == 0:
                results["all_passed"] = False
        else:
            results["checks"].append(
                {"check": "data_dir_exists", "path": str(data_dir), "passed": False}
            )
            results["all_passed"] = False

        # If MCP server is running, try to access it
        if self.check_mcp_server().get("running", False):
            try:
                import requests

                response = requests.get("http://localhost:8080/health", timeout=5)

                results["checks"].append(
                    {
                        "check": "api_health",
                        "status_code": response.status_code,
                        "response": response.text,
                        "passed": response.status_code == 200,
                    }
                )

                if response.status_code != 200:
                    results["all_passed"] = False
            except Exception as e:
                logger.error(f"Error checking API health: {e}")
                results["checks"].append(
                    {"check": "api_health", "error": str(e), "passed": False}
                )
                results["all_passed"] = False
        else:
            results["checks"].append(
                {
                    "check": "api_health",
                    "message": "MCP server not running, cannot check API health",
                    "passed": False,
                }
            )
            results["all_passed"] = False

        return results

    def generate_incident_report(
        self, issues: List[Dict[str, Any]], repairs: Dict[str, Any]
    ) -> str:
        """Generate incident report from issues and repairs.

        Args:
            issues: List of identified issues
            repairs: Repair actions taken

        Returns:
            Path to incident report file
        """
        logger.info("Generating incident report")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.report_dir / f"migration_incident_{timestamp}.md"

        # Create report content
        lines = []
        lines.append("# Migration Incident Report")
        lines.append("")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Summary section
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Service**: {self.mcp_service}")
        lines.append(
            f"- **Status**: {'Resolved' if repairs.get('success', False) else 'Unresolved'}"
        )
        lines.append(f"- **Critical Issues**: {len(issues)}")
        lines.append(f"- **Repair Actions**: {len(repairs.get('actions', []))}")
        lines.append("")

        # Issues section
        lines.append("## Critical Issues")
        lines.append("")

        if issues:
            for i, issue in enumerate(issues, 1):
                lines.append(f"{i}. **{issue.get('type', 'Unknown').title()} Error**")
                lines.append(f"   * File: {issue.get('file', 'Unknown')}")
                lines.append(f"   * Line: {issue.get('line', 'Unknown')}")
                lines.append(f"   * Time: {issue.get('timestamp', 'Unknown')}")
                lines.append(f"   * Message: `{issue.get('message', 'No message')}`")
                lines.append("")
        else:
            lines.append("No critical issues found.")
            lines.append("")

        # Repair actions section
        lines.append("## Repair Actions")
        lines.append("")

        actions = repairs.get("actions", [])
        if actions:
            for i, action in enumerate(actions, 1):
                lines.append(
                    f"{i}. **{action.get('action', 'Unknown').replace('_', ' ').title()}**"
                )
                lines.append(
                    f"   * Result: {'✅ Success' if action.get('success', False) else '❌ Failed'}"
                )

                if "command" in action:
                    lines.append(f"   * Command: `{action['command']}`")

                if "error" in action:
                    lines.append(f"   * Error: {action['error']}")

                if "suggestion" in action:
                    lines.append(f"   * Suggestion: {action['suggestion']}")

                lines.append("")
        else:
            lines.append("No repair actions taken.")
            lines.append("")

        # Verification section
        lines.append("## Data Integrity Verification")
        lines.append("")

        integrity = self.verify_data_integrity()
        lines.append(
            f"Overall Status: {'✅ All checks passed' if integrity.get('all_passed', False) else '❌ Some checks failed'}"
        )
        lines.append("")

        for check in integrity.get("checks", []):
            status = "✅ Passed" if check.get("passed", False) else "❌ Failed"
            lines.append(
                f"- **{check.get('check', 'Unknown').replace('_', ' ').title()}**: {status}"
            )

            if "path" in check:
                lines.append(f"  * Path: {check['path']}")

            if "file_count" in check:
                lines.append(f"  * Files: {check['file_count']}")

            if "error" in check:
                lines.append(f"  * Error: {check['error']}")

            if "message" in check:
                lines.append(f"  * Message: {check['message']}")

            lines.append("")

        # Next steps section
        lines.append("## Next Steps")
        lines.append("")

        if repairs.get("success", False) and integrity.get("all_passed", False):
            lines.append("✅ **All issues resolved. Migration can proceed.**")
            lines.append("")
            lines.append("Recommended actions:")
            lines.append("1. Monitor the MCP service for any recurring issues")
            lines.append("2. Proceed with the next migration phase")
            lines.append("3. Update documentation with resolution steps")
        elif repairs.get("success", False):
            lines.append("⚠️ **Service repaired but data integrity issues detected.**")
            lines.append("")
            lines.append("Recommended actions:")
            lines.append("1. Verify data consistency manually")
            lines.append("2. Run data repair utilities if needed")
            lines.append("3. Restart the migration process once data is verified")
        else:
            lines.append("❌ **Unresolved issues require manual intervention.**")
            lines.append("")
            lines.append("Recommended actions:")
            lines.append(
                "1. Check service logs: `sudo journalctl -u mcp-server --no-pager`"
            )
            lines.append("2. Verify configuration files: `cat /etc/mcp/config.json`")
            lines.append("3. Check disk space: `df -h`")
            lines.append("4. Check permissions: `ls -la /var/lib/mcp`")
            lines.append("5. Contact system administrator for assistance")

        # Write report to file
        try:
            with open(report_file, "w") as f:
                f.write("\n".join(lines))
            logger.info(f"Incident report saved to {report_file}")
        except Exception as e:
            logger.error(f"Error saving incident report: {e}")
            # Try writing to current directory
            try:
                backup_file = f"migration_incident_{timestamp}.md"
                with open(backup_file, "w") as f:
                    f.write("\n".join(lines))
                report_file = Path(backup_file)
                logger.info(f"Incident report saved to {report_file}")
            except Exception as e2:
                logger.error(f"Error saving backup incident report: {e2}")

        return str(report_file)


def main() -> int:
    """Main entry point.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Migration Error Resolution Tool")
    parser.add_argument("--log-path", help="Path to migration log file")
    parser.add_argument("--log-dir", default=MIGRATION_LOG_DIR, help="Log directory")
    parser.add_argument(
        "--report-dir", default=INCIDENT_REPORT_DIR, help="Incident report directory"
    )
    parser.add_argument(
        "--service", default=DEFAULT_MCP_SERVICE, help="MCP service name"
    )
    parser.add_argument(
        "--check", action="store_true", help="Check for critical errors"
    )
    parser.add_argument(
        "--repair", action="store_true", help="Attempt to repair issues"
    )
    parser.add_argument("--verify", action="store_true", help="Verify data integrity")
    parser.add_argument(
        "--report", action="store_true", help="Generate incident report"
    )
    parser.add_argument("--all", action="store_true", help="Run all actions")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Initialize resolver
    resolver = MigrationErrorResolver(
        log_dir=args.log_dir,
        report_dir=args.report_dir,
        mcp_service=args.service,
        verbose=args.verbose,
    )

    # If no specific actions requested, use --all
    if not (args.check or args.repair or args.verify or args.report):
        args.all = True

    results = {}
    critical_issues = []
    repair_results = {}
    integrity_results = {}
    report_path = None

    # Check for critical errors
    if args.check or args.all:
        critical_issues = resolver.parse_error_logs(args.log_path)
        results["critical_issues"] = critical_issues

        if not args.json:
            print("\n=== Critical Migration Errors ===\n")

            if critical_issues:
                print(f"Found {len(critical_issues)} critical errors:")
                for i, issue in enumerate(critical_issues[:5], 1):  # Show up to 5
                    print(f"{i}. {issue.get('type', 'Unknown').title()} Error")
                    print(
                        f"   File: {issue.get('file', 'Unknown')}:{issue.get('line', 'Unknown')}"
                    )
                    print(f"   Time: {issue.get('timestamp', 'Unknown')}")
                    print(f"   Message: {issue.get('message', 'No message')}")
                    print()

                if len(critical_issues) > 5:
                    print(f"... and {len(critical_issues) - 5} more errors")
            else:
                print("No critical errors found in logs")

            print()

    # Check MCP server status
    if args.repair or args.all:
        print("\n=== MCP Server Status ===\n")
        server_status = resolver.check_mcp_server()
        results["server_status"] = server_status

        if not args.json:
            print(f"Service: {server_status.get('service', 'unknown')}")
            print(f"Running: {'Yes' if server_status.get('running', False) else 'No'}")
            print(
                f"Port Available: {'Yes' if server_status.get('port_available', False) else 'No'}"
            )
            print()

    # Attempt repairs if needed
    if (args.repair or args.all) and (
        critical_issues or not server_status.get("running", False)
    ):
        print("\n=== Repairing MCP Server ===\n")
        repair_results = resolver.repair_mcp_server()
        results["repair_results"] = repair_results

        if not args.json:
            print(
                f"Repair {'successful' if repair_results.get('success', False) else 'failed'}"
            )

            actions = repair_results.get("actions", [])
            if actions:
                print("\nActions taken:")
                for i, action in enumerate(actions, 1):
                    status = "✅ Success" if action.get("success", False) else "❌ Failed"
                    print(
                        f"{i}. {action.get('action', 'Unknown').replace('_', ' ').title()}: {status}"
                    )

                    if "command" in action:
                        print(f"   Command: {action['command']}")

                    if "error" in action:
                        print(f"   Error: {action['error']}")

                    if "suggestion" in action:
                        print(f"   Suggestion: {action['suggestion']}")

                print()

    # Verify data integrity
    if args.verify or args.all:
        print("\n=== Verifying Data Integrity ===\n")
        integrity_results = resolver.verify_data_integrity()
        results["integrity_results"] = integrity_results

        if not args.json:
            status = (
                "All checks passed"
                if integrity_results.get("all_passed", False)
                else "Some checks failed"
            )
            print(f"Overall Status: {status}")
            print()

            for check in integrity_results.get("checks", []):
                status = "✅ Passed" if check.get("passed", False) else "❌ Failed"
                print(
                    f"- {check.get('check', 'Unknown').replace('_', ' ').title()}: {status}"
                )

                for key, value in check.items():
                    if key not in ["check", "passed"]:
                        print(f"  * {key}: {value}")

                print()

    # Generate incident report
    if args.report or args.all:
        report_path = resolver.generate_incident_report(critical_issues, repair_results)
        results["report_path"] = report_path

        if not args.json:
            print("\n=== Incident Report ===\n")
            print(f"Incident report saved to: {report_path}")
            print()

            # Try to open the report with default application
            if sys.platform.startswith("darwin"):  # macOS
                os.system(f"open {report_path}")
            elif sys.platform.startswith("win"):  # Windows
                os.system(f"start {report_path}")
            elif sys.platform.startswith("linux"):  # Linux
                os.system(f"xdg-open {report_path} 2>/dev/null")

    # Output JSON if requested
    if args.json:
        print(json.dumps(results, indent=2))

    # Determine exit code based on results
    if critical_issues and not repair_results.get("success", False):
        return 1  # Error
    elif repair_results.get("success", False) and not integrity_results.get(
        "all_passed", False
    ):
        return 2  # Warning
    else:
        return 0  # Success


if __name__ == "__main__":
    sys.exit(main())
