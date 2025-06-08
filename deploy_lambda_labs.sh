#!/bin/bash

echo "🚀 LAMBDA LABS DEPLOYMENT FOR CHERRY-AI.ME"
echo "==========================================="

# Configuration
INSTANCE_TYPE="gpu_1x_a10"
DOMAIN="cherry-ai.me"
DB_PASSWORD="OrchestraAI2024!"
REDIS_PASSWORD="RedisAuth2024!"

echo "📋 Step 1: Lambda Labs Instance Setup"
echo "Please ensure you have:"
echo "1. Created a Lambda Labs instance ($INSTANCE_TYPE)"
echo "2. Added your SSH key to the instance"
echo "3. Noted the instance IP address"
echo ""
read -p "Enter your Lambda Labs instance IP: " INSTANCE_IP
read -p "Enter path to your SSH private key: " SSH_KEY_PATH

echo "📋 Step 2: Connecting to instance and setting up environment..."

# Create setup script for remote execution
cat > setup_remote.sh << 'EOF'
#!/bin/bash

echo "🔧 Setting up Lambda Labs instance for Orchestra AI..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Node.js and pnpm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g pnpm

# Install Nginx and Certbot
sudo apt install nginx certbot python3-certbot-nginx -y

# Install Git
sudo apt install git -y

echo "✅ Base system setup complete!"
EOF

# Copy and execute setup script on remote instance
echo "📤 Uploading setup script to instance..."
scp -i "$SSH_KEY_PATH" setup_remote.sh ubuntu@$INSTANCE_IP:~/
ssh -i "$SSH_KEY_PATH" ubuntu@$INSTANCE_IP 'chmod +x setup_remote.sh && ./setup_remote.sh'

echo "📋 Step 3: Deploying Orchestra AI application..."

# Create application deployment script
cat > deploy_app.sh << EOF
#!/bin/bash

echo "🚀 Deploying Orchestra AI application..."

# Clone repository
git clone https://github.com/ai-cherry/orchestra-main.git
cd orchestra-main

# Create production environment file
cat > admin-interface/.env.local << 'ENVEOF'
NODE_ENV=production
DATABASE_URL=postgresql://orchestraadmin:${DB_PASSWORD}@localhost:5432/orchestraai
REDIS_URL=redis://:${REDIS_PASSWORD}@localhost:6379

# API Keys
REDIS_USER_API_KEY=S666q3cr9wmzpetc6iud02iqv26774azveodh2pfadrd7pgq8l7
REDIS_ACCOUNT_KEY=A4mmxx43yms087hucu51sxbau5mi9hmnz6u33k43mpauhof6rz2
PINECONE_API_KEY=pcsk_7PHV2G_Mj1rRCwiHZ7YsuuzJcqKch9akzNKXv6mfwDX65DenD8Q72w3Qjh4AmuataTnEDW
WEAVIATE_REST_ENDPOINT=w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud
WEAVIATE_GRPC_ENDPOINT=grpc-w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud
WEAVIATE_API_KEY=VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf

# GitHub and other service keys (add your actual keys)
GITHUB_TOKEN=your_github_token_here
LINEAR_API_KEY=your_linear_key_here
ASANA_API_KEY=your_asana_key_here
NOTION_API_KEY=your_notion_key_here
ENVEOF

# Create Docker Compose file
cat > docker-compose.prod.yml << 'DOCKEREOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: orchestraai
      POSTGRES_USER: orchestraadmin
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U orchestraadmin -d orchestraai"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  orchestra-ai:
    build: 
      context: ./admin-interface
      dockerfile: Dockerfile.prod
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://orchestraadmin:${DB_PASSWORD}@postgres:5432/orchestraai
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
    env_file:
      - ./admin-interface/.env.local
    ports:
      - "3000:3000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  redis_data:
DOCKEREOF

# Create production Dockerfile
cat > admin-interface/Dockerfile.prod << 'DOCKERFILEEOF'
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY pnpm-lock.yaml ./

# Install pnpm and dependencies
RUN npm install -g pnpm
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build application
RUN pnpm build

FROM node:18-alpine AS runner

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy built application
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/pnpm-lock.yaml ./

# Install production dependencies
RUN pnpm install --prod --frozen-lockfile

# Add health check endpoint
RUN echo 'const express = require("express"); const app = express(); app.get("/health", (req, res) => res.json({status: "ok"})); app.use(express.static("dist")); app.listen(3000);' > server.js

EXPOSE 3000

CMD ["node", "server.js"]
DOCKERFILEEOF

# Create database initialization script
cat > init.sql << 'SQLEOF'
-- Orchestra AI Database Schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (for future multi-user support)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    persona VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    context JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    platform VARCHAR(50), -- 'linear', 'github', 'asana', etc.
    external_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics table
