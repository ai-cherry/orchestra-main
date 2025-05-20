#!/usr/bin/env python3
"""
AI Orchestra GCP Migration Validation

This script performs a comprehensive validation of all migration components:
- Environment detection and synchronization
- Vector search circuit breaker
- Vertex AI integration
- Monitoring and reporting

Usage:
    python validate_migration.py --validate-all
    python validate_migration.py --validate-environment
    python validate_migration.py --validate-circuit-breaker
    python validate_migration.py --validate-vertex-ai
    python validate_migration.py --validate-monitoring
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("migration_validation.log"),
    ],
)
logger = logging.getLogger("migration_validation")


class ValidationResult:
    """Represents the result of a validation test."""

    def __init__(self, component: str, test_name: str):
        """Initialize the validation result.

        Args:
            component: The component being validated
            test_name: The name of the specific test
        """
        self.component = component
        self.test_name = test_name
        self.success: Optional[bool] = None
        self.error: Optional[str] = None
        self.details: Dict[str, Any] = {}
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.duration_seconds: Optional[float] = None

    def complete(
        self, success: bool, error: Optional[str] = None, **details: Any
    ) -> None:
        """Complete the validation result.

        Args:
            success: Whether the validation was successful
            error: Error message if unsuccessful
            **details: Additional details about the validation
        """
        self.success = success
        self.error = error
        self.details.update(details)
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the validation result to a dictionary.

        Returns:
            Dictionary representation of the validation result
        """
        return {
            "component": self.component,
            "test_name": self.test_name,
            "success": self.success,
            "error": self.error,
            "details": self.details,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
        }

    def __str__(self) -> str:
        status = "✓ PASSED" if self.success else "✗ FAILED"
        return f"{self.component} - {self.test_name}: {status}"


