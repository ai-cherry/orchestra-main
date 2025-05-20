#!/usr/bin/env python3
"""
Figma-GCP Sync Environment Validator

This script validates the entire Figma-GCP synchronization environment by running all
individual validators and generating a comprehensive report.

It checks:
1. Figma-GCP Sync functionality
2. Component Library mapping
3. Infrastructure configuration
4. CI/CD Pipeline setup
5. AI Validation requirements
"""

import os
import sys
import subprocess
import json
import argparse
from pathlib import Path
from datetime import datetime
import importlib.util
import shutil
import re
from typing import Dict, List, Any, Tuple, Optional


# ANSI colors for terminal output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str) -> None:
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")


def print_section(text: str) -> None:
    """Print a formatted section header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'-' * len(text)}{Colors.ENDC}")


def run_command(cmd: str, check: bool = True) -> Tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, and stderr"""
    try:
        result = subprocess.run(
            cmd, shell=True, check=False, capture_output=True, text=True
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        if check:
            print(f"{Colors.RED}Error running command: {cmd}{Colors.ENDC}")
            print(f"{Colors.RED}{str(e)}{Colors.ENDC}")
        return 1, "", str(e)


def check_script_exists(script_path: str) -> bool:
    """Check if a script exists"""
    return os.path.isfile(script_path)


def import_from_script(script_path: str, function_name: str):
    """Import a specific function from a Python script"""
    if not os.path.exists(script_path):
        return None

    try:
        spec = importlib.util.spec_from_file_location("module", script_path)
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, function_name):
            return getattr(module, function_name)
        else:
            return None
    except Exception as e:
        print(
            f"{Colors.RED}Error importing {function_name} from {script_path}: {str(e)}{Colors.ENDC}"
        )
        return None


def validate_figma_pat(figma_pat: Optional[str] = None) -> dict:
    """Validate Figma PAT scopes"""
    print_section("1. Validating Figma PAT Scopes")

    results = {"status": "failure", "details": {}, "passed": False}

    script_path = "scripts/validate_figma_pat.py"

    if not check_script_exists(script_path):
        print(f"{Colors.RED}Error: {script_path} doesn't exist{Colors.ENDC}")
        results["error"] = f"Script not found: {script_path}"
        return results

    # Try to import the validate_figma_pat function
    validate_func = import_from_script(script_path, "validate_figma_pat")

    if validate_func is not None:
        # Use the imported function
        print(f"{Colors.CYAN}Running Figma PAT validation...{Colors.ENDC}")
        try:
            passed = validate_func(figma_pat)
            results["passed"] = passed
            results["status"] = "success" if passed else "warning"
        except Exception as e:
            print(f"{Colors.RED}Error running validation: {str(e)}{Colors.ENDC}")
            results["error"] = str(e)
    else:
        # Fall back to running the script directly
        env = os.environ.copy()
        if figma_pat:
            env["FIGMA_PAT"] = figma_pat

        cmd = f"python {script_path}"
        exit_code, stdout, stderr = run_command(cmd, check=False)

        results["exit_code"] = exit_code
        results["stdout"] = stdout
        results["stderr"] = stderr

        if exit_code == 0:
            results["status"] = "success"
            results["passed"] = True
        else:
            results["status"] = "warning"
            results["passed"] = False

    return results


