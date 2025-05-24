#!/usr/bin/env python3
"""
Configuration Validator for AI Orchestra

This utility validates all configuration files and ensures system integrity
before MCP server startup and during CI/CD processes.

Features:
- YAML/JSON schema validation
- File existence checks
- Service connectivity tests
- Environment variable validation
- Resource availability checks
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Tuple

import yaml
from google.cloud import firestore, secretmanager
from google.cloud.exceptions import NotFound

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ConfigValidator:
    """Comprehensive configuration validator for the Orchestra system."""

    def __init__(self, project_id: str = "cherry-ai-project"):
        self.project_id = project_id
        self.errors: List[str] = []
        self.warnings: List[str] = []

    async def validate_all(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Run all validation checks.

        Returns:
            Tuple of (success, results_dict)
        """
        logger.info("Starting comprehensive configuration validation...")

        results = {"success": True, "checks": {}, "errors": [], "warnings": [], "timestamp": None}

        # Run validation checks
        checks = [
            ("yaml_configs", self._validate_yaml_configs),
            ("mcp_servers", self._validate_mcp_server_configs),
            ("environment", self._validate_environment),
            ("gcp_connectivity", self._validate_gcp_connectivity),
            ("firestore_schema", self._validate_firestore_schema),
            ("secret_access", self._validate_secret_access),
            ("file_permissions", self._validate_file_permissions),
            ("agent_configs", self._validate_agent_configs),
        ]

        for check_name, check_func in checks:
            try:
                logger.info(f"Running {check_name} validation...")
                check_result = await check_func()
                results["checks"][check_name] = check_result

                if not check_result.get("success", False):
                    results["success"] = False

            except Exception as e:
                logger.error(f"Error during {check_name} validation: {e}")
                results["checks"][check_name] = {"success": False, "error": str(e)}
                results["success"] = False

        results["errors"] = self.errors
        results["warnings"] = self.warnings

        return results["success"], results

    async def _validate_yaml_configs(self) -> Dict[str, Any]:
        """Validate all YAML configuration files."""
        yaml_files = [
            "mcp-servers/gcp-resources-server.yaml",
            "core/orchestrator/src/config/personas.yaml",
            "core/orchestrator/src/config/phi_config.yaml",
            "automation_config_sample.yaml",
            ".pre-commit-config.yaml",
            "cloudbuild_data_sync.yaml",
        ]

        results = {"success": True, "files": {}}

        for yaml_file in yaml_files:
            if os.path.exists(yaml_file):
                try:
                    with open(yaml_file, "r") as f:
                        yaml.safe_load(f)
                    results["files"][yaml_file] = {"valid": True}
                    logger.info(f"✓ {yaml_file} is valid YAML")
                except yaml.YAMLError as e:
                    results["files"][yaml_file] = {"valid": False, "error": str(e)}
                    self.errors.append(f"Invalid YAML in {yaml_file}: {e}")
                    results["success"] = False
            else:
                self.warnings.append(f"YAML file not found: {yaml_file}")
                results["files"][yaml_file] = {"valid": False, "error": "File not found"}

        return results

    async def _validate_mcp_server_configs(self) -> Dict[str, Any]:
        """Validate MCP server configurations."""
        mcp_configs = {
            "secret_manager": {"port": 8002, "config_file": "mcp-servers/gcp-resources-server.yaml"},
            "firestore": {"port": 8080, "config_file": "core/orchestrator/src/config/phi_config.yaml"},
        }

        results = {"success": True, "servers": {}}

        for server_name, config in mcp_configs.items():
            server_result = {"config_valid": False, "port_available": False}

            # Check config file exists
            if os.path.exists(config["config_file"]):
                server_result["config_valid"] = True
            else:
                self.errors.append(f"MCP server config missing: {config['config_file']}")
                results["success"] = False

            # Check port availability
            port = config["port"]
            try:
                import socket

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(("localhost", port))
                    if result == 0:
                        server_result["port_status"] = "in_use"
                        logger.info(f"Port {port} is in use (server may be running)")
                    else:
                        server_result["port_status"] = "available"
            except Exception as e:
                server_result["port_status"] = f"error: {e}"
                self.warnings.append(f"Could not check port {port}: {e}")

            results["servers"][server_name] = server_result

        return results

    async def _validate_environment(self) -> Dict[str, Any]:
        """Validate environment variables and system requirements."""
        required_env = ["PROJECT_ID", "FIRESTORE_COLLECTION", "PREFERRED_LLM_PROVIDER"]

        results = {"success": True, "environment": {}}

        for var in required_env:
            value = os.getenv(var)
            if value:
                results["environment"][var] = {
                    "present": True,
                    "value": value[:10] + "..." if len(value) > 10 else value,
                }
            else:
                results["environment"][var] = {"present": False}
                self.warnings.append(f"Environment variable not set: {var}")

        # Check Python version
        import sys

        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        results["python_version"] = python_version

        if sys.version_info < (3, 11):
            self.errors.append(f"Python 3.11+ required, found {python_version}")
            results["success"] = False

        return results

    async def _validate_gcp_connectivity(self) -> Dict[str, Any]:
        """Validate GCP service connectivity."""
        results = {"success": True, "services": {}}

        # Test Firestore connectivity
        try:
            client = firestore.AsyncClient(project=self.project_id)
            # Try to access a collection (doesn't need to exist)
            _ = client.collection("test_connectivity")
            results["services"]["firestore"] = {"accessible": True}
            await client.close()
        except Exception as e:
            results["services"]["firestore"] = {"accessible": False, "error": str(e)}
            self.errors.append(f"Cannot connect to Firestore: {e}")
            results["success"] = False

        # Test Secret Manager connectivity
        try:
            client = secretmanager.SecretManagerServiceAsyncClient()
            parent = f"projects/{self.project_id}"
            # List secrets (requires minimal permissions)
            request = secretmanager.ListSecretsRequest(parent=parent, page_size=1)
            _ = await client.list_secrets(request=request)
            results["services"]["secret_manager"] = {"accessible": True}
        except Exception as e:
            results["services"]["secret_manager"] = {"accessible": False, "error": str(e)}
            self.errors.append(f"Cannot connect to Secret Manager: {e}")
            results["success"] = False

        return results

    async def _validate_firestore_schema(self) -> Dict[str, Any]:
        """Validate Firestore collection schema and structure."""
        results = {"success": True, "collections": {}}

        required_collections = ["agents", "agent_logs", "memory_operations", "memories"]

        try:
            client = firestore.AsyncClient(project=self.project_id)

            for collection_name in required_collections:
                try:
                    # Check if collection exists by trying to get a document
                    collection_ref = client.collection(collection_name)
                    docs = collection_ref.limit(1)
                    doc_count = len([doc async for doc in docs.stream()])

                    results["collections"][collection_name] = {"exists": True, "sample_doc_count": doc_count}
                except Exception as e:
                    results["collections"][collection_name] = {"exists": False, "error": str(e)}
                    self.warnings.append(f"Collection {collection_name} may not exist: {e}")

            await client.close()
        except Exception as e:
            results["success"] = False
            self.errors.append(f"Cannot validate Firestore schema: {e}")

        return results

    async def _validate_secret_access(self) -> Dict[str, Any]:
        """Validate access to required secrets."""
        results = {"success": True, "secrets": {}}

        # Common secret names that might be used
        common_secrets = ["openrouter-api-key", "anthropic-api-key", "gemini-api-key"]

        try:
            client = secretmanager.SecretManagerServiceAsyncClient()

            for secret_name in common_secrets:
                try:
                    name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
                    _ = await client.access_secret_version(request={"name": name})
                    results["secrets"][secret_name] = {"accessible": True}
                except NotFound:
                    results["secrets"][secret_name] = {"accessible": False, "reason": "not_found"}
                    self.warnings.append(f"Secret {secret_name} not found (may not be required)")
                except Exception as e:
                    results["secrets"][secret_name] = {"accessible": False, "reason": str(e)}
                    self.warnings.append(f"Cannot access secret {secret_name}: {e}")

        except Exception as e:
            results["success"] = False
            self.errors.append(f"Cannot validate secret access: {e}")

        return results

    async def _validate_file_permissions(self) -> Dict[str, Any]:
        """Validate file permissions for critical files."""
        results = {"success": True, "files": {}}

        critical_files = ["scripts/check_venv.py", "scripts/check_dependencies.py", "requirements/base.txt", "Makefile"]

        for file_path in critical_files:
            if os.path.exists(file_path):
                stat_info = os.stat(file_path)
                permissions = oct(stat_info.st_mode)[-3:]

                results["files"][file_path] = {
                    "exists": True,
                    "permissions": permissions,
                    "readable": os.access(file_path, os.R_OK),
                    "writable": os.access(file_path, os.W_OK),
                }

                # Check if scripts are executable
                if file_path.endswith(".py") and not os.access(file_path, os.X_OK):
                    self.warnings.append(f"Script {file_path} is not executable")
            else:
                results["files"][file_path] = {"exists": False}
                self.errors.append(f"Critical file missing: {file_path}")
                results["success"] = False

        return results

    async def _validate_agent_configs(self) -> Dict[str, Any]:
        """Validate agent configuration files."""
        results = {"success": True, "configs": {}}

        agent_config_files = [
            "packages/agents/src/config_examples/phidata_config_example.yaml",
            "core/orchestrator/src/config/personas/sophia.yaml",
            "core/orchestrator/src/config/personas/gordon.yaml",
            "core/orchestrator/src/config/personas/cherry.yaml",
        ]

        for config_file in agent_config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, "r") as f:
                        config_data = yaml.safe_load(f)

                    # Basic validation - check for required fields
                    required_fields = ["name", "role"] if "personas" in config_file else ["agents"]

                    config_valid = all(field in config_data for field in required_fields)
                    results["configs"][config_file] = {
                        "valid": config_valid,
                        "structure": "correct" if config_valid else "missing_required_fields",
                    }

                    if not config_valid:
                        self.warnings.append(f"Agent config {config_file} missing required fields")

                except Exception as e:
                    results["configs"][config_file] = {"valid": False, "error": str(e)}
                    self.errors.append(f"Invalid agent config {config_file}: {e}")
                    results["success"] = False
            else:
                results["configs"][config_file] = {"valid": False, "error": "File not found"}
                self.warnings.append(f"Agent config file not found: {config_file}")

        return results


async def main():
    """Main entry point for the configuration validator."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate AI Orchestra configuration")
    parser.add_argument("--project-id", default="cherry-ai-project", help="GCP Project ID")
    parser.add_argument("--output", help="Output results to JSON file")
    parser.add_argument("--fail-fast", action="store_true", help="Exit on first error")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    validator = ConfigValidator(project_id=args.project_id)
    success, results = await validator.validate_all()

    # Add timestamp
    from datetime import datetime

    results["timestamp"] = datetime.now().isoformat()

    # Output results
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results written to {args.output}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"Configuration Validation {'PASSED' if success else 'FAILED'}")
    print(f"{'='*60}")

    if results["errors"]:
        print(f"\n❌ ERRORS ({len(results['errors'])}):")
        for error in results["errors"]:
            print(f"  • {error}")

    if results["warnings"]:
        print(f"\n⚠️  WARNINGS ({len(results['warnings'])}):")
        for warning in results["warnings"]:
            print(f"  • {warning}")

    # Check summary
    passed_checks = sum(1 for check in results["checks"].values() if check.get("success", False))
    total_checks = len(results["checks"])
    print(f"\n✅ PASSED: {passed_checks}/{total_checks} checks")

    if args.fail_fast and not success:
        sys.exit(1)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
