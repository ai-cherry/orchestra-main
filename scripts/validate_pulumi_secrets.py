#!/usr/bin/env python3
import subprocess
import sys

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
    "GONG_ACCESS_KEY",
    "SLIDESPEAK_API_KEY"
]

missing = []
for key in REQUIRED_SECRETS:
    result = subprocess.run(["pulumi", "config", "get", key], capture_output=True, text=True)
    if result.returncode != 0:
        missing.append(key)

if missing:
    print(f"❌ Missing required Pulumi secrets: {', '.join(missing)}")
    sys.exit(1)
else:
    print("✅ All required Pulumi secrets are set.")
    sys.exit(0) 