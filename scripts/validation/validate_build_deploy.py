#!/usr/bin/env python3
# validate_build_deploy.py - Validates Cloud Build and Cloud Deploy

import sys
import json
import argparse
import subprocess
import os
from pathlib import Path


def validate_cloudbuild_config():
    """Validate cloudbuild.yaml exists and is valid"""
    try:
        with open("cloudbuild.yaml", "r") as f:
            content = f.read()
        return True, "cloudbuild.yaml exists and is readable"
    except Exception as e:
        return False, f"Error with cloudbuild.yaml: {str(e)}"


def validate_cloudbuild_service(project_id, location):
    """Validate Cloud Build service is accessible"""
    try:
        result = subprocess.run(
            [
                "gcloud",
                "builds",
                "list",
                f"--project={project_id}",
                "--limit=1",
                "--format=json",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            builds = json.loads(result.stdout) if result.stdout.strip() else []
            return (
                True,
                f"Cloud Build service accessible, found {len(builds)} recent builds",
            )
        else:
            return False, f"Error accessing Cloud Build: {result.stderr}"
    except Exception as e:
        return False, f"Error accessing Cloud Build: {str(e)}"


def validate_artifact_registry(project_id, location):
    """Validate Artifact Registry is accessible"""
    try:
        result = subprocess.run(
            [
                "gcloud",
                "artifacts",
                "repositories",
                "list",
                f"--project={project_id}",
                f"--location={location}",
                "--format=json",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            repos = json.loads(result.stdout) if result.stdout.strip() else []
            return (
                True,
                f"Artifact Registry accessible, found {len(repos)} repositories",
            )
        else:
            return (
                False,
                f"Error listing Artifact Registry repositories: {result.stderr}",
            )
    except Exception as e:
        return False, f"Error accessing Artifact Registry: {str(e)}"


def validate_cloud_deploy(project_id, location):
    """Validate Cloud Deploy is accessible"""
    try:
        result = subprocess.run(
            [
                "gcloud",
                "deploy",
                "delivery-pipelines",
                "list",
                f"--project={project_id}",
                f"--region={location}",
                "--format=json",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            pipelines = json.loads(result.stdout) if result.stdout.strip() else []
            return (
                True,
                f"Cloud Deploy accessible, found {len(pipelines)} delivery pipelines",
            )
        else:
            return False, f"Error listing Cloud Deploy pipelines: {result.stderr}"
    except Exception as e:
        return False, f"Error accessing Cloud Deploy: {str(e)}"


def check_docker_install():
    """Check if Docker is installed and working"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            return True, f"Docker installed: {result.stdout.strip()}"
        else:
            return False, "Docker command failed"
    except Exception as e:
        return False, f"Docker not found or not installed: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description="Validate Cloud Build and Deploy")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    parser.add_argument("--location", required=True, help="GCP Location")
    args = parser.parse_args()

    print("### Cloud Build Configuration Validation")
    config_ok, config_msg = validate_cloudbuild_config()
    print(f"* Cloud Build Config: {'✅' if config_ok else '❌'}")
    print(f"  * {config_msg}")

    print("\n### Cloud Build Service Validation")
    build_ok, build_msg = validate_cloudbuild_service(args.project, args.location)
    print(f"* Cloud Build Service: {'✅' if build_ok else '❌'}")
    print(f"  * {build_msg}")

    print("\n### Artifact Registry Validation")
    artifact_ok, artifact_msg = validate_artifact_registry(args.project, args.location)
    print(f"* Artifact Registry: {'✅' if artifact_ok else '❌'}")
    print(f"  * {artifact_msg}")

    print("\n### Cloud Deploy Validation")
    deploy_ok, deploy_msg = validate_cloud_deploy(args.project, args.location)
    print(f"* Cloud Deploy: {'✅' if deploy_ok else '❌'}")
    print(f"  * {deploy_msg}")

    print("\n### Docker Validation")
    docker_ok, docker_msg = check_docker_install()
    print(f"* Docker: {'✅' if docker_ok else '❌'}")
    print(f"  * {docker_msg}")

    # Overall status
    all_ok = config_ok and build_ok and artifact_ok and deploy_ok and docker_ok
    print(f"\n### Overall Build & Deploy Validation: {'✅' if all_ok else '❌'}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
