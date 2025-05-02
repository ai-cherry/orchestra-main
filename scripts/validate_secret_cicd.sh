#!/bin/bash
# Validate secret management implementation

check_file() {
  if [ ! -f "$1" ]; then
    echo "Missing required file: $1"
    exit 1
  fi
}

check_permissions() {
  if [ ! -x "$1" ]; then
    echo "Missing execute permissions: $1"
    exit 1
  fi
}

# Validate core components
check_file ".github/workflows/deploy.yml"
check_file "scripts/secrets_setup.sh"
check_file "scripts/pre-commit-hook-template"

check_permissions "scripts/secrets_setup.sh"

# Validate workflow content
if ! grep -q "secrets_setup.sh" .github/workflows/deploy.yml; then
  echo "Secret management missing from workflow"
  exit 1
fi

echo "All secret management components validated successfully"
