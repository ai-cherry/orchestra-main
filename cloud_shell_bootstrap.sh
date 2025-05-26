#!/usr/bin/env bash
set -euo pipefail

# Bootstrap script for GCP Cloud Shell hybrid IDE setup
# Uses pip + requirements.txt + pip-tools for dependency management
# Installs pre-commit, sets up .envrc, and checks tool versions

# 1. Install asdf if not present
if ! command -v asdf &>/dev/null; then
  git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.14.0
  echo '. "$HOME/.asdf/asdf.sh"' >> ~/.bashrc
  . "$HOME/.asdf/asdf.sh"
fi

# 2. Install required asdf plugins and tools
asdf plugin add python || true
asdf plugin add terraform || true
asdf plugin add nodejs || true
asdf install --all

# 3. Ensure pip-tools is installed for pip-compile
if ! python3 -m pip show pip-tools &> /dev/null; then
  echo "Installing pip-tools (pip-compile, pip-sync)..."
  python3 -m pip install --user pip-tools
fi

# 4. Compile requirements if needed
REQ_DIR="$(dirname "${BASH_SOURCE[0]}")/requirements"
REQ_BASE_IN="$REQ_DIR/base.in"
REQ_BASE_TXT="$REQ_DIR/base.txt"
REQ_DEV_IN="$REQ_DIR/dev.in"
REQ_DEV_TXT="$REQ_DIR/dev.txt"

if [ -f "$REQ_BASE_IN" ] && { [ ! -f "$REQ_BASE_TXT" ] || [ "$REQ_BASE_IN" -nt "$REQ_BASE_TXT" ]; }; then
  echo "Compiling $REQ_BASE_IN -> $REQ_BASE_TXT"
  python3 -m piptools compile "$REQ_BASE_IN" --output-file "$REQ_BASE_TXT"
fi
if [ -f "$REQ_DEV_IN" ] && { [ ! -f "$REQ_DEV_TXT" ] || [ "$REQ_DEV_IN" -nt "$REQ_DEV_TXT" ]; }; then
  echo "Compiling $REQ_DEV_IN -> $REQ_DEV_TXT"
  python3 -m piptools compile "$REQ_DEV_IN" --output-file "$REQ_DEV_TXT"
fi

# 5. Install Python dependencies with pip
if [ -f "$REQ_DEV_TXT" ]; then
  python3 -m pip install -r "$REQ_DEV_TXT"
elif [ -f "$REQ_BASE_TXT" ]; then
  python3 -m pip install -r "$REQ_BASE_TXT"
else
  echo "ERROR: No requirements file found. Please ensure $REQ_BASE_TXT or $REQ_DEV_TXT exists."
  exit 1
fi

# 6. Install pre-commit and activate hooks
python3 -m pip install --user pre-commit
pre-commit install

# 7. Check tool versions for drift
asdf current
python --version
terraform version
node --version

# 8. Copy .envrc.example if .envrc does not exist
if [ ! -f .envrc ]; then
  cp .envrc.example .envrc
  echo ".envrc created from example. Edit as needed."
fi

echo "Cloud Shell hybrid IDE environment is ready. Run 'direnv allow' if using direnv."

# End of bootstrap script.
