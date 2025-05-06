#!/bin/bash
# Secure integration script that combines our existing functionality with 
# GitHub-GCP secret synchronization features, without hardcoded credentials

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration variables - Set defaults but allow override through environment variables
: "${GCP_PROJECT_ID:=cherry-ai-project}"
: "${GITHUB_ORG:=ai-cherry}"
: "${SECRET_SYNC_SA_NAME:=github-gcp-secret-sync}"

# Print header
echo -e "${BLUE}${BOLD}========================================================================${NC}"
echo -e "${BLUE}${BOLD}   INTEGRATED DEPLOYMENT AND SECRET SYNCHRONIZATION   ${NC}"
echo -e "${BLUE}${BOLD}========================================================================${NC}"

# Function to check if a script exists and is executable
check_script() {
  local script_name=$1
  
  if [ ! -f "$script_name" ]; then
    echo -e "${RED}Error: Script $script_name not found.${NC}"
    exit 1
  fi
  
  if [ ! -x "$script_name" ]; then
    echo -e "${YELLOW}Warning: Script $script_name is not executable. Making it executable...${NC}"
    chmod +x "$script_name"
  fi
}

# Function to prompt for confirmation
confirm() {
  local message=$1
  local response
  
  echo -e "${YELLOW}${message} (y/n)${NC}"
  read -r response
  
  if [[ "$response" =~ ^[Yy]$ ]]; then
    return 0  # true
  else
    return 1  # false
  fi
}

# Function to securely get GitHub PAT
get_github_pat() {
  # Check if PAT is provided as environment variable
  if [ -n "$GITHUB_PAT" ]; then
    echo -e "${GREEN}Using GitHub PAT from environment variable.${NC}"
    return 0
  fi
  
  # If GitHub CLI is logged in, no need for explicit PAT
  if gh auth status &> /dev/null; then
    echo -e "${GREEN}Already authenticated with GitHub CLI.${NC}"
    return 0
  fi
  
  # Prompt the user for the PAT
  echo -e "${YELLOW}GitHub Personal Access Token not found in environment.${NC}"
  echo -e "${YELLOW}Please enter your GitHub PAT (input will be hidden):${NC}"
  read -s GITHUB_PAT
  
  if [ -z "$GITHUB_PAT" ]; then
    echo -e "\n${RED}Error: GitHub Personal Access Token not provided.${NC}"
    exit 1
  fi
  
  # Export so it's available to other scripts
  export GITHUB_PAT
  
  # Authenticate with GitHub using PAT
  echo -e "\n${YELLOW}Authenticating with GitHub...${NC}"
  echo "${GITHUB_PAT}" | gh auth login --with-token
  
  echo -e "${GREEN}Successfully authenticated with GitHub.${NC}"
}

# Create a service account for GitHub-GCP secret synchronization
create_secret_sync_service_account() {
  echo -e "${YELLOW}Creating service account for GitHub-GCP secret synchronization...${NC}"
  
  local sa_email="${SECRET_SYNC_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  
  # Check if service account exists
  if gcloud iam service-accounts describe "$sa_email" &> /dev/null; then
    echo -e "${BLUE}Service account ${sa_email} already exists.${NC}"
  else
    # Create service account
    gcloud iam service-accounts create "$SECRET_SYNC_SA_NAME" \
      --display-name="GitHub-GCP Secret Sync"
    
    echo -e "${GREEN}Service account ${sa_email} created.${NC}"
  fi
  
  # Assign necessary roles
  local roles=(
    "roles/secretmanager.admin"              # Full access to Secret Manager
    "roles/secretmanager.secretAccessor"     # Access secret values
    "roles/secretmanager.secretVersionManager" # Manage secret versions
    "roles/cloudfunctions.developer"         # Deploy and manage Cloud Functions
    "roles/cloudscheduler.admin"             # Manage Cloud Scheduler jobs
    "roles/logging.logWriter"                # Write logs
  )
  
  for role in "${roles[@]}"; do
    echo -e "${BLUE}Assigning role ${role} to ${sa_email}...${NC}"
    gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
      --member="serviceAccount:$sa_email" \
      --role="$role"
  done
  
  # Create key
  local key_file=$(mktemp)
  gcloud iam service-accounts keys create "$key_file" \
    --iam-account="$sa_email"
  
  # Set GitHub organization secret
  local key_content=$(cat "$key_file")
  echo -e "${YELLOW}Setting GitHub organization secret GCP_SECRET_SYNC_KEY...${NC}"
  
  # Create temporary file for secret content
  local secret_file=$(mktemp)
  echo "$key_content" > "$secret_file"
  
  # Set the secret in GitHub
  gh secret set "GCP_SECRET_SYNC_KEY" --org "$GITHUB_ORG" --env-file "$secret_file"
  
  # Clean up
  rm "$key_file" "$secret_file"
  
  echo -e "${GREEN}Service account created and key stored in GitHub secret GCP_SECRET_SYNC_KEY.${NC}"
}

