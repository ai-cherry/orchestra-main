#!/bin/bash
# github_auth.sh - Enhanced GitHub authentication utility
# This script provides a centralized utility for GitHub authentication
# with support for different token types based on operation needs

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Create credentials directory if it doesn't exist
mkdir -p ~/.orchestra/credentials

# Function to check token expiration
check_token_expiration() {
    local token=$1
    local token_type=$2
    
    # For classic tokens, we can't check expiration directly
    # For fine-grained tokens, we can check the expiration via API
    if [ "$token_type" == "fine_grained" ]; then
        # Get token information using GitHub API
        local response=$(curl -s -H "Authorization: token $token" https://api.github.com/user)
        
        # Check if the response contains an error
        if echo "$response" | grep -q "Bad credentials"; then
            echo -e "${RED}Token has expired or is invalid.${NC}"
            return 1
        fi
    fi
    
    return 0
}

# Function to determine the appropriate token type for an operation
get_token_type_for_operation() {
    local operation=$1
    
    case "$operation" in
        "repo")
            # Repository operations need classic token with repo scope
            echo "classic"
            ;;
        "secrets")
            # Secrets management needs fine-grained token with specific permissions
            echo "fine_grained"
            ;;
        "packages")
            # Package management needs classic token with packages scope
            echo "classic"
            ;;
        "actions")
            # GitHub Actions management needs fine-grained token with specific permissions
            echo "fine_grained"
            ;;
        *)
            # Default to classic token for backward compatibility
            echo "classic"
            ;;
    esac
}

# Function to get GitHub token with fallbacks
get_github_token() {
    local operation=${1:-"default"}
    local token_type=$(get_token_type_for_operation "$operation")
    local token=""
    
    echo -e "${BLUE}Operation: $operation, Token type: $token_type${NC}" >&2
    
    # Try to get token from environment variables based on token type
    if [ "$token_type" == "fine_grained" ] && [ -n "$GH_FINE_GRAINED_TOKEN" ]; then
        token="$GH_FINE_GRAINED_TOKEN"
        echo -e "${GREEN}Using fine-grained token from environment variable${NC}" >&2
    elif [ "$token_type" == "classic" ] && [ -n "$GH_CLASSIC_PAT_TOKEN" ]; then
        token="$GH_CLASSIC_PAT_TOKEN"
        echo -e "${GREEN}Using classic token from environment variable${NC}" >&2
    elif [ -n "$GITHUB_TOKEN" ]; then
        token="$GITHUB_TOKEN"
        echo -e "${YELLOW}Using generic GITHUB_TOKEN from environment variable${NC}" >&2
    fi
    
    # If token is still empty, check stored credentials
    if [ -z "$token" ]; then
        if [ "$token_type" == "fine_grained" ] && [ -f ~/.orchestra/credentials/github-fine-grained-token.txt ]; then
            token=$(cat ~/.orchestra/credentials/github-fine-grained-token.txt)
            echo -e "${GREEN}Using fine-grained token from stored credentials${NC}" >&2
        elif [ "$token_type" == "classic" ] && [ -f ~/.orchestra/credentials/github-classic-token.txt ]; then
            token=$(cat ~/.orchestra/credentials/github-classic-token.txt)
            echo -e "${GREEN}Using classic token from stored credentials${NC}" >&2
        elif [ -f ~/.orchestra/credentials/github-token.txt ]; then
            token=$(cat ~/.orchestra/credentials/github-token.txt)
            echo -e "${YELLOW}Using generic token from stored credentials${NC}" >&2
        fi
    fi
    
    # If token is still empty, try to get from GitHub CLI
    if [ -z "$token" ]; then
        token=$(gh auth token 2>/dev/null || echo "")
        if [ -n "$token" ]; then
            echo -e "${YELLOW}Using token from GitHub CLI${NC}" >&2
        fi
    fi
    
    # If token is still empty, prompt user
    if [ -z "$token" ]; then
        echo -e "${YELLOW}No GitHub token found for $token_type operations. Please enter your GitHub Personal Access Token:${NC}" >&2
        read -s token
        echo >&2
        
        # Save token for future use
        if [ "$token_type" == "fine_grained" ]; then
            echo "$token" > ~/.orchestra/credentials/github-fine-grained-token.txt
            chmod 600 ~/.orchestra/credentials/github-fine-grained-token.txt
            echo -e "${GREEN}Saved fine-grained token for future use${NC}" >&2
        elif [ "$token_type" == "classic" ]; then
            echo "$token" > ~/.orchestra/credentials/github-classic-token.txt
            chmod 600 ~/.orchestra/credentials/github-classic-token.txt
            echo -e "${GREEN}Saved classic token for future use${NC}" >&2
        else
            echo "$token" > ~/.orchestra/credentials/github-token.txt
            chmod 600 ~/.orchestra/credentials/github-token.txt
            echo -e "${GREEN}Saved generic token for future use${NC}" >&2
        fi
    fi
    
    # Check token expiration
    if ! check_token_expiration "$token" "$token_type"; then
        echo -e "${RED}Token has expired. Please enter a new token:${NC}" >&2
        read -s token
        echo >&2
        
        # Save new token
        if [ "$token_type" == "fine_grained" ]; then
            echo "$token" > ~/.orchestra/credentials/github-fine-grained-token.txt
            chmod 600 ~/.orchestra/credentials/github-fine-grained-token.txt
        elif [ "$token_type" == "classic" ]; then
            echo "$token" > ~/.orchestra/credentials/github-classic-token.txt
            chmod 600 ~/.orchestra/credentials/github-classic-token.txt
        else
            echo "$token" > ~/.orchestra/credentials/github-token.txt
            chmod 600 ~/.orchestra/credentials/github-token.txt
        fi
    fi
    
    # Validate token
    if [ -z "$token" ]; then
        echo -e "${RED}Error: GitHub token not available.${NC}" >&2
        echo "You can also run 'gh auth login' to authenticate with GitHub CLI." >&2
        exit 1
    fi
    
    # Return the token
    echo "$token"
}

