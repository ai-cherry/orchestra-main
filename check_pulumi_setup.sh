#!/bin/bash

echo "=== Pulumi Setup Check ==="
echo

# Check if Pulumi is installed
if ! command -v pulumi &> /dev/null; then
    echo "❌ Pulumi is not installed"
    echo "   Install with: curl -fsSL https://get.pulumi.com | sh"
    exit 1
else
    echo "✅ Pulumi is installed: $(pulumi version)"
fi

# Check if logged in
if ! pulumi whoami &> /dev/null; then
    echo "❌ Not logged in to Pulumi"
    echo "   Options:"
    echo "   1. Use Pulumi Service: pulumi login"
    echo "   2. Use GCS backend: pulumi login gs://cherry-ai-project-pulumi-state"
else
    echo "✅ Logged in as: $(pulumi whoami)"
fi

# Check for PULUMI_ACCESS_TOKEN
if [ -z "$PULUMI_ACCESS_TOKEN" ]; then
    echo "⚠️  PULUMI_ACCESS_TOKEN is not set"
    echo "   This is required for CI/CD workflows"
else
    echo "✅ PULUMI_ACCESS_TOKEN is set"
fi

# Check Vultr authentication
if # vultr-cli auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "✅ Vultr authenticated as: $(# vultr-cli auth list --filter=status:ACTIVE --format='value(account)')"
else
    echo "❌ Not authenticated to Vultr"
fi

echo
echo "=== Pulumi Stacks ==="
if [ -d "infra/admin_ui_site" ]; then
    cd infra/admin_ui_site
    echo "Available stacks in admin_ui_site:"
    pulumi stack ls 2>/dev/null || echo "   No stacks found or not logged in"
fi