def validate_component_mapping() -> dict:
    """Validate component library mapping"""
    print_section("2. Validating Component Library Mapping")

    results = {"status": "failure", "details": {}, "passed": False}

    script_path = "scripts/improve_component_mapping.py"

    if not check_script_exists(script_path):
        print(f"{Colors.RED}Error: {script_path} doesn't exist{Colors.ENDC}")
        results["error"] = f"Script not found: {script_path}"
        return results

    # Run the script
    output_file = "component_mapping_analysis.csv"
    cmd = f"python {script_path} --output {output_file}"
    exit_code, stdout, stderr = run_command(cmd)

    results["exit_code"] = exit_code
    results["stdout"] = stdout
    results["stderr"] = stderr

    # Parse the output to extract key information
    if exit_code == 0:
        results["status"] = "success"

        # Check for Button variants
        if "Button variants" in stdout and "Found" in stdout:
            match = re.search(r"Found (\d+) button styles", stdout)
            if match and int(match.group(1)) >= 4:
                results["button_variants"] = {
                    "status": "success",
                    "count": int(match.group(1)),
                    "message": "Found sufficient button variants",
                }
                results["passed"] = True
            else:
                results["button_variants"] = {
                    "status": "failure",
                    "message": "Insufficient button variants",
                }
                results["passed"] = False

        # Check for Card elevation states
        if "Card" in stdout and "Found" in stdout:
            match = re.search(r"Found (\d+) card styles", stdout)
            if match and int(match.group(1)) >= 2:
                results["card_states"] = {
                    "status": "success",
                    "count": int(match.group(1)),
                    "message": "Found sufficient card elevation states",
                }
                results["passed"] = results["passed"] and True
            else:
                results["card_states"] = {
                    "status": "failure",
                    "message": "Insufficient card elevation states",
                }
                results["passed"] = False

        # Check for Input validation styles
        if "Input validation" in stdout:
            match = re.search(
                r"Found sufficient input validation styles: (\d+)", stdout
            )
            if match and int(match.group(1)) >= 3:
                results["input_styles"] = {
                    "status": "success",
                    "count": int(match.group(1)),
                    "message": "Found sufficient input validation styles",
                }
                results["passed"] = results["passed"] and True
            else:
                results["input_styles"] = {
                    "status": "failure",
                    "message": "Insufficient input validation styles",
                }
                results["passed"] = False
    else:
        results["status"] = "failure"
        results["message"] = "Component mapping validation failed"

    return results