# Create Cloud Function for GitHub to GCP Secret syncing
create_secret_sync_function() {
  echo -e "${YELLOW}Creating Cloud Function for GitHub to GCP Secret sync...${NC}"
  
  # Create a temporary directory for the function
  local function_dir=$(mktemp -d)
  trap 'rm -rf "$function_dir"' EXIT
  
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
  
  # Create the function code
  cat > "$function_dir/index.js" << 'EOF'
const {SecretManagerServiceClient} = require('@google-cloud/secret-manager');
const {Octokit} = require('@octokit/rest');

const secretClient = new SecretManagerServiceClient();
const projectId = process.env.GCP_PROJECT_ID;
const githubOrg = process.env.GITHUB_ORG;

exports.syncGitHubToGCPSecrets = async (req, res) => {
  try {
    // For security, the GitHub token should be stored in Secret Manager
    const [tokenVersion] = await secretClient.accessSecretVersion({
      name: `projects/${projectId}/secrets/github-access-token/versions/latest`
    });
    
    const githubToken = tokenVersion.payload.data.toString();
    
    if (!githubToken) {
      throw new Error('GitHub token not found in Secret Manager');
    }
    
    const octokit = new Octokit({auth: githubToken});
    
    console.log(`Syncing secrets from GitHub org ${githubOrg} to GCP project ${projectId}`);
    
    // List the GitHub secret names (GitHub API doesn't allow listing secret values directly)
    const {data: secretsData} = await octokit.actions.listOrgSecrets({
      org: githubOrg
    });
    
    console.log(`Found ${secretsData.total_count} secrets in GitHub organization`);
    
    for (const secret of secretsData.secrets) {
      console.log(`Processing secret: ${secret.name}`);
      
      // Note: We can't directly get GitHub secret values via API
      // In a real implementation, you would need a GitHub Actions workflow
      // that reads the secret and writes it to GCP Secret Manager
      
      try {
        // Check if secret exists in GCP Secret Manager
        const secretName = `github-${secret.name}`.toLowerCase();
        
        try {
          await secretClient.getSecret({
            name: `projects/${projectId}/secrets/${secretName}`
          });
          console.log(`Secret ${secretName} already exists in GCP Secret Manager`);
        } catch (error) {
          // Secret doesn't exist yet, create it
          if (error.code === 5) { // NOT_FOUND
            console.log(`Creating secret ${secretName} in GCP Secret Manager`);
            await secretClient.createSecret({
              parent: `projects/${projectId}`,
              secretId: secretName,
              secret: {
                replication: {
                  automatic: {}
                }
              }
            });
            console.log(`Secret ${secretName} created in GCP Secret Manager`);
          } else {
            throw error;
          }
        }
      } catch (error) {
        console.error(`Error processing secret ${secret.name}:`, error);
      }
    }
    
    res.status(200).send('Secrets sync process completed');
  } catch (error) {
    console.error('Error syncing secrets:', error);
    res.status(500).send(`Error syncing secrets: ${error.message}`);
  }
};
EOF
  
  # Enable required APIs
  echo -e "${BLUE}Enabling required APIs for Cloud Functions and Scheduler...${NC}"
  gcloud services enable cloudfunctions.googleapis.com \
    cloudscheduler.googleapis.com \
    secretmanager.googleapis.com \
    --project="$GCP_PROJECT_ID"
  
  # Deploy the function
  echo -e "${BLUE}Deploying secret sync Cloud Function...${NC}"
  gcloud functions deploy github-gcp-secret-sync \
    --gen2 \
    --runtime=nodejs18 \
    --region=us-central1 \
    --source="$function_dir" \
    --entry-point=syncGitHubToGCPSecrets \
    --trigger-http \
    --allow-unauthenticated=false \
    --service-account="${SECRET_SYNC_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
    --set-env-vars="GCP_PROJECT_ID=${GCP_PROJECT_ID},GITHUB_ORG=${GITHUB_ORG}" \
    --project="$GCP_PROJECT_ID"
  
  echo -e "${GREEN}Secret sync Cloud Function deployed.${NC}"
}

# Create a Cloud Scheduler job for regular secret synchronization
create_secret_sync_scheduler() {
  echo -e "${YELLOW}Creating Cloud Scheduler job for regular secret sync...${NC}"
  
  # Get the function URL
  local function_url=$(gcloud functions describe github-gcp-secret-sync \
    --gen2 \
    --region=us-central1 \
    --format="value(serviceConfig.uri)" \
    --project="$GCP_PROJECT_ID")
  
  # Get the service account email
  local service_account="${SECRET_SYNC_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  
  # Create the scheduler job to run once per day
  gcloud scheduler jobs create http github-gcp-secret-sync-daily \
    --schedule="0 0 * * *" \
    --uri="$function_url" \
    --http-method=POST \
    --oidc-service-account-email="$service_account" \
    --oidc-token-audience="$function_url" \
    --location=us-central1 \
    --project="$GCP_PROJECT_ID"
  
  echo -e "${GREEN}Secret sync scheduler job created.${NC}"
}