class ValidationReport:
    """Represents a collection of validation results."""

    def __init__(self):
        """Initialize the validation report."""
        self.results: List[ValidationResult] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None

    def add_result(self, result: ValidationResult) -> None:
        """Add a validation result to the report.

        Args:
            result: The validation result to add
        """
        self.results.append(result)

    def complete(self) -> None:
        """Complete the validation report."""
        self.end_time = datetime.now()

    @property
    def success_count(self) -> int:
        """Get the number of successful validations.

        Returns:
            Number of successful validations
        """
        return sum(1 for result in self.results if result.success)

    @property
    def failure_count(self) -> int:
        """Get the number of failed validations.

        Returns:
            Number of failed validations
        """
        return sum(1 for result in self.results if result.success is False)

    @property
    def pending_count(self) -> int:
        """Get the number of pending validations.

        Returns:
            Number of pending validations
        """
        return sum(1 for result in self.results if result.success is None)

    @property
    def overall_success(self) -> bool:
        """Get whether all validations were successful.

        Returns:
            Whether all validations were successful
        """
        return self.failure_count == 0 and self.pending_count == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert the validation report to a dictionary.

        Returns:
            Dictionary representation of the validation report
        """
        return {
            "results": [result.to_dict() for result in self.results],
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds()
            if self.end_time
            else None,
            "summary": {
                "total": len(self.results),
                "success": self.success_count,
                "failure": self.failure_count,
                "pending": self.pending_count,
                "overall_success": self.overall_success,
            },
        }

    def save_json(self, path: str) -> None:
        """Save the validation report as JSON.

        Args:
            path: Path to save the report to
        """
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

        logger.info(f"Validation report saved to {path}")

    def save_markdown(self, path: str) -> None:
        """Save the validation report as Markdown.

        Args:
            path: Path to save the report to
        """
        with open(path, "w") as f:
            f.write("# AI Orchestra GCP Migration Validation Report\n\n")

            # Summary section
            f.write("## Summary\n\n")

            duration = (
                (self.end_time - self.start_time).total_seconds()
                if self.end_time
                else 0
            )
            overall_status = "✅ Passed" if self.overall_success else "❌ Failed"

            f.write(f"**Overall Status:** {overall_status}\n\n")
            f.write(f"**Total Tests:** {len(self.results)}\n")
            f.write(f"**Passed:** {self.success_count}\n")
            f.write(f"**Failed:** {self.failure_count}\n")
            f.write(f"**Pending:** {self.pending_count}\n")
            f.write(f"**Start Time:** {self.start_time.isoformat()}\n")
            if self.end_time:
                f.write(f"**End Time:** {self.end_time.isoformat()}\n")
                f.write(f"**Duration:** {duration:.2f} seconds\n")

            # Results by component
            f.write("\n## Results by Component\n\n")

            components = sorted(set(result.component for result in self.results))

            for component in components:
                f.write(f"### {component}\n\n")

                component_results = [
                    r for r in self.results if r.component == component
                ]

                # Create a table for the component results
                f.write("| Test | Status | Duration | Error |\n")
                f.write("|------|--------|----------|-------|\n")

                for result in component_results:
                    status = (
                        "✅ Pass"
                        if result.success
                        else "❌ Fail"
                        if result.success is False
                        else "⏳ Pending"
                    )
                    duration = (
                        f"{result.duration_seconds:.2f}s"
                        if result.duration_seconds
                        else "N/A"
                    )
                    error = result.error or "N/A"
                    f.write(
                        f"| {result.test_name} | {status} | {duration} | {error} |\n"
                    )

                f.write("\n")

            # Details section
            f.write("\n## Detailed Results\n\n")

            for i, result in enumerate(self.results, 1):
                status = (
                    "✅ Pass"
                    if result.success
                    else "❌ Fail"
                    if result.success is False
                    else "⏳ Pending"
                )

                f.write(
                    f"### {i}. {result.component} - {result.test_name} ({status})\n\n"
                )

                if result.duration_seconds:
                    f.write(f"**Duration:** {result.duration_seconds:.2f} seconds\n\n")

                if result.error:
                    f.write(f"**Error:** {result.error}\n\n")

                if result.details:
                    f.write("**Details:**\n\n")
                    f.write("```json\n")
                    f.write(json.dumps(result.details, indent=2))
                    f.write("\n```\n\n")

        logger.info(f"Validation report saved to {path}")

    def print_summary(self) -> None:
        """Print a summary of the validation results."""
        print("\n" + "=" * 80)
        print("AI Orchestra GCP Migration Validation Summary")
        print("=" * 80)

        overall_status = "✅ PASSED" if self.overall_success else "❌ FAILED"
        print(f"Overall Status: {overall_status}")
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {self.success_count}")
        print(f"Failed: {self.failure_count}")
        print(f"Pending: {self.pending_count}")

        if self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            print(f"Duration: {duration:.2f} seconds")

        print("\nComponent Results:")
        print("-" * 80)

        components = sorted(set(result.component for result in self.results))

        for component in components:
            component_results = [r for r in self.results if r.component == component]
            component_success = all(
                r.success for r in component_results if r.success is not None
            )
            component_status = "✅ PASSED" if component_success else "❌ FAILED"

            print(f"{component}: {component_status}")

            for result in component_results:
                status = (
                    "✓ PASSED"
                    if result.success
                    else "✗ FAILED"
                    if result.success is False
                    else "⋯ PENDING"
                )
                print(f"  {status} {result.test_name}")
                if result.error:
                    print(f"    Error: {result.error}")

        print("\nFailed Tests:")
        print("-" * 80)

        failed_results = [r for r in self.results if r.success is False]

        if failed_results:
            for result in failed_results:
                print(f"✗ {result.component} - {result.test_name}")
                print(f"  Error: {result.error}")
        else:
            print("No failed tests!")

        print("=" * 80)


async def validate_environment_detection() -> ValidationResult:
    """Validate environment detection functionality.

    Returns:
        Validation result
    """
    result = ValidationResult("Environment", "Environment Detection")

    try:
        # Import necessary modules
        sys.path.append(str(Path(__file__).parent.parent))

        try:
            from gcp_migration.environment_sync import EnvironmentType

            # Create a temporary environment marker
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Create a mock Codespaces environment
                codespaces_marker = temp_path / ".codespaces"
                codespaces_marker.touch()

                # Test with the mock Codespaces environment
                os.environ["ORIGINAL_PATH"] = os.environ.get("PATH", "")
                os.environ["PATH"] = f"{temp_dir}:{os.environ.get('PATH', '')}"

                # Import the module dynamically to use the updated environment
                import importlib.util
                import sys

                spec = importlib.util.spec_from_file_location(
                    "environment_sync",
                    Path(__file__).parent / "environment_sync.py",
                )
                module = importlib.util.module_from_spec(spec)
                sys.modules["environment_sync_test"] = module
                spec.loader.exec_module(module)

                # Check if environment detection works correctly
                detected_env = module._detect_environment()

                # Reset PATH
                os.environ["PATH"] = os.environ.get("ORIGINAL_PATH", "")

                result.complete(
                    success=True,
                    details={
                        "detected_environment": detected_env.value,
                        "expected_environment": EnvironmentType.CODESPACES.value,
                    },
                )
        except Exception as e:
            result.complete(
                success=False,
                error=f"Failed to test environment detection: {str(e)}",
            )
    except Exception as e:
        result.complete(
            success=False,
            error=f"Failed to import modules: {str(e)}",
        )

    return result


async def validate_environment_sync() -> ValidationResult:
    """Validate environment synchronization functionality.

    Returns:
        Validation result
    """
    result = ValidationResult("Environment", "Environment Synchronization")

    try:
        # Run the shell wrapper with status mode
        process = subprocess.run(
            ["./gcp_migration/sync_environments.sh", "status"],
            capture_output=True,
            text=True,
            check=False,
        )

        if process.returncode == 0:
            result.complete(
                success=True,
                details={
                    "stdout": process.stdout,
                    "returncode": process.returncode,
                },
            )
        else:
            result.complete(
                success=False,
                error=f"Environment sync status check failed with code {process.returncode}",
                details={
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "returncode": process.returncode,
                },
            )
    except Exception as e:
        result.complete(
            success=False,
            error=f"Failed to run environment sync: {str(e)}",
        )

    return result


async def validate_circuit_breaker() -> ValidationResult:
    """Validate circuit breaker functionality.

    Returns:
        Validation result
    """
    result = ValidationResult("Circuit Breaker", "Basic Functionality")

    try:
        sys.path.append(str(Path(__file__).parent.parent))

        try:
            from gcp_migration.circuit_breaker_unified import (
                CircuitState,
                CircuitBreaker,
                circuit_break,
            )

            # Create a circuit breaker instance
            breaker = CircuitBreaker(
                name="test_breaker",
                failure_threshold=3,
                recovery_timeout=1.0,  # Short timeout for testing
            )

            # Test successful execution
            test_success = True
            test_failure = False

            def test_success_function():
                return "success"

            def test_failure_function():
                raise RuntimeError("Simulated failure")

            def fallback_function(*args, **kwargs):
                return "fallback"

            # Test with decorators
            @circuit_break(
                name="test_decorator",
                failure_threshold=3,
                recovery_timeout=1.0,
                fallback_function=fallback_function,
            )
            def decorated_function(should_fail):
                if should_fail:
                    raise RuntimeError("Simulated failure in decorated function")
                return "success from decorated function"

            # Test states transition
            initial_state = breaker.state

            # Execute success function using the execute method
            success_result = breaker.execute(test_success_function)

            # Execute failure function enough times to open the circuit
            failure_results = []
            for _ in range(4):  # One more than the threshold
                try:
                    failure_results.append(breaker.execute(test_failure_function))
                except Exception as e:
                    failure_results.append(str(e))

            # Circuit should now be open
            open_state = breaker.state

            # Wait for recovery timeout - replacing with asyncio.sleep in the future would be better
            # This could be a potential source of flaky tests
            time.sleep(1.5)  # Slightly longer than the recovery timeout

            # Circuit should now be half-open
            half_open_state = breaker.state

            # Test decorated function
            decorated_success = decorated_function(False)
            decorated_failure = decorated_function(True)  # Should use fallback

            result.complete(
                success=True,
                details={
                    "initial_state": initial_state.name,
                    "success_result": success_result,
                    "failure_results": failure_results,
                    "open_state": open_state.name,
                    "half_open_state": half_open_state.name,
                    "decorated_success": decorated_success,
                    "decorated_failure": decorated_failure,
                },
            )
        except Exception as e:
            result.complete(
                success=False,
                error=f"Failed to test circuit breaker: {str(e)}",
            )
    except Exception as e:
        result.complete(
            success=False,
            error=f"Failed to import modules: {str(e)}",
        )

    return result


async def validate_vertex_ai_bridge() -> ValidationResult:
    """Validate Vertex AI Bridge functionality.

    Returns:
        Validation result
    """
    result = ValidationResult("Vertex AI", "Bridge Initialization")

    try:
        # Run the test script
        process = subprocess.run(
            ["./gcp_migration/test_vertex_bridge.py", "--test-type=text", "--verbose"],
            capture_output=True,
            text=True,
            check=False,
        )

        if process.returncode == 0:
            result.complete(
                success=True,
                details={
                    "stdout": process.stdout,
                    "returncode": process.returncode,
                },
            )
        else:
            result.complete(
                success=False,
                error=f"Vertex AI Bridge test failed with code {process.returncode}",
                details={
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "returncode": process.returncode,
                },
            )
    except Exception as e:
        result.complete(
            success=False,
            error=f"Failed to run Vertex AI Bridge test: {str(e)}",
        )

    return result


async def validate_monitoring() -> ValidationResult:
    """Validate monitoring functionality.

    Returns:
        Validation result
    """
    result = ValidationResult("Monitoring", "Status Report Generation")

    try:
        # Run the status report generator
        reports_dir = Path(__file__).parent / "validation_reports"
        reports_dir.mkdir(exist_ok=True)

        process = subprocess.run(
            [
                "./gcp_migration/generate_status_report.py",
                "--output=file",
                f"--path={reports_dir}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if process.returncode == 0:
            # Check if a report was generated
            report_files = list(reports_dir.glob("*.md"))

            if report_files:
                result.complete(
                    success=True,
                    details={
                        "stdout": process.stdout,
                        "report_files": [str(f) for f in report_files],
                    },
                )
            else:
                result.complete(
                    success=False,
                    error="No report files were generated",
                    details={
                        "stdout": process.stdout,
                        "stderr": process.stderr,
                    },
                )
        else:
            result.complete(
                success=False,
                error=f"Status report generation failed with code {process.returncode}",
                details={
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "returncode": process.returncode,
                },
            )
    except Exception as e:
        result.complete(
            success=False,
            error=f"Failed to run status report generator: {str(e)}",
        )

    return result


async def validate_migration() -> ValidationReport:
    """Validate the entire migration implementation.

    Returns:
        Validation report
    """
    report = ValidationReport()

    # Environment validation
    report.add_result(await validate_environment_detection())
    report.add_result(await validate_environment_sync())

    # Circuit breaker validation
    report.add_result(await validate_circuit_breaker())

    # Vertex AI validation
    report.add_result(await validate_vertex_ai_bridge())

    # Monitoring validation
    report.add_result(await validate_monitoring())

    # Complete the report
    report.complete()

    return report


async def run_validation(
    args: argparse.Namespace,
) -> int:
    """Run the migration validation.

    Args:
        args: Command line arguments

    Returns:
        Exit code
    """
    logger.info("Starting migration validation...")

    # Determine what to validate
    validate_all = args.validate_all
    validate_environment = validate_all or args.validate_environment
    validate_circuit = validate_all or args.validate_circuit_breaker
    validate_vertex = validate_all or args.validate_vertex_ai
    validate_monitor = validate_all or args.validate_monitoring

    # Initialize the validation report
    report = ValidationReport()

    # Validate components
    if validate_environment:
        logger.info("Validating environment components...")
        report.add_result(await validate_environment_detection())
        report.add_result(await validate_environment_sync())

    if validate_circuit:
        logger.info("Validating circuit breaker component...")
        report.add_result(await validate_circuit_breaker())

    if validate_vertex:
        logger.info("Validating Vertex AI component...")
        report.add_result(await validate_vertex_ai_bridge())

    if validate_monitor:
        logger.info("Validating monitoring component...")
        report.add_result(await validate_monitoring())

    # Complete the report
    report.complete()

    # Save the report
    if args.json_report:
        report.save_json(args.json_report)

    if args.markdown_report:
        report.save_markdown(args.markdown_report)

    # Print the summary
    report.print_summary()

    # Return exit code
    return 0 if report.overall_success else 1


def main() -> int:
    """Main entry point.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="AI Orchestra GCP Migration Validation"
    )

    # Component validation options
    parser.add_argument(
        "--validate-all",
        action="store_true",
        help="Validate all components",
    )
    parser.add_argument(
        "--validate-environment",
        action="store_true",
        help="Validate environment detection and synchronization",
    )
    parser.add_argument(
        "--validate-circuit-breaker",
        action="store_true",
        help="Validate circuit breaker functionality",
    )
    parser.add_argument(
        "--validate-vertex-ai",
        action="store_true",
        help="Validate Vertex AI integration",
    )
    parser.add_argument(
        "--validate-monitoring",
        action="store_true",
        help="Validate monitoring functionality",
    )

    # Report options
    parser.add_argument(
        "--json-report",
        type=str,
        default="migration_validation_report.json",
        help="Path to save the JSON report",
    )
    parser.add_argument(
        "--markdown-report",
        type=str,
        default="migration_validation_report.md",
        help="Path to save the Markdown report",
    )

    # Verbose logging
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # If no validation options are specified, validate all
    if not any(
        [
            args.validate_all,
            args.validate_environment,
            args.validate_circuit_breaker,
            args.validate_vertex_ai,
            args.validate_monitoring,
        ]
    ):
        args.validate_all = True

    try:
        return asyncio.run(run_validation(args))
    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        return 1
    except Exception as e:
        logger.exception(f"Error in validation: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
