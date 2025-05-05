#!/bin/bash
# Script to authenticate with GitHub and GCP in a Codespaces environment
# This is useful when using the toolkit within GitHub Codespaces

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration variables
GCP_PROJECT_ID="cherry-ai-project"
GITHUB_ORG="ai-cherry"
GITHUB_PAT="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"

# Print header
echo -e "${BLUE}${BOLD}=================================================================${NC}"
echo -e "${BLUE}${BOLD}   GITHUB CODESPACES AUTHENTICATION HELPER   ${NC}"
echo -e "${BLUE}${BOLD}=================================================================${NC}"

# Check if running in Codespaces
check_codespaces() {
  if [ -n "$CODESPACES" ] && [ "$CODESPACES" = "true" ]; then
    echo -e "${GREEN}Running in GitHub Codespaces environment.${NC}"
    return 0
  else
    echo -e "${YELLOW}Not running in GitHub Codespaces environment.${NC}"
    echo -e "${YELLOW}This script is primarily designed for use with GitHub Codespaces.${NC}"
    echo -e "${YELLOW}Do you want to continue anyway? (y/n)${NC}"
    read -r continue_anyway
    if [[ "$continue_anyway" != "y" && "$continue_anyway" != "Y" ]]; then
      echo -e "${RED}Exiting.${NC}"
      exit 1
    fi
    return 1
  fi
}

# Authenticate with GitHub
authenticate_github() {
  echo -e "${YELLOW}Authenticating with GitHub...${NC}"
  
  # Create temp directory for tokens
  TEMP_DIR=$(mktemp -d)
  trap 'rm -rf "$TEMP_DIR"' EXIT
  
  # Save PAT to a temporary file
  local token_file="$TEMP_DIR/github_token"
  echo "$GITHUB_PAT" > "$token_file"
  
  # Authenticate with GitHub
  gh auth login --with-token < "$token_file"
  
  # Clean up
  rm "$token_file"
  
  # Verify authentication
  if ! gh auth status &> /dev/null; then
    echo -e "${RED}GitHub authentication failed.${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}Successfully authenticated with GitHub as $(gh api user | jq -r '.login')${NC}"
}

# Authenticate with GCP
authenticate_gcp() {
  echo -e "${YELLOW}Authenticating with GCP...${NC}"
  
  # Check if GCP service account key exists as an environment variable in Codespaces
  if [ -n "$GCP_SA_KEY" ]; then
    echo -e "${GREEN}Found GCP service account key in environment variables.${NC}"
    
    # Save key to a temporary file
    local key_file="$TEMP_DIR/gcp_key.json"
    echo "$GCP_SA_KEY" > "$key_file"
    
    # Authenticate with GCP
    gcloud auth activate-service-account --key-file="$key_file"
    
    # Clean up
    rm "$key_file"
  else
    echo -e "${YELLOW}No GCP service account key found in environment variables.${NC}"
    echo -e "${YELLOW}Would you like to authenticate with GCP using:${NC}"
    echo -e "1. Service account key from GitHub organization secrets"
    echo -e "2. Interactive login (will open browser)"
    echo -e "3. Skip GCP authentication"
    
    read -r auth_choice
    
    case $auth_choice in
      1)
        echo -e "${YELLOW}Fetching service account key from GitHub organization secrets...${NC}"
        
        # Check if already authenticated with GitHub
        if ! gh auth status &> /dev/null; then
          echo -e "${RED}You must authenticate with GitHub first.${NC}"
          authenticate_github
        fi
        
        # List available secrets
        local secrets=$(gh api "/orgs/$GITHUB_ORG/actions/secrets" | jq -r '.secrets[].name' | grep -E 'KEY|CREDENTIALS')
        
        if [ -z "$secrets" ]; then
          echo -e "${RED}No suitable GCP service account keys found in GitHub organization secrets.${NC}"
          echo -e "${YELLOW}Falling back to interactive login.${NC}"
          gcloud auth login
        else
          echo -e "${YELLOW}Available service account keys:${NC}"
          local i=1
          local secrets_array=()
          
          while read -r secret; do
            secrets_array+=("$secret")
            echo -e "$i. $secret"
            ((i++))
          done <<< "$secrets"
          
          read -p "Enter the number of the secret to use: " secret_num
          
          if [ "$secret_num" -ge 1 ] && [ "$secret_num" -le "${#secrets_array[@]}" ]; then
            local selected_secret="${secrets_array[$((secret_num-1))]}"
            echo -e "${YELLOW}Selected secret: $selected_secret${NC}"
            
            # GitHub API doesn't allow direct access to secret values
            # We need to inform the user
            echo -e "${RED}GitHub API doesn't allow direct access to secret values.${NC}"
            echo -e "${YELLOW}Please go to your GitHub organization settings and manually copy the value of:${NC}"
            echo -e "${BLUE}$selected_secret${NC}"
            
            echo -e "${YELLOW}Then paste it here (the input will be hidden):${NC}"
            read -s secret_value
            
            # Save key to a temporary file
            local key_file="$TEMP_DIR/gcp_key.json"
            echo "$secret_value" > "$key_file"
            
            # Authenticate with GCP
            gcloud auth activate-service-account --key-file="$key_file"
            
            # Clean up
            rm "$key_file"
          else
            echo -e "${RED}Invalid selection.${NC}"
            echo -e "${YELLOW}Falling back to interactive login.${NC}"
            gcloud auth login
          fi
        fi
        ;;
      
      2)
        echo -e "${YELLOW}Initiating interactive login...${NC}"
        gcloud auth login
        ;;
      
      3)
        echo -e "${YELLOW}Skipping GCP authentication.${NC}"
        ;;
      
      *)
        echo -e "${RED}Invalid choice.${NC}"
        echo -e "${YELLOW}Falling back to interactive login.${NC}"
        gcloud auth login
        ;;
    esac
  fi
  
  # Check if authenticated
  if gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${GREEN}Successfully authenticated with GCP as $(gcloud auth list --filter=status:ACTIVE --format="value(account)")${NC}"
    
    # Set project
    gcloud config set project "$GCP_PROJECT_ID"
    echo -e "${GREEN}GCP project set to: $GCP_PROJECT_ID${NC}"
  else
    echo -e "${YELLOW}Not authenticated with GCP.${NC}"
  fi
}

