#!/bin/bash
# Script to ensure Orchestra always runs in standard mode
# This script sets environment variables and patches necessary files

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}=====================================================${NC}"
echo -e "${BOLD}${BLUE}  ORCHESTRA STANDARD MODE ENFORCEMENT SCRIPT${NC}"
echo -e "${BOLD}${BLUE}=====================================================${NC}"

# Function to ensure files have correct permissions
ensure_permissions() {
  echo -e "\n${YELLOW}Ensuring script permissions...${NC}"
  find . -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null || echo -e "${RED}Could not set permissions on scripts${NC}"
  echo -e "${GREEN}Script permissions set.${NC}"
}

# Function to set environment variables
set_environment_variables() {
  echo -e "\n${YELLOW}Setting environment variables...${NC}"

  # Add to .bashrc if it exists
  if [ -f ~/.bashrc ]; then
    # Remove any existing Orchestra mode variables
    grep -v "USE_RECOVERY_MODE\|STANDARD_MODE" ~/.bashrc > ~/.bashrc.tmp
    mv ~/.bashrc.tmp ~/.bashrc

    # Add environment variables
    cat << 'EOF' >> ~/.bashrc

# Orchestra mode environment variables
export USE_RECOVERY_MODE=false
export STANDARD_MODE=true
EOF

    echo -e "${GREEN}Added environment variables to ~/.bashrc${NC}"
  fi

  # Set for current session
  export USE_RECOVERY_MODE=false
  export STANDARD_MODE=true

  echo -e "${GREEN}Environment variables set for current session:${NC}"
  echo -e "  USE_RECOVERY_MODE=${USE_RECOVERY_MODE}"
  echo -e "  STANDARD_MODE=${STANDARD_MODE}"
}

# Function to create or update .env file
update_env_file() {
  echo -e "\n${YELLOW}Updating .env file...${NC}"

  if [ -f .env ]; then
    echo -e "${YELLOW}Found existing .env file. Updating...${NC}"
    # Remove any existing mode settings
    grep -v "USE_RECOVERY_MODE\|STANDARD_MODE" .env > .env.tmp
    mv .env.tmp .env
  else
    echo -e "${YELLOW}Creating new .env file...${NC}"
    touch .env
  fi

  # Add standard mode settings
  cat << 'EOF' >> .env
# Force standard mode and disable recovery mode
USE_RECOVERY_MODE=false
STANDARD_MODE=true
EOF

  echo -e "${GREEN}.env file updated successfully.${NC}"
}

# Function to ensure docker-compose.yml has standard mode settings
check_docker_compose() {
  echo -e "\n${YELLOW}Checking docker-compose.yml...${NC}"

  if [ -f docker-compose.yml ]; then
    if grep -q "USE_RECOVERY_MODE=false" docker-compose.yml && grep -q "STANDARD_MODE=true" docker-compose.yml; then
      echo -e "${GREEN}docker-compose.yml has correct mode settings.${NC}"
    else
      echo -e "${YELLOW}docker-compose.yml may need updates to enforce standard mode.${NC}"
      echo -e "${YELLOW}Please ensure all services have the following environment variables:${NC}"
      echo -e "  - USE_RECOVERY_MODE=false"
      echo -e "  - STANDARD_MODE=true"
    fi
  else
    echo -e "${YELLOW}docker-compose.yml not found. Skipping check.${NC}"
  fi
}

