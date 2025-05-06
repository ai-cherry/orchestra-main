#!/bin/bash
# Script to set up and execute ongoing synchronization between GitHub organization secrets and GCP Secret Manager
# This script uses the provided GitHub PAT to authenticate and access GitHub secrets, and synchronizes them to GCP

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

# Temporary directory for files
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Print header
echo -e "${BLUE}=================================================================${NC}"
echo -e "${BLUE}${BOLD}   GITHUB TO GCP SECRET MANAGER SYNCHRONIZATION   ${NC}"
echo -e "${BLUE}=================================================================${NC}"

# Check requirements
check_requirements() {
  echo -e "${YELLOW}Checking requirements...${NC}"
  
  # Check for gcloud
  if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is required but not found.${NC}"
    exit 1
  fi
  
  # Check for GitHub CLI
  if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}GitHub CLI not found. Attempting to install...${NC}"
    
    if command -v apt-get &> /dev/null; then
      # Ubuntu/Debian
      echo -e "${BLUE}Installing GitHub CLI via apt...${NC}"
      curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
      echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
      sudo apt update
      sudo apt install gh -y
    elif command -v brew &> /dev/null; then
      # macOS with Homebrew
      echo -e "${BLUE}Installing GitHub CLI via Homebrew...${NC}"
      brew install gh
    else
      echo -e "${RED}Unable to install GitHub CLI automatically.${NC}"
      echo -e "Please install the GitHub CLI (gh) manually: https://cli.github.com/manual/installation"
      exit 1
    fi
  fi
  
  # Check for jq
  if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}jq not found. Attempting to install...${NC}"
    
    if command -v apt-get &> /dev/null; then
      # Ubuntu/Debian
      sudo apt-get install jq -y
    elif command -v brew &> /dev/null; then
      # macOS with Homebrew
      brew install jq
    else
      echo -e "${RED}Unable to install jq automatically.${NC}"
      echo -e "Please install jq manually: https://stedolan.github.io/jq/download/"
      exit 1
    fi
  fi
  
  echo -e "${GREEN}All requirements satisfied.${NC}"
}

# Authenticate with GitHub
authenticate_github() {
  echo -e "${YELLOW}Authenticating with GitHub using PAT...${NC}"
  
  # Save PAT to a temporary file
  local token_file="$TEMP_DIR/github_token"
  echo "$GITHUB_PAT" > "$token_file"
  
  # Authenticate with GitHub
  gh auth login --with-token < "$token_file"
  
  # Clean up
  rm "$token_file"
  
  echo -e "${GREEN}Successfully authenticated with GitHub.${NC}"
}

# Authenticate with GCP
authenticate_gcp() {
  echo -e "${YELLOW}Authenticating with GCP...${NC}"
  
  # Check if already authenticated
  if gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${GREEN}Already authenticated with GCP.${NC}"
  else
    echo -e "${RED}Not authenticated with GCP. Please run 'gcloud auth login' first.${NC}"
    exit 1
  fi
  
  # Set project
  gcloud config set project "$GCP_PROJECT_ID"
  
  echo -e "${GREEN}GCP project set to: $GCP_PROJECT_ID${NC}"
}

# Enable required GCP APIs
enable_apis() {
  echo -e "${YELLOW}Enabling required GCP APIs...${NC}"
  
  gcloud services enable secretmanager.googleapis.com --project="$GCP_PROJECT_ID"
  gcloud services enable cloudscheduler.googleapis.com --project="$GCP_PROJECT_ID"
  gcloud services enable cloudfunctions.googleapis.com --project="$GCP_PROJECT_ID"
  
  echo -e "${GREEN}Required APIs enabled.${NC}"
}

# List all GitHub organization secrets
list_github_secrets() {
  echo -e "${YELLOW}Fetching list of GitHub organization secrets...${NC}"
  
  # Get secrets list
  local secrets=$(gh api "/orgs/$GITHUB_ORG/actions/secrets" | jq -r '.secrets[].name')
  
  if [ -z "$secrets" ]; then
    echo -e "${RED}No secrets found in GitHub organization ${GITHUB_ORG}.${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}Found $(echo "$secrets" | wc -l) secrets in GitHub organization.${NC}"
  echo "$secrets"
}

