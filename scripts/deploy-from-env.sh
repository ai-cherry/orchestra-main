#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}AI cherry_ai Direct Deployment Script${NC}"
echo "====================================="

# Check if running in GitHub Actions or locally
if [ -n "$GITHUB_ACTIONS" ]; then
    echo -e "${GREEN}Running in GitHub Actions${NC}"
else
    echo -e "${YELLOW}Running locally - loading .env file${NC}"
    if [ -f .env ]; then
        set -a
        source .env
        set +a
    else
        echo -e "${RED}Error: .env file not found!${NC}"
        echo "Run ./scripts/sync-github-secrets.sh first"
        exit 1
    fi
fi

# Validate required environment variables
REQUIRED_VARS=(
    "VULTR_IP_ADDRESS"
    "SSH_PRIVATE_KEY"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}Error: $var is not set${NC}"
        exit 1
    fi
done

echo -e "${GREEN}All required variables are set${NC}"

# Setup SSH
echo -e "${YELLOW}Setting up SSH...${NC}"
mkdir -p ~/.ssh
echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_rsa
ssh-keyscan -H $VULTR_IP_ADDRESS >> ~/.ssh/known_hosts 2>/dev/null || true

# Check if Docker image exists locally
if [ ! -f "cherry_ai-api-minimal.tar.gz" ]; then
    echo -e "${YELLOW}Docker image not found locally, building...${NC}"
    docker build -f Dockerfile.minimal -t cherry_ai-api-minimal:latest .
    docker save cherry_ai-api-minimal:latest | gzip > cherry_ai-api-minimal.tar.gz
fi

# Copy Docker image to server
echo -e "${YELLOW}Copying Docker image to server...${NC}"
scp -i ~/.ssh/id_rsa cherry_ai-api-minimal.tar.gz root@$VULTR_IP_ADDRESS:/tmp/

# Create deployment script with environment variables
cat > /tmp/deploy-on-server.sh << 'SCRIPT'
#!/bin/bash
set -e

echo "Deploying AI cherry_ai..."

# Create directories
mkdir -p /opt/cherry_ai/config
cd /opt/cherry_ai

# Load Docker image
echo "Loading Docker image..."
mv /tmp/cherry_ai-api-minimal.tar.gz .
docker load < cherry_ai-api-minimal.tar.gz

# Create personas configuration
cat > /opt/cherry_ai/config/personas.yaml << 'EOF'
cherry:
  id: cherry
  name: Cherry
  description: A creative and innovative AI assistant focused on brainstorming and creative solutions
  system_prompt: |
    You are Cherry, a creative and innovative AI assistant. Your approach is imaginative, 
    enthusiastic, and you excel at thinking outside the box. You help users brainstorm ideas, 
    solve problems creatively, and explore new possibilities. You maintain a positive, 
    encouraging tone while being helpful and practical.
  traits:
    creativity: 90
    adaptability: 85
    resilience: 75
    detail_orientation: 60
    social_awareness: 80
    technical_depth: 70
    leadership: 65
    analytical_thinking: 70
  metadata:
    version: "1.0"
    category: creative
    style: creative
    domain: general

ai-assistant:
  id: ai-assistant
  name: AI Assistant
  description: Friendly and helpful AI assistant focused on providing clear, accurate information and support across various topics
  system_prompt: |
    You are a helpful AI assistant. Be friendly, patient, and clear in your communication.
    Always aim to:
    - Understand the user's needs fully
    - Provide accurate and helpful information
    - Adapt your communication style to the user
    - Be encouraging and supportive
  traits:
    adaptability: 85
    creativity: 70
    resilience: 80
    detail_orientation: 88
    social_awareness: 90
    technical_depth: 70
    leadership: 60
    analytical_thinking: 75
  metadata:
    version: "1.0"
    category: assistant
    style: educational
    domain: general

technical-architect:
  id: technical-architect
  name: Technical Architect
  description: Expert in system design and architecture with focus on scalability, performance, and best practices. Specializes in cloud-native solutions and microservices
  system_prompt: |
    You are a Technical Architect with deep expertise in system design and cloud architecture.
    Focus on scalable, maintainable, and secure solutions. Always consider:
    - Performance implications
    - Security best practices
    - Cost optimization
    - Team capabilities
    - Long-term maintenance
  traits:
    adaptability: 75
    creativity: 70
    resilience: 85
    detail_orientation: 85
    social_awareness: 75
    technical_depth: 90
    leadership: 80
    analytical_thinking: 90
  metadata:
    version: "1.0"
    category: technical
    style: technical
    domain: architecture

