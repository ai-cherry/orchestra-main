as#!/bin/bash
# Orchestra API Bootstrap Script
# One-command setup for local/cloud development using pip, requirements.txt, and pip-tools.
# Elegantly integrates dependency management, pre-commit, and secret sync with GCP Secret Manager.

set -euo pipefail

echo "=== [1/6] Ensuring pip and pip-tools are installed ==="
# Install pip-tools if not present (for pip-compile)
if ! python3 -m pip show pip-tools &> /dev/null; then
  echo "Installing pip-tools (pip-compile, pip-sync)..."
  python3 -m pip install --user pip-tools
fi

# Directory for requirements files
REQ_DIR="$(dirname "${BASH_SOURCE[0]}")/../requirements"
REQ_BASE_IN="$REQ_DIR/base.in"
REQ_BASE_TXT="$REQ_DIR/base.txt"
REQ_DEV_IN="$REQ_DIR/dev.in"
REQ_DEV_TXT="$REQ_DIR/dev.txt"

echo "=== [2/6] Compiling requirements (if needed) ==="
# Compile requirements if .txt files are missing or older than .in files
if [ -f "$REQ_BASE_IN" ] && { [ ! -f "$REQ_BASE_TXT" ] || [ "$REQ_BASE_IN" -nt "$REQ_BASE_TXT" ]; }; then
  echo "Compiling $REQ_BASE_IN -> $REQ_BASE_TXT"
  python3 -m piptools compile "$REQ_BASE_IN" --output-file "$REQ_BASE_TXT"
fi
if [ -f "$REQ_DEV_IN" ] && { [ ! -f "$REQ_DEV_TXT" ] || [ "$REQ_DEV_IN" -nt "$REQ_DEV_TXT" ]; }; then
  echo "Compiling $REQ_DEV_IN -> $REQ_DEV_TXT"
  python3 -m piptools compile "$REQ_DEV_IN" --output-file "$REQ_DEV_TXT"
fi

echo "=== [3/6] Installing dependencies with pip ==="
# Prefer dev.txt if present, else base.txt
if [ -f "$REQ_DEV_TXT" ]; then
  python3 -m pip install -r "$REQ_DEV_TXT"
elif [ -f "$REQ_BASE_TXT" ]; then
  python3 -m pip install -r "$REQ_BASE_TXT"
else
  echo "ERROR: No requirements file found. Please ensure $REQ_BASE_TXT or $REQ_DEV_TXT exists."
  exit 1
fi

echo "=== [4/6] Installing pre-commit and hooks ==="
python3 -m pip install --user pre-commit
pre-commit install

echo "=== [5/6] Setting up .env file and syncing secrets from GCP Secret Manager ==="
if [ ! -f .env ]; then
  cp .env.example .env 2>/dev/null || touch .env
  echo "# Edit .env with your local secrets or use GCP Secret Manager in production." >> .env
fi

# --- Secret Sync Section ---
# To automatically sync secrets from Google Secret Manager into .env, run:
#   bash secret-management/scripts/sync_env_from_gcp_secrets.sh
# (Edit the script to list your required secrets and set your GCP project ID.)
# This ensures your local environment matches production secrets.

echo "=== [6/6] Bootstrap complete. You can now run your API locally: ==="
echo "  uvicorn orchestra_api.main:app --reload"

# For production, ensure secrets are synced and use:
#   uvicorn orchestra_api.main:app --host 0.0.0.0 --port 8080

# End of bootstrap script.
