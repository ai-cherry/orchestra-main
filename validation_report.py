#!/usr/bin/env python3
"""
Codespaces Environment Validation Script

This script performs a comprehensive validation of the Codespaces environment
based on the specified requirements for:
1. Figma-GCP Sync
2. Component Library Cross-Check
3. Infrastructure Readiness
4. CI/CD Pipeline
5. AI Validation Requirements
"""

import os
import sys
import json
import subprocess
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import re


# ANSI colors for better output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    @classmethod
    def success(cls, text: str) -> str:
        return f"{cls.GREEN}✅ {text}{cls.ENDC}"

    @classmethod
    def warning(cls, text: str) -> str:
        return f"{cls.WARNING}⚠️ {text}{cls.ENDC}"

    @classmethod
    def failure(cls, text: str) -> str:
        return f"{cls.FAIL}❌ {text}{cls.ENDC}"

    @classmethod
    def pending(cls, text: str) -> str:
        return f"{cls.CYAN}⎔ {text}{cls.ENDC}"

    @classmethod
    def header(cls, text: str) -> str:
        return f"{cls.HEADER}{cls.BOLD}{text}{cls.ENDC}"

    @classmethod
    def section(cls, text: str) -> str:
        return f"{cls.BLUE}{cls.BOLD}{text}{cls.ENDC}"


