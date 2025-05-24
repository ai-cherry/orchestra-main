#!/usr/bin/env python3
"""
Secret Manager to Docker Build Arguments Integration

This utility helps safely integrate GCP Secret Manager secrets with Docker builds
by providing mechanisms to:

1. Generate --build-arg arguments for docker build commands
2. Create temporary environment files for docker-compose
3. Update .devcontainer/devcontainer.json environment settings

Usage:
    # Generate build args for a Docker build
    python docker_secrets.py build-args --project-id=my-project --secrets=DB_PASSWORD,API_KEY

    # Generate an env file for docker-compose
    python docker_secrets.py env-file --project-id=my-project --output=.env.build

    # Update devcontainer.json with the latest secret values
    python docker_secrets.py update-devcontainer --project-id=my-project
"""

import argparse
import json
import os
import subprocess
import sys
from typing import Dict, List, Optional

# Add the parent directory to the path so we can import the client library
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

try:
    from python.gcp_secret_client import SecretClient, SecretAccessError
except ImportError:
    print("Cannot import SecretClient. Make sure the library is installed or in the path.")
    print("You can install it with: pip install -e ../../python")
    sys.exit(1)


def get_secrets(client: SecretClient, secret_ids: List[str], project_id: Optional[str] = None) -> Dict[str, str]:
    """
    Retrieve multiple secrets from Secret Manager.

    Args:
        client: SecretClient instance
        secret_ids: List of secret IDs to retrieve
        project_id: Optional project ID override

    Returns:
        Dictionary mapping secret IDs to their values
    """
    results = {}
    errors = []

    for secret_id in secret_ids:
        try:
            value = client.get_secret(
                secret_id=secret_id,
                project_id=project_id,
                version="latest",
                fallback=None,
                allow_missing=False,
            )
            results[secret_id] = value
        except SecretAccessError as e:
            errors.append(f"Error accessing secret '{secret_id}': {e}")

    if errors:
        print("Errors encountered retrieving secrets:", file=sys.stderr)
        for error in errors:
            print(f"  • {error}", file=sys.stderr)

    return results


def generate_build_args(secrets: Dict[str, str]) -> str:
    """
    Generate Docker build arguments from secrets.

    Args:
        secrets: Dictionary of secret ID to value

    Returns:
        String formatted as Docker --build-arg arguments
    """
    build_args = []

    for secret_id, value in secrets.items():
        # Escape special characters
        escaped_value = value.replace("'", "'\\''")
        build_arg = f"--build-arg {secret_id}='{escaped_value}'"
        build_args.append(build_arg)

    return " ".join(build_args)


def generate_env_file(secrets: Dict[str, str], output_path: str) -> None:
    """
    Generate an environment file from secrets.

    Args:
        secrets: Dictionary of secret ID to value
        output_path: Path where the env file will be written
    """
    with open(output_path, "w") as f:
        f.write("# Generated environment file with secrets from GCP Secret Manager\n")
        f.write("# DO NOT COMMIT THIS FILE\n\n")

        for secret_id, value in secrets.items():
            # Escape special characters
            escaped_value = value.replace('"', '\\"')
            f.write(f'{secret_id}="{escaped_value}"\n')

    # Set restrictive permissions
    os.chmod(output_path, 0o600)

    print(f"Environment file generated at {output_path}")
    print(f"File permissions set to 0600 (read/write for owner only)")


def update_devcontainer_json(
    secrets: Dict[str, str], devcontainer_path: str = ".devcontainer/devcontainer.json"
) -> None:
    """
    Update devcontainer.json with environment variables from secrets.

    Args:
        secrets: Dictionary of secret ID to value
        devcontainer_path: Path to devcontainer.json
    """
    if not os.path.exists(devcontainer_path):
        print(f"Error: {devcontainer_path} does not exist", file=sys.stderr)
        return

    # Read the existing devcontainer.json
    try:
        with open(devcontainer_path, "r") as f:
            devcontainer = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: {devcontainer_path} is not valid JSON", file=sys.stderr)
        return

    # Make sure the customizations and vscode sections exist
    if "customizations" not in devcontainer:
        devcontainer["customizations"] = {}

    if "vscode" not in devcontainer["customizations"]:
        devcontainer["customizations"]["vscode"] = {}

    # Update settings for terminal.integrated.env
    if "settings" not in devcontainer["customizations"]["vscode"]:
        devcontainer["customizations"]["vscode"]["settings"] = {}

    if "terminal.integrated.env.linux" not in devcontainer["customizations"]["vscode"]["settings"]:
        devcontainer["customizations"]["vscode"]["settings"]["terminal.integrated.env.linux"] = {}

    # Add the secrets to the terminal environment
    terminal_env = devcontainer["customizations"]["vscode"]["settings"]["terminal.integrated.env.linux"]
    for secret_id, value in secrets.items():
        terminal_env[secret_id] = value

    # Also update the remoteEnv if it exists
    if "remoteEnv" not in devcontainer:
        devcontainer["remoteEnv"] = {}

    for secret_id, value in secrets.items():
        devcontainer["remoteEnv"][secret_id] = value

    # Write the updated devcontainer.json
    with open(devcontainer_path, "w") as f:
        json.dump(devcontainer, f, indent=4)

    print(f"Updated {devcontainer_path} with {len(secrets)} secret environment variables")
    print("WARNING: The devcontainer.json now contains sensitive values.")
    print("Ensure this file is not committed to version control.")
    print("Consider using a template and generating the final version only for local use.")