# Function to ensure force_standard_mode.py is up to date
update_force_standard_mode() {
  echo -e "\n${YELLOW}Updating force_standard_mode.py...${NC}"

  if [ -f force_standard_mode.py ]; then
    echo -e "${YELLOW}force_standard_mode.py exists. Ensuring it's up to date...${NC}"
  else
    echo -e "${YELLOW}Creating force_standard_mode.py...${NC}"
  fi

  # Write the force_standard_mode.py file
  cat << 'EOF' > force_standard_mode.py
"""
Force standard mode by patching the core/orchestrator/src/main.py module directly.
This script runs before the application starts and modifies the in-memory module.
"""

import sys
import importlib
import os

def patch_module():
    """
    Patch the core.orchestrator.src.main module to force standard mode
    """
    # First, ensure the Python path includes the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    # Force environment variables
    os.environ["USE_RECOVERY_MODE"] = "false"
    os.environ["STANDARD_MODE"] = "true"
    os.environ["PYTHONPATH"] = script_dir

    print("=== DEBUG: Environment Variables at Startup ===")
    for key, value in sorted(os.environ.items()):
        if key in ["ENVIRONMENT", "PYTHONPATH", "STANDARD_MODE", "USE_RECOVERY_MODE"]:
            print(f"{key}={value}")

    print("=== DEBUG: Python Path ===")
    for path in sys.path:
        print(path)
    print("=== DEBUG: End Environment Info ===")

    # Try to load the module
    try:
        # Reload the main module to ensure it picks up these changes
        if "core.orchestrator.src.main" in sys.modules:
            # Force reload the module if it's already loaded
            importlib.reload(sys.modules["core.orchestrator.src.main"])
        else:
            # Import it for the first time
            importlib.import_module("core.orchestrator.src.main")

        # Directly patch the module variables
        import core.orchestrator.src.main

        # Print debug info
        print(f"DEBUG: Environment would set RECOVERY_MODE={core.orchestrator.src.main.RECOVERY_MODE}")
        print(f"DEBUG: Environment would set STANDARD_MODE={core.orchestrator.src.main.STANDARD_MODE}")

        # Force override the mode
        core.orchestrator.src.main.RECOVERY_MODE = False
        core.orchestrator.src.main.STANDARD_MODE = True

        print(f"DEBUG: HARD OVERRIDE ACTIVE: RECOVERY_MODE=False, STANDARD_MODE=True")
        print(f"Starting with RECOVERY_MODE=False, STANDARD_MODE=True (HARD OVERRIDE)")
    except ImportError as e:
        print(f"Warning: Could not import core.orchestrator.src.main module: {e}")
        print("Will continue with environment variables only.")

    print("тЪая╕П APPLYING HARD OVERRIDE: Forcing standard mode and disabling recovery mode!")

if __name__ == "__main__":
    patch_module()
EOF

  echo -e "${GREEN}force_standard_mode.py updated successfully.${NC}"
}

# Function to ensure Dockerfile has the correct settings
check_dockerfile() {
  echo -e "\n${YELLOW}Checking Dockerfile...${NC}"

  if [ -f Dockerfile ]; then
    if grep -q "ENV USE_RECOVERY_MODE=false" Dockerfile && grep -q "ENV STANDARD_MODE=true" Dockerfile; then
      echo -e "${GREEN}Dockerfile has correct mode settings.${NC}"
    else
      echo -e "${YELLOW}Dockerfile may need updates to enforce standard mode.${NC}"
      echo -e "${YELLOW}Please ensure the Dockerfile has these environment variables:${NC}"
      echo -e "  ENV USE_RECOVERY_MODE=false"
      echo -e "  ENV STANDARD_MODE=true"
    fi
  else
    echo -e "${YELLOW}Dockerfile not found. Skipping check.${NC}"
  fi
}

# Function to create a startup hook script
create_startup_hook() {
  echo -e "\n${YELLOW}Creating startup hook script...${NC}"

  cat << 'EOF' > startup_hook.sh
#!/bin/bash
# Startup hook script to enforce standard mode at runtime

# Set environment variables
export USE_RECOVERY_MODE=false
export STANDARD_MODE=true

# Force standard mode via Python
python3 -c "
import os
os.environ['USE_RECOVERY_MODE'] = 'false'
os.environ['STANDARD_MODE'] = 'true'
print('STARTUP HOOK: Enforced standard mode through environment variables')
"

# Execute the original command
exec "$@"
EOF

  chmod +x startup_hook.sh
  echo -e "${GREEN}Created startup_hook.sh successfully.${NC}"
}

# Execute all functions
ensure_permissions
set_environment_variables
update_env_file
check_docker_compose
update_force_standard_mode
check_dockerfile
create_startup_hook

echo -e "\n${GREEN}Standard mode enforcement complete.${NC}"
echo -e "${YELLOW}To apply changes immediately:${NC}"
echo -e "  1. Source environment variables: ${BLUE}source ~/.bashrc${NC}"
echo -e "  2. Run force_standard_mode.py: ${BLUE}python force_standard_mode.py${NC}"
echo -e "  3. For Docker environments: ${BLUE}docker-compose down && docker-compose up -d${NC}"
echo -e "\n${BOLD}${BLUE}For complete enforcement in production environments:${NC}"
echo -e "  1. Ensure your container orchestration system sets these environment variables"
echo -e "  2. Add force_standard_mode.py execution to your container ENTRYPOINT"
echo -e "  3. Consider using startup_hook.sh as your container entrypoint wrapper"

echo -e "\n${BOLD}${GREEN}Standard Mode should now be permanently enforced${NC}"