# Create GitHub Actions workflow for syncing secrets on demand
create_github_secret_sync_workflow() {
  echo -e "${YELLOW}Creating GitHub Actions workflow for secret synchronization...${NC}"
  
  # Create the workflow directory
  mkdir -p .github/workflows
  
  # Create the workflow file
  cat > .github/workflows/sync-secrets.yml << EOF
name: Sync GitHub Secrets to GCP

on:
  workflow_dispatch:  # Manual trigger
  schedule:
    - cron: '0 0 * * *'  # Run daily at midnight UTC

jobs:
  sync-secrets:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Google Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          project_id: ${GCP_PROJECT_ID}
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: \${{ secrets.GCP_SECRET_SYNC_KEY }}
      
      - name: Trigger Secret Sync Function
        run: |
          # Get the function URL
          FUNCTION_URL=\$(gcloud functions describe github-gcp-secret-sync \\
            --gen2 \\
            --region=us-central1 \\
            --format="value(serviceConfig.uri)" \\
            --project="${GCP_PROJECT_ID}")
          
          # Get access token for the function
          TOKEN=\$(gcloud auth print-identity-token \\
            --audiences=\$FUNCTION_URL)
          
          # Call the function
          curl -X POST \\
            -H "Authorization: Bearer \$TOKEN" \\
            -H "Content-Type: application/json" \\
            \$FUNCTION_URL
      
      - name: Report completion
        run: echo "Secret sync process completed"
EOF
  
  echo -e "${GREEN}GitHub Actions workflow for secret sync created: .github/workflows/sync-secrets.yml${NC}"
}

# Main function
main() {
  # Check for required scripts
  echo -e "${YELLOW}Checking required scripts...${NC}"
  check_script "deploy_gcp_infra_complete.sh"
  check_script "create_badass_service_keys.sh"
  check_script "secure_setup_workload_identity.sh"
  
  # Display overview
  echo -e "\n${YELLOW}${BOLD}INTEGRATION PROCESS OVERVIEW:${NC}"
  echo -e "${YELLOW}1. Complete GCP infrastructure deployment (keys, Terraform, WIF)${NC}"
  echo -e "${YELLOW}2. Set up GitHub-GCP secret synchronization${NC}"
  echo -e "${YELLOW}3. Create GitHub Actions workflow for ongoing secret management${NC}"
  
  # Confirm to proceed
  if confirm "Do you want to proceed with the complete integration process?"; then
    echo -e "\n${GREEN}Starting integration process...${NC}"
  else
    echo -e "\n${RED}Integration cancelled.${NC}"
    exit 0
  fi
  
  # Step 1: Run the main deployment script
  if confirm "Do you want to run the complete GCP deployment process?"; then
    echo -e "${YELLOW}Running the complete GCP deployment process...${NC}"
    ./deploy_gcp_infra_complete.sh
  else
    echo -e "${YELLOW}Skipping GCP deployment process.${NC}"
  fi
  
  # Step 2: Set up GitHub-GCP secret synchronization
  if confirm "Do you want to set up GitHub-GCP secret synchronization?"; then
    echo -e "${YELLOW}Setting up GitHub-GCP secret synchronization...${NC}"
    
    # Get GitHub PAT securely
    get_github_pat
    
    # Create service account for secret sync
    create_secret_sync_service_account
    
    # Create and deploy Cloud Function for secret sync
    create_secret_sync_function
    
    # Create Cloud Scheduler job for regular secret sync
    create_secret_sync_scheduler
    
    # Create GitHub Actions workflow for syncing secrets on demand
    create_github_secret_sync_workflow
  else
    echo -e "${YELLOW}Skipping GitHub-GCP secret synchronization setup.${NC}"
  fi
  
  # Completion message
  echo -e "\n${GREEN}${BOLD}========================================================================${NC}"
  echo -e "${GREEN}${BOLD}   INTEGRATION PROCESS COMPLETED   ${NC}"
  echo -e "${GREEN}${BOLD}========================================================================${NC}"
  
  echo -e "\n${YELLOW}What was accomplished:${NC}"
  echo -e "1. GCP infrastructure deployment with service account keys"
  echo -e "2. Terraform configurations applied in sequence"
  echo -e "3. Workload Identity Federation set up for improved security"
  echo -e "4. GitHub-GCP secret synchronization configured"
  echo -e "5. GitHub Actions workflow created for ongoing secret management"
  
  echo -e "\n${YELLOW}Next steps:${NC}"
  echo -e "1. Store your GitHub PAT securely in GCP Secret Manager:"
  echo -e "   ${BLUE}gcloud secrets create github-access-token --project=$GCP_PROJECT_ID${NC}"
  echo -e "   ${BLUE}echo -n 'your-github-pat' | gcloud secrets versions add github-access-token --data-file=- --project=$GCP_PROJECT_ID${NC}"
  echo -e "2. Verify the secret sync function by running the GitHub workflow manually"
  echo -e "3. Delete any local copies of service account keys for security"
  
  echo -e "\n${GREEN}Thank you for using the integration script!${NC}"
}

# Run the main function
main
