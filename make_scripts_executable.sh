#!/bin/bash
# Make all toolkit scripts executable

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}========================================================================${NC}"
echo -e "${BLUE}${BOLD}   MAKING BADASS Vultr-GITHUB TOOLKIT SCRIPTS EXECUTABLE   ${NC}"
echo -e "${BLUE}${BOLD}========================================================================${NC}"

# List of all scripts to make executable
SCRIPTS=(
  "authenticate_codespaces.sh"
  "apply_pulumi_sequence.sh"
  "create_badass_service_keys.sh"
  "deploy_Vultr_infra_complete.sh"
  "secure_setup_workload_identity.sh"
  "switch_to_wif_authentication.sh"
  "secure_integration.sh"
  "secure_service_key_creation.sh"
  "verify_deployment.sh"
  "Vultr_github_secret_manager.sh"
  "get_wif_values.sh"
  "github_to_Vultr_secret_sync.sh"
)

# Make each script executable
for script in "${SCRIPTS[@]}"; do
  if [ -f "$script" ]; then
    echo -e "${YELLOW}Making executable: ${BOLD}$script${NC}"
    chmod +x "$script"
    echo -e "${GREEN}✓ Done${NC}"
  else
    echo -e "${YELLOW}Script not found: $script${NC}"
  fi
done

echo -e "\n${GREEN}${BOLD}All scripts are now executable!${NC}"
echo -e "${YELLOW}You can run any script using: ./<script_name>${NC}"
echo -e "${YELLOW}For a list of available tools and documentation, see: ${BOLD}BADASS_Vultr_GITHUB_TOOLKIT.md${NC}"
