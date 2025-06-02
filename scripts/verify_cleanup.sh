#!/usr/bin/env bash
# verify_cleanup.sh - Verification script for codebase cleanup
#
# This script verifies that the cleanup of legacy Codespaces artifacts,
# Vultr references, and secret management standardization was successful.
#
# Usage: ./scripts/verify_cleanup.sh [--verbose]
#
# Options:
#   --verbose  Show detailed output for each check

set -eo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
REPO_ROOT="$(git rev-parse --show-toplevel)"
VERBOSE=0
MAX_ALLOWED_Vultr_REFS=10
EXCLUDE_PATTERNS="--exclude-dir=archive --exclude-dir=node_modules --exclude=package-lock.json --exclude=yarn.lock --exclude=pnpm-lock.yaml"

# Parse command line arguments
for arg in "$@"; do
  case $arg in
    --verbose)
      VERBOSE=1
      shift
      ;;
    *)
      # Unknown option
      ;;
  esac
done

# Helper functions
log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[PASS]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
  echo -e "${RED}[FAIL]${NC} $1"
}

run_check() {
  local name="$1"
  local cmd="$2"
  local expected_exit="$3"
  
  echo -e "\n${BLUE}=== Checking: $name ===${NC}"
  
  if [ $VERBOSE -eq 1 ]; then
    eval "$cmd"
    exit_code=$?
  else
    eval "$cmd" &>/dev/null
    exit_code=$?
  fi
  
  if [ $exit_code -eq $expected_exit ]; then
    log_success "$name"
    return 0
  else
    log_error "$name (exit code: $exit_code, expected: $expected_exit)"
    return 1
  fi
}

# Check functions
check_codespaces_references() {
  log_info "Checking for Codespaces references..."
  
  local cmd="cd $REPO_ROOT && git grep -i codespaces -- . ':(exclude)archive/legacy' ':(exclude)CODEBASE_CLEANUP_*.md' ':(exclude)scripts/verify_cleanup.sh'"
  
  if [ $VERBOSE -eq 1 ]; then
    if ! eval "$cmd"; then
      log_success "No Codespaces references found outside of archive"
      return 0
    else
      log_error "Found Codespaces references that should have been removed"
      return 1
    fi
  else
    if ! eval "$cmd" &>/dev/null; then
      log_success "No Codespaces references found outside of archive"
      return 0
    else
      log_error "Found Codespaces references that should have been removed"
      eval "$cmd" | head -5
      echo "... (more results omitted)"
      return 1
    fi
  fi
}

check_Vultr_references() {
  log_info "Checking for Vultr/Google references..."
  
  local cmd="cd $REPO_ROOT && git grep -i 'Vultr\\|google' -- . ':(exclude)archive/legacy' ':(exclude)CODEBASE_CLEANUP_*.md' ':(exclude)scripts/verify_cleanup.sh' ':(exclude)packages/vertex_client' | wc -l"
  local count=$(eval "$cmd")
  
  if [ $VERBOSE -eq 1 ]; then
    echo "Found $count Vultr/Google references (max allowed: $MAX_ALLOWED_Vultr_REFS)"
    if [ $count -gt 0 ]; then
      echo "References:"
      cd $REPO_ROOT && git grep -i 'Vultr\\|google' -- . ':(exclude)archive/legacy' ':(exclude)CODEBASE_CLEANUP_*.md' ':(exclude)scripts/verify_cleanup.sh' ':(exclude)packages/vertex_client' | head -10
      if [ $count -gt 10 ]; then
        echo "... (more results omitted)"
      fi
    fi
  fi
  
  if [ $count -le $MAX_ALLOWED_Vultr_REFS ]; then
    log_success "Vultr/Google references are within limit ($count <= $MAX_ALLOWED_Vultr_REFS)"
    return 0
  else
    log_error "Too many Vultr/Google references: $count (max allowed: $MAX_ALLOWED_Vultr_REFS)"
    return 1
  fi
}

