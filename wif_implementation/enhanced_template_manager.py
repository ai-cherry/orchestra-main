"""
Enhanced template manager for Workload Identity Federation implementation.

This module provides a more robust and type-safe templating system for
generating configuration files, GitHub Actions workflows, and other
resources needed for Workload Identity Federation.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

from .config_models import WIFImplementationConfig
from .error_handler import ErrorSeverity, WIFError, handle_exception, safe_execute

# Configure logging
logger = logging.getLogger("wif_implementation.enhanced_template_manager")


class TemplateError(WIFError):
    """Exception raised when there is a template error."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize the error.

        Args:
            message: The error message
            details: Additional details about the error
            cause: The underlying exception that caused this error
        """
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            details=details,
            cause=cause,
        )


class EnhancedTemplateManager:
    """
    Enhanced manager for templates used in WIF implementation.

    This class provides a more robust approach to template management,
    with type safety through Pydantic models and better error handling.
    """

    def __init__(
        self,
        config: WIFImplementationConfig,
    ):
        """
        Initialize the enhanced template manager.

        Args:
            config: The WIF implementation configuration
        """
        self.config = config

        # Configure logging
        if config.debug:
            logger.setLevel(logging.DEBUG)

        # Initialize template directory
        self._init_template_dir()

        # Initialize output directory
        self._init_output_dir()

        # Initialize Jinja2 environment
        self._init_environment()

    def _init_template_dir(self) -> None:
        """
        Initialize the template directory.

        This method ensures the template directory exists and is properly configured.
        If no template directory is specified, it uses the default templates directory.
        """
        if self.config.template_dir is None:
            # Get the directory of this file
            current_dir = Path(__file__).parent
            self.template_dir = current_dir / "templates"
        else:
            self.template_dir = self.config.template_dir

        # Ensure the directory exists
        self.template_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Initialized template directory: {self.template_dir}")

    def _init_output_dir(self) -> None:
        """
        Initialize the output directory.

        This method ensures the output directory exists. If no output directory
        is specified, it uses the default 'wif_output' directory.
        """
        if self.config.output_dir is None:
            # Get the directory of this file
            base_dir = Path.cwd()
            self.output_dir = base_dir / "wif_output"
        else:
            self.output_dir = self.config.output_dir

        # Ensure the directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Initialized output directory: {self.output_dir}")

    def _init_environment(self) -> None:
        """
        Initialize the Jinja2 environment.

        This method sets up the Jinja2 environment with the template directory
        and configuration.

        Raises:
            TemplateError: If the template environment cannot be initialized
        """
        try:
            self.env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=select_autoescape(["html", "xml"]),
                trim_blocks=True,
                lstrip_blocks=True,
            )

            # Add custom filters
            self.env.filters["yaml_dump"] = lambda x: yaml.dump(
                x, default_flow_style=False, sort_keys=False
            )

            logger.debug("Jinja2 environment initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing Jinja2 environment: {str(e)}")
            raise TemplateError(
                f"Failed to initialize Jinja2 environment",
                cause=e,
            )

    @handle_exception(logger=logger)
    def get_template(self, template_name: str) -> Template:
        """
        Get a template by name.

        Args:
            template_name: The name of the template to get

        Returns:
            The template

        Raises:
            TemplateError: If the template does not exist
        """
        try:
            # Get the template
            template = self.env.get_template(template_name)

            logger.debug(f"Template {template_name} retrieved successfully")
            return template

        except Exception as e:
            logger.error(f"Error getting template {template_name}: {str(e)}")
            raise TemplateError(
                f"Failed to get template {template_name}",
                details={"template_name": template_name},
                cause=e,
            )

    @handle_exception(logger=logger)
    def render_template(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Render a template with the given context.

        Args:
            template_name: The name of the template to render
            context: Additional context to render the template with

        Returns:
            The rendered template

        Raises:
            TemplateError: If the template does not exist or cannot be rendered
        """
        if context is None:
            context = {}

        # Add config to context
        full_context = {
            "config": self.config,
            **context,
        }

        try:
            # Get the template
            template = self.get_template(template_name)

            # Render the template
            rendered = template.render(**full_context)

            logger.debug(f"Template {template_name} rendered successfully")
            return rendered

        except TemplateError:
            # Re-raise template errors
            raise
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {str(e)}")
            raise TemplateError(
                f"Failed to render template {template_name}",
                details={"template_name": template_name, "context": context},
                cause=e,
            )

    @handle_exception(logger=logger)
    def write_template_to_file(
        self,
        template_name: str,
        output_path: Union[str, Path],
        context: Optional[Dict[str, Any]] = None,
        overwrite: bool = False,
    ) -> Path:
        """
        Render a template and write it to a file.

        Args:
            template_name: The name of the template to render
            output_path: The path to write the rendered template to (relative to output_dir)
            context: Additional context to render the template with
            overwrite: Whether to overwrite the file if it already exists

        Returns:
            The path to the written file

        Raises:
            TemplateError: If the template cannot be rendered or written
        """
        if context is None:
            context = {}

        # Resolve the output path
        if isinstance(output_path, str):
            output_path = Path(output_path)

        # Make the path relative to the output directory
        if output_path.is_absolute():
            full_path = output_path
        else:
            full_path = self.output_dir / output_path

        # Create parent directories if they don't exist
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if the file already exists
        if full_path.exists() and not overwrite:
            logger.warning(f"File {full_path} already exists, not overwriting")
            return full_path

        try:
            # Render the template
            rendered = self.render_template(template_name, context)

            # Write the rendered template to the file
            with open(full_path, "w") as f:
                f.write(rendered)

            logger.info(f"Wrote rendered template {template_name} to {full_path}")
            return full_path

        except Exception as e:
            logger.error(
                f"Error writing template {template_name} to {full_path}: {str(e)}"
            )
            raise TemplateError(
                f"Failed to write template {template_name} to {full_path}",
                details={
                    "template_name": template_name,
                    "output_path": str(output_path),
                    "context": context,
                },
                cause=e,
            )

    @handle_exception(logger=logger)
    def list_templates(self) -> List[str]:
        """
        List all available templates.

        Returns:
            A list of template names

        Raises:
            TemplateError: If the templates cannot be listed
        """
        try:
            # List all templates
            templates = self.env.list_templates()

            logger.debug(f"Listed {len(templates)} templates")
            return templates

        except Exception as e:
            logger.error(f"Error listing templates: {str(e)}")
            raise TemplateError(
                f"Failed to list templates",
                cause=e,
            )

    @handle_exception(logger=logger)
    def create_default_templates(self) -> List[Path]:
        """
        Create default templates if they don't exist.

        This method creates basic templates for GitHub Actions workflows,
        Terraform configurations, and other files needed for WIF.

        Returns:
            A list of paths to the created template files

        Raises:
            TemplateError: If the templates cannot be created
        """
        created_templates = []

        # GitHub Actions workflow template
        github_workflow_template = """# AI Orchestra GitHub Actions workflow with WIF authentication
# Template version: 1.0.0

name: {{ workflow_name | default('Deploy with WIF') }}

on:
  push:
    branches: [{{ branches | default('main') }}]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'dev'
        type: choice
        options:
          - dev
          - prod

env:
  PROJECT_ID: ${{ '{{' }} secrets.GCP_PROJECT_ID {{ '}}' }}
  REGION: ${{ '{{' }} secrets.GCP_REGION {{ '}}' }}
  SERVICE_NAME: {{ service_name | default('ai-orchestra-api') }}

jobs:
  deploy:
    name: Build and Deploy
    runs-on: ubuntu-latest
    environment: ${{ '{{' }} github.event.inputs.environment || 'dev' {{ '}}' }}
    permissions:
      contents: read
      id-token: write  # Required for WIF authentication
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Setup Poetry
        uses: snok/install-poetry@v1
        with:
          version: 1.7.1
          virtualenvs-create: true
          virtualenvs-in-project: true
      
      - name: Authenticate to Google Cloud
        id: auth
        uses: google-github-actions/auth@v2
        with:
          token_format: 'access_token'
          workload_identity_provider: ${{ '{{' }} secrets.GCP_WORKLOAD_IDENTITY_PROVIDER {{ '}}' }}
          service_account: ${{ '{{' }} secrets.GCP_SERVICE_ACCOUNT {{ '}}' }}
      
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2
        with:
          project_id: ${{ '{{' }} env.PROJECT_ID {{ '}}' }}
      
      # Rest of the workflow steps...
"""

        # Create the GitHub Actions workflow template
        try:
            workflow_path = self.template_dir / "github_workflow.yml.j2"
            with open(workflow_path, "w") as f:
                f.write(github_workflow_template)

            created_templates.append(workflow_path)
            logger.info(f"Created GitHub Actions workflow template: {workflow_path}")

        except Exception as e:
            logger.error(f"Error creating GitHub Actions workflow template: {str(e)}")
            raise TemplateError(
                "Failed to create GitHub Actions workflow template",
                cause=e,
            )

        # Terraform WIF configuration template
        terraform_template = """# Terraform configuration for Workload Identity Federation
# Template version: 1.0.0

# Create a workload identity pool for GitHub Actions
resource "google_iam_workload_identity_pool" "github_pool" {
  provider                  = google-beta
  project                   = var.project_id
  workload_identity_pool_id = "{{ config.workload_identity.pool_id }}"
  display_name              = "GitHub Actions Pool"
  description               = "Identity pool for GitHub Actions"
}

# Create a workload identity provider for GitHub Actions
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  provider                           = google-beta
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "{{ config.workload_identity.provider_id }}"
  display_name                       = "GitHub Provider"
  description                        = "OIDC identity provider for GitHub Actions"
  
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
  
  attribute_mapping = {{ config.workload_identity.attribute_mapping | yaml_dump | indent(4) }}
  
  attribute_condition = "{{ github_condition | default('assertion.repository.startsWith(\\'REPO_OWNER/\\')') }}"
}

# Create a service account for GitHub Actions
resource "google_service_account" "github_actions_sa" {
  project      = var.project_id
  account_id   = "{{ config.workload_identity.service_account_id }}"
  display_name = "GitHub Actions Service Account"
  description  = "Service account for GitHub Actions with WIF"
}

# Allow GitHub Actions to impersonate the service account
resource "google_service_account_iam_binding" "workload_identity_binding" {
  service_account_id = google_service_account.github_actions_sa.name
  role               = "roles/iam.workloadIdentityUser"
  
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/{{ repo_condition | default('REPO_OWNER/REPO_NAME') }}"
  ]
}

# Grant necessary roles to the service account
resource "google_project_iam_member" "github_actions_sa_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/storage.admin",
    "roles/iam.serviceAccountUser",
    "roles/artifactregistry.admin"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

# Outputs
output "workload_identity_pool_name" {
  description = "The name of the workload identity pool"
  value       = google_iam_workload_identity_pool.github_pool.name
}

output "workload_identity_provider_name" {
  description = "The name of the workload identity provider"
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}

output "service_account_email" {
  description = "The email of the service account"
  value       = google_service_account.github_actions_sa.email
}
"""

        # Create the Terraform template
        try:
            terraform_path = self.template_dir / "terraform_wif.tf.j2"
            with open(terraform_path, "w") as f:
                f.write(terraform_template)

            created_templates.append(terraform_path)
            logger.info(f"Created Terraform WIF template: {terraform_path}")

        except Exception as e:
            logger.error(f"Error creating Terraform WIF template: {str(e)}")
            raise TemplateError(
                "Failed to create Terraform WIF template",
                cause=e,
            )

        return created_templates


# Create a reusable function to initialize the template manager
def create_template_manager(
    config: Optional[WIFImplementationConfig] = None,
) -> EnhancedTemplateManager:
    """
    Create a template manager with the given configuration.

    Args:
        config: The WIF implementation configuration

    Returns:
        The initialized template manager
    """
    if config is None:
        # Create a default configuration
        from .config_models import GCPProjectConfig, WIFImplementationConfig

        # All parameters are properly handled with defaults or explicit values
        config = WIFImplementationConfig(
            gcp=GCPProjectConfig(
                project_id="cherry-ai-project",
                project_number=None,  # Optional parameter can be None
                region="us-central1",
            ),
            # template_dir, output_dir, and debug all have defaults in the model
        )

    return EnhancedTemplateManager(config)