# Set up Codespaces environment
setup_codespaces_environment() {
  echo -e "${YELLOW}Setting up Codespaces environment...${NC}"
  
  # Check if .bashrc or .zshrc exists and add convenience aliases
  if [ -f "$HOME/.bashrc" ]; then
    echo -e "${YELLOW}Adding convenience aliases to .bashrc...${NC}"
    
    # Add aliases if they don't already exist
    if ! grep -q "# Badass GCP & GitHub Integration Toolkit aliases" "$HOME/.bashrc"; then
      cat >> "$HOME/.bashrc" << EOF

# Badass GCP & GitHub Integration Toolkit aliases
alias run-toolkit="cd $PWD && ./gcp_github_secret_manager.sh"
alias verify-deployment="cd $PWD && ./verify_deployment.sh"
alias setup-keys="cd $PWD && ./configure_badass_keys_and_sync.sh"
alias sync-secrets="cd $PWD && ./github_to_gcp_secret_sync.sh"
EOF
      echo -e "${GREEN}Aliases added to .bashrc${NC}"
    else
      echo -e "${GREEN}Aliases already exist in .bashrc${NC}"
    fi
  fi
  
  if [ -f "$HOME/.zshrc" ]; then
    echo -e "${YELLOW}Adding convenience aliases to .zshrc...${NC}"
    
    # Add aliases if they don't already exist
    if ! grep -q "# Badass GCP & GitHub Integration Toolkit aliases" "$HOME/.zshrc"; then
      cat >> "$HOME/.zshrc" << EOF

# Badass GCP & GitHub Integration Toolkit aliases
alias run-toolkit="cd $PWD && ./gcp_github_secret_manager.sh"
alias verify-deployment="cd $PWD && ./verify_deployment.sh"
alias setup-keys="cd $PWD && ./configure_badass_keys_and_sync.sh"
alias sync-secrets="cd $PWD && ./github_to_gcp_secret_sync.sh"
EOF
      echo -e "${GREEN}Aliases added to .zshrc${NC}"
    else
      echo -e "${GREEN}Aliases already exist in .zshrc${NC}"
    fi
  fi
  
  echo -e "${YELLOW}Making all scripts executable...${NC}"
  chmod +x *.sh
  
  echo -e "${GREEN}Codespaces environment setup complete.${NC}"
}

# Show next steps
show_next_steps() {
  echo -e "\n${BLUE}${BOLD}NEXT STEPS${NC}"
  echo -e "${YELLOW}You can now:${NC}"
  echo -e "1. Run the interactive toolkit to set up service accounts and sync:"
  echo -e "   ${BLUE}./gcp_github_secret_manager.sh${NC}"
  echo -e "2. Verify your deployment:"
  echo -e "   ${BLUE}./verify_deployment.sh${NC}"
  echo -e "3. Start from scratch by creating service accounts and setting up sync:"
  echo -e "   ${BLUE}./configure_badass_keys_and_sync.sh${NC}"
  echo -e "4. Just synchronize GitHub secrets to GCP Secret Manager:"
  echo -e "   ${BLUE}./github_to_gcp_secret_sync.sh${NC}"
  
  echo -e "\n${YELLOW}If you sourced your shell configuration or start a new terminal, you can use:${NC}"
  echo -e "   ${BLUE}run-toolkit${NC} - Run the interactive toolkit"
  echo -e "   ${BLUE}verify-deployment${NC} - Verify your deployment"
  echo -e "   ${BLUE}setup-keys${NC} - Set up service accounts and sync"
  echo -e "   ${BLUE}sync-secrets${NC} - Synchronize GitHub secrets to GCP"
  
  echo -e "\n${YELLOW}For more information, see:${NC}"
  echo -e "   ${BLUE}BADASS_GCP_GITHUB_TOOLKIT.md${NC} - Overview and quick start guide"
  echo -e "   ${BLUE}GITHUB_GCP_SERVICE_KEYS_README.md${NC} - Detailed documentation"
  echo -e "   ${BLUE}POST_DEPLOYMENT_VERIFICATION_CHECKLIST.md${NC} - Verification checklist"
}

# Main function
main() {
  # Check if running in Codespaces
  check_codespaces
  
  # Authenticate with GitHub
  authenticate_github
  
  # Authenticate with GCP
  authenticate_gcp
  
  # Set up Codespaces environment
  setup_codespaces_environment
  
  # Show next steps
  show_next_steps
  
  echo -e "\n${GREEN}${BOLD}Authentication and setup completed!${NC}"
}

# Execute main function
main
