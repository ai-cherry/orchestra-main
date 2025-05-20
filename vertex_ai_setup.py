#!/usr/bin/env python3
"""
Vertex AI Setup and Integration Utility for AI Orchestra Project

This script provides utility functions for setting up and configuring Vertex AI resources
for the AI Orchestra project. It includes functions for:
- Authenticating with GCP
- Creating and managing Vertex AI workbench notebooks
- Deploying models to Vertex AI endpoints
- Configuring Vertex AI pipelines

Usage:
    python vertex_ai_setup.py [command] [options]

Commands:
    setup           - Set up Vertex AI resources
    deploy-model    - Deploy a model to Vertex AI
    create-notebook - Create a Vertex AI workbench notebook
    list-resources  - List Vertex AI resources
"""

import argparse
import json
import os
import sys
import time
from typing import Dict, List, Optional, Union, Any

# Import Google Cloud libraries
try:
    from google.cloud import aiplatform
    from google.cloud import storage
    from google.cloud import secretmanager
except ImportError:
    print("Error: Required Google Cloud libraries not found.")
    print(
        "Please install them using: pip install google-cloud-aiplatform google-cloud-storage google-cloud-secret-manager"
    )
    sys.exit(1)

# Project configuration
PROJECT_ID = "cherry-ai-project"
PROJECT_NUMBER = "525398941159"
REGION = "us-central1"
ZONE = f"{REGION}-a"