class ValidationResult:
    """Tracks validation results for each category and requirement"""

    def __init__(self):
        self.results = {}
        self.current_category = None

    def set_category(self, category: str) -> None:
        """Set the current category being validated"""
        self.current_category = category
        if category not in self.results:
            self.results[category] = []

    def add_result(self, check_name: str, status: str, description: str) -> None:
        """Add a validation result"""
        if not self.current_category:
            raise ValueError("Category not set")

        self.results[self.current_category].append(
            {
                "check": check_name,
                "status": status,  # "success", "warning", "failure", "pending"
                "description": description,
            }
        )

    def success(self, check_name: str, description: str) -> None:
        """Add a successful validation result"""
        self.add_result(check_name, "success", description)

    def warning(self, check_name: str, description: str) -> None:
        """Add a warning validation result"""
        self.add_result(check_name, "warning", description)

    def failure(self, check_name: str, description: str) -> None:
        """Add a failed validation result"""
        self.add_result(check_name, "failure", description)

    def pending(self, check_name: str, description: str) -> None:
        """Add a pending validation result"""
        self.add_result(check_name, "pending", description)

    def summary(self) -> Dict[str, Dict[str, int]]:
        """Get a summary of validation results"""
        summary = {}
        for category, results in self.results.items():
            category_summary = {
                "success": 0,
                "warning": 0,
                "failure": 0,
                "pending": 0,
                "total": len(results),
            }

            for result in results:
                category_summary[result["status"]] += 1

            summary[category] = category_summary

        return summary

    def print_results(self) -> None:
        """Print validation results in a formatted way"""
        print("\n" + Colors.header("CODESPACES ENVIRONMENT VALIDATION REPORT"))
        print("=" * 80)

        for category, results in self.results.items():
            print(f"\n{Colors.section(category)}")
            print("-" * 80)

            for result in results:
                if result["status"] == "success":
                    status_str = Colors.success(result["check"])
                elif result["status"] == "warning":
                    status_str = Colors.warning(result["check"])
                elif result["status"] == "failure":
                    status_str = Colors.failure(result["check"])
                else:  # pending
                    status_str = Colors.pending(result["check"])

                print(f"{status_str}: {result['description']}")

        # Print summary
        print("\n" + Colors.header("VALIDATION SUMMARY"))
        print("=" * 80)

        summary = self.summary()
        all_success = True

        for category, stats in summary.items():
            status = f"{stats['success']}/{stats['total']} checks passed"

            if stats["failure"] > 0:
                status_str = Colors.failure(status)
                all_success = False
            elif stats["warning"] > 0:
                status_str = Colors.warning(status)
                all_success = False
            elif stats["pending"] > 0:
                status_str = Colors.pending(status)
                all_success = False
            else:
                status_str = Colors.success(status)

            print(f"{Colors.section(category)}: {status_str}")

        if all_success:
            print(f"\n{Colors.success('All validation checks passed!')}")
        else:
            print(f"\n{Colors.warning('Some checks require attention.')}")

        # Print fix instructions if there are failures
        if any(stats["failure"] > 0 for stats in summary.values()):
            print(f"\n{Colors.section('RECOMMENDED FIXES')}")
            print("-" * 80)
            self._print_fix_instructions()

    def _print_fix_instructions(self) -> None:
        """Print fix instructions for failed checks"""
        for category, results in self.results.items():
            for result in results:
                if result["status"] in ["failure", "warning"]:
                    check_name = result["check"]
                    print(f"\n{Colors.section(f'For {category} - {check_name}:')}")
                    fixes = self._get_fix_instructions(category, check_name)
                    for fix in fixes:
                        print(f"  - {fix}")

    def _get_fix_instructions(self, category: str, check_name: str) -> List[str]:
        """Get fix instructions for a specific failed check"""
        # Define potential fixes based on category and check name
        fixes = {
            "Figma-GCP Sync Validation": {
                "FIGMA_PAT Permissions": [
                    "Regenerate your Figma PAT with the required scopes: files:read, variables:write, code_connect:write",
                    "Update the FIGMA_PAT in your environment variables or secrets",
                ]
            },
            "Component Library Cross-Check": {
                "Match component-adaptation-mapping.json": [
                    "Update the component-adaptation-mapping.json file to match the implementation in variables.js and styles.xml",
                    "Ensure all component variants are properly mapped",
                ]
            },
            "Infrastructure Readiness Check": {
                "Terraform Provisioning": [
                    "Verify Terraform configuration in infra/vertex_workbench_config.tf",
                    "Ensure all required resources are properly configured",
                ],
                "Service Account Roles": [
                    "Check if the service account has all required roles",
                    'Grant missing roles using: gcloud projects add-iam-policy-binding [PROJECT_ID] --member="serviceAccount:[SA_EMAIL]" --role="[ROLE]"',
                ],
            },
            "CI/CD Pipeline Verification": {
                "GitHub Actions": [
                    "Verify webhook configuration for Figma file changes",
                    "Check the GitHub workflow files to ensure proper triggers and actions",
                ],
                "Secrets Mapping": [
                    "Update the secrets mapping in scripts/update_github_org_secrets.sh",
                    "Verify that all required secrets are properly mapped",
                ],
            },
            "AI Validation Requirements": {
                "Cline MCP": [
                    "Install or update required Cline MCP tools",
                    "Verify versions using: cline verify tool [TOOL_NAME] --min-version [VERSION]",
                ],
                "Vertex AI": [
                    "Verify Vertex AI configuration for design token validation",
                    "Check component test case generation capabilities",
                ],
            },
        }

        # Return fixes for the specific category and check, or a generic message
        if category in fixes and check_name in fixes[category]:
            return fixes[category][check_name]
        else:
            return ["Review the requirements and update accordingly"]


