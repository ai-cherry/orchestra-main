#!/usr/bin/env python3
# codespaces_gcp_integration.py - Programmatic integration between GitHub Codespaces and GCP

import argparse
import os
import subprocess

import requests
from google.cloud import secretmanager


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="GitHub Codespaces and GCP integration tool"
    )

    # Main command
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Codespaces commands
    codespace_parser = subparsers.add_parser(
        "codespace", help="Codespace management commands"
    )
    codespace_subparsers = codespace_parser.add_subparsers(dest="codespace_command")

    # Create codespace with GCP env vars
    create_parser = codespace_subparsers.add_parser(
        "create", help="Create a new codespace with GCP environment"
    )
    create_parser.add_argument(
        "--repo", required=True, help="Repository name (owner/repo)"
    )
    create_parser.add_argument(
        "--branch", default="main", help="Branch to create codespace from"
    )
    create_parser.add_argument(
        "--machine", default="standardLinux32gb", help="Machine type"
    )
    create_parser.add_argument("--gcp-project", required=True, help="GCP project ID")
    create_parser.add_argument("--service-account", help="Service account email to use")

    # Sync GCP secrets to codespace
    sync_parser = codespace_subparsers.add_parser(
        "sync-secrets", help="Sync GCP secrets to codespace"
    )
    sync_parser.add_argument("--codespace-name", required=True, help="Codespace name")
    sync_parser.add_argument(
        "--secret-prefix", default="github_", help="Secret prefix in GCP Secret Manager"
    )

    # GCP commands
    gcp_parser = subparsers.add_parser("gcp", help="GCP management commands")
    gcp_subparsers = gcp_parser.add_subparsers(dest="gcp_command")

    # Create GCP service account for GitHub
    sa_parser = gcp_subparsers.add_parser(
        "create-sa", help="Create a GCP service account for GitHub"
    )
    sa_parser.add_argument("--name", required=True, help="Service account name")
    sa_parser.add_argument("--description", help="Service account description")
    sa_parser.add_argument(
        "--github-repo", required=True, help="GitHub repository to grant access to"
    )
    sa_parser.add_argument(
        "--roles", nargs="+", help="Roles to grant to the service account"
    )

    # Create GitHub secret from GCP key
    secret_parser = gcp_subparsers.add_parser(
        "create-secret", help="Create GitHub secret from GCP key"
    )
    secret_parser.add_argument(
        "--repo", required=True, help="Repository name (owner/repo)"
    )
    secret_parser.add_argument(
        "--secret-name", required=True, help="Secret name in GitHub"
    )
    secret_parser.add_argument(
        "--gcp-secret", required=True, help="Secret name in GCP Secret Manager"
    )

    return parser.parse_args()


def get_github_token() -> str:
    """Get GitHub token from environment."""
    token = os.environ.get("GH_PAT_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError(
            "GitHub token not found. Set GH_PAT_TOKEN or GITHUB_TOKEN environment variable."
        )
    return token


def create_codespace_with_gcp(args):
    """Create a new codespace with GCP environment variables."""
    token = get_github_token()

    # Get GCP credentials if service account is provided
    gcp_env_vars = {
        "CLOUDSDK_CORE_PROJECT": args.gcp_project,
    }

    if args.service_account:
        # Get or create service account key
        client = secretmanager.SecretManagerServiceClient()
        secret_name = f"projects/{args.gcp_project}/secrets/github-{args.service_account.split('@')[0]}/versions/latest"

        try:
            response = client.access_secret_version(request={"name": secret_name})
            sa_key_json = response.payload.data.decode("UTF-8")
            print("Using existing service account key from Secret Manager")
        except Exception as e:
            print(f"No existing key found, creating new one: {e}")
            # Create new key using gcloud (alternative: use google-auth)
            subprocess.run(
                [
                    "gcloud",
                    "iam",
                    "service-accounts",
                    "keys",
                    "create",
                    "--iam-account",
                    args.service_account,
                    "/tmp/sa-key.json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            with open("/tmp/sa-key.json", "r") as f:
                sa_key_json = f.read()

            # Store in Secret Manager
            parent = f"projects/{args.gcp_project}"
            secret_id = f"github-{args.service_account.split('@')[0]}"

            try:
                client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": secret_id,
                        "secret": {"replication": {"automatic": {}}},
                    }
                )
            except Exception:
                print(f"Secret {secret_id} already exists, updating it")

            client.add_secret_version(
                request={
                    "parent": f"{parent}/secrets/{secret_id}",
                    "payload": {"data": sa_key_json.encode("UTF-8")},
                }
            )

        # Add to environment variables
        gcp_env_vars["GOOGLE_CREDENTIALS"] = sa_key_json

    # Create codespace using GitHub API
    url = "https://api.github.com/user/codespaces"

    data = {
        "repository_id": args.repo,
        "ref": args.branch,
        "machine": args.machine,
        "location": "WestUs2",  # Choose appropriate location
        "environment_variables": [
            {"name": name, "value": value} for name, value in gcp_env_vars.items()
        ],
    }

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    codespace = response.json()
    print(f"Created codespace: {codespace['name']}")
    print(f"URL: {codespace['web_url']}")
    return codespace