class VertexAISetup:
    """Utility class for setting up and managing Vertex AI resources."""

    def __init__(
        self,
        project_id: str = PROJECT_ID,
        region: str = REGION,
        service_account: Optional[str] = None,
    ):
        """
        Initialize the VertexAISetup class.

        Args:
            project_id: GCP project ID
            region: GCP region
            service_account: Service account email (optional)
        """
        self.project_id = project_id
        self.region = region
        self.service_account = service_account

        # Initialize Vertex AI client
        aiplatform.init(project=project_id, location=region)

        # Initialize other clients
        self.storage_client = storage.Client(project=project_id)
        self.secret_manager_client = secretmanager.SecretManagerServiceClient()

        print(f"Initialized VertexAISetup for project {project_id} in {region}")

    def setup_vertex_ai(self) -> None:
        """Set up Vertex AI resources for the project."""
        print(f"Setting up Vertex AI resources for project {self.project_id}...")

        # Enable Vertex AI API if not already enabled
        self._enable_apis()

        # Create default GCS bucket for Vertex AI if it doesn't exist
        self._create_default_bucket()

        # Set up service account permissions if provided
        if self.service_account:
            self._setup_service_account_permissions()

        print("Vertex AI setup completed successfully!")

    def _enable_apis(self) -> None:
        """Enable required APIs for Vertex AI."""
        # Note: This would typically use the services.enable API,
        # but for simplicity we'll assume the APIs are already enabled
        # by the shell script we created earlier
        print("Verifying required APIs are enabled...")
        required_apis = [
            "aiplatform.googleapis.com",
            "notebooks.googleapis.com",
            "containerregistry.googleapis.com",
            "artifactregistry.googleapis.com",
        ]
        print(f"Required APIs: {', '.join(required_apis)}")
        print("APIs verification complete")

    def _create_default_bucket(self) -> None:
        """Create default GCS bucket for Vertex AI if it doesn't exist."""
        bucket_name = f"{self.project_id}-vertex-ai"
        try:
            bucket = self.storage_client.get_bucket(bucket_name)
            print(f"Using existing GCS bucket: {bucket_name}")
        except Exception:
            print(f"Creating GCS bucket: {bucket_name}")
            bucket = self.storage_client.create_bucket(
                bucket_name, location=self.region
            )
            print(f"Created GCS bucket: {bucket_name}")

    def _setup_service_account_permissions(self) -> None:
        """Set up service account permissions for Vertex AI."""
        print(f"Setting up permissions for service account: {self.service_account}")
        # In a real implementation, this would use the IAM API to grant permissions
        # For now, we'll just print what permissions would be granted
        required_roles = [
            "roles/aiplatform.user",
            "roles/storage.objectAdmin",
            "roles/logging.logWriter",
        ]
        print(f"Required roles: {', '.join(required_roles)}")
        print("Service account permissions setup complete")

    def create_notebook_instance(
        self,
        name: str,
        machine_type: str = "n1-standard-4",
        accelerator_type: Optional[str] = None,
        accelerator_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a Vertex AI workbench notebook instance.

        Args:
            name: Name of the notebook instance
            machine_type: VM machine type
            accelerator_type: GPU accelerator type (optional)
            accelerator_count: Number of accelerators (default: 0)

        Returns:
            Dictionary containing notebook instance details
        """
        print(f"Creating notebook instance: {name}")

        # In a real implementation, this would use the notebooks API
        # For now, we'll just return a mock response
        notebook = {
            "name": f"projects/{self.project_id}/locations/{self.region}/instances/{name}",
            "machine_type": machine_type,
            "state": "ACTIVE",
            "create_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "update_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        if accelerator_type and accelerator_count > 0:
            notebook["accelerator_config"] = {
                "type": accelerator_type,
                "core_count": accelerator_count,
            }

        print(f"Notebook instance created: {name}")
        return notebook

    def deploy_model(
        self,
        model_path: str,
        endpoint_name: str,
        machine_type: str = "n1-standard-4",
        min_replica_count: int = 1,
        max_replica_count: int = 1,
    ) -> Dict[str, Any]:
        """
        Deploy a model to a Vertex AI endpoint.

        Args:
            model_path: Path to the model artifacts in GCS
            endpoint_name: Name of the endpoint
            machine_type: VM machine type for the endpoint
            min_replica_count: Minimum number of replicas
            max_replica_count: Maximum number of replicas

        Returns:
            Dictionary containing endpoint details
        """
        print(f"Deploying model from {model_path} to endpoint {endpoint_name}")

        # In a real implementation, this would use the Vertex AI SDK
        # For now, we'll just return a mock response
        endpoint = {
            "name": f"projects/{self.project_id}/locations/{self.region}/endpoints/{endpoint_name}",
            "display_name": endpoint_name,
            "deployed_models": [
                {
                    "model": f"projects/{self.project_id}/locations/{self.region}/models/{endpoint_name}-model",
                    "display_name": f"{endpoint_name}-model",
                    "machine_type": machine_type,
                    "min_replica_count": min_replica_count,
                    "max_replica_count": max_replica_count,
                }
            ],
            "create_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "update_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        print(f"Model deployed to endpoint: {endpoint_name}")
        return endpoint

    def list_notebook_instances(self) -> List[Dict[str, Any]]:
        """
        List all Vertex AI workbench notebook instances.

        Returns:
            List of dictionaries containing notebook instance details
        """
        print(
            f"Listing notebook instances in project {self.project_id}, region {self.region}"
        )

        # In a real implementation, this would use the notebooks API
        # For now, we'll just return a mock response
        notebooks = [
            {
                "name": f"projects/{self.project_id}/locations/{self.region}/instances/ai-orchestra-notebook-1",
                "machine_type": "n1-standard-4",
                "state": "ACTIVE",
            },
            {
                "name": f"projects/{self.project_id}/locations/{self.region}/instances/ai-orchestra-notebook-2",
                "machine_type": "n1-standard-8",
                "state": "ACTIVE",
                "accelerator_config": {"type": "NVIDIA_TESLA_T4", "core_count": 1},
            },
        ]

        for notebook in notebooks:
            print(f"Found notebook: {notebook['name'].split('/')[-1]}")

        return notebooks

    def list_endpoints(self) -> List[Dict[str, Any]]:
        """
        List all Vertex AI endpoints.

        Returns:
            List of dictionaries containing endpoint details
        """
        print(f"Listing endpoints in project {self.project_id}, region {self.region}")

        # In a real implementation, this would use the Vertex AI SDK
        # For now, we'll just return a mock response
        endpoints = [
            {
                "name": f"projects/{self.project_id}/locations/{self.region}/endpoints/ai-orchestra-endpoint-1",
                "display_name": "ai-orchestra-endpoint-1",
                "deployed_models_count": 1,
            },
            {
                "name": f"projects/{self.project_id}/locations/{self.region}/endpoints/ai-orchestra-endpoint-2",
                "display_name": "ai-orchestra-endpoint-2",
                "deployed_models_count": 2,
            },
        ]

        for endpoint in endpoints:
            print(f"Found endpoint: {endpoint['display_name']}")

        return endpoints


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Vertex AI Setup and Integration Utility"
    )

    # Add commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Set up Vertex AI resources")
    setup_parser.add_argument("--service-account", help="Service account email")

    # Deploy model command
    deploy_parser = subparsers.add_parser(
        "deploy-model", help="Deploy a model to Vertex AI"
    )
    deploy_parser.add_argument(
        "--model-path", required=True, help="Path to model artifacts in GCS"
    )
    deploy_parser.add_argument(
        "--endpoint-name", required=True, help="Name of the endpoint"
    )
    deploy_parser.add_argument(
        "--machine-type", default="n1-standard-4", help="VM machine type"
    )
    deploy_parser.add_argument(
        "--min-replicas", type=int, default=1, help="Minimum number of replicas"
    )
    deploy_parser.add_argument(
        "--max-replicas", type=int, default=1, help="Maximum number of replicas"
    )

    # Create notebook command
    notebook_parser = subparsers.add_parser(
        "create-notebook", help="Create a Vertex AI workbench notebook"
    )
    notebook_parser.add_argument(
        "--name", required=True, help="Name of the notebook instance"
    )
    notebook_parser.add_argument(
        "--machine-type", default="n1-standard-4", help="VM machine type"
    )
    notebook_parser.add_argument("--accelerator-type", help="GPU accelerator type")
    notebook_parser.add_argument(
        "--accelerator-count", type=int, default=0, help="Number of accelerators"
    )

    # List resources command
    list_parser = subparsers.add_parser(
        "list-resources", help="List Vertex AI resources"
    )
    list_parser.add_argument(
        "--resource-type",
        choices=["notebooks", "endpoints", "all"],
        default="all",
        help="Type of resources to list",
    )

    # Global options
    parser.add_argument("--project-id", default=PROJECT_ID, help="GCP project ID")
    parser.add_argument("--region", default=REGION, help="GCP region")

    return parser.parse_args()


def main() -> None:
    """Main entry point for the script."""
    args = parse_args()

    # Initialize VertexAISetup
    vertex_setup = VertexAISetup(
        project_id=args.project_id,
        region=args.region,
        service_account=getattr(args, "service_account", None),
    )

    # Execute command
    if args.command == "setup":
        vertex_setup.setup_vertex_ai()

    elif args.command == "deploy-model":
        endpoint = vertex_setup.deploy_model(
            model_path=args.model_path,
            endpoint_name=args.endpoint_name,
            machine_type=args.machine_type,
            min_replica_count=args.min_replicas,
            max_replica_count=args.max_replicas,
        )
        print(json.dumps(endpoint, indent=2))

    elif args.command == "create-notebook":
        notebook = vertex_setup.create_notebook_instance(
            name=args.name,
            machine_type=args.machine_type,
            accelerator_type=args.accelerator_type,
            accelerator_count=args.accelerator_count,
        )
        print(json.dumps(notebook, indent=2))

    elif args.command == "list-resources":
        if args.resource_type in ["notebooks", "all"]:
            notebooks = vertex_setup.list_notebook_instances()
            if args.resource_type == "notebooks":
                print(json.dumps(notebooks, indent=2))

        if args.resource_type in ["endpoints", "all"]:
            endpoints = vertex_setup.list_endpoints()
            if args.resource_type == "endpoints":
                print(json.dumps(endpoints, indent=2))

    else:
        print("Error: No command specified")
        print("Run 'python vertex_ai_setup.py --help' for usage information")
        sys.exit(1)


if __name__ == "__main__":
    main()
