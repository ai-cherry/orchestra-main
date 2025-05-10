#!/bin/bash
# test_wif_tools.sh - Script to demonstrate the usage of WIF tools
# This script shows how to use all the WIF tools together in a workflow

set -e  # Exit on any error

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}=================================================================${NC}"
echo -e "${BLUE}${BOLD}   TESTING WORKLOAD IDENTITY FEDERATION TOOLS   ${NC}"
echo -e "${BLUE}=================================================================${NC}"

# Function to print section header
section() {
    echo ""
    echo -e "${BOLD}${BLUE}==== $1 ====${NC}"
    echo ""
}

# Function to print success message
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print warning message
warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Function to print error message
error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to run a command and check its exit code
run_command() {
    local command="$1"
    local description="$2"
    
    echo -e "${YELLOW}Running: ${command}${NC}"
    
    if eval "$command"; then
        success "$description completed successfully"
        return 0
    else
        error "$description failed"
        return 1
    fi
}

# Check if all required tools exist
section "Checking for WIF Tools"

tools=(
    "wif_reference_scanner.py"
    "wif_dependency_validator.py"
    "wif_docs_synchronizer.py"
    "wif_error_handler.py"
    "setup_wif.sh"
    "verify_wif_setup.sh"
    "migrate_to_wif.sh"
)

all_tools_exist=true
for tool in "${tools[@]}"; do
    if [ -f "$tool" ] && [ -x "$tool" ]; then
        success "Found $tool"
    else
        if [ -f "$tool" ]; then
            warning "Found $tool but it's not executable. Making it executable..."
            chmod +x "$tool"
            success "Made $tool executable"
        else
            error "Could not find $tool"
            all_tools_exist=false
        fi
    fi
done

if [ "$all_tools_exist" = false ]; then
    error "Some tools are missing. Please make sure all tools are available."
    exit 1
fi

# Create a test directory
section "Creating Test Environment"

test_dir="wif_tools_test_$(date +%Y%m%d%H%M%S)"
mkdir -p "$test_dir"
success "Created test directory: $test_dir"

# Create some test files with references to old WIF components
echo "Creating test files..."

# Create a test script with references to old components
cat > "$test_dir/test_script.sh" << 'EOF'
#!/bin/bash
# Test script with references to old WIF components

# Source the GitHub authentication utility
source github_auth.sh.updated

# Set up GitHub secrets
./setup_github_secrets.sh.updated

# Update WIF secrets
./update_wif_secrets.sh.updated

# Verify GitHub secrets
./verify_github_secrets.sh

# Use the GitHub workflow template
cp github-workflow-wif-template.yml.updated .github/workflows/deploy.yml

# Read the documentation
cat docs/workload_identity_federation.md
EOF
chmod +x "$test_dir/test_script.sh"
success "Created test script with references to old components"

# Create a test markdown file with references to old components
cat > "$test_dir/test_doc.md" << 'EOF'
# Test Documentation

## Setup Instructions

1. Run `setup_github_secrets.sh.updated` to set up GitHub secrets
2. Run `update_wif_secrets.sh.updated` to update WIF secrets
3. Run `verify_github_secrets.sh` to verify GitHub secrets
4. Copy `github-workflow-wif-template.yml.updated` to `.github/workflows/deploy.yml`

For more information, see [Workload Identity Federation](docs/workload_identity_federation.md).

## Code Example

```bash
# Source the GitHub authentication utility
source github_auth.sh.updated

# Set up GitHub secrets
./setup_github_secrets.sh.updated
```
EOF
success "Created test markdown file with references to old components"

# Create a test workflow file with references to old components
mkdir -p "$test_dir/.github/workflows"
cat > "$test_dir/.github/workflows/test_workflow.yml" << 'EOF'
name: Test Workflow

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up environment
        run: |
          ./setup_github_secrets.sh.updated
          ./update_wif_secrets.sh.updated
          ./verify_github_secrets.sh
      
      - name: Deploy
        run: |
          cp github-workflow-wif-template.yml.updated .github/workflows/deploy.yml
EOF
success "Created test workflow file with references to old components"

# Run the reference scanner
section "Running WIF Reference Scanner"

run_command "./wif_reference_scanner.py --path $test_dir --scan-only --verbose" "Reference scanning"
run_command "./wif_reference_scanner.py --path $test_dir --update --backup --report --output $test_dir/reference_report.md --verbose" "Reference updating"

# Run the documentation synchronizer
section "Running WIF Documentation Synchronizer"

run_command "./wif_docs_synchronizer.py --path $test_dir --docs-path $test_dir --scan-only --verbose" "Documentation scanning"
run_command "./wif_docs_synchronizer.py --path $test_dir --docs-path $test_dir --update --backup --report --output $test_dir/docs_report.md --verbose" "Documentation updating"

# Run the dependency validator
section "Running WIF Dependency Validator"

run_command "./wif_dependency_validator.py --check-deps --verbose" "Dependency checking"
run_command "./wif_dependency_validator.py --validate-scripts --validate-workflow --report --output $test_dir/validation_report.md --verbose" "Script and workflow validation"

# Run the error handler
section "Running WIF Error Handler"

# Create a test script that will succeed
cat > "$test_dir/test_success.sh" << 'EOF'
#!/bin/bash
echo "This script will succeed"
exit 0
EOF
chmod +x "$test_dir/test_success.sh"

# Create a test script that will fail
cat > "$test_dir/test_failure.sh" << 'EOF'
#!/bin/bash
echo "This script will fail"
echo "Error: command not found: gh" >&2
exit 1
EOF
chmod +x "$test_dir/test_failure.sh"

run_command "./wif_error_handler.py --log-file $test_dir/error.log --verbose wrap $test_dir/test_success.sh" "Error handling with successful script"
run_command "./wif_error_handler.py --log-file $test_dir/error.log --verbose wrap $test_dir/test_failure.sh || true" "Error handling with failing script"

# Run the migration script
section "Running Migration Script"

run_command "cp migrate_to_wif.sh $test_dir/ && cd $test_dir && ../migrate_to_wif.sh || true" "Migration script"

# Show test results
section "Test Results"

echo -e "${GREEN}${BOLD}All tests completed!${NC}"
echo ""
echo "Test artifacts are available in the $test_dir directory:"
echo "- Reference scanner report: $test_dir/reference_report.md"
echo "- Documentation synchronizer report: $test_dir/docs_report.md"
echo "- Dependency validator report: $test_dir/validation_report.md"
echo "- Error handler log: $test_dir/error.log"
echo ""
echo "You can examine these files to see the results of the tests."
echo ""
echo -e "${YELLOW}Note: Some tests may have shown warnings or errors. This is expected as part of the testing process.${NC}"
echo -e "${YELLOW}The tools are designed to handle and report these issues.${NC}"
echo ""
echo -e "${GREEN}${BOLD}To clean up the test environment, run:${NC}"
echo "rm -rf $test_dir"