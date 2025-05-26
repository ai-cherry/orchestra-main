#!/usr/bin/env python3
"""Migrate all secrets from GitHub and Google Secret Manager to Pulumi."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional
import requests
from google.cloud import secretmanager
from google.oauth2 import service_account


class SecretMigrator:
    """Handles migration of secrets from various sources to Pulumi."""

    def __init__(self):
        self.github_token = os.environ.get("GITHUB_PAT", "")
        self.github_org = "ai-cherry"
        self.github_repo = "orchestra-main"
        self.gcp_project = os.environ.get("GCP_PROJECT_ID", "cherry-ai-project")
        self.pulumi_passphrase = "orchestra-dev-123"
        self.secrets_collected = {}

    def setup_gcp_client(self) -> Optional[secretmanager.SecretManagerServiceClient]:
        """Setup GCP Secret Manager client."""
        try:
            # Try to use service account if available
            sa_path = Path(".secrets/orchestra-service-key.json")
            if sa_path.exists():
                credentials = service_account.Credentials.from_service_account_file(
                    str(sa_path)
                )
                return secretmanager.SecretManagerServiceClient(credentials=credentials)
            else:
                # Fall back to default credentials
                return secretmanager.SecretManagerServiceClient()
        except Exception as e:
            print(f"⚠️  Could not setup GCP client: {e}")
            return None

    def get_github_secrets(self) -> Dict[str, str]:
        """Fetch all secrets from GitHub repository."""
        print("📥 Fetching GitHub secrets...")
        secrets = {}

        if not self.github_token:
            print("⚠️  No GITHUB_PAT found, skipping GitHub secrets")
            return secrets

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Get repository secrets
        url = f"https://api.github.com/repos/{self.github_org}/{self.github_repo}/actions/secrets"

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                secret_names = [s["name"] for s in response.json().get("secrets", [])]
                print(
                    f"   Found {len(secret_names)} GitHub secrets: {', '.join(secret_names)}"
                )

                # Note: We can't get the actual values via API, only names
                # We'll need to map known patterns
                for name in secret_names:
                    if name in [
                        "OPENAI_API_KEY",
                        "ANTHROPIC_API_KEY",
                        "OPENROUTER_API_KEY",
                        "PORTKEY_API_KEY",
                        "DIGITALOCEAN_TOKEN",
                        "PULUMI_ACCESS_TOKEN",
                        "MONGODB_URI",
                        "WEAVIATE_API_KEY",
                    ]:
                        # These will need to be provided from environment or other sources
                        env_value = os.environ.get(name)
                        if env_value:
                            secrets[name] = env_value
                            print(f"   ✓ Found {name} in environment")
            else:
                print(f"⚠️  Could not fetch GitHub secrets: {response.status_code}")
        except Exception as e:
            print(f"⚠️  Error fetching GitHub secrets: {e}")

        return secrets

    def get_gcp_secrets(self) -> Dict[str, str]:
        """Fetch all secrets from Google Secret Manager."""
        print("📥 Fetching GCP secrets...")
        secrets = {}

        client = self.setup_gcp_client()
        if not client:
            return secrets

        try:
            parent = f"projects/{self.gcp_project}"

            # List all secrets
            for secret in client.list_secrets(request={"parent": parent}):
                secret_name = secret.name.split("/")[-1]

                # Get the latest version
                try:
                    version_name = f"{secret.name}/versions/latest"
                    response = client.access_secret_version(
                        request={"name": version_name}
                    )
                    secret_value = response.payload.data.decode("UTF-8")

                    # Map GCP secret names to standard names
                    mapped_name = self.map_secret_name(secret_name)
                    secrets[mapped_name] = secret_value
                    print(f"   ✓ Found {secret_name} -> {mapped_name}")

                except Exception as e:
                    print(f"   ⚠️  Could not access {secret_name}: {e}")

        except Exception as e:
            print(f"⚠️  Error fetching GCP secrets: {e}")

        return secrets

    def map_secret_name(self, name: str) -> str:
        """Map various secret naming conventions to standard names."""
        mappings = {
            # Common variations
            "openai-api-key": "OPENAI_API_KEY",
            "openai_api_key": "OPENAI_API_KEY",
            "OPENAI_KEY": "OPENAI_API_KEY",
            "anthropic-api-key": "ANTHROPIC_API_KEY",
            "anthropic_api_key": "ANTHROPIC_API_KEY",
            "CLAUDE_API_KEY": "ANTHROPIC_API_KEY",
            "mongodb-uri": "MONGODB_URI",
            "mongodb_uri": "MONGODB_URI",
            "MONGO_CONNECTION_STRING": "MONGODB_URI",
            "weaviate-api-key": "WEAVIATE_API_KEY",
            "weaviate_api_key": "WEAVIATE_API_KEY",
            "dragonfly-uri": "DRAGONFLY_URI",
            "dragonfly_uri": "DRAGONFLY_URI",
            "REDIS_URI": "DRAGONFLY_URI",
            "digitalocean-token": "DIGITALOCEAN_TOKEN",
            "do_token": "DIGITALOCEAN_TOKEN",
            "DO_API_TOKEN": "DIGITALOCEAN_TOKEN",
        }

        # Return mapped name or original if no mapping
        return mappings.get(name, name.upper())

    def get_env_secrets(self) -> Dict[str, str]:
        """Get secrets from environment variables and config files."""
        print("📥 Checking environment and config files...")
        secrets = {}

        # Check managed-services.env
        config_path = Path("config/managed-services.env")
        if config_path.exists():
            print("   Reading config/managed-services.env...")
            with open(config_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"')

                        # Map to standard names
                        if key == "MONGODB_URI":
                            secrets["MONGODB_URI"] = value
                        elif key == "DRAGONFLY_URL":
                            secrets["DRAGONFLY_URI"] = value
                        elif key == "WEAVIATE_REST_ENDPOINT":
                            secrets["WEAVIATE_URL"] = value
                        elif key == "WEAVIATE_API_KEY":
                            secrets["WEAVIATE_API_KEY"] = value
                        elif key == "PULUMI_ACCESS_TOKEN":
                            secrets["PULUMI_ACCESS_TOKEN"] = value

        # Check environment variables
        env_keys = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "OPENROUTER_API_KEY",
            "PORTKEY_API_KEY",
            "DIGITALOCEAN_TOKEN",
            "MONGODB_URI",
            "DRAGONFLY_URI",
            "WEAVIATE_URL",
            "WEAVIATE_API_KEY",
            "PULUMI_ACCESS_TOKEN",
            "PERPLEXITY_API_KEY",
        ]

        for key in env_keys:
            if key in os.environ and os.environ[key]:
                secrets[key] = os.environ[key]
                print(f"   ✓ Found {key} in environment")

        return secrets

    def collect_all_secrets(self) -> Dict[str, str]:
        """Collect secrets from all sources."""
        print("\n🔍 Collecting secrets from all sources...\n")

        # Priority order: Environment/Config > GCP > GitHub
        env_secrets = self.get_env_secrets()
        gcp_secrets = self.get_gcp_secrets()
        github_secrets = self.get_github_secrets()

        # Merge with priority
        all_secrets = {}
        all_secrets.update(github_secrets)  # Lowest priority
        all_secrets.update(gcp_secrets)  # Medium priority
        all_secrets.update(env_secrets)  # Highest priority

        # Filter out empty values
        all_secrets = {
            k: v
            for k, v in all_secrets.items()
            if v and v != "your-" + k.lower() + "-here"
        }

        print(f"\n📊 Collected {len(all_secrets)} unique secrets")
        return all_secrets

    def store_in_pulumi(self, secrets: Dict[str, str]) -> None:
        """Store all secrets in Pulumi."""
        print("\n📤 Storing secrets in Pulumi...\n")

        # Change to infra directory
        original_dir = os.getcwd()
        infra_dir = Path("infra")

        if not infra_dir.exists():
            print("❌ infra directory not found!")
            return

        os.chdir(infra_dir)
        os.environ["PULUMI_CONFIG_PASSPHRASE"] = self.pulumi_passphrase

        try:
            # Ensure stack exists
            subprocess.run(
                ["pulumi", "stack", "select", "dev"], capture_output=True, check=False
            )

            # Map secrets to Pulumi config keys
            pulumi_mappings = {
                "MONGODB_URI": "mongo_uri",
                "DRAGONFLY_URI": "dragonfly_uri",
                "WEAVIATE_URL": "weaviate_url",
                "WEAVIATE_API_KEY": "weaviate_api_key",
                "OPENAI_API_KEY": "openai_api_key",
                "ANTHROPIC_API_KEY": "anthropic_api_key",
                "OPENROUTER_API_KEY": "openrouter_api_key",
                "PORTKEY_API_KEY": "portkey_api_key",
                "PERPLEXITY_API_KEY": "perplexity_api_key",
                "DIGITALOCEAN_TOKEN": "digitalocean:token",
                "PULUMI_ACCESS_TOKEN": "pulumi_access_token",
            }

            for env_key, pulumi_key in pulumi_mappings.items():
                if env_key in secrets:
                    print(f"   Setting {pulumi_key}...")
                    subprocess.run(
                        [
                            "pulumi",
                            "config",
                            "set",
                            "--secret",
                            pulumi_key,
                            secrets[env_key],
                        ],
                        capture_output=True,
                        check=True,
                    )
                    print(f"   ✓ Stored {env_key} as {pulumi_key}")

            print("\n✅ All secrets stored in Pulumi!")

        except Exception as e:
            print(f"❌ Error storing secrets: {e}")
        finally:
            os.chdir(original_dir)

    def generate_summary(self, secrets: Dict[str, str]) -> None:
        """Generate a summary of migrated secrets."""
        print("\n📋 Migration Summary\n")
        print("=" * 50)

        required_secrets = [
            "MONGODB_URI",
            "DRAGONFLY_URI",
            "WEAVIATE_URL",
            "WEAVIATE_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "DIGITALOCEAN_TOKEN",
        ]

        optional_secrets = [
            "OPENROUTER_API_KEY",
            "PORTKEY_API_KEY",
            "PERPLEXITY_API_KEY",
            "PULUMI_ACCESS_TOKEN",
        ]

        print("Required Secrets:")
        for secret in required_secrets:
            status = "✅" if secret in secrets else "❌"
            print(f"  {status} {secret}")

        print("\nOptional Secrets:")
        for secret in optional_secrets:
            status = "✅" if secret in secrets else "⚪"
            print(f"  {status} {secret}")

        missing = [s for s in required_secrets if s not in secrets]
        if missing:
            print(f"\n⚠️  Missing required secrets: {', '.join(missing)}")
            print(
                "   Please set these manually or provide them via environment variables"
            )

    def run(self):
        """Run the complete migration process."""
        print("🚀 Starting secret migration to Pulumi\n")

        # Collect all secrets
        secrets = self.collect_all_secrets()

        if not secrets:
            print("❌ No secrets found to migrate!")
            return 1

        # Store in Pulumi
        self.store_in_pulumi(secrets)

        # Generate summary
        self.generate_summary(secrets)

        # Generate .env file
        print("\n🔧 Generating .env file...")
        subprocess.run(
            [sys.executable, "scripts/generate_env_from_pulumi.py"], check=True
        )

        print("\n✅ Migration complete!")
        print("\nNext steps:")
        print("1. Review the migration summary above")
        print("2. Add any missing required secrets manually")
        print("3. Source the environment: source .env")
        print("4. Test your application")
        print("5. Clean up old secret sources (GitHub/GCP)")

        return 0


def main():
    """Main entry point."""
    migrator = SecretMigrator()
    return migrator.run()


if __name__ == "__main__":
    exit(main())