# Function to authenticate with GitHub
authenticate_github() {
    local token=$1
    local operation=${2:-"default"}
    
    # If no token provided, get one
    if [ -z "$token" ]; then
        token=$(get_github_token "$operation")
    fi
    
    # Authenticate with GitHub CLI
    echo -e "${GREEN}Authenticating with GitHub...${NC}"
    echo "$token" | gh auth login --with-token
    
    # Configure git to use the token (simpler approach)
    git config --global credential.helper store
    
    echo -e "${GREEN}Successfully authenticated with GitHub${NC}"
}

# Function to check if token has necessary scopes
check_token_scopes() {
    local token=$1
    local required_scope=$2
    
    # Get token scopes using GitHub API
    local scopes=$(curl -s -I -H "Authorization: token $token" https://api.github.com/user | grep -i "x-oauth-scopes" | cut -d: -f2 | tr -d ' ')
    
    # Check if the required scope is in the list
    if echo "$scopes" | grep -q "$required_scope"; then
        return 0
    else
        return 1
    fi
}

# Function to suggest token rotation
suggest_token_rotation() {
    local token_type=$1
    local token_file=$2
    
    # Check if token file exists
    if [ -f "$token_file" ]; then
        # Get file modification time
        local mod_time=$(stat -c %Y "$token_file" 2>/dev/null || stat -f %m "$token_file" 2>/dev/null)
        local current_time=$(date +%s)
        local age_days=$(( (current_time - mod_time) / 86400 ))
        
        # If token is older than 90 days, suggest rotation
        if [ $age_days -gt 90 ]; then
            echo -e "${YELLOW}Your $token_type token is $age_days days old. Consider rotating it for security.${NC}"
            echo -e "${YELLOW}Would you like to create a new token now? (y/n)${NC}"
            read -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${YELLOW}Please enter your new GitHub Personal Access Token:${NC}"
                read -s new_token
                echo
                
                # Save new token
                echo "$new_token" > "$token_file"
                chmod 600 "$token_file"
                echo -e "${GREEN}Saved new $token_type token for future use${NC}"
                
                # Re-authenticate with new token
                authenticate_github "$new_token"
            fi
        fi
    fi
}

# Main function
main() {
    # Check if GitHub CLI is installed
    if ! command -v gh &> /dev/null; then
        echo -e "${YELLOW}GitHub CLI not found. Please install it: https://cli.github.com/${NC}"
        exit 1
    fi
    
    # Get operation from command line argument
    local operation="${1:-default}"
    
    # Get GitHub token
    GITHUB_TOKEN=$(get_github_token "$operation")
    
    # Authenticate with GitHub
    authenticate_github "$GITHUB_TOKEN" "$operation"
    
    # Check if token has necessary scopes
    case "$operation" in
        "repo")
            if ! check_token_scopes "$GITHUB_TOKEN" "repo"; then
                echo -e "${YELLOW}Warning: Your token may not have the 'repo' scope, which is required for repository operations.${NC}"
            fi
            ;;
        "secrets")
            if ! check_token_scopes "$GITHUB_TOKEN" "admin:org"; then
                echo -e "${YELLOW}Warning: Your token may not have the 'admin:org' scope, which is required for secrets management.${NC}"
            fi
            ;;
        "packages")
            if ! check_token_scopes "$GITHUB_TOKEN" "write:packages"; then
                echo -e "${YELLOW}Warning: Your token may not have the 'write:packages' scope, which is required for package management.${NC}"
            fi
            ;;
    esac
    
    # Suggest token rotation
    local token_type=$(get_token_type_for_operation "$operation")
    if [ "$token_type" == "fine_grained" ]; then
        suggest_token_rotation "fine-grained" ~/.orchestra/credentials/github-fine-grained-token.txt
    elif [ "$token_type" == "classic" ]; then
        suggest_token_rotation "classic" ~/.orchestra/credentials/github-classic-token.txt
    else
        suggest_token_rotation "generic" ~/.orchestra/credentials/github-token.txt
    fi
    
    # Export the token for other scripts to use
    export GITHUB_TOKEN
    
    echo -e "${GREEN}GitHub authentication completed successfully${NC}"
}

# If this script is being sourced, don't run main
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi