#!/bin/bash
# Setup development environment on DigitalOcean droplets
# Run this from your Paperspace environment to configure DO droplets

set -e

# Configuration
VECTOR_IP="68.183.170.81"  # superagi-dev-sfo2-01
APP_IP="159.65.79.26"      # ubuntu-s-2vcpu-8gb-160gb-intel-sfo2-01
SSH_KEY_PATH="~/.ssh/id_ed25519"  # Updated to use existing key

echo "🚀 Setting up DigitalOcean development environment..."

# Step 1: Install Python venv on App droplet
echo "📦 Installing Python venv on App droplet..."
ssh -o StrictHostKeyChecking=no -i $SSH_KEY_PATH root@$APP_IP << 'EOF'
apt-get update
apt-get install -y python3.10-venv python3-pip git postgresql-16 postgresql-contrib-16
mkdir -p /opt/orchestra
cd /opt/orchestra
python3 -m venv venv
source venv/bin/activate

# Install PostgreSQL extensions
sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS pgvector;"
sudo -u postgres psql -c "CREATE DATABASE orchestrator;"
sudo -u postgres psql -c "CREATE USER orchestrator WITH ENCRYPTED PASSWORD 'dev-password-123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE orchestrator TO orchestrator;"
EOF

# Step 2: Clone repository to App droplet
echo "📂 Cloning repository..."
ssh -i $SSH_KEY_PATH root@$APP_IP << EOF
cd /opt/orchestra
git clone https://github.com/your-org/orchestra-main.git .
source venv/bin/activate
pip install -r requirements/base.txt
EOF

# Step 3: Install Weaviate on Vector droplet
echo "🔮 Installing Weaviate on Vector droplet..."
ssh -o StrictHostKeyChecking=no -i $SSH_KEY_PATH root@$VECTOR_IP << 'EOF'
apt-get update
apt-get install -y docker.io
systemctl enable docker
systemctl start docker

# Create Weaviate docker-compose
cat > /opt/weaviate-compose.yml << 'WEAVIATE'
version: '3.4'
services:
  weaviate:
    image: cr.weaviate.io/semitechnologies/weaviate:1.30.1
    restart: always
    ports:
      - "8080:8080"
      - "50051:50051"
    environment:
      QUERY_DEFAULTS_LIMIT: 20
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      ENABLE_MODULES: 'text2vec-openai,reranker-openai,agents'
      CLUSTER_HOSTNAME: 'weaviate-node'
      QUERY_DEFAULT_ACORN_ENABLED: 'true'
    volumes:
      - /var/lib/weaviate:/var/lib/weaviate
WEAVIATE

docker-compose -f /opt/weaviate-compose.yml up -d
EOF

# Step 4: Setup SSH access for development
echo "🔑 Setting up SSH access..."
mkdir -p ~/.ssh/config.d
cat > ~/.ssh/config.d/orchestra-do << EOF
Host do-vector
    HostName $VECTOR_IP
    User root
    IdentityFile $SSH_KEY_PATH

Host do-app
    HostName $APP_IP
    User root
    IdentityFile $SSH_KEY_PATH
EOF

# Include the config in main SSH config
if ! grep -q "Include config.d/*" ~/.ssh/config 2>/dev/null; then
    echo "Include config.d/*" >> ~/.ssh/config
fi

echo "✅ Basic setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. SSH to app droplet: ssh do-app"
echo "2. Activate venv: source /opt/orchestra/venv/bin/activate"
echo "3. Set environment variables in /opt/orchestra/.env"
echo "4. Start development!"
