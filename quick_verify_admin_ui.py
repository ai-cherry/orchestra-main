#!/usr/bin/env python3
"""
"""
    print("Error: Required packages not installed. Run:")
    print("pip install requests beautifulsoup4 colorama tabulate")
    sys.exit(1)

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Constants
DEFAULT_URL = "https://cherry-ai.me"
DEFAULT_API_URL = "https://cherry-ai.me/api"
DEFAULT_TIMEOUT = 10
DEFAULT_JS_THRESHOLD = 100000  # 100KB
DEFAULT_CSS_THRESHOLD = 10000  # 10KB
USER_AGENT = "Cherry-Admin-UI-Verifier/1.0"

# Status indicators
STATUS_OK = f"{Fore.GREEN}✓{Style.RESET_ALL}"
STATUS_WARNING = f"{Fore.YELLOW}⚠{Style.RESET_ALL}"
STATUS_ERROR = f"{Fore.RED}✗{Style.RESET_ALL}"
STATUS_INFO = f"{Fore.BLUE}ℹ{Style.RESET_ALL}"

class AdminUIVerifier:
    """Main verifier class for Cherry Admin UI."""
        """Initialize with command line arguments."""
            "accessibility": {"status": "Unknown", "details": [], "critical": True},
            "resources": {"status": "Unknown", "details": [], "critical": True},
            "api": {"status": "Unknown", "details": [], "critical": False},
            "performance": {"status": "Unknown", "details": [], "critical": False},
            "summary": {"status": "Unknown", "details": [], "critical": True},
        }

        # Performance metrics
        self.performance_metrics = {}

        # Session for requests
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def run(self) -> Dict[str, Any]:
        """Run all verification checks and return results."""
            if self.results["accessibility"]["status"] == "OK":
                self._check_resources()

            # Check API endpoints if not skipped
            if not self.skip_api:
                self._check_api_endpoints()

            # Run performance checks if requested
            if self.run_performance:
                self._check_performance()

            # Generate summary
            self._generate_summary()

        except Exception:


            pass
            print(f"\n{STATUS_INFO} Verification interrupted by user.")
            self.results["summary"]["status"] = "Interrupted"
            self.results["summary"]["details"].append("Verification was interrupted by user.")
        except Exception:

            pass
            print(f"\n{STATUS_ERROR} Unexpected error: {str(e)}")
            self.results["summary"]["status"] = "Error"
            self.results["summary"]["details"].append(f"Unexpected error: {str(e)}")

        # Add execution time
        execution_time = time.time() - start_time
        self.results["execution_time"] = execution_time
        self.results["timestamp"] = datetime.now().isoformat()

        return self.results

    def _check_accessibility(self) -> None:
        """Check if the site is accessible."""
        print(f"\n{Fore.CYAN}Checking site accessibility...{Style.RESET_ALL}")

        try:


            pass
            start_time = time.time()
            response = self.session.get(self.url, timeout=self.timeout)
            response_time = time.time() - start_time

            self.results["accessibility"]["details"].append(f"HTTP Status: {response.status_code}")
            self.results["accessibility"]["details"].append(f"Response Time: {response_time:.2f}s")

            if response.status_code == 200:
                self.results["accessibility"]["status"] = "OK"
                print(f"{STATUS_OK} Site is accessible (HTTP 200)")
                print(f"{STATUS_OK} Response time: {response_time:.2f}s")

                # Check content size
                content_size = len(response.text)
                self.results["accessibility"]["details"].append(f"Content Size: {content_size} bytes")

                if content_size < 500:
                    self.results["accessibility"]["status"] = "Warning"
                    self.results["accessibility"]["details"].append(
                        "Content size is suspiciously small. Possible blank page."
                    )
                    print(f"{STATUS_WARNING} Content size is suspiciously small: {content_size} bytes")
                else:
                    print(f"{STATUS_OK} Content size: {content_size} bytes")

                # Save HTML content for resource checking
                self.html_content = response.text
            else:
                self.results["accessibility"]["status"] = "Error"
                self.results["accessibility"]["details"].append(f"Unexpected HTTP status: {response.status_code}")
                print(f"{STATUS_ERROR} Site returned HTTP {response.status_code}")

        except Exception:


            pass
            self.results["accessibility"]["status"] = "Error"
            self.results["accessibility"]["details"].append(f"Connection timed out after {self.timeout}s")
            print(f"{STATUS_ERROR} Connection timed out after {self.timeout}s")

        except Exception:


            pass
            self.results["accessibility"]["status"] = "Error"
            self.results["accessibility"]["details"].append("Connection error. Site may be down or unreachable.")
            print(f"{STATUS_ERROR} Connection error. Site may be down or unreachable.")

        except Exception:


            pass
            self.results["accessibility"]["status"] = "Error"
            self.results["accessibility"]["details"].append(f"Request error: {str(e)}")
            print(f"{STATUS_ERROR} Request error: {str(e)}")

    def _check_resources(self) -> None:
        """Check if JS and CSS resources are properly loaded."""
        print(f"\n{Fore.CYAN}Checking resources...{Style.RESET_ALL}")

        try:


            pass
            soup = BeautifulSoup(self.html_content, "html.parser")

            # Check for JavaScript files
            js_files = []
            for script in soup.find_all("script"):
                if script.has_attr("src") and script["src"].endswith(".js"):
                    js_files.append(script["src"])

            # Check for CSS files
            css_files = []
            for link in soup.find_all("link"):
                if (
                    link.has_attr("rel")
                    and "stylesheet" in link["rel"]
                    and link.has_attr("href")
                    and link["href"].endswith(".css")
                ):
                    css_files.append(link["href"])

            self.results["resources"]["details"].append(f"JavaScript Files: {len(js_files)}")
            self.results["resources"]["details"].append(f"CSS Files: {len(css_files)}")

            # Validate resources
            if not js_files:
                self.results["resources"]["status"] = "Error"
                self.results["resources"]["details"].append("No JavaScript files found in HTML")
                print(f"{STATUS_ERROR} No JavaScript files found in HTML")
            else:
                print(f"{STATUS_OK} Found {len(js_files)} JavaScript file(s)")

                # Check each JS file
                js_issues = 0
                for js_file in js_files:
                    js_url = urljoin(self.url, js_file)
                    try:

                        pass
                        js_response = self.session.head(js_url, timeout=self.timeout)

                        if js_response.status_code == 200:
                            # Get file size with a GET request if HEAD doesn't provide it
                            if "content-length" not in js_response.headers:
                                js_response = self.session.get(js_url, timeout=self.timeout)

                            js_size = int(js_response.headers.get("content-length", 0))
                            if js_size == 0 and hasattr(js_response, "content"):
                                js_size = len(js_response.content)

                            if js_size < self.js_threshold:
                                self.results["resources"]["details"].append(
                                    f"JavaScript file {js_file} is too small: {js_size} bytes"
                                )
                                print(f"{STATUS_WARNING} JavaScript file {js_file} is too small: {js_size} bytes")
                                js_issues += 1
                            else:
                                self.results["resources"]["details"].append(
                                    f"JavaScript file {js_file} size: {js_size} bytes"
                                )
                                if self.verbose:
                                    print(f"{STATUS_OK} JavaScript file {js_file} size: {js_size} bytes")
                        else:
                            self.results["resources"]["details"].append(
                                f"JavaScript file {js_file} returned HTTP {js_response.status_code}"
                            )
                            print(f"{STATUS_ERROR} JavaScript file {js_file} returned HTTP {js_response.status_code}")
                            js_issues += 1

                    except Exception:


                        pass
                        self.results["resources"]["details"].append(
                            f"Error accessing JavaScript file {js_file}: {str(e)}"
                        )
                        print(f"{STATUS_ERROR} Error accessing JavaScript file {js_file}: {str(e)}")
                        js_issues += 1

                if js_issues > 0:
                    self.results["resources"]["status"] = (
                        "Warning" if self.results["resources"]["status"] != "Error" else "Error"
                    )

            if not css_files:
                self.results["resources"]["status"] = "Error"
                self.results["resources"]["details"].append("No CSS files found in HTML")
                print(f"{STATUS_ERROR} No CSS files found in HTML")
            else:
                print(f"{STATUS_OK} Found {len(css_files)} CSS file(s)")

                # Check each CSS file
                css_issues = 0
                for css_file in css_files:
                    css_url = urljoin(self.url, css_file)
                    try:

                        pass
                        css_response = self.session.head(css_url, timeout=self.timeout)

                        if css_response.status_code == 200:
                            # Get file size with a GET request if HEAD doesn't provide it
                            if "content-length" not in css_response.headers:
                                css_response = self.session.get(css_url, timeout=self.timeout)

                            css_size = int(css_response.headers.get("content-length", 0))
                            if css_size == 0 and hasattr(css_response, "content"):
                                css_size = len(css_response.content)

                            if css_size < self.css_threshold:
                                self.results["resources"]["details"].append(
                                    f"CSS file {css_file} is too small: {css_size} bytes"
                                )
                                print(f"{STATUS_WARNING} CSS file {css_file} is too small: {css_size} bytes")
                                css_issues += 1
                            else:
                                self.results["resources"]["details"].append(
                                    f"CSS file {css_file} size: {css_size} bytes"
                                )
                                if self.verbose:
                                    print(f"{STATUS_OK} CSS file {css_file} size: {css_size} bytes")
                        else:
                            self.results["resources"]["details"].append(
                                f"CSS file {css_file} returned HTTP {css_response.status_code}"
                            )
                            print(f"{STATUS_ERROR} CSS file {css_file} returned HTTP {css_response.status_code}")
                            css_issues += 1

                    except Exception:


                        pass
                        self.results["resources"]["details"].append(f"Error accessing CSS file {css_file}: {str(e)}")
                        print(f"{STATUS_ERROR} Error accessing CSS file {css_file}: {str(e)}")
                        css_issues += 1

                if css_issues > 0:
                    self.results["resources"]["status"] = (
                        "Warning" if self.results["resources"]["status"] != "Error" else "Error"
                    )

            # Set overall status if not already set
            if self.results["resources"]["status"] == "Unknown":
                self.results["resources"]["status"] = "OK"
                print(f"{STATUS_OK} All resources checked successfully")

        except Exception:


            pass
            self.results["resources"]["status"] = "Error"
            self.results["resources"]["details"].append(f"Error checking resources: {str(e)}")
            print(f"{STATUS_ERROR} Error checking resources: {str(e)}")

    def _check_api_endpoints(self) -> None:
        """Check API endpoints."""
        print(f"\n{Fore.CYAN}Checking API endpoints...{Style.RESET_ALL}")

        # Define API endpoints to check
        endpoints = [
            {"path": "/api/health", "method": "GET", "expected_status": 200},
            {"path": "/api/version", "method": "GET", "expected_status": 200},
            # Add more endpoints as needed
        ]

        if self.mock_api:
            self.results["api"]["status"] = "Mocked"
            self.results["api"]["details"].append("Using mock API responses")
            print(f"{STATUS_INFO} Using mock API responses")

            # Simulate API responses
            for endpoint in endpoints:
                self.results["api"]["details"].append(f"Mocked {endpoint['method']} {endpoint['path']}: OK")
                print(f"{STATUS_OK} Mocked {endpoint['method']} {endpoint['path']}: OK")

            return

        # Check each endpoint
        api_issues = 0
        for endpoint in endpoints:
            endpoint_url = urljoin(self.api_url, endpoint["path"].lstrip("/"))
            method = endpoint["method"].upper()
            expected_status = endpoint["expected_status"]

            try:


                pass
                start_time = time.time()

                if method == "GET":
                    response = self.session.get(endpoint_url, timeout=self.timeout)
                elif method == "POST":
                    response = self.session.post(endpoint_url, json={}, timeout=self.timeout)
                else:
                    response = self.session.request(method, endpoint_url, timeout=self.timeout)

                response_time = time.time() - start_time

                if response.status_code == expected_status:
                    self.results["api"]["details"].append(f"{method} {endpoint['path']}: OK ({response_time:.2f}s)")
                    if self.verbose:
                        print(f"{STATUS_OK} {method} {endpoint['path']}: OK ({response_time:.2f}s)")
                else:
                    self.results["api"]["details"].append(
                        f"{method} {endpoint['path']}: Unexpected status {response.status_code} (expected {expected_status})"
                    )
                    print(
                        f"{STATUS_WARNING} {method} {endpoint['path']}: Unexpected status {response.status_code} (expected {expected_status})"
                    )
                    api_issues += 1

            except Exception:


                pass
                self.results["api"]["details"].append(f"{method} {endpoint['path']}: Error - {str(e)}")
                print(f"{STATUS_ERROR} {method} {endpoint['path']}: Error - {str(e)}")
                api_issues += 1

        # Set overall API status
        if api_issues == 0:
            self.results["api"]["status"] = "OK"
            print(f"{STATUS_OK} All API endpoints checked successfully")
        elif api_issues < len(endpoints):
            self.results["api"]["status"] = "Warning"
            print(f"{STATUS_WARNING} Some API endpoints have issues ({api_issues}/{len(endpoints)})")
        else:
            self.results["api"]["status"] = "Error"
            print(f"{STATUS_ERROR} All API endpoints have issues")

    def _check_performance(self) -> None:
        """Check page load performance using Selenium."""
        print(f"\n{Fore.CYAN}Checking performance...{Style.RESET_ALL}")

        try:


            pass
            # Dynamically import Selenium to avoid dependency if not needed
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
        except Exception:

            pass
            self.results["performance"]["status"] = "Skipped"
            self.results["performance"]["details"].append(
                "Selenium not installed. Run: pip install selenium webdriver-manager"
            )
            print(f"{STATUS_WARNING} Selenium not installed. Run: pip install selenium webdriver-manager")
            return

        try:


            pass
            # Set up Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            # Create Chrome driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # Set page load timeout
            driver.set_page_load_timeout(self.timeout * 2)

            # Measure page load time
            start_time = time.time()
            driver.get(self.url)
            load_time = time.time() - start_time

            # Get performance metrics using JavaScript
            navigation_timing = driver.execute_script(
                """
            """
                self.results["performance"]["details"].append(f"{metric}: {value:.2f}s")

            # Add Selenium measured load time
            self.results["performance"]["details"].append(f"seleniumLoadTime: {load_time:.2f}s")

            # Check if page is interactive
            is_interactive = driver.execute_script("return document.readyState") == "complete"
            self.results["performance"]["details"].append(f"pageInteractive: {is_interactive}")

            # Check for JavaScript errors
            js_errors = driver.execute_script(
                """
            """
                self.results["performance"]["details"].append(f"JavaScript Errors: {len(js_errors)}")
                for error in js_errors:
                    self.results["performance"]["details"].append(f"JS Error: {error}")
                self.results["performance"]["status"] = "Warning"
            else:
                self.results["performance"]["details"].append("No JavaScript errors detected")

            # Set performance status based on load time
            page_load_time = navigation_timing.get("pageLoadTime", load_time)
            if page_load_time < 1.0:
                self.results["performance"]["status"] = "OK"
                print(f"{STATUS_OK} Page load time: {page_load_time:.2f}s (Good)")
            elif page_load_time < 3.0:
                self.results["performance"]["status"] = "OK"
                print(f"{STATUS_OK} Page load time: {page_load_time:.2f}s (Acceptable)")
            else:
                self.results["performance"]["status"] = "Warning"
                print(f"{STATUS_WARNING} Page load time: {page_load_time:.2f}s (Slow)")

            # Print other metrics
            if self.verbose:
                print(f"{STATUS_INFO} DOM Interactive: {navigation_timing.get('domInteractiveTime', 'N/A'):.2f}s")
                print(f"{STATUS_INFO} DOM Content Loaded: {navigation_timing.get('domContentLoadedTime', 'N/A'):.2f}s")
                print(f"{STATUS_INFO} DOM Processing: {navigation_timing.get('domProcessingTime', 'N/A'):.2f}s")

            # Close the browser
            driver.quit()

        except Exception:


            pass
            self.results["performance"]["status"] = "Error"
            self.results["performance"]["details"].append(f"Error measuring performance: {str(e)}")
            print(f"{STATUS_ERROR} Error measuring performance: {str(e)}")

    def _generate_summary(self) -> None:
        """Generate summary of all checks."""
        print(f"\n{Fore.CYAN}Generating summary...{Style.RESET_ALL}")

        # Count issues by severity
        errors = 0
        warnings = 0
        ok = 0

        for key, result in self.results.items():
            if key == "summary" or key == "execution_time" or key == "timestamp":
                continue

            if result["status"] == "Error":
                errors += 1
            elif result["status"] == "Warning":
                warnings += 1
            elif result["status"] == "OK":
                ok += 1

        # Determine overall status
        if errors > 0:
            overall_status = "Error"
        elif warnings > 0:
            overall_status = "Warning"
        elif ok > 0:
            overall_status = "OK"
        else:
            overall_status = "Unknown"

        # Set summary status
        self.results["summary"]["status"] = overall_status

        # Add summary details
        self.results["summary"]["details"].append(f"Total checks: {errors + warnings + ok}")
        self.results["summary"]["details"].append(f"Errors: {errors}")
        self.results["summary"]["details"].append(f"Warnings: {warnings}")
        self.results["summary"]["details"].append(f"OK: {ok}")

        # Print summary
        if overall_status == "OK":
            print(f"{STATUS_OK} All checks passed successfully!")
        elif overall_status == "Warning":
            print(f"{STATUS_WARNING} Some checks have warnings.")
        elif overall_status == "Error":
            print(f"{STATUS_ERROR} Some checks have errors.")
        else:
            print(f"{STATUS_INFO} Check results are inconclusive.")

        print(f"{STATUS_INFO} Errors: {errors}, Warnings: {warnings}, OK: {ok}")

    def generate_report(self) -> str:
        """Generate a report based on the results."""
        if self.output_format == "json":
            return self._generate_json_report()
        elif self.output_format == "html":
            return self._generate_html_report()
        else:
            return self._generate_text_report()

    def _generate_text_report(self) -> str:
        """Generate a text report."""
        lines.append("=" * 80)
        lines.append(f"Cherry Admin UI Verification Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        lines.append(f"URL: {self.url}")
        lines.append(f"API URL: {self.api_url}")
        lines.append(f"Execution Time: {self.results.get('execution_time', 0):.2f}s")
        lines.append("=" * 80)
        lines.append("")

        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 80)
        status_icon = (
            STATUS_OK
            if self.results["summary"]["status"] == "OK"
            else (
                STATUS_WARNING
                if self.results["summary"]["status"] == "Warning"
                else STATUS_ERROR if self.results["summary"]["status"] == "Error" else STATUS_INFO
            )
        )
        lines.append(f"Overall Status: {status_icon} {self.results['summary']['status']}")
        # TODO: Consider using list comprehension for better performance

        for detail in self.results["summary"]["details"]:
            lines.append(f"  {detail}")
        lines.append("")

        # Detailed results
        for key, result in self.results.items():
            if key in ["summary", "execution_time", "timestamp"]:
                continue

            lines.append(key.upper())
            lines.append("-" * 80)
            status_icon = (
                STATUS_OK
                if result["status"] == "OK"
                else (
                    STATUS_WARNING
                    if result["status"] == "Warning"
                    else STATUS_ERROR if result["status"] == "Error" else STATUS_INFO
                )
            )
            lines.append(f"Status: {status_icon} {result['status']}")
            # TODO: Consider using list comprehension for better performance

            for detail in result["details"]:
                lines.append(f"  {detail}")
            lines.append("")

        # Performance metrics if available
        if self.performance_metrics:
            lines.append("PERFORMANCE METRICS")
            lines.append("-" * 80)
            for metric, value in self.performance_metrics.items():
                lines.append(f"{metric}: {value:.2f}s")
            lines.append("")

        # Footer
        lines.append("=" * 80)
        lines.append("End of Report")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _generate_json_report(self) -> str:
        """Generate a JSON report."""
        """Generate an HTML report."""
        html = f"""
    <div class="container">
        <h1>Cherry Admin UI Verification Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>URL: {self.url}</p>
        <p>API URL: {self.api_url}</p>
        <p>Execution Time: {self.results.get('execution_time', 0):.2f}s</p>
        
        <div class="summary">
            <h2>Summary</h2>
            <p class="status-{self.results['summary']['status'].lower()}">
                Overall Status: {self.results['summary']['status']}
            </p>
            <ul>
"""
        for detail in self.results["summary"]["details"]:
            html += f"                <li>{detail}</li>\n"

        html += """
"""
            if key in ["summary", "execution_time", "timestamp"]:
                continue

            html += f"""        <div class="section">
            <h2>{key.title()}</h2>
            <p class="status-{result['status'].lower()}">Status: {result['status']}</p>
            <ul>
"""
            for detail in result["details"]:
                html += f"                <li>{detail}</li>\n"

            html += """
"""
            html += """        <div class="section">
            <h2>Performance Metrics</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
"""
                html += f"""
                    <td class="metric">{metric}</td>
                    <td>{value:.2f}s</td>
                </tr>
"""
            html += """
"""
        html += """
"""
        """Save the report to a file if output_file is specified."""
            with open(self.output_file, "w") as f:
                f.write(report)
            print(f"{STATUS_OK} Report saved to {self.output_file}")
        except Exception:

            pass
            print(f"{STATUS_ERROR} Failed to save report: {str(e)}")

    def get_exit_code(self) -> int:
        """Get exit code based on results for CI/CD integration."""
                if key in ["summary", "execution_time", "timestamp"]:
                    continue

                if result.get("critical", False) and result["status"] == "Error":
                    return 2  # Critical error

            # Check summary status
            if self.results["summary"]["status"] == "Error":
                return 1  # Non-critical error
            else:
                return 0  # Success
        else:
            # In normal mode, any error is a failure
            if self.results["summary"]["status"] == "Error":
                return 2
            elif self.results["summary"]["status"] == "Warning":
                return 1
            else:
                return 0

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Verify Cherry Admin UI deployment")

    parser.add_argument("--url", default=DEFAULT_URL, help=f"Site URL to check (default: {DEFAULT_URL})")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help=f"API URL to check (default: {DEFAULT_API_URL})")
    parser.add_argument(
        "--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})"
    )
    parser.add_argument("--output", help="Write report to file")
    parser.add_argument(
        "--format", choices=["text", "json", "html"], default="text", help="Output format (default: text)"
    )
    parser.add_argument("--skip-api", action="store_true", help="Skip API endpoint testing")
    parser.add_argument("--mock-api", action="store_true", help="Use mock API responses instead of real requests")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--ci", action="store_true", help="CI mode (exit code based on critical checks only)")
    parser.add_argument(
        "--threshold-js",
        type=int,
        default=DEFAULT_JS_THRESHOLD,
        help=f"Minimum expected JS file size in bytes (default: {DEFAULT_JS_THRESHOLD})",
    )
    parser.add_argument(
        "--threshold-css",
        type=int,
        default=DEFAULT_CSS_THRESHOLD,
        help=f"Minimum expected CSS file size in bytes (default: {DEFAULT_CSS_THRESHOLD})",
    )
    parser.add_argument("--performance", action="store_true", help="Run performance checks (requires Chrome)")

    return parser.parse_args()

def main() -> None:
    """Main function."""
    print("\n" + report)
    verifier.save_report(report)

    # Exit with appropriate code
    sys.exit(verifier.get_exit_code())

if __name__ == "__main__":
    main()