def validate_infrastructure() -> dict:
    """Validate infrastructure configuration"""
    print_section("3. Validating Infrastructure Configuration")

    results = {"status": "failure", "details": {}, "passed": False}

    # Check Terraform files
    tf_config_path = "infra/vertex_workbench_config.tf"
    tf_vars_path = "infra/vertex_workbench.tfvars"

    if not os.path.exists(tf_config_path):
        print(f"{Colors.RED}Error: {tf_config_path} doesn't exist{Colors.ENDC}")
        results["error"] = f"File not found: {tf_config_path}"
        return results

    # Read the config file
    with open(tf_config_path, "r") as f:
        tf_config = f.read()

    # Check for Vertex AI Workbench (n1-standard-4)
    if "machine_type" in tf_config and "n1-standard-4" in tf_config:
        results["vertex_ai"] = {
            "status": "success",
            "message": "Vertex AI Workbench properly configured with n1-standard-4",
        }
        print(
            f"{Colors.GREEN}✓ Vertex AI Workbench properly configured with n1-standard-4{Colors.ENDC}"
        )
    else:
        results["vertex_ai"] = {
            "status": "failure",
            "message": "Vertex AI Workbench not configured with n1-standard-4",
        }
        print(
            f"{Colors.RED}✗ Vertex AI Workbench not configured with n1-standard-4{Colors.ENDC}"
        )

    # Check for Firestore NATIVE with backup policies
    if "google_firestore_database" in tf_config and "FIRESTORE_NATIVE" in tf_config:
        if "google_storage_bucket" in tf_config and "firestore_backups" in tf_config:
            results["firestore"] = {
                "status": "success",
                "message": "Firestore NATIVE configured with backup policies",
            }
            print(
                f"{Colors.GREEN}✓ Firestore NATIVE configured with backup policies{Colors.ENDC}"
            )
        else:
            results["firestore"] = {
                "status": "warning",
                "message": "Firestore NATIVE configured without clear backup policies",
            }
            print(
                f"{Colors.YELLOW}⚠ Firestore NATIVE configured without clear backup policies{Colors.ENDC}"
            )
    else:
        results["firestore"] = {
            "status": "failure",
            "message": "Firestore NATIVE not properly configured",
        }
        print(f"{Colors.RED}✗ Firestore NATIVE not properly configured{Colors.ENDC}")

    # Check for Memorystore Redis (3GB)
    if "google_redis_instance" in tf_config and "memory_size_gb = 3" in tf_config:
        results["redis"] = {
            "status": "success",
            "message": "Memorystore Redis configured with 3GB capacity",
        }
        print(
            f"{Colors.GREEN}✓ Memorystore Redis configured with 3GB capacity{Colors.ENDC}"
        )
    else:
        results["redis"] = {
            "status": "failure",
            "message": "Memorystore Redis not configured with 3GB capacity",
        }
        print(
            f"{Colors.RED}✗ Memorystore Redis not configured with 3GB capacity{Colors.ENDC}"
        )

    # Check for service account roles
    required_roles = [
        "roles/secretmanager.secretAccessor",
        "roles/aiplatform.user",
        "roles/redis.editor",
    ]

    missing_roles = []
    for role in required_roles:
        if role not in tf_config:
            missing_roles.append(role)

    if not missing_roles:
        results["roles"] = {
            "status": "success",
            "message": "Service account has all required roles",
        }
        print(f"{Colors.GREEN}✓ Service account has all required roles{Colors.ENDC}")
    else:
        results["roles"] = {
            "status": "failure",
            "message": f"Service account missing roles: {', '.join(missing_roles)}",
        }
        print(
            f"{Colors.RED}✗ Service account missing roles: {', '.join(missing_roles)}{Colors.ENDC}"
        )

    # Overall result is successful if all checks passed
    results["passed"] = (
        results.get("vertex_ai", {}).get("status") == "success"
        and results.get("firestore", {}).get("status") in ["success", "warning"]
        and results.get("redis", {}).get("status") == "success"
        and results.get("roles", {}).get("status") == "success"
    )

    results["status"] = "success" if results["passed"] else "failure"

    return results