def docker_build_with_secrets(
    client: SecretClient,
    docker_file: str,
    tag: str,
    secret_ids: List[str],
    project_id: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
) -> None:
    """
    Run a Docker build with secrets from Secret Manager as build arguments.

    Args:
        client: SecretClient instance
        docker_file: Path to Dockerfile
        tag: Tag for the built image
        secret_ids: List of secret IDs to include as build args
        project_id: Optional project ID override
        extra_args: Additional arguments to pass to docker build
    """
    # Get secrets
    secrets = get_secrets(client, secret_ids, project_id)

    if not secrets:
        print("No secrets retrieved, cannot proceed with build", file=sys.stderr)
        sys.exit(1)

    # Generate build args
    build_args = generate_build_args(secrets)

    # Build the command
    cmd = f"docker build -f {docker_file} -t {tag} {build_args}"
    if extra_args:
        cmd += " " + " ".join(extra_args)

    # Run the command
    print(f"Running Docker build with secrets as build arguments")
    result = subprocess.run(cmd, shell=True)

    if result.returncode != 0:
        print(f"Docker build failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)
    else:
        print(f"Docker build completed successfully with tag {tag}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Integrate GCP Secret Manager with Docker builds and devcontainers")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: build-args
    build_args_parser = subparsers.add_parser("build-args", help="Generate Docker build arguments")
    build_args_parser.add_argument("--project-id", required=True, help="GCP Project ID")
    build_args_parser.add_argument("--secrets", required=True, help="Comma-separated list of secret IDs")

    # Command: env-file
    env_file_parser = subparsers.add_parser("env-file", help="Generate environment file for Docker Compose")
    env_file_parser.add_argument("--project-id", required=True, help="GCP Project ID")
    env_file_parser.add_argument("--secrets", required=True, help="Comma-separated list of secret IDs")
    env_file_parser.add_argument("--output", default=".env.build", help="Output file path")

    # Command: update-devcontainer
    devcontainer_parser = subparsers.add_parser(
        "update-devcontainer", help="Update devcontainer.json with secret values"
    )
    devcontainer_parser.add_argument("--project-id", required=True, help="GCP Project ID")
    devcontainer_parser.add_argument("--secrets", required=True, help="Comma-separated list of secret IDs")
    devcontainer_parser.add_argument(
        "--devcontainer-path",
        default=".devcontainer/devcontainer.json",
        help="Path to devcontainer.json",
    )

    # Command: docker-build
    docker_build_parser = subparsers.add_parser("docker-build", help="Run docker build with secrets as build args")
    docker_build_parser.add_argument("--project-id", required=True, help="GCP Project ID")
    docker_build_parser.add_argument("--secrets", required=True, help="Comma-separated list of secret IDs")
    docker_build_parser.add_argument("--dockerfile", default="Dockerfile", help="Path to Dockerfile")
    docker_build_parser.add_argument("--tag", required=True, help="Tag for the built image")
    docker_build_parser.add_argument("--extra-args", help="Additional arguments for docker build")

    return parser.parse_args()


def main():
    """Main entry point for the script."""
    args = parse_args()

    if not args.command:
        print("Error: No command specified", file=sys.stderr)
        print("Run with --help to see available commands", file=sys.stderr)
        sys.exit(1)

    # Initialize the client
    client = SecretClient(project_id=args.project_id)

    # Parse the list of secrets
    secret_ids = args.secrets.split(",")

    if args.command == "build-args":
        # Get secrets and generate build args
        secrets = get_secrets(client, secret_ids, args.project_id)
        if secrets:
            build_args = generate_build_args(secrets)
            print(build_args)

    elif args.command == "env-file":
        # Get secrets and generate env file
        secrets = get_secrets(client, secret_ids, args.project_id)
        if secrets:
            generate_env_file(secrets, args.output)

    elif args.command == "update-devcontainer":
        # Get secrets and update devcontainer.json
        secrets = get_secrets(client, secret_ids, args.project_id)
        if secrets:
            update_devcontainer_json(secrets, args.devcontainer_path)

    elif args.command == "docker-build":
        # Run Docker build with secrets
        extra_args = args.extra_args.split() if args.extra_args else None
        docker_build_with_secrets(
            client=client,
            docker_file=args.dockerfile,
            tag=args.tag,
            secret_ids=secret_ids,
            project_id=args.project_id,
            extra_args=extra_args,
        )


if __name__ == "__main__":
    main()