def sync_gcp_secrets_to_codespace(args):
    """Sync GCP secrets to a GitHub Codespace."""
    token = get_github_token()
    codespace_name = args.codespace_name

    # Get GCP secret client
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")

    if not project_id:
        raise ValueError(
            "GCP project ID not found. Set GOOGLE_CLOUD_PROJECT environment variable."
        )

    # List secrets with the given prefix
    parent = f"projects/{project_id}"

    # List all secrets
    try:
        secrets = list(client.list_secrets(request={"parent": parent}))
    except Exception as e:
        print(f"Error listing secrets: {e}")
        return

    # Filter secrets by prefix
    filtered_secrets = [
        secret
        for secret in secrets
        if secret.name.split("/")[-1].startswith(args.secret_prefix)
    ]

    if not filtered_secrets:
        print(f"No secrets found with prefix '{args.secret_prefix}'")
        return

    print(f"Found {len(filtered_secrets)} secrets to sync")

    # Get the latest versions of each secret
    env_vars = {}
    for secret in filtered_secrets:
        secret_name = secret.name
        try:
            response = client.access_secret_version(
                request={"name": f"{secret_name}/versions/latest"}
            )
            secret_value = response.payload.data.decode("UTF-8")
            # Remove prefix from variable name
            var_name = (
                secret_name.split("/")[-1].replace(args.secret_prefix, "").upper()
            )
            env_vars[var_name] = secret_value
        except Exception as e:
            print(f"Error accessing secret {secret_name}: {e}")

    # Update codespace with the environment variables
    url = (
        f"https://api.github.com/user/codespaces/{codespace_name}/environment-variables"
    )

    data = {
        "environment_variables": [
            {"name": name, "value": value} for name, value in env_vars.items()
        ]
    }

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    print(
        f"Successfully synced {len(env_vars)} secrets to codespace {args.codespace_name}"
    )


