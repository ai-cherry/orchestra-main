#!/bin/bash
# Pulumi Secrets Setup Script
# This script will set all required secrets in Pulumi Cloud for the current stack.

set -e

REQUIRED_SECRETS=(
  "OPENAI_API_KEY"
  "NOTION_API_TOKEN"
  "ANTHROPIC_API_KEY"
  "VERCEL_TOKEN"
  "LAMBDA_LABS_API_KEY"
)

for SECRET in "${REQUIRED_SECRETS[@]}"; do
  VALUE="${!SECRET}"
  if [ -z "$VALUE" ]; then
    read -s -p "Enter value for $SECRET: " VALUE
    echo
  fi
  pulumi config set --secret "$SECRET" "$VALUE"
done

echo "✅ All required secrets have been set in Pulumi Cloud for the current stack."
pulumi config --show-secrets 