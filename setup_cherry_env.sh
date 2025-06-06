#!/bin/bash
# Setup Cherry AI Environment from GitHub Secrets or .env file

echo "🔧 Setting up Cherry AI environment..."

# Check if .env exists
if [ -f .env ]; then
    echo "✅ Found .env file, loading environment variables..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found. Creating from env.example..."
    cp env.example .env
    echo "📝 Please update .env with your actual values"
fi

# Check for required environment variables
REQUIRED_VARS=(
    "POSTGRES_PASSWORD"
    "REDIS_PASSWORD"
    "PINECONE_API_KEY"
    "WEAVIATE_API_KEY"
    "JWT_SECRET"
    "ADMIN_API_KEY"
)

MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=($var)
    fi
done

if [ ${#MISSING_VARS[@]} -eq 0 ]; then
    echo "✅ All required environment variables are set"
else
    echo "❌ Missing required environment variables:"
    printf '%s\n' "${MISSING_VARS[@]}"
    echo ""
    echo "These should be set in:"
    echo "1. GitHub Secrets (for CI/CD)"
    echo "2. Local .env file (for development)"
    echo ""
    echo "GitHub Secrets detected in workflows:"
    echo "- PINECONE_API_KEY"
    echo "- WEAVIATE_URL"
    echo "- WEAVIATE_API_KEY"
    echo "- REDIS_USER_API_KEY"
    echo "- REDIS_ACCOUNT_KEY"
    exit 1
fi

# Export additional Cherry AI specific variables
export CHERRY_AI_ENV="production"
export LAMBDA_HOST="150.136.94.139"
export POSTGRES_HOST="${POSTGRES_HOST:-$LAMBDA_HOST}"
export REDIS_HOST="${REDIS_HOST:-$LAMBDA_HOST}"

echo "✅ Environment setup complete"
echo ""
echo "📊 Configuration Summary:"
echo "- Lambda Host: $LAMBDA_HOST"
echo "- PostgreSQL: $POSTGRES_HOST:5432"
echo "- Redis: $REDIS_HOST:6379"
echo "- Weaviate: $WEAVIATE_URL"
echo "- Environment: $CHERRY_AI_ENV"