#!/bin/bash

echo "🚀 DEPLOYING ORCHESTRA AI TO CHERRY-AI.ME"
echo "=========================================="

# Check for required environment variables
if [ -z "$PULUMI_CONFIG_PASSPHRASE" ] || \
   [ -z "$DATABASE_PASSWORD" ] || \
   [ -z "$REDIS_AUTH_TOKEN" ] || \
   [ -z "$PINECONE_API_KEY" ] || \
   [ -z "$WEAVIATE_API_KEY" ]; then
    echo "❌ Error: Required environment variables are not set."
    echo "Please set PULUMI_CONFIG_PASSPHRASE, DATABASE_PASSWORD, REDIS_AUTH_TOKEN, PINECONE_API_KEY, and WEAVIATE_API_KEY."
    exit 1
fi

export PATH=$PATH:$HOME/.pulumi/bin

# Navigate to project root
cd /tmp/orchestra-main

echo "📋 Step 1: Configuring Pulumi secrets from environment variables..."

# Configure AWS region
pulumi config set aws:region us-east-1

# Set domain configuration
pulumi config set domain:name cherry-ai.me
pulumi config set domain:subdomain app

# Configure secrets from environment variables
pulumi config set --secret database:password "$DATABASE_PASSWORD"
pulumi config set --secret redis:auth_token "$REDIS_AUTH_TOKEN"
pulumi config set --secret pinecone:api_key "$PINECONE_API_KEY"
pulumi config set --secret weaviate:api_key "$WEAVIATE_API_KEY"

# Configure Weaviate endpoints
pulumi config set weaviate:rest_endpoint "${WEAVIATE_REST_ENDPOINT:-w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud}"
pulumi config set weaviate:grpc_endpoint "${WEAVIATE_GRPC_ENDPOINT:-grpc-w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud}"

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

