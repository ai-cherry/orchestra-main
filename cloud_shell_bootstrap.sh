#!/usr/bin/env bash
set -euo pipefail

# Bootstrap script for GCP Cloud Shell hybrid IDE setup

# 1. Install asdf if not present
if ! command -v asdf &>/dev/null; then
  git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.14.0
  echo '. "$HOME/.asdf/asdf.sh"' >> ~/.bashrc
  . "$HOME/.asdf/asdf.sh"
fi

# 2. Install required asdf plugins and tools
asdf plugin add python || true
asdf plugin add poetry || true
asdf plugin add terraform || true
asdf plugin add nodejs || true
asdf install --all

# 3. Install Poetry dependencies
poetry install

# 4. Install pre-commit and activate hooks
pip install --user pre-commit
pre-commit install

# 5. Check tool versions for drift
asdf current
python --version
poetry --version
terraform version
node --version

# 6. Copy .envrc.example if .envrc does not exist
if [ ! -f .envrc ]; then
  cp .envrc.example .envrc
  echo ".envrc created from example. Edit as needed."
fi

echo "Cloud Shell hybrid IDE environment is ready. Run 'direnv allow' if using direnv."
