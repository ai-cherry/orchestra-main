"""
Orchestra AI - Infrastructure and Secrets Management
Manages all secrets, API keys, and infrastructure configuration
"""

import pulumi
import json
from typing import Dict, Any

# Get config
config = pulumi.Config()

# Define all required secrets
REQUIRED_SECRETS = [
    "OPENAI_API_KEY",
    "NOTION_API_TOKEN",
    "ANTHROPIC_API_KEY",
    "VERCEL_TOKEN",
    "LAMBDA_LABS_API_KEY",
    "PINECONE_API_KEY",
    "WEAVIATE_API_KEY",
    "OPENROUTER_API_KEY",
    "PERPLEXITY_API_KEY",
    "PORTKEY_API_KEY",
    "GITHUB_PAT",
    "SLACK_BOT_TOKEN",
    "SLACK_APP_TOKEN",
    "NEO4J_PASSWORD",
    "GONG_ACCESS_KEY",
    "SLIDESPEAK_API_KEY"
]

# Get all secrets from config
secrets: Dict[str, pulumi.Output[str]] = {}
for secret_name in REQUIRED_SECRETS:
    try:
        secrets[secret_name] = config.require_secret(secret_name)
    except Exception as e:
        print(f"Warning: Secret {secret_name} not configured")

# Export all secrets (they remain encrypted in state)
for name, value in secrets.items():
    pulumi.export(name, value)

# Export a configuration summary (without actual secret values)
summary = {
    "configured_secrets": list(secrets.keys()),
    "total_secrets": len(secrets),
    "missing_secrets": [s for s in REQUIRED_SECRETS if s not in secrets],
    "stack_name": pulumi.get_stack(),
    "project_name": pulumi.get_project()
}

pulumi.export('configuration_summary', json.dumps(summary, indent=2)) 