# Create secret in GCP Secret Manager
create_gcp_secret() {
  local secret_name=$1
  
  # Convert to lowercase and prefix with github- to avoid name conflicts
  local gcp_secret_name="github-$(echo $secret_name | tr '[:upper:]' '[:lower:]')"
  
  echo -e "${BLUE}Creating secret in GCP Secret Manager: ${gcp_secret_name}${NC}"
  
  # Check if secret already exists
  if gcloud secrets describe "$gcp_secret_name" --project="$GCP_PROJECT_ID" &> /dev/null; then
    echo -e "${YELLOW}Secret ${gcp_secret_name} already exists in GCP Secret Manager.${NC}"
  else
    # Create new secret
    gcloud secrets create "$gcp_secret_name" \
      --project="$GCP_PROJECT_ID"
    
    # Add a placeholder version
    echo "PLACEHOLDER - This secret needs to be updated manually with the actual value from GitHub" |
      gcloud secrets versions add "$gcp_secret_name" \
        --data-file=- \
        --project="$GCP_PROJECT_ID"
    
    echo -e "${GREEN}Secret ${gcp_secret_name} created in GCP Secret Manager.${NC}"
  fi
}

# Create Cloud Function for GitHub-GCP secret sync
create_sync_function() {
  echo -e "${YELLOW}Creating Cloud Function for GitHub-GCP secret sync...${NC}"
  
  # Create function directory
  local function_dir="$TEMP_DIR/github-gcp-sync"
  mkdir -p "$function_dir"
  
  # Create package.json
  cat > "$function_dir/package.json" << 'EOF'
{
  "name": "github-gcp-secret-sync",
  "version": "1.0.0",
  "description": "Sync GitHub organization secrets to GCP Secret Manager",
  "main": "index.js",
  "dependencies": {
    "@google-cloud/secret-manager": "^4.2.0",
    "@octokit/rest": "^19.0.7"
  }
}
EOF
  
  # Create index.js
  cat > "$function_dir/index.js" << EOF
const {SecretManagerServiceClient} = require('@google-cloud/secret-manager');
const {Octokit} = require('@octokit/rest');

const secretClient = new SecretManagerServiceClient();
const projectId = '$GCP_PROJECT_ID';
const githubOrg = '$GITHUB_ORG';

exports.syncGitHubToGCPSecrets = async (req, res) => {
  try {
    // Get GitHub token from Secret Manager
    const [version] = await secretClient.accessSecretVersion({
      name: \`projects/\${projectId}/secrets/github-pat/versions/latest\`
    });
    
    const githubToken = version.payload.data.toString();
    if (!githubToken) {
      throw new Error('GitHub token not available');
    }
    
    const octokit = new Octokit({auth: githubToken});
    console.log(\`Starting sync from GitHub org \${githubOrg} to GCP project \${projectId}\`);
    
    // List GitHub secrets (names only - values are not accessible via API)
    const {data} = await octokit.actions.listOrgSecrets({
      org: githubOrg
    });
    
    console.log(\`Found \${data.total_count} secrets in GitHub organization\`);
    
    // In a real implementation, you would need a secure way to get the secret values
    // GitHub API doesn't allow direct access to secret values for security reasons
    // This is a simplified implementation that only syncs secret names
    
    for (const secret of data.secrets) {
      const secretName = \`github-\${secret.name.toLowerCase()}\`;
      
      try {
        // Check if secret exists
        await secretClient.accessSecretVersion({
          name: \`projects/\${projectId}/secrets/\${secretName}/versions/latest\`
        });
        
        console.log(\`Secret \${secretName} already exists in GCP\`);
      } catch (error) {
        // Secret doesn't exist, create it with placeholder
        console.log(\`Creating secret placeholder for \${secretName}\`);
        
        try {
          await secretClient.createSecret({
            parent: \`projects/\${projectId}\`,
            secretId: secretName,
            secret: {
              replication: {
                automatic: {}
              }
            }
          });
          
          // Add a version with placeholder value
          await secretClient.addSecretVersion({
            parent: \`projects/\${projectId}/secrets/\${secretName}\`,
            payload: {
              data: Buffer.from('Placeholder - Update this with actual secret value')
            }
          });
          
          console.log(\`Created secret placeholder for \${secretName}\`);
        } catch (createError) {
          console.error(\`Error creating secret \${secretName}:\`, createError);
        }
      }
    }
    
    res.status(200).send(\`Synchronized \${data.total_count} secrets (names only)\`);
  } catch (error) {
    console.error('Error in secret sync function:', error);
    res.status(500).send(\`Error: \${error.message}\`);
  }
};
EOF
  
  # Create service account for the function
  local sa_name="github-secret-sync-sa"
  local sa_email="${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  
  if ! gcloud iam service-accounts describe "$sa_email" --project="$GCP_PROJECT_ID" &> /dev/null; then
    gcloud iam service-accounts create "$sa_name" \
      --display-name="GitHub Secret Sync Function SA" \
      --project="$GCP_PROJECT_ID"
    
    # Assign necessary roles
    gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
      --member="serviceAccount:$sa_email" \
      --role="roles/secretmanager.admin"
  fi
  
  # Deploy the function
  gcloud functions deploy github-gcp-secret-sync \
    --gen2 \
    --runtime=nodejs18 \
    --region=us-central1 \
    --source="$function_dir" \
    --entry-point=syncGitHubToGCPSecrets \
    --trigger-http \
    --allow-unauthenticated=false \
    --service-account="$sa_email" \
    --project="$GCP_PROJECT_ID"
  
  echo -e "${GREEN}Cloud Function for GitHub-GCP secret sync created.${NC}"
  
  # Store GitHub PAT in Secret Manager for the function to use
  if ! gcloud secrets describe "github-pat" --project="$GCP_PROJECT_ID" &> /dev/null; then
    echo -e "${BLUE}Storing GitHub PAT in Secret Manager...${NC}"
    echo -n "$GITHUB_PAT" | gcloud secrets create "github-pat" \
      --data-file=- \
      --project="$GCP_PROJECT_ID"
  fi
  
  # Grant the service account access to the GitHub PAT secret
  gcloud secrets add-iam-policy-binding "github-pat" \
    --member="serviceAccount:$sa_email" \
    --role="roles/secretmanager.secretAccessor" \
    --project="$GCP_PROJECT_ID"
}

# Create Cloud Scheduler job for automated sync
create_scheduler_job() {
  echo -e "${YELLOW}Creating Cloud Scheduler job for automated sync...${NC}"
  
  # Get function URL
  local function_url=$(gcloud functions describe github-gcp-secret-sync \
    --gen2 \
    --region=us-central1 \
    --format="value(serviceConfig.uri)" \
    --project="$GCP_PROJECT_ID")
  
  # Service account for the scheduler job
  local sa_name="github-secret-sync-sa"
  local sa_email="${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  
  # Create scheduler job
  gcloud scheduler jobs create http github-gcp-secret-sync-daily \
    --schedule="0 0 * * *" \
    --uri="$function_url" \
    --http-method=POST \
    --oidc-service-account-email="$sa_email" \
    --oidc-token-audience="$function_url" \
    --location=us-central1 \
    --project="$GCP_PROJECT_ID" || \
  echo -e "${YELLOW}Scheduler job may already exist. Trying to update...${NC}" && \
  gcloud scheduler jobs update http github-gcp-secret-sync-daily \
    --schedule="0 0 * * *" \
    --uri="$function_url" \
    --http-method=POST \
    --oidc-service-account-email="$sa_email" \
    --oidc-token-audience="$function_url" \
    --location=us-central1 \
    --project="$GCP_PROJECT_ID"
  
  echo -e "${GREEN}Cloud Scheduler job created/updated.${NC}"
}

# Main function
main() {
  # Check requirements
  check_requirements
  
  # Authenticate with GitHub
  authenticate_github
  
  # Authenticate with GCP
  authenticate_gcp
  
  # Enable required APIs
  enable_apis
  
  # List GitHub secrets
  github_secrets=$(list_github_secrets)
  
  # Create each secret in GCP Secret Manager
  echo -e "${YELLOW}Creating secrets in GCP Secret Manager...${NC}"
  for secret in $github_secrets; do
    create_gcp_secret "$secret"
  done
  
  # Create Cloud Function for automated sync
  create_sync_function
  
  # Create Cloud Scheduler job for automated sync
  create_scheduler_job
  
  echo -e "\n${BLUE}=================================================================${NC}"
  echo -e "${GREEN}${BOLD}   GITHUB TO GCP SECRET SYNCHRONIZATION COMPLETE   ${NC}"
  echo -e "${BLUE}=================================================================${NC}"
  
  echo -e "\n${YELLOW}Summary:${NC}"
  echo -e "1. Synchronized $(echo "$github_secrets" | wc -l) GitHub secrets to GCP Secret Manager"
  echo -e "2. Created Cloud Function for automated sync: github-gcp-secret-sync"
  echo -e "3. Created Cloud Scheduler job for daily sync: github-gcp-secret-sync-daily"
  
  echo -e "\n${YELLOW}IMPORTANT:${NC}"
  echo -e "1. The GitHub API doesn't allow direct access to secret values for security reasons"
  echo -e "2. The secrets in GCP Secret Manager contain placeholder values"
  echo -e "3. You'll need to manually update each secret with its actual value"
  echo -e "4. The automated sync will maintain the secret structure but not update values"
  
  echo -e "\n${YELLOW}Next Steps:${NC}"
  echo -e "1. Review the secrets in GCP Secret Manager"
  echo -e "2. Update the secret values manually"
  echo -e "3. Test the automated sync by running the Cloud Scheduler job manually"
}

# Execute the main function
main