class EnvironmentValidator:
    """Validates the Codespaces environment against the specified requirements"""

    def __init__(self):
        self.results = ValidationResult()
        self.root_path = Path(".")

    def validate_all(self) -> ValidationResult:
        """Run all validation checks"""
        self.validate_figma_gcp_sync()
        self.validate_component_library()
        self.validate_infrastructure()
        self.validate_cicd_pipeline()
        self.validate_ai_requirements()

        return self.results

    def validate_figma_gcp_sync(self) -> None:
        """Validate Figma-GCP Sync functionality"""
        self.results.set_category("Figma-GCP Sync Validation")

        # Check if figma_gcp_sync.py exists
        figma_script_path = self.root_path / "scripts" / "figma_gcp_sync.py"

        if figma_script_path.exists():
            self.results.success("Script Existence", "figma_gcp_sync.py exists")

            # Check script capabilities by parsing the file
            with open(figma_script_path, "r") as f:
                script_content = f.read()

            # Check for Terraform variables.tf conversion
            if "generate_terraform" in script_content:
                self.results.success(
                    "Terraform Variables",
                    "Can convert Figma variables to Terraform variables.tf",
                )
            else:
                self.results.failure(
                    "Terraform Variables",
                    "Cannot find Terraform conversion functionality",
                )

            # Check for Secret Manager update via vertex_agent SA
            if "update_secret" in script_content and "GCPManager" in script_content:
                self.results.success(
                    "Secret Manager Update",
                    "Can update Secret Manager via vertex_agent SA",
                )
            else:
                self.results.failure(
                    "Secret Manager Update",
                    "Cannot find Secret Manager update functionality",
                )

            # Check for platform-specific style file generation
            style_generators = [
                "generate_css",
                "generate_js",
                "generate_android_xml",
                "generate_ios_swift",
            ]
            found_generators = [
                gen for gen in style_generators if gen in script_content
            ]

            if len(found_generators) >= 3:  # At least 3 platforms supported
                self.results.success(
                    "Style Generation",
                    f"Can generate platform-specific style files ({len(found_generators)} platforms)",
                )
            else:
                self.results.failure(
                    "Style Generation",
                    f"Limited platform support for style generation (only {len(found_generators)} platforms)",
                )
        else:
            self.results.failure("Script Existence", "figma_gcp_sync.py does not exist")

        # Check FIGMA_PAT permissions
        # Note: We can't directly check the permissions, but we can check if it's mentioned in the script
        pat_scopes = ["files:read", "variables:write", "code_connect:write"]
        missing_scopes = []

        # Ideally, we'd check the actual PAT, but we can only check if the script mentions the required scopes
        for scope in pat_scopes:
            if figma_script_path.exists() and scope not in script_content:
                missing_scopes.append(scope)

        if not missing_scopes:
            self.results.pending(
                "FIGMA_PAT Permissions", "Scope validation requires manual verification"
            )
        else:
            self.results.warning(
                "FIGMA_PAT Permissions",
                f"Script doesn't explicitly check for these scopes: {', '.join(missing_scopes)}",
            )

    def validate_component_library(self) -> None:
        """Validate Component Library Cross-Check"""
        self.results.set_category("Component Library Cross-Check")

        # Check if component-adaptation-mapping.json exists
        mapping_path = self.root_path / "component-adaptation-mapping.json"
        variables_js_path = (
            self.root_path / "packages" / "ui" / "src" / "tokens" / "variables.js"
        )
        android_styles_path = (
            self.root_path
            / "packages"
            / "ui"
            / "android"
            / "src"
            / "main"
            / "res"
            / "values"
            / "styles.xml"
        )

        if not mapping_path.exists():
            self.results.failure(
                "Mapping File", "component-adaptation-mapping.json does not exist"
            )
            return

        if not variables_js_path.exists():
            self.results.failure(
                "Variables JS", "packages/ui/src/tokens/variables.js does not exist"
            )
            return

        if not android_styles_path.exists():
            self.results.failure(
                "Android Styles",
                "packages/ui/android/src/main/res/values/styles.xml does not exist",
            )
            return

        # Load the mapping file
        with open(mapping_path, "r") as f:
            mapping_data = json.load(f)

        # Load variables.js (as text, since we'll just do pattern matching)
        with open(variables_js_path, "r") as f:
            variables_js = f.read()

        # Load Android styles.xml
        with open(android_styles_path, "r") as f:
            android_styles = f.read()

        # Check for Button variants (should have 4)
        button_variants_in_mapping = [
            k for k in mapping_data.keys() if k.startswith("Button")
        ]
        button_styles_in_android = re.findall(
            r'style name="Orchestra\.Button\.([^"]+)"', android_styles
        )

        if len(button_styles_in_android) >= 4:
            button_styles_str = ", ".join(button_styles_in_android)
            self.results.success(
                "Button Variants",
                f"Found {len(button_styles_in_android)} button styles in Android: {button_styles_str}",
            )
        else:
            self.results.failure(
                "Button Variants",
                f"Expected at least 4 button variants, found {len(button_styles_in_android)}",
            )

        # Check for Card elevation states (should have 2)
        card_variants_in_mapping = [
            k for k in mapping_data.keys() if k.startswith("Card")
        ]
        card_styles_in_android = re.findall(
            r'style name="Orchestra\.Card([^"]*)"', android_styles
        )

        if len(card_styles_in_android) >= 2:
            card_styles_str = ", ".join(
                [s if s else "Default" for s in card_styles_in_android]
            )
            self.results.success(
                "Card Elevation States",
                f"Found {len(card_styles_in_android)} card styles in Android: {card_styles_str}",
            )
        else:
            self.results.failure(
                "Card Elevation States",
                f"Expected at least 2 card elevation states, found {len(card_styles_in_android)}",
            )

        # Check for Input validation styles (should have 3)
        input_variants_in_mapping = [
            k for k in mapping_data.keys() if k.startswith("Input")
        ]
        input_fields_in_android = re.findall(
            r"TextInputLayout|TextInputEditText|boxStrokeColor|errorTextColor",
            android_styles,
        )

        input_validation_count = len(set(input_fields_in_android))
        if input_validation_count >= 3:
            self.results.success(
                "Input Validation Styles",
                f"Found sufficient input validation styles: {input_validation_count} relevant properties",
            )
        else:
            self.results.failure(
                "Input Validation Styles",
                f"Expected at least 3 input validation styles, found {input_validation_count} relevant properties",
            )

        # Check for matching between mapping and implementations
        # Note: This is a more complex check that would require deeper parsing
        # For now, we'll just check if the keys exist in both files
        components_in_mapping = list(mapping_data.keys())

        # Basic check to see if component names appear in the implementation files
        match_count = 0
        for component in components_in_mapping:
            component_base = component.split(" ")[0].lower()
            if (
                component_base in variables_js.lower()
                and component_base in android_styles.lower()
            ):
                match_count += 1

        match_percentage = (
            (match_count / len(components_in_mapping)) * 100
            if components_in_mapping
            else 0
        )

        if match_percentage >= 80:
            self.results.success(
                "Match component-adaptation-mapping.json",
                f"Found {match_percentage:.0f}% of components in implementation files",
            )
        else:
            self.results.warning(
                "Match component-adaptation-mapping.json",
                f"Only {match_percentage:.0f}% of components found in implementation files",
            )

    def validate_infrastructure(self) -> None:
        """Validate Infrastructure Readiness Check"""
        self.results.set_category("Infrastructure Readiness Check")

        # Check if terraform configuration exists
        tf_config_path = self.root_path / "infra" / "vertex_workbench_config.tf"
        tf_vars_path = self.root_path / "infra" / "vertex_workbench.tfvars"

        if not tf_config_path.exists():
            self.results.failure(
                "Terraform Config", "infra/vertex_workbench_config.tf does not exist"
            )
            return

        if not tf_vars_path.exists():
            self.results.warning(
                "Terraform Variables", "infra/vertex_workbench.tfvars does not exist"
            )

        # Load terraform config
        with open(tf_config_path, "r") as f:
            tf_config = f.read()

        # Check for Vertex AI Workbench (n1-standard-4)
        if "machine_type" in tf_config and "n1-standard-4" in tf_config:
            self.results.success(
                "Vertex AI Workbench", "Configured with n1-standard-4 instance type"
            )
        else:
            self.results.failure(
                "Vertex AI Workbench", "Not configured with n1-standard-4 instance type"
            )

        # Check for Firestore NATIVE with backup policies
        if (
            "google_firestore_database" in tf_config
            and 'type                        = "FIRESTORE_NATIVE"' in tf_config
        ):
            if (
                "google_storage_bucket" in tf_config
                and "firestore_backups" in tf_config
            ):
                self.results.success(
                    "Firestore NATIVE", "Configured with backup policies"
                )
            else:
                self.results.warning(
                    "Firestore NATIVE", "Configured but without clear backup policies"
                )
        else:
            self.results.failure("Firestore NATIVE", "Not configured properly")

        # Check for Memorystore Redis (3GB)
        if "google_redis_instance" in tf_config and "memory_size_gb = 3" in tf_config:
            self.results.success("Memorystore Redis", "Configured with 3GB capacity")
        else:
            self.results.failure(
                "Memorystore Redis", "Not configured with 3GB capacity"
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
            self.results.success(
                "Service Account Roles", "All required roles are assigned"
            )
        else:
            self.results.failure(
                "Service Account Roles", f"Missing roles: {', '.join(missing_roles)}"
            )

    def validate_cicd_pipeline(self) -> None:
        """Validate CI/CD Pipeline Verification"""
        self.results.set_category("CI/CD Pipeline Verification")

        # Check for GitHub Actions workflow files
        github_actions_dir = self.root_path / ".github" / "workflows"

        if not github_actions_dir.exists():
            self.results.warning(
                "GitHub Actions Directory", ".github/workflows directory does not exist"
            )

        # Since we don't have clear access to the GitHub workflows, we'll mark these as pending
        self.results.pending(
            "GitHub Actions Trigger",
            "Trigger on Figma file changes (webhook ID:368236963)",
        )
        self.results.pending(
            "GitHub Actions Validation", "Run vertex-ai-validate on style changes"
        )
        self.results.pending(
            "GitHub Actions Deployment", "Deploy to Cloud Run with canary staging"
        )

        # Check for secrets mapping
        secrets_script_path = (
            self.root_path / "scripts" / "update_github_org_secrets.sh"
        )

        if not secrets_script_path.exists():
            self.results.failure(
                "Secrets Mapping Script",
                "scripts/update_github_org_secrets.sh does not exist",
            )
            return

        with open(secrets_script_path, "r") as f:
            secrets_script = f.read()

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
            self.results.success(
                "Secrets Mapping", "All required secrets are properly mapped"
            )
        else:
            self.results.failure(
                "Secrets Mapping", f"Missing mappings: {', '.join(missing_mappings)}"
            )

    def validate_ai_requirements(self) -> None:
        """Validate AI Validation Requirements"""
        self.results.set_category("AI Validation Requirements")

        # For Cline MCP tools, we'd need to run actual commands,
        # but we'll just check if there are any scripts that reference these tools
        cline_tools = [
            ("figma-sync", "1.3.0"),
            ("terraform-linter", "2.8"),
            ("gcp-cost", "0.9"),
        ]

        for tool_name, min_version in cline_tools:
            self.results.pending(
                f"Cline MCP: {tool_name}", f"Version {min_version}+ required"
            )

        # Check for Vertex AI validation capabilities
        vertex_ai_check_1 = False
        vertex_ai_check_2 = False

        # Look for any script that might validate design tokens
        for py_file in self.root_path.glob("**/*.py"):
            with open(py_file, "r") as f:
                py_content = f.read()

            if (
                "from google.cloud import aiplatform" in py_content
                and "validate" in py_content.lower()
                and "design" in py_content.lower()
            ):
                vertex_ai_check_1 = True

            if (
                "from google.cloud import aiplatform" in py_content
                and "component" in py_content.lower()
                and "test" in py_content.lower()
            ):
                vertex_ai_check_2 = True

        if vertex_ai_check_1:
            self.results.success(
                "Vertex AI Design Token Validation",
                "Found code for validating design tokens via AutoML",
            )
        else:
            self.results.pending(
                "Vertex AI Design Token Validation",
                "Could not verify AutoML design token validation",
            )

        if vertex_ai_check_2:
            self.results.success(
                "Vertex AI Component Test Cases",
                "Found code for generating component test cases",
            )
        else:
            self.results.pending(
                "Vertex AI Component Test Cases",
                "Could not verify component test case generation",
            )


def main():
    """Main entry point"""
    print("Starting Codespaces environment validation...")

    validator = EnvironmentValidator()
    results = validator.validate_all()

    results.print_results()

    # Determine exit code based on validation results
    summary = results.summary()
    failures = sum(stats["failure"] for stats in summary.values())

    sys.exit(1 if failures > 0 else 0)


if __name__ == "__main__":
    main()
