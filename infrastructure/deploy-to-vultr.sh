#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}AI Orchestra Vultr Deployment Script${NC}"
echo "====================================="

# Check if required environment variables are set
if [ -z "$VULTR_API_KEY" ]; then
    echo -e "${RED}Error: VULTR_API_KEY environment variable is not set${NC}"
    echo "Please set it with: export VULTR_API_KEY=your-api-key"
    exit 1
fi

# Check if SSH keys exist
if [ ! -f ~/.ssh/id_rsa.pub ]; then
    echo -e "${YELLOW}SSH key not found. Generating new SSH key...${NC}"
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
fi

SSH_PUBLIC_KEY=$(cat ~/.ssh/id_rsa.pub)
SSH_PRIVATE_KEY=$(cat ~/.ssh/id_rsa)

# Navigate to Pulumi directory
cd infrastructure/pulumi

# Install Pulumi if not installed
if ! command -v pulumi &> /dev/null; then
    echo -e "${YELLOW}Installing Pulumi...${NC}"
    curl -fsSL https://get.pulumi.com | sh
    export PATH=$PATH:$HOME/.pulumi/bin
fi

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
cat > requirements.txt <<EOF
pulumi>=3.0.0,<4.0.0
pulumi-vultr>=1.0.0
pulumi-command>=0.4.0
EOF
pip install -r requirements.txt

# Initialize Pulumi stack
echo -e "${YELLOW}Initializing Pulumi stack...${NC}"
pulumi stack init production --non-interactive || pulumi stack select production

# Set configuration
echo -e "${YELLOW}Setting Pulumi configuration...${NC}"
pulumi config set vultr:apiKey $VULTR_API_KEY --secret
pulumi config set sshPublicKey "$SSH_PUBLIC_KEY" --secret
pulumi config set sshPrivateKey "$SSH_PRIVATE_KEY" --secret
pulumi config set region ewr  # New Jersey
pulumi config set instanceType vc2-2c-4gb  # 2 vCPU, 4GB RAM

# Deploy infrastructure
echo -e "${GREEN}Deploying infrastructure to Vultr...${NC}"
pulumi up --yes

# Get the instance IP
INSTANCE_IP=$(pulumi stack output instance_ip)
echo -e "${GREEN}Instance deployed at: $INSTANCE_IP${NC}"

# Wait for instance to be ready
echo -e "${YELLOW}Waiting for instance to be ready...${NC}"
sleep 60

# Copy Docker image to the server
echo -e "${YELLOW}Copying Docker image to server...${NC}"
cd ../..
scp -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa orchestra-api-minimal.tar.gz root@$INSTANCE_IP:/opt/orchestra/

# Deploy the application
echo -e "${YELLOW}Deploying application...${NC}"
ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa root@$INSTANCE_IP << 'ENDSSH'
cd /opt/orchestra

# Load Docker image
echo "Loading Docker image..."
docker load < orchestra-api-minimal.tar.gz

# Copy persona configurations
mkdir -p /opt/orchestra/config/personas
cat > /opt/orchestra/config/personas.yaml << 'EOF'
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

# Stop any existing container
docker stop orchestra-api 2>/dev/null || true
docker rm orchestra-api 2>/dev/null || true

# Run the container
echo "Starting Orchestra API container..."
docker run -d \
  --name orchestra-api \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /opt/orchestra/config:/app/core/orchestrator/src/config \
  -e ENVIRONMENT=production \
  -e CORS_ORIGINS="*" \
  orchestra-api-minimal:latest

# Check if container is running
sleep 5
if docker ps | grep orchestra-api; then
    echo "Orchestra API is running!"
else
    echo "Failed to start Orchestra API"
    docker logs orchestra-api
    exit 1
fi

# Test the API
echo "Testing API..."
curl -s http://localhost:8000/api/health | jq .

echo "Deployment complete!"
ENDSSH

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}API URL: http://$INSTANCE_IP${NC}"
echo -e "${GREEN}SSH: ssh root@$INSTANCE_IP${NC}"