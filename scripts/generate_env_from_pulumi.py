#!/usr/bin/env python3
"""Generate .env file from Pulumi secrets."""

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict


def get_pulumi_config() -> Dict[str, Any]:
    """Get all Pulumi configuration including secrets."""
    # Change to infra directory
    original_dir = os.getcwd()
    infra_dir = Path(__file__).parent.parent / "infra"
    os.chdir(infra_dir)

    try:
        # Set passphrase
        os.environ["PULUMI_CONFIG_PASSPHRASE"] = "orchestra-dev-123"

        # Get config with secrets
        result = subprocess.run(
            ["pulumi", "config", "--json", "--show-secrets"],
            capture_output=True,
            text=True,
            check=True,
        )

        config = json.loads(result.stdout)
        return config
    finally:
        os.chdir(original_dir)


def generate_env_file(config: Dict[str, Any], output_path: Path) -> None:
    """Generate .env file from Pulumi config."""

    # Mapping of Pulumi config keys to env var names
    mapping = {
        "mongo_uri": "MONGODB_URI",
        "dragonfly_uri": "DRAGONFLY_URI",
        "weaviate_url": "WEAVIATE_URL",
        "weaviate_api_key": "WEAVIATE_API_KEY",
        "openai_api_key": "OPENAI_API_KEY",
        "anthropic_api_key": "ANTHROPIC_API_KEY",
        "openrouter_api_key": "OPENROUTER_API_KEY",
        "portkey_api_key": "PORTKEY_API_KEY",
        "digitalocean:token": "DIGITALOCEAN_TOKEN",
        "pulumi_access_token": "PULUMI_ACCESS_TOKEN",
    }

    env_content = """# Orchestra AI Configuration
# Generated from Pulumi secrets - DO NOT COMMIT!
# Run: python scripts/generate_env_from_pulumi.py

# Environment
ENVIRONMENT=development
PYTHONPATH=/workspace

"""

    # Add database services
    env_content += "# Database Services\n"
    if "mongo_uri" in config:
        env_content += f"MONGODB_URI={config['mongo_uri']['value']}\n"
        env_content += f"MONGO_URI={config['mongo_uri']['value']}\n"

    if "dragonfly_uri" in config:
        env_content += f"DRAGONFLY_URI={config['dragonfly_uri']['value']}\n"
        # Parse host and port from URI
        uri = config["dragonfly_uri"]["value"]
        if "://" in uri:
            parts = uri.split("://")[1].split("@")[1].split(":")
            host = parts[0]
            port = parts[1].split("/")[0] if "/" in parts[1] else parts[1]
            env_content += f"REDIS_HOST={host}\n"
            env_content += f"REDIS_PORT={port}\n"

    # Add vector search
    env_content += "\n# Vector Search\n"
    if "weaviate_url" in config:
        env_content += f"WEAVIATE_URL={config['weaviate_url']['value']}\n"
    if "weaviate_api_key" in config:
        env_content += f"WEAVIATE_API_KEY={config['weaviate_api_key']['value']}\n"

    # Add LLM services
    env_content += "\n# LLM Services\n"
    for pulumi_key, env_key in mapping.items():
        if pulumi_key in config and "api_key" in pulumi_key:
            env_content += f"{env_key}={config[pulumi_key]['value']}\n"

    # Add deployment tokens
    env_content += "\n# Deployment\n"
    if "digitalocean:token" in config:
        env_content += f"DIGITALOCEAN_TOKEN={config['digitalocean:token']['value']}\n"
    if "pulumi_access_token" in config:
        env_content += f"PULUMI_ACCESS_TOKEN={config['pulumi_access_token']['value']}\n"

    # Add application defaults
    env_content += "\n# Application\n"
    env_content += "SITE_URL=http://localhost:8000\n"
    env_content += "SITE_TITLE=Orchestra AI Development\n"
    env_content += "API_HOST=0.0.0.0\n"
    env_content += "API_PORT=8000\n"

    # Write the file
    output_path.write_text(env_content)
    print(f"✅ Generated {output_path}")

    # Also create .env.example with placeholders
    example_content = env_content
    for key in [
        "MONGODB_URI",
        "MONGO_URI",
        "DRAGONFLY_URI",
        "WEAVIATE_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENROUTER_API_KEY",
        "PORTKEY_API_KEY",
        "DIGITALOCEAN_TOKEN",
        "PULUMI_ACCESS_TOKEN",
    ]:
        if key in example_content:
            example_content = example_content.replace(
                f"{key}={config.get(mapping.get(key, key).lower(), {}).get('value', '')}",
                f"{key}=your_{key.lower()}_here",
            )

    example_path = output_path.parent / ".env.example"
    example_path.write_text(example_content)
    print(f"✅ Generated {example_path}")


def main():
    """Main function."""
    try:
        # Get Pulumi config
        print("📥 Reading Pulumi configuration...")
        config = get_pulumi_config()

        # Generate .env file
        project_root = Path(__file__).parent.parent
        env_path = project_root / ".env"

        generate_env_file(config, env_path)

        # Add to .gitignore if not already there
        gitignore_path = project_root / ".gitignore"
        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text()
            if ".env" not in gitignore_content:
                gitignore_path.write_text(gitignore_content + "\n# Environment files\n.env\n")
                print("✅ Added .env to .gitignore")

        print("\n🎉 Environment setup complete!")
        print("   Run: source .env")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
