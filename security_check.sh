#!/bin/bash
# Simplified security check script for single-developer project

# Print section header with color
print_header() {
  echo -e "\n\033[1;34m==== $1 ====\033[0m"
}

print_header "Simplified Security Check"

# Check for basic security tools
if ! command -v pip &> /dev/null; then
  echo "pip is not installed. Please install Python and pip."
  exit 1
fi

# Basic dependency check - no policy enforcement
print_header "Basic Dependency Check"
if [ -f "pyproject.toml" ]; then
  echo "Found pyproject.toml - checking dependencies"
  # Simple grep for known vulnerable package versions
  grep -E "pyyaml<5.4|cryptography<3.3|pillow<8.1.0" pyproject.toml && echo "WARNING: Potentially vulnerable package versions found"
elif [ -f "requirements.txt" ]; then
  echo "Found requirements.txt - checking dependencies"
  grep -E "pyyaml<5.4|cryptography<3.3|pillow<8.1.0" requirements.txt && echo "WARNING: Potentially vulnerable package versions found"
else
  echo "No dependency files found to check"
fi

print_header "Security Recommendations"
echo "1. Keep dependencies updated regularly"
echo "2. Consider using 'pip list --outdated' to check for outdated packages"
echo "3. For production deployments, consider more thorough security scanning"

print_header "Security Check Complete"
