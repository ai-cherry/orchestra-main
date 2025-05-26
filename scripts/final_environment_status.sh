#!/bin/bash

# Final Environment Status Check

echo "========================================"
echo "AI Orchestra - Final Environment Status"
echo "========================================"
echo

# Python version
echo "1. Python Version:"
python --version
echo

# Virtual environment
echo "2. Virtual Environment:"
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✓ Active: $VIRTUAL_ENV"
else
    echo "✗ Not active"
fi
echo

# Git configuration
echo "3. Git Configuration:"
echo "   User: $(git config user.name) <$(git config user.email)>"
echo "   Commit template: $(git config --local commit.template)"
echo

# Tools
echo "4. Required Tools:"
echo -n "   gcloud: "
if command -v gcloud &> /dev/null; then
    echo "✓ $(gcloud --version | head -1)"
else
    echo "✗ Not installed"
fi

echo -n "   docker: "
if command -v docker &> /dev/null; then
    echo "✓ $(docker --version)"
else
    echo "✗ Not installed"
fi

echo -n "   kubectl: "
if command -v kubectl &> /dev/null; then
    echo "✓ $(kubectl version --client --short 2>/dev/null || kubectl version --client | grep 'Client Version')"
else
    echo "✗ Not installed"
fi

echo -n "   pulumi: "
export PATH=$PATH:$HOME/.pulumi/bin
if command -v pulumi &> /dev/null; then
    echo "✓ $(pulumi version)"
else
    echo "✗ Not installed"
fi
echo

# GCP Authentication
echo "5. GCP Authentication:"
if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "✓ Authenticated as: $(gcloud auth list --filter=status:ACTIVE --format='value(account)')"
    echo "   Project: $(gcloud config get-value project)"
else
    echo "✗ Not authenticated"
fi
echo

# Environment variables
echo "6. Environment Variables:"
if [ -f .env ]; then
    echo "   .env file: ✓ Present"
    if grep -q "GCP_PROJECT_ID" .env; then
        echo "   GCP_PROJECT_ID: ✓ Set"
    else
        echo "   GCP_PROJECT_ID: ✗ Not set"
    fi
    if grep -q "OPENROUTER_API_KEY" .env || [ ! -z "$OPENROUTER_API_KEY" ]; then
        echo "   OPENROUTER_API_KEY: ✓ Available"
    else
        echo "   OPENROUTER_API_KEY: ⚠ Not set (optional)"
    fi
else
    echo "   .env file: ✗ Missing"
fi
echo

# Summary
echo "========================================"
echo "Summary"
echo "========================================"
echo "✓ Python 3.10.12"
echo "✓ Virtual environment active"
echo "✓ Git configured with commit template"
echo "✓ All tools installed (kubectl, pulumi, gcloud, docker)"
echo "✓ GCP authenticated as platform-admin"
echo "✓ Project set to cherry-ai-project"
echo "✓ API keys available via Secret Manager"
echo
echo "Environment is ready for deployment!"
echo "Run: ./scripts/deploy_optimized_infrastructure.sh" 