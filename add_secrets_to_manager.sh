#!/bin/bash
# add_secrets_to_manager.sh
# This script copies API keys from .env to Secret Manager WITHOUT removing them from .env

set -e  # Exit on any error

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Load environment variables from .env
if [ ! -f .env ]; then
  echo -e "${RED}Error: .env file not found!${NC}"
  exit 1
fi

echo -e "${YELLOW}Loading environment variables from .env...${NC}"
set -a
source .env
set +a

# Check if required vars are set
if [ -z "$GCP_PROJECT_ID" ]; then
  echo -e "${RED}Error: GCP_PROJECT_ID is not set in .env file!${NC}"
  exit 1
fi

# Check authentication to GCP
echo -e "${YELLOW}Checking GCP authentication...${NC}"
if ! gcloud auth print-access-token &>/dev/null; then
  echo -e "${RED}Not authenticated to GCP. Run 'gcloud auth login' first.${NC}"
  exit 1
fi

# Set project
echo -e "${YELLOW}Setting GCP project ID to: $GCP_PROJECT_ID${NC}"
gcloud config set project $GCP_PROJECT_ID

# Function to safely create/update a secret
create_or_update_secret() {
  local secret_name=$1
  local secret_value=$2
  local description=$3
  local env=${ENVIRONMENT:-production}

  if [ -z "$secret_value" ]; then
    echo -e "${YELLOW}Skipping empty value for ${secret_name}${NC}"
    return 0
  fi

  # Full secret ID with environment
  local full_secret_id="${secret_name}-${env}"
  
  echo -e "${YELLOW}Processing: ${full_secret_id}${NC}"

  # Check if secret exists
  if gcloud secrets describe "$full_secret_id" &>/dev/null; then
    echo "Secret ${full_secret_id} exists, adding new version..."
    echo -n "$secret_value" | gcloud secrets versions add "$full_secret_id" --data-file=- --quiet
  else
    echo "Creating new secret ${full_secret_id}..."
    echo -n "$secret_value" | gcloud secrets create "$full_secret_id" \
      --replication-policy="user-managed" \
      --locations="${GCP_LOCATION:-us-central1}" \
      --description="$description" \
      --data-file=- --quiet
  fi
  
  echo -e "${GREEN}✓ Successfully stored ${secret_name}${NC}"
}

echo -e "\n${YELLOW}=== Adding LLM API Keys to Secret Manager ===${NC}"
create_or_update_secret "anthropic-api-key" "$ANTHROPIC_API_KEY" "Anthropic API key for Claude models"
create_or_update_secret "openai-api-key" "$OPENAI_API_KEY" "OpenAI API key for GPT models"
create_or_update_secret "openrouter-api-key" "$OPENROUTER_API_KEY" "OpenRouter API key for multi-model access"
create_or_update_secret "mistral-api-key" "$MISTRAL_API_KEY" "Mistral AI API key"
create_or_update_secret "together-ai-api-key" "$TOGETHER_AI_API_KEY" "Together.ai API key"
create_or_update_secret "deepseek-api-key" "$DEEPSEEK_API_KEY" "DeepSeek AI API key"
create_or_update_secret "perplexity-api-key" "$PERPLEXITY_API_KEY" "Perplexity AI API key"
create_or_update_secret "cohere-api-key" "$COHERE_API_KEY" "Cohere API key"
create_or_update_secret "huggingface-api-token" "$HUGGINGFACE_API_TOKEN" "HuggingFace API token"
create_or_update_secret "eleven-labs-api-key" "$ELEVEN_LABS_API_KEY" "ElevenLabs API key for voice synthesis"

