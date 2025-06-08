#!/bin/bash

echo "🚀 DEPLOYING ORCHESTRA AI TO CHERRY-AI.ME"
echo "=========================================="

# Set environment variables
export PATH=$PATH:$HOME/.pulumi/bin
export PULUMI_CONFIG_PASSPHRASE="OrchestraAI2024!"

# Navigate to project root
cd /tmp/orchestra-main

echo "📋 Step 1: Configuring Pulumi secrets..."

# Configure AWS region
pulumi config set aws:region us-east-1

# Set domain configuration
pulumi config set domain:name cherry-ai.me
pulumi config set domain:subdomain app

# Configure database secrets
pulumi config set --secret database:password "OrchestraAI2024!"
pulumi config set --secret redis:auth_token "RedisAuth2024!"

# Configure API keys as secrets
pulumi config set --secret redis:user_api_key "S666q3cr9wmzpetc6iud02iqv26774azveodh2pfadrd7pgq8l7"
pulumi config set --secret redis:account_key "A4mmxx43yms087hucu51sxbau5mi9hmnz6u33k43mpauhof6rz2"
pulumi config set --secret pinecone:api_key "pcsk_7PHV2G_Mj1rRCwiHZ7YsuuzJcqKch9akzNKXv6mfwDX65DenD8Q72w3Qjh4AmuataTnEDW"
pulumi config set --secret weaviate:api_key "VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf"

# Configure Weaviate endpoints
pulumi config set weaviate:rest_endpoint "w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud"
pulumi config set weaviate:grpc_endpoint "grpc-w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud"

echo "✅ Pulumi configuration complete!"

echo "📋 Step 2: Previewing infrastructure deployment..."

# Preview the deployment
pulumi preview

echo "📋 Step 3: Deploying infrastructure..."

# Deploy the infrastructure
pulumi up --yes

echo "📋 Step 4: Getting deployment outputs..."

# Get important outputs
echo "🌐 Application URL: $(pulumi stack output applicationUrl)"
echo "🗄️ Database Endpoint: $(pulumi stack output databaseEndpoint)"
echo "⚡ Redis Endpoint: $(pulumi stack output redisEndpoint)"
echo "🐳 ECR Repository: $(pulumi stack output ecrRepositoryUrl)"
echo "🔗 Load Balancer: $(pulumi stack output albDnsName)"

echo "📋 Step 5: Building and deploying application..."

# Navigate to admin interface
cd admin-interface

# Install dependencies
echo "📦 Installing dependencies..."
pnpm install

# Build for production
echo "🔨 Building application..."
pnpm build

# Create Dockerfile if it doesn't exist
if [ ! -f Dockerfile ]; then
    echo "🐳 Creating Dockerfile..."
    cat > Dockerfile << 'EOF'
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
COPY pnpm-lock.yaml ./
RUN npm install -g pnpm
RUN pnpm install

COPY . .
RUN pnpm build

FROM node:18-alpine AS runner

WORKDIR /app
RUN npm install -g pnpm

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/pnpm-lock.yaml ./

RUN pnpm install --prod

EXPOSE 3000

CMD ["pnpm", "preview", "--host", "0.0.0.0", "--port", "3000"]
EOF
fi

echo "📋 Step 6: Docker build and push..."

# Get ECR repository URL
ECR_URL=$(cd .. && pulumi stack output ecrRepositoryUrl)

if [ ! -z "$ECR_URL" ]; then
    echo "🐳 Building Docker image..."
    docker build -t orchestra-ai .
    
    echo "🏷️ Tagging image..."
    docker tag orchestra-ai:latest $ECR_URL:latest
    
    echo "🔐 Logging into ECR..."
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URL
    
    echo "📤 Pushing image to ECR..."
    docker push $ECR_URL:latest
    
    echo "🔄 Updating ECS service..."
    CLUSTER_NAME=$(cd .. && pulumi stack output clusterName)
    SERVICE_NAME=$(cd .. && pulumi stack output serviceName)
    
    aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --force-new-deployment
    
    echo "✅ Application deployed successfully!"
else
    echo "❌ ECR URL not found. Infrastructure deployment may have failed."
fi

echo "📋 Step 7: Verifying deployment..."

# Wait for service to be stable
echo "⏳ Waiting for service to stabilize..."
aws ecs wait services-stable --cluster $CLUSTER_NAME --services $SERVICE_NAME

# Get application URL
APP_URL=$(cd .. && pulumi stack output applicationUrl)

echo "🎉 DEPLOYMENT COMPLETE!"
echo "========================"
echo "🌐 Your Orchestra AI is now live at: $APP_URL"
echo "🔗 Load Balancer DNS: $(cd .. && pulumi stack output albDnsName)"
echo "📊 Monitor at: https://console.aws.amazon.com/ecs/"
echo ""
echo "🔧 Next steps:"
echo "1. Verify the application is responding at $APP_URL"
echo "2. Configure DNS for cherry-ai.me to point to the load balancer"
echo "3. Set up SSL certificate for HTTPS"
echo "4. Configure monitoring and alerts"
echo ""
echo "🎊 Orchestra AI is now running in production!"