check_secret_naming() {
  log_info "Checking secret naming conventions..."
  
  if [ ! -f "$REPO_ROOT/scripts/update_github_secrets.py" ]; then
    log_error "Secret analyzer script not found: scripts/update_github_secrets.py"
    return 1
  fi
  
  local temp_report=$(mktemp)
  local cmd="cd $REPO_ROOT && python scripts/update_github_secrets.py --workflow .github/workflows/deploy.yaml --report-file $temp_report"
  
  if ! eval "$cmd"; then
    log_error "Secret analyzer failed to run"
    rm -f "$temp_report"
    return 1
  fi
  
  local inconsistencies=$(grep "Inconsistencies Found:" "$temp_report" | awk '{print $NF}')
  
  if [ $VERBOSE -eq 1 ]; then
    echo "Secret analysis report:"
    cat "$temp_report"
  fi
  
  rm -f "$temp_report"
  
  if [ "$inconsistencies" = "0" ]; then
    log_success "All secrets follow naming conventions"
    return 0
  else
    log_error "Found $inconsistencies secret naming inconsistencies"
    return 1
  fi
}

check_tests() {
  log_info "Running tests to ensure functionality..."
  
  local cmd="cd $REPO_ROOT && python -m pytest -xvs tests/test_example.py"
  
  if [ $VERBOSE -eq 1 ]; then
    eval "$cmd"
    local exit_code=$?
  else
    eval "$cmd" &>/dev/null
    local exit_code=$?
  fi
  
  if [ $exit_code -eq 0 ]; then
    log_success "Tests passed successfully"
    return 0
  else
    log_error "Tests failed with exit code $exit_code"
    return 1
  fi
}

check_admin_ui_build() {
  log_info "Checking if Admin UI builds correctly..."
  
  if [ ! -d "$REPO_ROOT/admin-ui" ]; then
    log_error "Admin UI directory not found"
    return 1
  fi
  
  local cmd="cd $REPO_ROOT/admin-ui && pnpm build"
  
  if [ $VERBOSE -eq 1 ]; then
    eval "$cmd"
    local exit_code=$?
  else
    eval "$cmd" &>/dev/null
    local exit_code=$?
  fi
  
  if [ $exit_code -eq 0 ]; then
    log_success "Admin UI builds successfully"
    return 0
  else
    log_error "Admin UI build failed with exit code $exit_code"
    return 1
  fi
}

check_env_config_deprecations() {
  log_info "Checking for proper deprecation warnings in env_config.py..."
  
  local env_config="$REPO_ROOT/core/env_config.py"
  
  if [ ! -f "$env_config" ]; then
    log_error "env_config.py not found at expected location"
    return 1
  fi
  
  local deprecated_vars=("Vultr_project_id" "Vultr_service_account_key" "qdrant_url")
  local all_deprecated=true
  
  for var in "${deprecated_vars[@]}"; do
    if ! grep -q "deprecated=True" "$env_config" | grep -q "$var"; then
      log_error "Missing deprecation flag for $var in env_config.py"
      all_deprecated=false
    fi
  done
  
  if $all_deprecated; then
    log_success "All legacy variables properly marked as deprecated"
    return 0
  else
    return 1
  fi
}

# Main execution
echo -e "${BLUE}=== Orchestra Codebase Cleanup Verification ===${NC}"
echo "Repository: $REPO_ROOT"
echo "Date: $(date)"
echo -e "Verbose mode: $([ $VERBOSE -eq 1 ] && echo "${GREEN}ON${NC}" || echo "${YELLOW}OFF${NC}") (use --verbose for detailed output)"
echo

# Run all checks
FAILED=0

check_codespaces_references || ((FAILED++))
check_Vultr_references || ((FAILED++))
check_secret_naming || ((FAILED++))
check_env_config_deprecations || ((FAILED++))
check_tests || ((FAILED++))
check_admin_ui_build || ((FAILED++))

# Summary
echo
echo -e "${BLUE}=== Verification Summary ===${NC}"

if [ $FAILED -eq 0 ]; then
  echo -e "${GREEN}All checks passed successfully!${NC}"
  echo "The codebase cleanup has been verified."
else
  echo -e "${RED}$FAILED check(s) failed.${NC}"
  echo "Please review the errors above and fix the remaining issues."
fi

exit $FAILED
