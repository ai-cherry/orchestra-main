#!/bin/bash

# Print section header with color
print_header() {
  echo -e "\n\033[1;34m==== $1 ====\033[0m"
}

# Check if a command exists and print its version
check_version() {
  if command -v $1 &> /dev/null; then
    print_header "$2 Version"
    $3
  else
    echo -e "\033[1;31m$2 is not installed or not available in PATH\033[0m"
  fi
}

# Print environment information
print_header "Environment Information"
echo "Date: $(date)"
echo "User: $(whoami)"
echo "Current directory: $(pwd)"

# Check Python version
check_version "python" "Python" "python --version"

# Check Poetry version
check_version "poetry" "Poetry" "poetry --version"

# Check Docker version
check_version "docker" "Docker" "docker --version"

# Check Terraform version
check_version "terraform" "Terraform" "terraform --version"

# Install poetry dependencies
print_header "Installing Poetry Dependencies"
poetry install --with dev

print_header "Verification Complete"
echo "All required tools have been checked and dependencies installed."

print_header "Security Verification"
echo "To check your project for security vulnerabilities, run:"
echo -e "\033[1;32m./security_check.sh\033[0m"
echo "This will scan your dependencies for potential security issues and provide recommendations."
