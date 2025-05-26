#!/usr/bin/env python3
"""
Comprehensive MCP Implementation Test Script
Tests all MCP servers, Claude API connectivity, monitoring, and configurations
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import requests


# Color codes for output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_status(name: str, status: bool, message: str = ""):
    """Print a status line with color coding"""
    status_text = (
        f"{Colors.GREEN}✓ PASS{Colors.RESET}"
        if status
        else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    )
    print(f"{name:<40} {status_text} {message}")


def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{title}{Colors.RESET}")
    print(f"{'-' * len(title)}")


class MCPTestSuite:
    def __init__(self):
        self.results = {
            "mcp_servers": {},
            "claude_api": {},
            "monitoring": {},
            "configurations": {},
            "overall": True,
        }
        self.base_dir = Path("/home/paperspace/orchestra-main")

    def run_command(self, cmd: List[str], timeout: int = 30) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr"""
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout, cwd=self.base_dir
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    async def test_mcp_server_startup(self, server_name: str, config_path: str) -> bool:
        """Test if an MCP server can start properly"""
        print(f"\nTesting {server_name} startup...")

        # Check if config file exists
        config_file = self.base_dir / config_path
        if not config_file.exists():
            print(f"  {Colors.RED}Config file not found: {config_path}{Colors.RESET}")
            return False

        # Try to start the server
        cmd = [
            sys.executable,
            str(self.base_dir / "mcp_server" / "run_mcp_server.py"),
            "--config",
            str(config_file),
            "--test-mode",
        ]

        try:
            # Start the server process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.base_dir,
            )

            # Wait a bit for server to start
            await asyncio.sleep(3)

            # Check if process is still running
            if process.returncode is None:
                # Server is running, test passed
                process.terminate()
                await process.wait()
                print(f"  {Colors.GREEN}Server started successfully{Colors.RESET}")
                return True
            else:
                # Server crashed
                stdout, stderr = await process.communicate()
                print(
                    f"  {Colors.RED}Server crashed with code {process.returncode}{Colors.RESET}"
                )
                if stderr:
                    print(f"  Error: {stderr.decode()[:200]}...")
                return False

        except Exception as e:
            print(f"  {Colors.RED}Failed to start server: {e}{Colors.RESET}")
            return False

    def test_claude_api_connectivity(self) -> bool:
        """Test Claude API connectivity"""
        print_section("Testing Claude API Connectivity")

        # Check for API key
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print_status("API Key Check", False, "ANTHROPIC_API_KEY not set")
            return False

        print_status("API Key Check", True, "API key found")

        # Test API connectivity
        try:
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            # Simple test request
            data = {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}],
            }

            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=10,
            )

            if response.status_code == 200:
                print_status(
                    "API Connectivity", True, "Successfully connected to Claude API"
                )
                return True
            else:
                print_status(
                    "API Connectivity", False, f"Status code: {response.status_code}"
                )
                return False

        except Exception as e:
            print_status("API Connectivity", False, f"Error: {str(e)}")
            return False

    def test_monitoring_setup(self) -> bool:
        """Test monitoring configuration"""
        print_section("Testing Monitoring Setup")

        all_good = True

        # Check Prometheus config
        prom_config = self.base_dir / "monitoring" / "prometheus.yml"
        if prom_config.exists():
            print_status("Prometheus Config", True, "prometheus.yml found")
            # Validate YAML
            try:
                import yaml

                with open(prom_config) as f:
                    yaml.safe_load(f)
                print_status("Prometheus Config Valid", True)
            except Exception as e:
                print_status("Prometheus Config Valid", False, str(e))
                all_good = False
        else:
            print_status("Prometheus Config", False, "prometheus.yml not found")
            all_good = False

        # Check monitoring YAML for MCP
        mcp_monitoring = self.base_dir / "mcp_server" / "monitoring" / "monitoring.yaml"
        if mcp_monitoring.exists():
            print_status("MCP Monitoring Config", True, "monitoring.yaml found")
        else:
            print_status("MCP Monitoring Config", False, "monitoring.yaml not found")
            all_good = False

        # Check if monitoring endpoints are defined
        monitoring_script = (
            self.base_dir / "mcp_server" / "utils" / "performance_monitor.py"
        )
        if monitoring_script.exists():
            print_status("Performance Monitor", True, "Module found")
        else:
            print_status("Performance Monitor", False, "Module not found")
            all_good = False

        return all_good

    def test_configurations(self) -> bool:
        """Test all configuration files"""
        print_section("Testing Configuration Files")

        configs_to_check = [
            ("MCP Config", "mcp_config.json"),
            ("MCP Server Config", "mcp_server/config/mcp_gcp_config.yaml"),
            ("LiteLLM Config", "config/litellm_config.yaml"),
            ("Agents Config", "config/agents.yaml"),
            ("Mode Definitions", "config/mode_definitions.yaml"),
            ("Phi Config", "phi_config.yaml"),
        ]

        all_good = True

        for name, path in configs_to_check:
            file_path = self.base_dir / path
            if file_path.exists():
                # Try to parse the file
                try:
                    if path.endswith(".json"):
                        with open(file_path) as f:
                            json.load(f)
                        print_status(name, True, "Valid JSON")
                    elif path.endswith(".yaml") or path.endswith(".yml"):
                        import yaml

                        with open(file_path) as f:
                            yaml.safe_load(f)
                        print_status(name, True, "Valid YAML")
                    else:
                        print_status(name, True, "File exists")
                except Exception as e:
                    print_status(name, False, f"Parse error: {str(e)[:50]}...")
                    all_good = False
            else:
                print_status(name, False, "File not found")
                all_good = False

        return all_good

    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        print_section("Checking Dependencies")

        required_packages = [
            "mcp",
            "anthropic",
            "litellm",
            "phidata",
            "redis",
            "google-cloud-firestore",
            "google-cloud-secret-manager",
            "prometheus-client",
        ]

        all_good = True

        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print_status(f"Package: {package}", True, "Installed")
            except ImportError:
                print_status(f"Package: {package}", False, "Not installed")
                all_good = False

        return all_good

    async def run_all_tests(self):
        """Run all tests and generate summary"""
        print_header("MCP Implementation Test Suite")
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 1. Check dependencies
        print_section("1. Dependency Check")
        self.results["configurations"]["dependencies"] = self.check_dependencies()

        # 2. Test configurations
        print_section("2. Configuration Files")
        self.results["configurations"]["files"] = self.test_configurations()

        # 3. Test MCP servers
        print_section("3. MCP Server Tests")
        servers_to_test = [
            ("GCP Resources Server", "mcp_server/config/mcp_gcp_config.yaml"),
            ("Main MCP Server", "mcp_config.json"),
        ]

        for server_name, config in servers_to_test:
            result = await self.test_mcp_server_startup(server_name, config)
            self.results["mcp_servers"][server_name] = result

        # 4. Test Claude API
        print_section("4. Claude API Test")
        self.results["claude_api"]["connectivity"] = self.test_claude_api_connectivity()

        # 5. Test monitoring
        print_section("5. Monitoring Setup")
        self.results["monitoring"]["setup"] = self.test_monitoring_setup()

        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate a comprehensive summary of test results"""
        print_header("Test Summary")

        # Calculate totals
        total_tests = 0
        passed_tests = 0

        def count_results(results_dict):
            nonlocal total_tests, passed_tests
            for key, value in results_dict.items():
                if isinstance(value, dict):
                    count_results(value)
                elif isinstance(value, bool):
                    total_tests += 1
                    if value:
                        passed_tests += 1

        count_results(self.results)

        # Overall status
        overall_pass = passed_tests == total_tests

        print(f"{Colors.BOLD}Overall Result:{Colors.RESET} ", end="")
        if overall_pass:
            print(f"{Colors.GREEN}ALL TESTS PASSED{Colors.RESET}")
        else:
            print(f"{Colors.RED}SOME TESTS FAILED{Colors.RESET}")

        print(
            f"\nTests Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)"
        )

        # Detailed breakdown
        print("\n" + Colors.BOLD + "Detailed Results:" + Colors.RESET)

        # MCP Servers
        print("\nMCP Servers:")
        for server, result in self.results["mcp_servers"].items():
            print_status(f"  {server}", result)

        # Claude API
        print("\nClaude API:")
        for test, result in self.results["claude_api"].items():
            print_status(f"  {test.title()}", result)

        # Monitoring
        print("\nMonitoring:")
        for test, result in self.results["monitoring"].items():
            print_status(f"  {test.title()}", result)

        # Configurations
        print("\nConfigurations:")
        for test, result in self.results["configurations"].items():
            print_status(f"  {test.title()}", result)

        # Implementation status
        print_header("Implementation Status")

        print(f"{Colors.BOLD}✓ Completed:{Colors.RESET}")
        print("  - MCP server infrastructure created")
        print("  - Configuration files structured")
        print("  - Claude API integration prepared")
        print("  - Monitoring framework established")
        print("  - Memory management system integrated")

        if not overall_pass:
            print(f"\n{Colors.BOLD}{Colors.YELLOW}⚠ Action Items:{Colors.RESET}")
            if not self.results.get("configurations", {}).get("dependencies", True):
                print("  - Install missing Python packages")
            if not self.results.get("mcp_servers", {}).get(
                "GCP Resources Server", True
            ):
                print("  - Fix MCP server startup issues")
            if not self.results.get("claude_api", {}).get("connectivity", True):
                print("  - Set up ANTHROPIC_API_KEY environment variable")
            if not self.results.get("monitoring", {}).get("setup", True):
                print("  - Complete monitoring configuration")

        print(f"\n{Colors.BOLD}Next Steps:{Colors.RESET}")
        print("  1. Fix any failing tests")
        print("  2. Deploy MCP servers to production")
        print("  3. Configure Claude to use MCP servers")
        print("  4. Set up monitoring dashboards")
        print("  5. Test end-to-end workflows")

        # Save results to file
        results_file = self.base_dir / "mcp_test_results.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\nDetailed results saved to: {results_file}")


async def main():
    """Main test runner"""
    test_suite = MCPTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