def validate_cicd_pipeline() -> dict:
    """Validate CI/CD pipeline configuration"""
    print_section("4. Validating CI/CD Pipeline")

    results = {"status": "failure", "details": {}, "passed": False}

    # Check GitHub Actions workflow
    workflow_path = ".github/workflows/figma-gcp-sync.yml"

    if not os.path.exists(workflow_path):
        print(f"{Colors.YELLOW}Warning: {workflow_path} doesn't exist{Colors.ENDC}")
        results["workflow"] = {
            "status": "warning",
            "message": f"Workflow file not found: {workflow_path}",
        }
    else:
        # Read the workflow file
        with open(workflow_path, "r") as f:
            workflow_content = f.read()

        # Check for repository_dispatch trigger with Figma file changes
        if (
            "repository_dispatch" in workflow_content
            and "figma-update" in workflow_content
        ):
            results["trigger"] = {
                "status": "success",
                "message": "GitHub Actions configured to trigger on Figma file changes",
            }
            print(
                f"{Colors.GREEN}✓ GitHub Actions configured to trigger on Figma file changes{Colors.ENDC}"
            )
        else:
            results["trigger"] = {
                "status": "warning",
                "message": "GitHub Actions may not be configured to trigger on Figma file changes",
            }
            print(
                f"{Colors.YELLOW}⚠ GitHub Actions may not be configured to trigger on Figma file changes{Colors.ENDC}"
            )

        # Check for design token validation
        if "validate" in workflow_content and "design" in workflow_content:
            results["validation"] = {
                "status": "success",
                "message": "GitHub Actions includes validation step for design tokens",
            }
            print(
                f"{Colors.GREEN}✓ GitHub Actions includes validation step for design tokens{Colors.ENDC}"
            )
        else:
            results["validation"] = {
                "status": "warning",
                "message": "GitHub Actions may not include validation step for design tokens",
            }
            print(
                f"{Colors.YELLOW}⚠ GitHub Actions may not include validation step for design tokens{Colors.ENDC}"
            )

        # Check for Cloud Run deployment with canary staging
        if "Cloud Run" in workflow_content and "canary" in workflow_content:
            results["deployment"] = {
                "status": "success",
                "message": "GitHub Actions includes Cloud Run deployment with canary staging",
            }
            print(
                f"{Colors.GREEN}✓ GitHub Actions includes Cloud Run deployment with canary staging{Colors.ENDC}"
            )
        else:
            results["deployment"] = {
                "status": "warning",
                "message": "GitHub Actions may not include Cloud Run deployment with canary staging",
            }
            print(
                f"{Colors.YELLOW}⚠ GitHub Actions may not include Cloud Run deployment with canary staging{Colors.ENDC}"
            )

    # Check secrets mapping
    secrets_script_path = "scripts/update_github_org_secrets.sh"

    if not os.path.exists(secrets_script_path):
        print(f"{Colors.RED}Error: {secrets_script_path} doesn't exist{Colors.ENDC}")
        results["secrets_script"] = {
            "status": "failure",
            "message": f"Secrets script not found: {secrets_script_path}",
        }
    else:
        # Read the secrets script
        with open(secrets_script_path, "r") as f:
            secrets_script = f.read()

        # Check required mappings
        required_mappings = [
            ("ORG_GCP_CREDENTIALS", "GCP_SA_KEY_JSON"),
            ("ORG_REDIS_PASSWORD", "REDIS_PASSWORD"),
        ]

        missing_mappings = []
        for github_secret, env_var in required_mappings:
            if (
                f'["{github_secret}"]' not in secrets_script
                or env_var not in secrets_script
            ):
                missing_mappings.append(f"{github_secret} → {env_var}")

        if not missing_mappings:
            results["secrets"] = {
                "status": "success",
                "message": "All required secrets are properly mapped",
            }
            print(
                f"{Colors.GREEN}✓ All required secrets are properly mapped{Colors.ENDC}"
            )
        else:
            results["secrets"] = {
                "status": "failure",
                "message": f"Missing secret mappings: {', '.join(missing_mappings)}",
            }
            print(
                f"{Colors.RED}✗ Missing secret mappings: {', '.join(missing_mappings)}{Colors.ENDC}"
            )

    # Check Figma webhook setup script
    webhook_script_path = "scripts/setup_figma_webhook.sh"

    if not os.path.exists(webhook_script_path):
        print(
            f"{Colors.YELLOW}Warning: {webhook_script_path} doesn't exist{Colors.ENDC}"
        )
        results["webhook_script"] = {
            "status": "warning",
            "message": f"Webhook setup script not found: {webhook_script_path}",
        }
    else:
        results["webhook_script"] = {
            "status": "success",
            "message": "Figma webhook setup script exists",
        }
        print(f"{Colors.GREEN}✓ Figma webhook setup script exists{Colors.ENDC}")

    # Overall result
    # Success if secrets are properly mapped and either workflow is properly configured or webhook script exists
    results["passed"] = results.get("secrets", {}).get("status") == "success" and (
        results.get("trigger", {}).get("status") == "success"
        or results.get("webhook_script", {}).get("status") == "success"
    )

    results["status"] = "success" if results["passed"] else "warning"

    return results


