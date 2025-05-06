#!/bin/bash

# Print section header with color
print_header() {
  echo -e "\n\033[1;34m==== $1 ====\033[0m"
}

print_header "Python Security Verification"

# Check if safety is installed
if ! command -v safety &> /dev/null; then
  echo "Safety is not installed. Installing now..."
  pip install safety
fi

# Upgrade pip if needed
pip_version=$(pip --version | awk '{print $2}')
echo "Current pip version: $pip_version"
echo "Upgrading pip to latest version..."
python3 -m pip install --upgrade pip

# Create a default security policy file if it doesn't exist
if [ ! -f ".safety-policy.yml" ]; then
  print_header "Creating Safety Policy File"
  cat > .safety-policy.yml <<EOL
security:
  ignore-unpinned-requirements: false  # Report vulnerabilities in unpinned packages
  ignore-vulnerabilities:
    # Add any vulnerabilities you want to ignore here
    # Example: 
    # - vulnerability-id: 12345
    #   reason: "Not applicable to our usage pattern"
EOL
  echo "Created .safety-policy.yml with unpinned package checking enabled"
fi

# Run safety scan on requirements files
print_header "Running Security Scan"
if [ -f "requirements.txt" ]; then
  safety scan --policy-file .safety-policy.yml --file requirements.txt
elif [ -f "requirements-consolidated.txt" ]; then
  safety scan --policy-file .safety-policy.yml --file requirements-consolidated.txt
elif [ -f "pyproject.toml" ]; then
  safety scan --policy-file .safety-policy.yml --file pyproject.toml
else
  echo "No requirements file found. Creating an example of pinned requirements..."
  cat > example-pinned-requirements.txt <<EOL
# Example of pinned requirements based on scan results
# Replace with your actual versions as needed

# Instead of aiohttp>=3.8.5, use:
aiohttp==3.8.5

# Instead of python-multipart>=0.0.6, use:
python-multipart==0.0.6

# Instead of starlette>=0.31.0, use:
starlette==0.31.0

# Instead of fastapi>=0.103.1, use:
fastapi==0.103.1
EOL
  echo "Created example-pinned-requirements.txt"
  safety scan --policy-file .safety-policy.yml --file example-pinned-requirements.txt
fi

print_header "Security Recommendations"
echo "1. Pin all production dependencies to specific versions to prevent automatic updates to vulnerable versions."
echo "2. Use the newer 'safety scan' command instead of the deprecated 'check' command."
echo "3. Consider adding a pre-commit hook or CI/CD step to check for security vulnerabilities."
echo "4. Review the .safety-policy.yml file and customize it for your project's needs."

print_header "Security Check Complete"