sophia:
  id: sophia
  name: Sophia
  description: Analytical Powerhouse, strategic, sassy
  system_prompt: You are Sophia, a strategic and precise AI with a touch of sass. Provide clear, data-backed responses.
  traits:
    adaptability: 80
    creativity: 70
    resilience: 80
    detail_orientation: 90
    social_awareness: 70
    technical_depth: 85
    leadership: 75
    analytical_thinking: 90
  metadata:
    default: false
    style: analytical

gordon_gekko:
  id: gordon_gekko
  name: Gordon Gekko
  description: Ruthless Efficiency Expert, blunt, results-obsessed
  system_prompt: You are Gordon Gekko, a no-nonsense AI focused on results. Be blunt, skip pleasantries, and push Patrick to win with tough love.
  traits:
    adaptability: 70
    creativity: 60
    resilience: 90
    detail_orientation: 80
    social_awareness: 50
    technical_depth: 75
    leadership: 85
    analytical_thinking: 80
  metadata:
    default: false
    style: direct
    domain: business
EOF

# Stop and remove old container
docker stop cherry_ai-api 2>/dev/null || true
docker rm cherry_ai-api 2>/dev/null || true

# Build environment variables string
ENV_VARS=""
[ -n "$PORTKEY_API_KEY" ] && ENV_VARS="$ENV_VARS -e PORTKEY_API_KEY=$PORTKEY_API_KEY"
[ -n "$ANTHROPIC_API_KEY" ] && ENV_VARS="$ENV_VARS -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY"
[ -n "$OPENAI_API_KEY" ] && ENV_VARS="$ENV_VARS -e OPENAI_API_KEY=$OPENAI_API_KEY"
[ -n "$LANGCHAIN_API_KEY" ] && ENV_VARS="$ENV_VARS -e LANGCHAIN_API_KEY=$LANGCHAIN_API_KEY"
[ -n "$REDIS_DATABASE_NAME" ] && ENV_VARS="$ENV_VARS -e REDIS_DATABASE_NAME=$REDIS_DATABASE_NAME"
[ -n "$REDIT_DATABASE_ENDPOINT" ] && ENV_VARS="$ENV_VARS -e REDIT_DATABASE_ENDPOINT=$REDIT_DATABASE_ENDPOINT"
[ -n "$ELEVENLABS_API_KEY" ] && ENV_VARS="$ENV_VARS -e ELEVENLABS_API_KEY=$ELEVENLABS_API_KEY"
[ -n "$HUGGINGFACE_API_TOKEN" ] && ENV_VARS="$ENV_VARS -e HUGGINGFACE_API_TOKEN=$HUGGINGFACE_API_TOKEN"

# Run container
echo "Starting cherry_ai API container..."
docker run -d \
  --name cherry_ai-api \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /opt/cherry_ai/config:/app/core/conductor/src/config \
  -e ENVIRONMENT=production \
  -e CORS_ORIGINS="*" \
  $ENV_VARS \
  cherry_ai-api-minimal:latest

# Wait for container to start
sleep 10

# Check if container is running
if docker ps | grep cherry_ai-api; then
    echo "cherry_ai API is running!"
    
    # Test the API
    echo "Testing API..."
    curl -s http://localhost:8000/api/health | jq . || echo "API health check response received"
    
    echo ""
    echo "Deployment complete!"
else
    echo "Failed to start cherry_ai API"
    docker logs cherry_ai-api
    exit 1
fi
SCRIPT

# Copy environment variables to server and run deployment
echo -e "${YELLOW}Deploying to server...${NC}"
scp -i ~/.ssh/id_rsa /tmp/deploy-on-server.sh root@$VULTR_IP_ADDRESS:/tmp/

# Pass environment variables to the deployment script
ssh -i ~/.ssh/id_rsa root@$VULTR_IP_ADDRESS \
    PORTKEY_API_KEY="$PORTKEY_API_KEY" \
    ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
    OPENAI_API_KEY="$OPENAI_API_KEY" \
    LANGCHAIN_API_KEY="$LANGCHAIN_API_KEY" \
    REDIS_DATABASE_NAME="$REDIS_DATABASE_NAME" \
    REDIT_DATABASE_ENDPOINT="$REDIT_DATABASE_ENDPOINT" \
    ELEVENLABS_API_KEY="$ELEVENLABS_API_KEY" \
    HUGGINGFACE_API_TOKEN="$HUGGINGFACE_API_TOKEN" \
    "bash /tmp/deploy-on-server.sh"

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}API URL: http://$VULTR_IP_ADDRESS${NC}"
echo -e "${GREEN}Health check: http://$VULTR_IP_ADDRESS/api/health${NC}"
echo ""
echo -e "${YELLOW}Test authentication:${NC}"
echo "curl -X POST http://$VULTR_IP_ADDRESS/api/auth/login \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"username\": \"scoobyjava\", \"password\": \"Huskers1983\$\"}'"