def validate_ai_requirements() -> dict:
    """Validate AI validation requirements"""
    print_section("5. Validating AI Requirements")

    results = {"status": "failure", "details": {}, "passed": False}

    # Check Cline MCP tools
    script_path = "scripts/verify_cline_tools.py"
    config_path = "config/cline_tools.json"

    if not os.path.exists(script_path):
        print(f"{Colors.YELLOW}Warning: {script_path} doesn't exist{Colors.ENDC}")
        results["cline_script"] = {
            "status": "warning",
            "message": f"Cline MCP verification script not found: {script_path}",
        }
    else:
        # Run the script if it exists
        cmd = f"python {script_path} --config {config_path}"
        exit_code, stdout, stderr = run_command(cmd, check=False)

        results["cline_output"] = {
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
        }

        if exit_code == 0:
            results["cline"] = {
                "status": "success",
                "message": "All Cline MCP tools meet version requirements",
            }
            print(
                f"{Colors.GREEN}✓ All Cline MCP tools meet version requirements{Colors.ENDC}"
            )
        else:
            # Parse output to identify missing or outdated tools
            missing_tools = []
            if "Missing tools" in stdout:
                missing_section = stdout.split("Missing tools:")[1].split("\n\n")[0]
                for line in missing_section.strip().split("\n"):
                    if line.strip():
                        missing_tools.append(line.strip())

            if missing_tools:
                results["cline"] = {
                    "status": "warning",
                    "message": f"Missing Cline MCP tools: {', '.join(missing_tools)}",
                    "missing_tools": missing_tools,
                }
                print(
                    f"{Colors.YELLOW}⚠ Missing Cline MCP tools: {', '.join(missing_tools)}{Colors.ENDC}"
                )
            else:
                results["cline"] = {
                    "status": "warning",
                    "message": "Cline MCP tools verification failed",
                }
                print(
                    f"{Colors.YELLOW}⚠ Cline MCP tools verification failed{Colors.ENDC}"
                )

    # Look for Vertex AI validation in Python files
    found_vertex_validation = False
    found_component_test = False

    for py_file in Path(".").glob("**/*.py"):
        try:
            with open(py_file, "r") as f:
                content = f.read()

                if "google.cloud" in content and "aiplatform" in content:
                    if (
                        "validate" in content.lower() and "design" in content.lower()
                    ) or ("validate_design_tokens" in content):
                        found_vertex_validation = True

                    if "component" in content.lower() and "test" in content.lower():
                        found_component_test = True
        except Exception:
            # Skip files that can't be read
            continue

    if found_vertex_validation:
        results["vertex_validation"] = {
            "status": "success",
            "message": "Found code for validating design tokens via Vertex AI",
        }
        print(
            f"{Colors.GREEN}✓ Found code for validating design tokens via Vertex AI{Colors.ENDC}"
        )
    else:
        results["vertex_validation"] = {
            "status": "warning",
            "message": "Could not find code for validating design tokens via Vertex AI",
        }
        print(
            f"{Colors.YELLOW}⚠ Could not find code for validating design tokens via Vertex AI{Colors.ENDC}"
        )

    if found_component_test:
        results["component_test"] = {
            "status": "success",
            "message": "Found code for generating component test cases",
        }
        print(
            f"{Colors.GREEN}✓ Found code for generating component test cases{Colors.ENDC}"
        )
    else:
        results["component_test"] = {
            "status": "warning",
            "message": "Could not find code for generating component test cases",
        }
        print(
            f"{Colors.YELLOW}⚠ Could not find code for generating component test cases{Colors.ENDC}"
        )

    # Overall result
    # Consider it a success if either Cline tools pass or we found Vertex AI validation code
    results["passed"] = (
        results.get("cline", {}).get("status") in ["success", "warning"]
        or results.get("vertex_validation", {}).get("status") == "success"
    )

    results["status"] = "success" if results["passed"] else "warning"

    return results


