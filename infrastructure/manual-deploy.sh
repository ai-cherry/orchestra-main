#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}AI Orchestra Manual Deployment Script${NC}"
echo "======================================"

# Check if server IP is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Please provide the Vultr server IP address${NC}"
    echo "Usage: ./manual-deploy.sh <SERVER_IP>"
    echo "Example: ./manual-deploy.sh 45.32.123.456"
    exit 1
fi

SERVER_IP=$1
echo -e "${YELLOW}Deploying to server: $SERVER_IP${NC}"

# Check if Docker image exists
if [ ! -f "orchestra-api-minimal.tar.gz" ]; then
    echo -e "${RED}Error: Docker image not found!${NC}"
    echo "Please build it first with:"
    echo "docker build -f Dockerfile.minimal -t orchestra-api-minimal:latest ."
    echo "docker save orchestra-api-minimal:latest | gzip > orchestra-api-minimal.tar.gz"
    exit 1
fi

# Create SSH directory if it doesn't exist
mkdir -p ~/.ssh

# Copy Docker image to server
echo -e "${YELLOW}Copying Docker image to server...${NC}"
echo "If prompted, enter the root password for your Vultr server"
scp -o StrictHostKeyChecking=no orchestra-api-minimal.tar.gz root@$SERVER_IP:/tmp/

# Create deployment script
cat > /tmp/deploy-on-server.sh << 'SCRIPT'
#!/bin/bash
set -e

echo "Setting up AI Orchestra on server..."

# Update system
apt-get update
apt-get upgrade -y

# Install Docker if not installed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Install nginx if not installed
if ! command -v nginx &> /dev/null; then
    echo "Installing nginx..."
    apt-get install -y nginx
fi

# Install jq for JSON parsing
apt-get install -y jq

# Create directories
mkdir -p /opt/orchestra/config
mkdir -p /opt/orchestra/data

# Load Docker image
echo "Loading Docker image..."
cd /opt/orchestra
mv /tmp/orchestra-api-minimal.tar.gz .
docker load < orchestra-api-minimal.tar.gz

# Create personas configuration
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

# Configure nginx
cat > /etc/nginx/sites-available/orchestra << 'NGINX'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

# Enable nginx site
ln -sf /etc/nginx/sites-available/orchestra /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx

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

# Wait for container to start
sleep 5

# Check if container is running
if docker ps | grep orchestra-api; then
    echo "Orchestra API is running!"
    
    # Test the API
    echo "Testing API..."
    curl -s http://localhost:8000/api/health | jq .
    
    echo ""
    echo "Deployment complete!"
    echo "API is available at: http://$(curl -s ifconfig.me)"
else
    echo "Failed to start Orchestra API"
    docker logs orchestra-api
    exit 1
fi
SCRIPT

# Copy and run deployment script on server
echo -e "${YELLOW}Running deployment on server...${NC}"
scp -o StrictHostKeyChecking=no /tmp/deploy-on-server.sh root@$SERVER_IP:/tmp/
ssh -o StrictHostKeyChecking=no root@$SERVER_IP "chmod +x /tmp/deploy-on-server.sh && /tmp/deploy-on-server.sh"

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}API URL: http://$SERVER_IP${NC}"
echo -e "${GREEN}Health check: http://$SERVER_IP/api/health${NC}"
echo ""
echo -e "${YELLOW}Test authentication:${NC}"
echo "curl -X POST http://$SERVER_IP/api/auth/login \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"username\": \"scoobyjava\", \"password\": \"Huskers1983\$\"}'"