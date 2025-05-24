#!/bin/bash
# Bootstrap script for Pulumi GCP infra-as-code using Python venv + pip (no Poetry)
# Ensures a clean, minimal, and reproducible setup for a single-developer workflow.

set -e

cd "$(dirname "$0")"

echo "==> Creating Python virtual environment in ./venv"
python3 -m venv venv

echo "==> Activating virtual environment"
source venv/bin/activate

echo "==> Upgrading pip"
pip install --upgrade pip

echo "==> Installing dependencies from requirements.txt"
pip install -r requirements.txt

echo "==> Pulumi dependencies installed."
echo
echo "==> Next steps:"
echo "1. Initialize your Pulumi project (if not already done):"
echo "   pulumi new gcp-python"
echo "   # Follow prompts for project name, stack, and region."
echo
echo "2. Configure your stack (example for dev):"
echo "   pulumi stack init dev"
echo "   pulumi config set gcp:project <your-gcp-project-id>"
echo "   pulumi config set gcp:region <your-gcp-region>"
echo
echo "3. Define your GCP resources in infra/__main__.py"
echo
echo "4. Deploy with:"
echo "   pulumi up"
echo
echo "5. For more info, see infra/README.md"