#!/usr/bin/env python3
"""
SuperAGI Deployment Verification Script
======================================
This script verifies all components of the SuperAGI deployment including:
- Pulumi infrastructure
- Kubernetes resources
- MongoDB connectivity
- SuperAGI functionality
- Secret management
"""

import asyncio
import json
import logging
import os
import subprocess
from typing import List, Tuple
from datetime import datetime

import requests
from kubernetes import client, config
from google.cloud import firestore
import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# Color codes for output
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


class DeploymentVerifier:
    """Main verification class for SuperAGI deployment"""

    def __init__(self):
        self.results = {
            "pulumi": {},
            "kubernetes": {},
            "mongodb": {},
            "superagi": {},
            "secrets": {},
            "integration": {},
        }
        self.errors = []
        self.warnings = []

    def print_header(self, text: str):
        """Print a formatted header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}\n")

    def print_success(self, message: str):
        """Print success message"""
        print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")

    def print_error(self, message: str):
        """Print error message"""
        print(f"{Colors.RED}✗ {message}{Colors.ENDC}")
        self.errors.append(message)

    def print_warning(self, message: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠ {message}{Colors.ENDC}")
        self.warnings.append(message)

    def print_info(self, message: str):
        """Print info message"""
        print(f"  {message}")

    def run_command(self, command: List[str]) -> Tuple[bool, str, str]:
        """Run a shell command and return success, stdout, stderr"""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr
        except Exception as e:
            return False, "", str(e)

    def verify_pulumi_configuration(self):
        """Verify Pulumi stack and configuration"""
        self.print_header("Pulumi Configuration Verification")

        # Check if Pulumi is installed
        success, stdout, stderr = self.run_command(["pulumi", "version"])
        if success:
            self.print_success(f"Pulumi installed: {stdout.strip()}")
            self.results["pulumi"]["installed"] = True
        else:
            self.print_error("Pulumi not installed or not in PATH")
            self.results["pulumi"]["installed"] = False
            return

        # Check current stack
        success, stdout, stderr = self.run_command(["pulumi", "stack", "ls"])
        if success:
            self.print_success("Pulumi stacks available")
            self.print_info(f"Stacks:\n{stdout}")
            self.results["pulumi"]["stacks"] = stdout
        else:
            self.print_error("Failed to list Pulumi stacks")

        # Check stack outputs
        success, stdout, stderr = self.run_command(
            ["pulumi", "stack", "output", "--json"]
        )
        if success:
            try:
                outputs = json.loads(stdout)
                self.print_success("Stack outputs retrieved")

                # Check for expected outputs
                expected_outputs = [
                    "cluster_name",
                    "cluster_endpoint",
                    "superagi_service_ip",
                    "namespace",
                ]

                for output in expected_outputs:
                    if output in outputs:
                        self.print_success(
                            f"Output '{output}' found: {outputs[output]}"
                        )
                        self.results["pulumi"][output] = outputs[output]
                    else:
                        self.print_warning(f"Expected output '{output}' not found")

            except json.JSONDecodeError:
                self.print_error("Failed to parse stack outputs")
        else:
            self.print_error("Failed to get stack outputs")

        # Verify Pulumi ESC
        success, stdout, stderr = self.run_command(["esc", "env", "list"])
        if success:
            self.print_success("Pulumi ESC configured")
            self.results["pulumi"]["esc_configured"] = True
        else:
            self.print_warning("Pulumi ESC not configured (optional)")
            self.results["pulumi"]["esc_configured"] = False

    def verify_kubernetes_resources(self):
        """Verify Kubernetes resources are deployed correctly"""
        self.print_header("Kubernetes Resources Verification")

        try:
            # Load kubeconfig
            config.load_kube_config()
            v1 = client.CoreV1Api()
            apps_v1 = client.AppsV1Api()

            self.print_success("Connected to Kubernetes cluster")

            # Check namespace
            namespace = "superagi"
            try:
                v1.read_namespace(namespace)
                self.print_success(f"Namespace '{namespace}' exists")
                self.results["kubernetes"]["namespace"] = True
            except client.exceptions.ApiException:
                self.print_error(f"Namespace '{namespace}' not found")
                self.results["kubernetes"]["namespace"] = False
                return

            # Check deployments
            deployments = apps_v1.list_namespaced_deployment(namespace)
            expected_deployments = ["superagi", "dragonfly"]

            for expected in expected_deployments:
                found = False
                for deployment in deployments.items:
                    if deployment.metadata.name == expected:
                        found = True
                        ready = deployment.status.ready_replicas or 0
                        desired = deployment.spec.replicas

                        if ready == desired:
                            self.print_success(
                                f"Deployment '{expected}': {ready}/{desired} replicas ready"
                            )
                            self.results["kubernetes"][
                                f"{expected}_deployment"
                            ] = "ready"
                        else:
                            self.print_warning(
                                f"Deployment '{expected}': {ready}/{desired} replicas ready"
                            )
                            self.results["kubernetes"][
                                f"{expected}_deployment"
                            ] = "not_ready"
                        break

                if not found:
                    self.print_error(f"Deployment '{expected}' not found")
                    self.results["kubernetes"][f"{expected}_deployment"] = "missing"

            # Check services
            services = v1.list_namespaced_service(namespace)
            expected_services = ["superagi", "dragonfly"]

            for expected in expected_services:
                found = False
                for service in services.items:
                    if service.metadata.name == expected:
                        found = True
                        service_type = service.spec.type

                        if expected == "superagi" and service_type == "LoadBalancer":
                            if service.status.load_balancer.ingress:
                                ip = service.status.load_balancer.ingress[0].ip
                                self.print_success(
                                    f"Service '{expected}' exposed at: {ip}"
                                )
                                self.results["kubernetes"][
                                    f"{expected}_service_ip"
                                ] = ip
                            else:
                                self.print_warning(
                                    f"Service '{expected}' LoadBalancer IP pending"
                                )
                                self.results["kubernetes"][
                                    f"{expected}_service_ip"
                                ] = "pending"
                        else:
                            self.print_success(
                                f"Service '{expected}' type: {service_type}"
                            )
                            self.results["kubernetes"][
                                f"{expected}_service"
                            ] = service_type
                        break

                if not found:
                    self.print_error(f"Service '{expected}' not found")
                    self.results["kubernetes"][f"{expected}_service"] = "missing"

            # Check pods
            pods = v1.list_namespaced_pod(namespace)
            pod_statuses = {}

            for pod in pods.items:
                app_label = pod.metadata.labels.get("app", "unknown")
                status = pod.status.phase

                if app_label not in pod_statuses:
                    pod_statuses[app_label] = []

                pod_statuses[app_label].append(
                    {
                        "name": pod.metadata.name,
                        "status": status,
                        "ready": all(
                            c.ready for c in pod.status.container_statuses or []
                        ),
                    }
                )

            for app, pods in pod_statuses.items():
                ready_count = sum(1 for p in pods if p["ready"])
                total_count = len(pods)

                if ready_count == total_count:
                    self.print_success(
                        f"Pods for '{app}': {ready_count}/{total_count} ready"
                    )
                else:
                    self.print_warning(
                        f"Pods for '{app}': {ready_count}/{total_count} ready"
                    )

                self.results["kubernetes"][f"{app}_pods"] = {
                    "ready": ready_count,
                    "total": total_count,
                }

        except Exception as e:
            self.print_error(f"Failed to connect to Kubernetes: {str(e)}")
            self.results["kubernetes"]["connected"] = False

    def verify_mongodb_migration(self):
        """Verify MongoDB setup and data migration"""
        self.print_header("MongoDB Migration Verification")

        # For SuperAGI, we're using DragonflyDB (Redis-compatible) for short-term memory
        # and Firestore for long-term storage, not MongoDB
        self.print_info("SuperAGI uses DragonflyDB + Firestore, not MongoDB")

        # Verify DragonflyDB connectivity
        try:
            # Get DragonflyDB service endpoint
            config.load_kube_config()
            v1 = client.CoreV1Api()

            v1.read_namespaced_service("dragonfly", "superagi")
            dragonfly_host = "dragonfly.superagi.svc.cluster.local"
            dragonfly_port = 6379

            # Test Redis connection (DragonflyDB is Redis-compatible)
            r = redis.Redis(
                host=dragonfly_host, port=dragonfly_port, decode_responses=True
            )
            r.ping()

            self.print_success(
                f"DragonflyDB connected at {dragonfly_host}:{dragonfly_port}"
            )
            self.results["mongodb"]["dragonfly_connected"] = True

            # Check some basic stats
            info = r.info()
            self.print_info(
                f"DragonflyDB version: {info.get('redis_version', 'unknown')}"
            )
            self.print_info(f"Connected clients: {info.get('connected_clients', 0)}")
            self.print_info(f"Used memory: {info.get('used_memory_human', 'unknown')}")

        except Exception as e:
            self.print_error(f"Failed to connect to DragonflyDB: {str(e)}")
            self.results["mongodb"]["dragonfly_connected"] = False

        # Verify Firestore connectivity
        try:
            project_id = os.environ.get("GCP_PROJECT_ID")
            if project_id:
                db = firestore.Client(project=project_id)

                # Test connection by reading a collection
                collections = list(db.collections())
                self.print_success(f"Firestore connected to project: {project_id}")
                self.print_info(f"Collections found: {len(collections)}")

                # Check for agents collection
                agents_ref = db.collection("agents")
                agents = list(agents_ref.stream())
                self.print_info(f"Agents in Firestore: {len(agents)}")

                self.results["mongodb"]["firestore_connected"] = True
                self.results["mongodb"]["agent_count"] = len(agents)
            else:
                self.print_warning("GCP_PROJECT_ID not set, skipping Firestore check")
                self.results["mongodb"]["firestore_connected"] = False

        except Exception as e:
            self.print_error(f"Failed to connect to Firestore: {str(e)}")
            self.results["mongodb"]["firestore_connected"] = False

    def verify_superagi_deployment(self):
        """Verify SuperAGI is running and functional"""
        self.print_header("SuperAGI Deployment Verification")

        # Get service endpoint
        service_ip = self.results.get("kubernetes", {}).get("superagi_service_ip")

        if not service_ip or service_ip == "pending":
            self.print_warning("SuperAGI service IP not available, trying port-forward")

            # Try port-forward as fallback
            try:
                # Start port-forward in background
                port_forward = subprocess.Popen(
                    [
                        "kubectl",
                        "port-forward",
                        "-n",
                        "superagi",
                        "service/superagi",
                        "8080:8080",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                # Wait a bit for port-forward to establish
                import time

                time.sleep(3)

                service_url = "http://localhost:8080"
            except Exception as e:
                self.print_error(f"Failed to setup port-forward: {str(e)}")
                return
        else:
            service_url = f"http://{service_ip}:8080"

        # Test health endpoint
        try:
            response = requests.get(f"{service_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.print_success("SuperAGI health check passed")
                self.print_info(f"Status: {health_data.get('status', 'unknown')}")
                self.print_info(f"Version: {health_data.get('version', 'unknown')}")

                # Check service health
                services = health_data.get("services", {})
                for service, status in services.items():
                    if status == "healthy":
                        self.print_success(f"Service '{service}': {status}")
                    else:
                        self.print_warning(f"Service '{service}': {status}")

                self.results["superagi"]["health"] = health_data
            else:
                self.print_error(
                    f"Health check failed with status: {response.status_code}"
                )
                self.results["superagi"]["health"] = "failed"

        except Exception as e:
            self.print_error(f"Failed to reach SuperAGI: {str(e)}")
            self.results["superagi"]["health"] = "unreachable"

        # Test agent listing
        try:
            response = requests.get(f"{service_url}/agents", timeout=10)
            if response.status_code == 200:
                agents_data = response.json()
                agents = agents_data.get("agents", [])
                self.print_success(f"Found {len(agents)} agents")

                for agent in agents:
                    self.print_info(f"Agent: {agent.get('id')} - {agent.get('type')}")

                self.results["superagi"]["agents"] = agents
            else:
                self.print_error(f"Failed to list agents: {response.status_code}")

        except Exception as e:
            self.print_error(f"Failed to list agents: {str(e)}")

        # Clean up port-forward if used
        if "port_forward" in locals():
            port_forward.terminate()

    def verify_secrets_management(self):
        """Verify secrets are properly configured"""
        self.print_header("Secrets Management Verification")

        # Check environment variables
        required_env_vars = ["GCP_PROJECT_ID", "OPENROUTER_API_KEY"]

        for var in required_env_vars:
            if os.environ.get(var):
                self.print_success(f"Environment variable '{var}' is set")
                self.results["secrets"][var] = "set"
            else:
                self.print_warning(f"Environment variable '{var}' not set")
                self.results["secrets"][var] = "missing"

        # Check Kubernetes secrets
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()

            secrets = v1.list_namespaced_secret("superagi")
            secret_names = [s.metadata.name for s in secrets.items]

            if "superagi-secrets" in secret_names:
                self.print_success("Kubernetes secret 'superagi-secrets' exists")
                self.results["secrets"]["k8s_secret"] = True

                # Check secret keys
                secret = v1.read_namespaced_secret("superagi-secrets", "superagi")
                if "openrouter-api-key" in secret.data:
                    self.print_success("OpenRouter API key found in secret")
                else:
                    self.print_warning("OpenRouter API key not found in secret")
            else:
                self.print_warning("Kubernetes secret 'superagi-secrets' not found")
                self.results["secrets"]["k8s_secret"] = False

        except Exception as e:
            self.print_error(f"Failed to check Kubernetes secrets: {str(e)}")

        # Check for old Google Secrets Manager references
        self.print_info("\nChecking for legacy Google Secrets Manager references...")

        # Search for old references in code
        success, stdout, stderr = self.run_command(
            [
                "grep",
                "-r",
                "google.cloud.secretmanager",
                ".",
                "--exclude-dir=.git",
                "--exclude-dir=venv",
                "--exclude-dir=.mypy_cache",
            ]
        )

        if success and stdout:
            self.print_warning("Found Google Secrets Manager references:")
            self.print_info(stdout)
            self.results["secrets"]["legacy_references"] = True
        else:
            self.print_success("No Google Secrets Manager references found")
            self.results["secrets"]["legacy_references"] = False

    def verify_integration(self):
        """Verify end-to-end integration"""
        self.print_header("Integration Verification")

        # Test a simple agent execution
        service_ip = self.results.get("kubernetes", {}).get("superagi_service_ip")

        if not service_ip or service_ip == "pending":
            service_url = "http://localhost:8080"

            # Setup port-forward
            port_forward = subprocess.Popen(
                [
                    "kubectl",
                    "port-forward",
                    "-n",
                    "superagi",
                    "service/superagi",
                    "8080:8080",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            import time

            time.sleep(3)
        else:
            service_url = f"http://{service_ip}:8080"

        try:
            # Test agent execution
            test_payload = {
                "agent_id": "researcher",
                "task": "Test task for verification",
                "memory_context": True,
            }

            response = requests.post(
                f"{service_url}/agents/execute", json=test_payload, timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                self.print_success("Agent execution test passed")
                self.print_info(f"Task ID: {result.get('task_id')}")
                self.print_info(f"Status: {result.get('status')}")

                if result.get("result"):
                    self.print_info(
                        f"Output: {result['result'].get('output', '')[:100]}..."
                    )

                self.results["integration"]["agent_execution"] = "success"
            else:
                self.print_error(f"Agent execution failed: {response.status_code}")
                self.print_info(response.text)
                self.results["integration"]["agent_execution"] = "failed"

        except Exception as e:
            self.print_error(f"Integration test failed: {str(e)}")
            self.results["integration"]["agent_execution"] = "error"

        finally:
            if "port_forward" in locals():
                port_forward.terminate()

    def generate_report(self):
        """Generate final verification report"""
        self.print_header("Verification Summary")

        # Calculate statistics
        total_checks = 0
        passed_checks = 0

        for category, checks in self.results.items():
            for check, result in checks.items():
                total_checks += 1
                if result and result not in [
                    "failed",
                    "missing",
                    "error",
                    "unreachable",
                    False,
                ]:
                    passed_checks += 1

        success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0

        # Print summary
        print(f"{Colors.BOLD}Overall Success Rate: {success_rate:.1f}%{Colors.ENDC}")
        print(f"{Colors.GREEN}Passed: {passed_checks}{Colors.ENDC}")
        print(f"{Colors.RED}Failed: {total_checks - passed_checks}{Colors.ENDC}")

        if self.errors:
            print(f"\n{Colors.RED}Errors ({len(self.errors)}):{Colors.ENDC}")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}Warnings ({len(self.warnings)}):{Colors.ENDC}")
            for warning in self.warnings:
                print(f"  - {warning}")

        # Save detailed report
        report_file = f"superagi_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "summary": {
                        "total_checks": total_checks,
                        "passed_checks": passed_checks,
                        "success_rate": success_rate,
                        "errors": len(self.errors),
                        "warnings": len(self.warnings),
                    },
                    "results": self.results,
                    "errors": self.errors,
                    "warnings": self.warnings,
                },
                f,
                indent=2,
            )

        print(f"\n{Colors.BLUE}Detailed report saved to: {report_file}{Colors.ENDC}")

        # Recommendations
        print(f"\n{Colors.BOLD}Recommendations:{Colors.ENDC}")

        if success_rate < 100:
            if (
                not self.results.get("kubernetes", {}).get("superagi_deployment")
                == "ready"
            ):
                print("  - Wait for SuperAGI deployment to be fully ready")
                print("    Run: kubectl rollout status deployment/superagi -n superagi")

            if not self.results.get("secrets", {}).get("k8s_secret"):
                print("  - Create Kubernetes secret for API keys")
                print(
                    "    Run: kubectl create secret generic superagi-secrets --from-literal=openrouter-api-key=$OPENROUTER_API_KEY -n superagi"
                )

            if self.results.get("secrets", {}).get("legacy_references"):
                print("  - Remove Google Secrets Manager references from code")
                print("    Update code to use environment variables or Pulumi ESC")

        else:
            print("  ✓ All checks passed! Your SuperAGI deployment is ready.")

    async def run_all_verifications(self):
        """Run all verification steps"""
        print(
            f"{Colors.BOLD}{Colors.BLUE}SuperAGI Deployment Verification Tool{Colors.ENDC}"
        )
        print(
            f"Starting verification at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Run all verifications
        self.verify_pulumi_configuration()
        self.verify_kubernetes_resources()
        self.verify_mongodb_migration()
        self.verify_superagi_deployment()
        self.verify_secrets_management()
        self.verify_integration()

        # Generate report
        self.generate_report()


def main():
    """Main entry point"""
    verifier = DeploymentVerifier()
    asyncio.run(verifier.run_all_verifications())


if __name__ == "__main__":
    main()