echo -e "\n${YELLOW}=== Adding Data Services & Tools API Keys to Secret Manager ===${NC}"
create_or_update_secret "portkey-api-key" "$PORTKEY_API_KEY" "Portkey API key for LLM routing"
create_or_update_secret "apify-api-token" "$APIFY_API_TOKEN" "Apify API token for web scraping"
create_or_update_secret "apollo-io-api-key" "$APOLLO_IO_API_KEY" "Apollo.io API key"
create_or_update_secret "brave-api-key" "$BRAVE_API_KEY" "Brave Search API key"
create_or_update_secret "exa-api-key" "$EXA_API_KEY" "Exa API key"
create_or_update_secret "eden-ai-api-key" "$EDEN_AI_API_KEY" "Eden AI API key"
create_or_update_secret "figma-pat" "$FIGMA_PERSONAL_ACCESS_TOKEN" "Figma Personal Access Token"
create_or_update_secret "langsmith-api-key" "$LANGSMITH_API_KEY" "LangSmith API key"
create_or_update_secret "notion-api-key" "$NOTION_API_KEY" "Notion API key"
create_or_update_secret "phantom-buster-api-key" "$PHANTOM_BUSTER_API_KEY" "PhantomBuster API key"
create_or_update_secret "pinecone-api-key" "$PINECONE_API_KEY" "Pinecone vector DB API key"
create_or_update_secret "sourcegraph-access-token" "$SOURCEGRAPH_ACCESS_TOKEN" "Sourcegraph access token"
create_or_update_secret "tavily-api-key" "$TAVILY_API_KEY" "Tavily API key for search"
create_or_update_secret "twingly-api-key" "$TWINGLY_API_KEY" "Twingly API key"
create_or_update_secret "zenrows-api-key" "$ZENROWS_API_KEY" "ZenRows API key for web scraping"

echo -e "\n${YELLOW}=== Adding GCP Configuration Secrets to Secret Manager ===${NC}"
create_or_update_secret "gcp-client-secret" "$GCP_CLIENT_SECRET" "GCP OAuth client secret"
create_or_update_secret "gcp-service-account-key" "$GCP_SERVICE_ACCOUNT_KEY" "GCP service account key"
create_or_update_secret "vertex-agent-key" "$VERTEX_AGENT_KEY" "Vertex AI agent key"

echo -e "\n${YELLOW}=== Adding GitHub Configuration Secrets to Secret Manager ===${NC}"
create_or_update_secret "github-pat" "$GH_PERSONAL_ACCESS_TOKEN" "GitHub Personal Access Token"

echo -e "\n${YELLOW}=== Adding Terraform Configuration Secrets to Secret Manager ===${NC}"
create_or_update_secret "terraform-api-token" "$TERRAFORM_API_TOKEN" "Terraform Cloud API token"
create_or_update_secret "terraform-organization-token" "$TERRAFORM_ORGANIZATION_TOKEN" "Terraform Cloud organization token"

echo -e "\n${YELLOW}=== Adding Database Configuration Secrets to Secret Manager ===${NC}"
create_or_update_secret "redis-password" "$REDIS_PASSWORD" "Redis password"
create_or_update_secret "postgres-password" "$CLOUD_SQL_PASSWORD_SECRET_NAME" "PostgreSQL password secret name"
create_or_update_secret "neo4j-password" "$NEO4J_PASSWORD" "Neo4j password"
create_or_update_secret "neo4j-client-secret" "$NEO4J_CLIENT_SECRET" "Neo4j client secret"

echo -e "\n${YELLOW}=== Adding Docker Configuration Secrets to Secret Manager ===${NC}"
create_or_update_secret "docker-pat" "$DOCKER_PERSONAL_ACCESS_TOKEN" "Docker Personal Access Token"

echo -e "\n${GREEN}=== Secret Migration Complete! ===${NC}"
echo -e "All API keys and sensitive values have been copied to Secret Manager."
echo -e "${YELLOW}Note: All original values remain in your .env file as requested.${NC}"
echo -e "\nTo view secrets in GCP Console, visit:"
echo -e "https://console.cloud.google.com/security/secret-manager?project=$GCP_PROJECT_ID"
