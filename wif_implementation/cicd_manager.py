"""CI/CD manager for WIF implementation."""

import json
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable

from .error_handler import WIFError, ErrorSeverity, handle_exception, safe_execute
from . import ImplementationPhase, TaskStatus, Task, ImplementationPlan

logger = logging.getLogger("wif_implementation.cicd_manager")


class CICDError(WIFError):
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            details=details,
            cause=cause,
        )


class CICDManager:
    def __init__(
        self,
        base_path: Optional[Union[str, Path]] = None,
        verbose: bool = False,
        dry_run: bool = False,
    ):
        if base_path is None:
            base_path = Path(".")

        self.base_path = Path(base_path).resolve()
        self.verbose = verbose
        self.dry_run = dry_run
        self.pipelines: List[Dict[str, Any]] = []

        if verbose:
            logger.setLevel(logging.DEBUG)

    def execute_task(self, task_name: str, plan: ImplementationPlan) -> bool:
        task = plan.get_task_by_name(task_name)
        if not task:
            logger.error(f"Task {task_name} not found")
            return False

        if task.phase != ImplementationPhase.CICD:
            logger.error(f"Task {task_name} not in CICD phase")
            return False

        task_map = {
            "identify_pipelines": self._identify_pipelines,
            "analyze_auth_methods": self._analyze_auth_methods,
            "create_templates": self._create_templates,
            "update_pipelines": self._update_pipelines,
            "test_pipelines": self._test_pipelines,
            "monitor_deployments": self._monitor_deployments,
        }

        if task_name in task_map:
            return task_map[task_name](plan)

        logger.error(f"Unknown task: {task_name}")
        return False

    @handle_exception
    def _identify_pipelines(self, plan: ImplementationPlan) -> bool:
        logger.info("identify_pipelines:start")

        # Find GitHub Actions workflow files
        github_workflow_dir = self.base_path / ".github" / "workflows"
        if github_workflow_dir.exists():
            for workflow_file in github_workflow_dir.glob("*.yml"):
                pipeline = {
                    "type": "github_actions",
                    "path": str(workflow_file.relative_to(self.base_path)),
                    "name": workflow_file.stem,
                }
                self.pipelines.append(pipeline)
                logger.info(f"Found GitHub Actions workflow: {pipeline['path']}")

        # Find GitLab CI files
        gitlab_ci_file = self.base_path / ".gitlab-ci.yml"
        if gitlab_ci_file.exists():
            pipeline = {
                "type": "gitlab_ci",
                "path": str(gitlab_ci_file.relative_to(self.base_path)),
                "name": "gitlab-ci",
            }
            self.pipelines.append(pipeline)
            logger.info(f"Found GitLab CI file: {pipeline['path']}")

        # Find Cloud Build files
        for cloudbuild_file in self.base_path.glob("**/cloudbuild*.{yaml,yml}"):
            pipeline = {
                "type": "cloud_build",
                "path": str(cloudbuild_file.relative_to(self.base_path)),
                "name": cloudbuild_file.stem,
            }
            self.pipelines.append(pipeline)
            logger.info(f"Found Cloud Build file: {pipeline['path']}")

        # Find Jenkins files
        for jenkins_file in self.base_path.glob("**/Jenkinsfile"):
            pipeline = {
                "type": "jenkins",
                "path": str(jenkins_file.relative_to(self.base_path)),
                "name": jenkins_file.parent.name,
            }
            self.pipelines.append(pipeline)
            logger.info(f"Found Jenkins file: {pipeline['path']}")

        # Find Azure Pipelines files
        for azure_file in self.base_path.glob("**/azure-pipelines.yml"):
            pipeline = {
                "type": "azure_pipelines",
                "path": str(azure_file.relative_to(self.base_path)),
                "name": azure_file.parent.name,
            }
            self.pipelines.append(pipeline)
            logger.info(f"Found Azure Pipelines file: {pipeline['path']}")

        logger.info(f"identify_pipelines:complete:count={len(self.pipelines)}")
        return True

    @handle_exception
    def _analyze_auth_methods(self, plan: ImplementationPlan) -> bool:
        logger.info("analyze_auth_methods:start")

        # Check if pipelines have been identified
        if not self.pipelines:
            logger.error("No pipelines identified")
            return False

        # Analyze each pipeline
        for pipeline in self.pipelines:
            pipeline_path = self.base_path / pipeline["path"]

            # Read the pipeline file
            try:
                with open(pipeline_path, "r") as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"Error reading pipeline file {pipeline_path}: {str(e)}")
                continue

            # Analyze GitHub Actions workflows
            if pipeline["type"] == "github_actions":
                # Check for service account key authentication
                if re.search(r"google-github-actions/auth@v\d+", content):
                    # Check for Workload Identity Federation
                    if re.search(r"workload_identity_provider", content):
                        pipeline["auth_method"] = "wif"
                        logger.info(
                            f"Pipeline {pipeline['name']} uses Workload Identity Federation"
                        )
                    else:
                        pipeline["auth_method"] = "service_account_key"
                        logger.info(
                            f"Pipeline {pipeline['name']} uses service account key"
                        )
                elif re.search(r"google-github-actions/setup-gcloud@v\d+", content):
                    pipeline["auth_method"] = "service_account_key"
                    logger.info(f"Pipeline {pipeline['name']} uses service account key")
                else:
                    pipeline["auth_method"] = "unknown"
                    logger.info(
                        f"Pipeline {pipeline['name']} uses unknown authentication method"
                    )

            # Analyze Cloud Build files
            elif pipeline["type"] == "cloud_build":
                # Cloud Build uses the default service account
                pipeline["auth_method"] = "default_service_account"
                logger.info(f"Pipeline {pipeline['name']} uses default service account")

            # Analyze GitLab CI files
            elif pipeline["type"] == "gitlab_ci":
                # Check for service account key authentication
                if re.search(r"gcloud auth activate-service-account", content):
                    pipeline["auth_method"] = "service_account_key"
                    logger.info(f"Pipeline {pipeline['name']} uses service account key")
                else:
                    pipeline["auth_method"] = "unknown"
                    logger.info(
                        f"Pipeline {pipeline['name']} uses unknown authentication method"
                    )

            # Analyze Jenkins files
            elif pipeline["type"] == "jenkins":
                # Check for service account key authentication
                if re.search(r"gcloud auth activate-service-account", content):
                    pipeline["auth_method"] = "service_account_key"
                    logger.info(f"Pipeline {pipeline['name']} uses service account key")
                else:
                    pipeline["auth_method"] = "unknown"
                    logger.info(
                        f"Pipeline {pipeline['name']} uses unknown authentication method"
                    )

            # Analyze Azure Pipelines files
            elif pipeline["type"] == "azure_pipelines":
                # Check for service account key authentication
                if re.search(r"gcloud auth activate-service-account", content):
                    pipeline["auth_method"] = "service_account_key"
                    logger.info(f"Pipeline {pipeline['name']} uses service account key")
                else:
                    pipeline["auth_method"] = "unknown"
                    logger.info(
                        f"Pipeline {pipeline['name']} uses unknown authentication method"
                    )

        logger.info("analyze_auth_methods:complete")
        return True

    @handle_exception
    def _create_templates(self, plan: ImplementationPlan) -> bool:
        logger.info("create_templates:start")

        # Create templates directory
        templates_dir = self.base_path / "wif_templates"

        if self.dry_run:
            logger.info(f"Would create templates directory: {templates_dir}")
        else:
            templates_dir.mkdir(exist_ok=True)
            logger.info(f"Created templates directory: {templates_dir}")

        # Create templates with minimal formatting
        templates = {
            "github-workflow-wif-template.yml": {
                "name": "Deploy with WIF",
                "on": {"push": {"branches": ["main"]}, "workflow_dispatch": {}},
                "permissions": {"contents": "read", "id-token": "write"},
                "jobs": {
                    "deploy": {
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {"uses": "actions/checkout@v3"},
                            {
                                "uses": "google-github-actions/auth@v1",
                                "with": {
                                    "workload_identity_provider": "projects/PROJECT_ID/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID",
                                    "service_account": "SERVICE_ACCOUNT_EMAIL",
                                },
                            },
                            {"uses": "google-github-actions/setup-gcloud@v1"},
                            {
                                "run": "gcloud run deploy SERVICE_NAME --source . --region REGION --platform managed --allow-unauthenticated"
                            },
                        ],
                    }
                },
            },
            "cloudbuild-template.yaml": {
                "steps": [
                    {
                        "name": "gcr.io/cloud-builders/docker",
                        "args": ["build", "-t", "gcr.io/$PROJECT_ID/IMAGE_NAME", "."],
                    },
                    {
                        "name": "gcr.io/cloud-builders/docker",
                        "args": ["push", "gcr.io/$PROJECT_ID/IMAGE_NAME"],
                    },
                    {
                        "name": "gcr.io/cloud-builders/gcloud",
                        "args": [
                            "run",
                            "deploy",
                            "SERVICE_NAME",
                            "--image",
                            "gcr.io/$PROJECT_ID/IMAGE_NAME",
                            "--region",
                            "REGION",
                            "--platform",
                            "managed",
                            "--allow-unauthenticated",
                        ],
                    },
                ],
                "images": ["gcr.io/$PROJECT_ID/IMAGE_NAME"],
            },
            "gitlab-ci-wif-template.yml": {
                "stages": ["deploy"],
                "deploy": {
                    "stage": "deploy",
                    "image": "google/cloud-sdk:latest",
                    "script": [
                        "gcloud iam workload-identity-pools create-cred-config projects/PROJECT_ID/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID --service-account=SERVICE_ACCOUNT_EMAIL --output-file=wif.json",
                        "gcloud auth login --cred-file=wif.json",
                        "gcloud run deploy SERVICE_NAME --source . --region REGION --platform managed --allow-unauthenticated",
                    ],
                    "only": ["main"],
                },
            },
        }

        if self.dry_run:
            for template_name in templates:
                logger.info(f"Would create template: {template_name}")
        else:
            import yaml

            for template_name, template_data in templates.items():
                template_path = templates_dir / template_name
                with open(template_path, "w") as f:
                    if template_name.endswith(".yml") or template_name.endswith(
                        ".yaml"
                    ):
                        yaml.dump(template_data, f, default_flow_style=False)
                    else:
                        json.dump(template_data, f, indent=2)
                logger.info(f"template:created:{template_name}")

        logger.info("create_templates:complete")
        return True

    @handle_exception
    def _update_pipelines(self, plan: ImplementationPlan) -> bool:
        logger.info("update_pipelines:start")

        # Check if pipelines have been identified and analyzed
        if not self.pipelines:
            logger.error("No pipelines identified")
            return False

        # Check if templates directory exists
        templates_dir = self.base_path / "wif_templates"
        if not templates_dir.exists():
            logger.error(f"Templates directory not found: {templates_dir}")
            return False

        # Update each pipeline
        for pipeline in self.pipelines:
            # Skip pipelines that already use WIF
            if pipeline.get("auth_method") == "wif":
                logger.info(
                    f"Pipeline {pipeline['name']} already uses Workload Identity Federation"
                )
                continue

            # Skip pipelines with unknown authentication method
            if pipeline.get("auth_method") == "unknown":
                logger.warning(
                    f"Pipeline {pipeline['name']} has unknown authentication method, skipping"
                )
                continue

            # Update GitHub Actions workflows
            if pipeline["type"] == "github_actions":
                self._update_github_workflow(pipeline)

            # Update Cloud Build files
            elif pipeline["type"] == "cloud_build":
                logger.info(
                    f"Cloud Build pipeline {pipeline['name']} uses default service account, no update needed"
                )

            # Update GitLab CI files
            elif pipeline["type"] == "gitlab_ci":
                self._update_gitlab_ci(pipeline)

            # Update Jenkins files
            elif pipeline["type"] == "jenkins":
                logger.warning(
                    f"Jenkins pipeline {pipeline['name']} update not implemented"
                )

            # Update Azure Pipelines files
            elif pipeline["type"] == "azure_pipelines":
                logger.warning(
                    f"Azure Pipelines pipeline {pipeline['name']} update not implemented"
                )

        logger.info("update_pipelines:complete")
        return True

    @handle_exception
    def _update_github_workflow(self, pipeline: Dict[str, Any]) -> bool:
        logger.info(f"update_github_workflow:start:{pipeline['name']}")

        pipeline_path = self.base_path / pipeline["path"]

        # Read the pipeline file
        try:
            with open(pipeline_path, "r") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading pipeline file {pipeline_path}: {str(e)}")
            return False

        # Create a backup
        backup_path = pipeline_path.with_suffix(f"{pipeline_path.suffix}.bak")

        if self.dry_run:
            logger.info(f"Would create backup: {backup_path}")
            logger.info(f"Would update GitHub Actions workflow: {pipeline_path}")
        else:
            # Create a backup
            shutil.copy2(pipeline_path, backup_path)
            logger.info(f"Created backup: {backup_path}")

            # Update the workflow
            # Replace service account key authentication with WIF
            if re.search(r"google-github-actions/auth@v\d+", content):
                # Replace service account key with WIF
                content = re.sub(
                    r"(google-github-actions/auth@v\d+.*?)(\s+with:.*?)(\s+credentials_json:.*?)(\s+)",
                    r"\1\2\n        workload_identity_provider: 'projects/PROJECT_ID/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID'\n        service_account: 'SERVICE_ACCOUNT_EMAIL'\4",
                    content,
                    flags=re.DOTALL,
                )
            elif re.search(r"google-github-actions/setup-gcloud@v\d+", content):
                # Add auth action before setup-gcloud
                content = re.sub(
                    r"(google-github-actions/setup-gcloud@v\d+.*?)(\s+with:.*?)(\s+)",
                    r"google-github-actions/auth@v1\2\n        workload_identity_provider: 'projects/PROJECT_ID/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID'\n        service_account: 'SERVICE_ACCOUNT_EMAIL'\3\1\2\3",
                    content,
                    flags=re.DOTALL,
                )

            # Add permissions if not present
            if not re.search(r"permissions:", content):
                content = re.sub(
                    r"(on:.*?)(\s+jobs:)",
                    r"\1\n\npermissions:\n  contents: read\n  id-token: write\2",
                    content,
                    flags=re.DOTALL,
                )

            # Write the updated workflow
            with open(pipeline_path, "w") as f:
                f.write(content)

            logger.info(f"Updated GitHub Actions workflow: {pipeline_path}")

        logger.info(f"update_github_workflow:complete:{pipeline['name']}")
        return True

    @handle_exception
    def _update_gitlab_ci(self, pipeline: Dict[str, Any]) -> bool:
        logger.info(f"update_gitlab_ci:start:{pipeline['name']}")

        pipeline_path = self.base_path / pipeline["path"]

        # Read the pipeline file
        try:
            with open(pipeline_path, "r") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading pipeline file {pipeline_path}: {str(e)}")
            return False

        # Create a backup
        backup_path = pipeline_path.with_suffix(f"{pipeline_path.suffix}.bak")

        if self.dry_run:
            logger.info(f"Would create backup: {backup_path}")
            logger.info(f"Would update GitLab CI file: {pipeline_path}")
        else:
            # Create a backup
            shutil.copy2(pipeline_path, backup_path)
            logger.info(f"Created backup: {backup_path}")

            # Update the pipeline
            # Replace service account key authentication with WIF
            if re.search(r"gcloud auth activate-service-account", content):
                # Replace service account key with WIF
                content = re.sub(
                    r"gcloud auth activate-service-account.*?--key-file=.*?(\s+)",
                    r"gcloud iam workload-identity-pools create-cred-config projects/PROJECT_ID/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID --service-account=SERVICE_ACCOUNT_EMAIL --output-file=wif.json\n    - gcloud auth login --cred-file=wif.json\1",
                    content,
                    flags=re.DOTALL,
                )

            # Write the updated pipeline
            with open(pipeline_path, "w") as f:
                f.write(content)

            logger.info(f"Updated GitLab CI file: {pipeline_path}")

        logger.info(f"update_gitlab_ci:complete:{pipeline['name']}")
        return True

    @handle_exception
    def _test_pipelines(self, plan: ImplementationPlan) -> bool:
        logger.info("test_pipelines:start")

        if self.dry_run:
            logger.info("Would test pipeline execution")
            return True

        # Check if GitHub CLI is available
        if self._check_command("gh"):
            # Find GitHub Actions workflow files
            github_workflow_dir = self.base_path / ".github" / "workflows"
            if github_workflow_dir.exists():
                for workflow_file in github_workflow_dir.glob("*.yml"):
                    workflow_name = workflow_file.stem

                    # Check if the workflow has a workflow_dispatch trigger
                    try:
                        with open(workflow_file, "r") as f:
                            content = f.read()
                            if "workflow_dispatch" in content:
                                logger.info(
                                    f"Testing GitHub Actions workflow: {workflow_name}"
                                )

                                try:
                                    # Run the workflow
                                    subprocess.check_call(
                                        ["gh", "workflow", "run", workflow_name],
                                        cwd=self.base_path,
                                    )
                                    logger.info(
                                        f"Workflow {workflow_name} triggered successfully"
                                    )
                                except subprocess.CalledProcessError as e:
                                    logger.error(
                                        f"Error triggering workflow {workflow_name}: {str(e)}"
                                    )
                    except Exception as e:
                        logger.error(
                            f"Error reading workflow file {workflow_file}: {str(e)}"
                        )

        logger.info("test_pipelines:complete")
        return True

    @handle_exception
    def _monitor_deployments(self, plan: ImplementationPlan) -> bool:
        logger.info("monitor_deployments:start")

        if self.dry_run:
            logger.info("Would monitor production deployments")
            return True

        # Check if GitHub CLI is available
        if self._check_command("gh"):
            # List recent workflow runs
            try:
                logger.info("Listing recent GitHub Actions workflow runs")

                subprocess.check_call(
                    ["gh", "run", "list", "--limit", "5"],
                    cwd=self.base_path,
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"Error listing workflow runs: {str(e)}")

        # Check if gcloud is available
        if self._check_command("gcloud"):
            # List recent Cloud Build builds
            try:
                logger.info("Listing recent Cloud Build builds")

                subprocess.check_call(
                    ["gcloud", "builds", "list", "--limit", "5"],
                    cwd=self.base_path,
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"Error listing Cloud Build builds: {str(e)}")

        logger.info("monitor_deployments:complete")
        return True

    def _check_command(self, command: str) -> bool:
        try:
            subprocess.check_call(
                ["which", command],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except subprocess.CalledProcessError:
            return False