CREATE TABLE analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_persona ON conversations(persona);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_platform ON tasks(platform);
CREATE INDEX idx_analytics_user_id ON analytics(user_id);
CREATE INDEX idx_analytics_event_type ON analytics(event_type);

-- Insert default user
INSERT INTO users (email, name) VALUES ('admin@cherry-ai.me', 'Orchestra AI Admin');
SQLEOF

echo "🐳 Building and starting services..."

# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service health
docker-compose -f docker-compose.prod.yml ps

echo "✅ Orchestra AI application deployed!"
EOF

# Upload and execute application deployment
echo "📤 Deploying application to instance..."
scp -i "$SSH_KEY_PATH" deploy_app.sh ubuntu@$INSTANCE_IP:~/
ssh -i "$SSH_KEY_PATH" ubuntu@$INSTANCE_IP "chmod +x deploy_app.sh && ./deploy_app.sh"

echo "📋 Step 4: Configuring Nginx and SSL..."

# Create Nginx configuration script
cat > setup_nginx.sh << EOF
#!/bin/bash

echo "🌐 Setting up Nginx and SSL for $DOMAIN..."

# Create Nginx site configuration
sudo tee /etc/nginx/sites-available/$DOMAIN << 'NGINXEOF'
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://localhost:3000/health;
        access_log off;
    }
    
    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        proxy_pass http://localhost:3000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINXEOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

echo "✅ Nginx configured successfully!"
EOF

# Upload and execute Nginx setup
scp -i "$SSH_KEY_PATH" setup_nginx.sh ubuntu@$INSTANCE_IP:~/
ssh -i "$SSH_KEY_PATH" ubuntu@$INSTANCE_IP "chmod +x setup_nginx.sh && ./setup_nginx.sh"

echo "📋 Step 5: Setting up SSL certificate..."

# SSL setup script
cat > setup_ssl.sh << EOF
#!/bin/bash

echo "🔒 Setting up SSL certificate for $DOMAIN..."

# Get SSL certificate
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# Set up auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

echo "✅ SSL certificate configured!"
EOF

# Upload and execute SSL setup
scp -i "$SSH_KEY_PATH" setup_ssl.sh ubuntu@$INSTANCE_IP:~/
ssh -i "$SSH_KEY_PATH" ubuntu@$INSTANCE_IP "chmod +x setup_ssl.sh && ./setup_ssl.sh"

echo "📋 Step 6: Final verification..."

# Test the deployment
echo "🧪 Testing deployment..."
sleep 10

if curl -f -s "http://$INSTANCE_IP:3000/health" > /dev/null; then
    echo "✅ Application is responding on port 3000"
else
    echo "❌ Application not responding on port 3000"
fi

if curl -f -s "http://$INSTANCE_IP" > /dev/null; then
    echo "✅ Nginx is serving the application"
else
    echo "❌ Nginx not serving the application"
fi

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"
echo ""
echo "🌐 Your Orchestra AI is now running at:"
echo "   HTTP:  http://$INSTANCE_IP"
echo "   HTTPS: https://$DOMAIN (after DNS propagation)"
echo ""
echo "📊 Instance Details:"
echo "   IP Address: $INSTANCE_IP"
echo "   Instance Type: $INSTANCE_TYPE"
echo "   SSH Access: ssh -i $SSH_KEY_PATH ubuntu@$INSTANCE_IP"
echo ""
echo "🔧 Next Steps:"
echo "1. Update DNS records for $DOMAIN to point to $INSTANCE_IP"
echo "2. Wait for DNS propagation (5-30 minutes)"
echo "3. Test HTTPS access at https://$DOMAIN"
echo "4. Monitor logs: ssh -i $SSH_KEY_PATH ubuntu@$INSTANCE_IP 'docker-compose -f orchestra-main/docker-compose.prod.yml logs -f'"
echo ""
echo "💰 Cost: ~\$0.60/hour (\$432/month for 24/7 operation)"
echo "🎊 Orchestra AI is now live on Lambda Labs!"

# Cleanup temporary files
rm -f setup_remote.sh deploy_app.sh setup_nginx.sh setup_ssl.sh

echo ""
echo "🔍 To check status:"
echo "   ssh -i $SSH_KEY_PATH ubuntu@$INSTANCE_IP 'docker-compose -f orchestra-main/docker-compose.prod.yml ps'"
echo ""
echo "🔄 To restart services:"
echo "   ssh -i $SSH_KEY_PATH ubuntu@$INSTANCE_IP 'cd orchestra-main && docker-compose -f docker-compose.prod.yml restart'"