def create_gcp_sa_for_github(args):
    """Create a GCP service account for GitHub Actions."""
    # Parse GitHub repo format owner/repo
    if "/" not in args.github_repo:
        raise ValueError("GitHub repository must be in the format 'owner/repo'")

    owner, repo = args.github_repo.split("/")

    # Create service account
    subprocess.run(
        [
            "gcloud",
            "iam",
            "service-accounts",
            "create",
            args.name,
            "--description",
            args.description or f"Service account for GitHub repo {args.github_repo}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    print(f"Created service account: {args.name}")

    # Get project ID
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        project_id = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    # Grant roles
    sa_email = f"{args.name}@{project_id}.iam.gserviceaccount.com"

    roles = args.roles or ["roles/viewer"]
    for role in roles:
        subprocess.run(
            [
                "gcloud",
                "projects",
                "add-iam-policy-binding",
                project_id,
                "--member",
                f"serviceAccount:{sa_email}",
                "--role",
                role,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        print(f"Granted role {role} to {sa_email}")

    # Create service account key
    key_path = f"/tmp/{args.name}-key.json"
    subprocess.run(
        [
            "gcloud",
            "iam",
            "service-accounts",
            "keys",
            "create",
            key_path,
            "--iam-account",
            sa_email,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    print(f"Created service account key at {key_path}")

    # Store key in Secret Manager
    client = secretmanager.SecretManagerServiceClient()
    secret_id = f"github-{args.name}"

    try:
        client.create_secret(
            request={
                "parent": f"projects/{project_id}",
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )
    except Exception:
        print(f"Secret {secret_id} already exists, updating it")

    # Read key file and add to secret manager
    with open(key_path, "r") as f:
        key_json = f.read()

    client.add_secret_version(
        request={
            "parent": f"projects/{project_id}/secrets/{secret_id}",
            "payload": {"data": key_json.encode("UTF-8")},
        }
    )

    print(f"Stored key in Secret Manager as {secret_id}")

    # Create GitHub Actions workflow identity configuration
    create_workload_identity_pool(project_id, owner, repo)

    return {
        "service_account_email": sa_email,
        "key_path": key_path,
        "secret_name": secret_id,
    }


def create_workload_identity_pool(project_id, github_owner, github_repo):
    """Create a Workload Identity Federation pool for GitHub Actions."""
    # Check if pool already exists
    try:
        subprocess.run(
            [
                "gcloud",
                "iam",
                "workload-identity-pools",
                "describe",
                "github-pool",
                "--location",
                "global",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        print("Workload Identity Pool already exists")
    except subprocess.CalledProcessError:
        # Create pool
        subprocess.run(
            [
                "gcloud",
                "iam",
                "workload-identity-pools",
                "create",
                "github-pool",
                "--location",
                "global",
                "--display-name",
                "GitHub Actions Pool",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        print("Created Workload Identity Pool: github-pool")

    # Get pool name
    pool_name = (
        f"projects/{project_id}/locations/global/workloadIdentityPools/github-pool"
    )

    # Check if provider exists
    try:
        subprocess.run(
            [
                "gcloud",
                "iam",
                "workload-identity-pools",
                "providers",
                "describe",
                "github-provider",
                "--workload-identity-pool",
                "github-pool",
                "--location",
                "global",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        print("Workload Identity Provider already exists")
    except subprocess.CalledProcessError:
        # Create provider
        subprocess.run(
            [
                "gcloud",
                "iam",
                "workload-identity-pools",
                "providers",
                "create-oidc",
                "github-provider",
                "--workload-identity-pool",
                "github-pool",
                "--location",
                "global",
                "--issuer-uri",
                "https://token.actions.githubusercontent.com",
                "--attribute-mapping",
                "google.subject=assertion.sub,attribute.repository=assertion.repository",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        print("Created Workload Identity Provider: github-provider")

    # Get provider name
    provider_name = f"{pool_name}/providers/github-provider"

    print(f"Workload Identity Provider: {provider_name}")
    print("This can be used in GitHub Actions to authenticate to GCP")
    print(f"Repository: {github_owner}/{github_repo}")

    # Print GitHub Actions YAML example
    print("\nExample GitHub Actions workflow YAML:")
    print(
        f"""
    name: GCP Authentication Example

    on:
      push:
        branches: [ main ]

    jobs:
      deploy:
        runs-on: ubuntu-latest
        permissions:
          contents: read
          id-token: write

        steps:
          - uses: actions/checkout@v3

          - id: 'auth'
            uses: 'google-github-actions/auth@v1'
            with:
              workload_identity_provider: '{provider_name}'
              service_account: 'SERVICE_ACCOUNT_EMAIL'
    """
    )

    return provider_name


def create_github_secret_from_gcp(args):
    """Create a GitHub secret from a GCP Secret Manager secret."""
    token = get_github_token()

    # Get the GCP secret
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")

    if not project_id:
        raise ValueError(
            "GCP project ID not found. Set GOOGLE_CLOUD_PROJECT environment variable."
        )

    # Get the secret value
    secret_name = f"projects/{project_id}/secrets/{args.gcp_secret}/versions/latest"
    try:
        response = client.access_secret_version(request={"name": secret_name})
        secret_value = response.payload.data.decode("UTF-8")
    except Exception as e:
        raise ValueError(f"Error accessing GCP secret {args.gcp_secret}: {e}")

    # Create GitHub secret
    # First, we need the public key for the repository
    url = f"https://api.github.com/repos/{args.repo}/actions/secrets/public-key"

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    public_key_data = response.json()
    public_key = public_key_data["key"]
    key_id = public_key_data["key_id"]

    # Encrypt the secret using the public key
    from nacl import encoding, public

    def encrypt(public_key: str, secret_value: str) -> str:
        """Encrypt a secret using a public key."""
        public_key = public.PublicKey(
            public_key.encode("utf-8"), encoding.Base64Encoder()
        )
        sealed_box = public.SealedBox(public_key)
        encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
        return encoding.Base64Encoder().encode(encrypted).decode("utf-8")

    encrypted_value = encrypt(public_key, secret_value)

    # Create the secret
    url = f"https://api.github.com/repos/{args.repo}/actions/secrets/{args.secret_name}"

    data = {"encrypted_value": encrypted_value, "key_id": key_id}

    response = requests.put(url, headers=headers, json=data)
    response.raise_for_status()

    print(
        f"Successfully created GitHub secret {args.secret_name} from GCP secret {args.gcp_secret}"
    )


def main():
    """Main entry point."""
    args = parse_args()

    if args.command == "codespace":
        if args.codespace_command == "create":
            create_codespace_with_gcp(args)
        elif args.codespace_command == "sync-secrets":
            sync_gcp_secrets_to_codespace(args)
    elif args.command == "gcp":
        if args.gcp_command == "create-sa":
            create_gcp_sa_for_github(args)
        elif args.gcp_command == "create-secret":
            create_github_secret_from_gcp(args)
    else:
        print("No command specified. Use --help for usage information.")


if __name__ == "__main__":
    main()