def generate_report(
    validation_results: Dict[str, Dict], output_file: Optional[str] = None
) -> None:
    """Generate a validation report"""
    print_header("VALIDATION REPORT SUMMARY")

    # Count successes and failures
    successes = sum(1 for k, v in validation_results.items() if v.get("passed", False))
    total = len(validation_results)

    # Overall status
    if successes == total:
        overall_status = (
            f"{Colors.GREEN}All checks passed ({successes}/{total}){Colors.ENDC}"
        )
    elif successes >= total * 0.8:
        overall_status = (
            f"{Colors.YELLOW}Most checks passed ({successes}/{total}){Colors.ENDC}"
        )
    else:
        overall_status = (
            f"{Colors.RED}Several checks failed ({successes}/{total}){Colors.ENDC}"
        )

    print(f"\nOverall Status: {overall_status}")

    # Print section summaries
    for section, results in validation_results.items():
        status = results.get("status", "unknown")
        if status == "success":
            status_str = f"{Colors.GREEN}Passed{Colors.ENDC}"
        elif status == "warning":
            status_str = f"{Colors.YELLOW}Passed with warnings{Colors.ENDC}"
        else:
            status_str = f"{Colors.RED}Failed{Colors.ENDC}"

        print(f"• {section}: {status_str}")

    # Generate recommendations
    print_section("RECOMMENDATIONS")

    any_recommendations = False

    for section, results in validation_results.items():
        if not results.get("passed", True):
            any_recommendations = True
            print(f"\n{Colors.BOLD}{section}:{Colors.ENDC}")

            # Different recommendations based on section
            if section == "Figma PAT Validation":
                print(
                    f"  • Ensure FIGMA_PAT environment variable is set with a token that has the required scopes:"
                )
                print(f"    - files:read")
                print(f"    - variables:write")
                print(f"    - code_connect:write")
                print(
                    f"  • You can validate it manually: python scripts/validate_figma_pat.py"
                )

            elif section == "Component Library Validation":
                print(
                    f"  • Ensure the component-adaptation-mapping.json properly maps to the implementation files"
                )
                print(
                    f"  • Run the component mapping analysis: python scripts/improve_component_mapping.py"
                )

            elif section == "Infrastructure Validation":
                if (
                    "vertex_ai" in results
                    and results["vertex_ai"].get("status") != "success"
                ):
                    print(
                        f"  • Update Vertex AI Workbench configuration to use n1-standard-4 instance type"
                    )

                if (
                    "firestore" in results
                    and results["firestore"].get("status") != "success"
                ):
                    print(f"  • Configure Firestore NATIVE with proper backup policies")

                if "redis" in results and results["redis"].get("status") != "success":
                    print(
                        f"  • Update Memorystore Redis configuration to use 3GB capacity"
                    )

                if "roles" in results and results["roles"].get("status") != "success":
                    print(f"  • Ensure service account has all required roles:")
                    for role in [
                        "roles/secretmanager.secretAccessor",
                        "roles/aiplatform.user",
                        "roles/redis.editor",
                    ]:
                        if role in results.get("roles", {}).get("message", ""):
                            print(f"    - Add {role}")

            elif section == "CI/CD Pipeline Validation":
                if (
                    "trigger" in results
                    and results["trigger"].get("status") != "success"
                ):
                    print(
                        f"  • Configure GitHub Actions workflow to trigger on Figma file changes"
                    )
                    print(
                        f"    - Add 'on.repository_dispatch.types: [figma-update]' to workflow file"
                    )

                if (
                    "secrets" in results
                    and results["secrets"].get("status") != "success"
                ):
                    print(
                        f"  • Update secrets mapping in scripts/update_github_org_secrets.sh"
                    )

                if (
                    "webhook_script" not in results
                    or results["webhook_script"].get("status") != "success"
                ):
                    print(
                        f"  • Create a script to set up Figma webhook: scripts/setup_figma_webhook.sh"
                    )

            elif section == "AI Requirements Validation":
                if "cline" in results and results["cline"].get("status") != "success":
                    print(f"  • Install or update Cline MCP tools:")
                    for tool in results.get("cline", {}).get(
                        "missing_tools", ["figma-sync", "terraform-linter", "gcp-cost"]
                    ):
                        print(f"    - cline install {tool}")

                if (
                    "vertex_validation" in results
                    and results["vertex_validation"].get("status") != "success"
                ):
                    print(f"  • Implement Vertex AI validation for design tokens")

                if (
                    "component_test" in results
                    and results["component_test"].get("status") != "success"
                ):
                    print(f"  • Implement Vertex AI component test case generation")

    if not any_recommendations:
        print(
            f"{Colors.GREEN}No recommendations needed - all checks passed!{Colors.ENDC}"
        )

    # Save report to file if requested
    if output_file:
        # Create a version of the results without ANSI color codes
        clean_results = {}
        for section, results in validation_results.items():
            clean_results[section] = {
                k: v for k, v in results.items() if k != "stdout" and k != "stderr"
            }

        try:
            with open(output_file, "w") as f:
                f.write("# Figma-GCP Sync Validation Report\n\n")
                f.write(
                    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

                # Write overall summary
                f.write("## Summary\n\n")
                f.write(
                    f"Overall Status: {'Passed' if successes == total else 'Warning' if successes >= total * 0.8 else 'Failed'}\n"
                )
                f.write(f"Passed: {successes}/{total} checks\n\n")

                # Write section results
                for section, results in clean_results.items():
                    f.write(f"### {section}\n\n")
                    f.write(f"Status: {results.get('status', 'unknown').title()}\n\n")

                    # Write details for each section
                    for key, value in results.items():
                        if key not in [
                            "status",
                            "passed",
                            "details",
                            "error",
                        ] and isinstance(value, dict):
                            f.write(f"- {key}: {value.get('message', 'No details')}\n")

                    f.write("\n")

                # Write recommendations
                f.write("## Recommendations\n\n")
                if any_recommendations:
                    for section, results in clean_results.items():
                        if not results.get("passed", True):
                            f.write(f"### {section}\n\n")

                            # Section-specific recommendations
                            if section == "Figma PAT Validation":
                                f.write(
                                    "- Ensure FIGMA_PAT environment variable is set with a token that has the required scopes:\n"
                                )
                                f.write("  - files:read\n")
                                f.write("  - variables:write\n")
                                f.write("  - code_connect:write\n")
                                f.write(
                                    "- You can validate it manually: python scripts/validate_figma_pat.py\n"
                                )

                            # Add similar content for other sections
                            # ...

                            f.write("\n")
                else:
                    f.write("No recommendations needed - all checks passed!\n")

            print(f"{Colors.GREEN}Report saved to {output_file}{Colors.ENDC}")
        except Exception as e:
            print(
                f"{Colors.RED}Error saving report to {output_file}: {str(e)}{Colors.ENDC}"
            )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Validate Figma-GCP synchronization environment"
    )
    parser.add_argument(
        "--figma-pat",
        help="Figma Personal Access Token (if not provided, will use FIGMA_PAT env var)",
    )
    parser.add_argument(
        "--output",
        default="validation_report.md",
        help="Output file for validation report (default: validation_report.md)",
    )
    parser.add_argument("--verbose", action="store_true", help="Print verbose output")

    args = parser.parse_args()

    print_header("FIGMA-GCP SYNC ENVIRONMENT VALIDATOR")

    # Run each validation check
    validation_results = {
        "Figma PAT Validation": validate_figma_pat(args.figma_pat),
        "Component Library Validation": validate_component_mapping(),
        "Infrastructure Validation": validate_infrastructure(),
        "CI/CD Pipeline Validation": validate_cicd_pipeline(),
        "AI Requirements Validation": validate_ai_requirements(),
    }

    # Generate report
    generate_report(validation_results, args.output)

    # Return exit code based on validation results
    successes = sum(1 for k, v in validation_results.items() if v.get("passed", False))
    total = len(validation_results)

    # Return 0 if all checks passed, or if at least 80% passed
    if successes == total:
        # All checks passed
        return 0
    elif successes >= total * 0.8:
        # Most checks passed
        return 0
    else:
        # Several checks failed
        return 1


if __name__ == "__main__":
    sys.exit(main())
