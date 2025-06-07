#!/bin/bash
# Deploy Admin Interface to Production
# Works with Lambda Labs infrastructure

set -e

echo "🚀 Deploying Admin Interface to Production"
echo "========================================="

# Configuration
ADMIN_DIR="admin-interface"
DEPLOY_HOST="${LAMBDA_HOST:-localhost}"
DEPLOY_PORT="${ADMIN_PORT:-3000}"

# Check if we're in the right directory
if [ ! -d "$ADMIN_DIR" ]; then
    echo "❌ Error: admin-interface directory not found"
    exit 1
fi

cd $ADMIN_DIR

# Option 1: Local Development Server
deploy_local() {
    echo "📦 Starting local development server..."
    
    # Check if production HTML exists
    if [ -f "production-admin-interface.html" ]; then
        echo "✅ Using production-admin-interface.html"
        
        # Simple Python HTTP server
        echo "🌐 Starting server on http://localhost:$DEPLOY_PORT"
        python3 -m http.server $DEPLOY_PORT --bind 0.0.0.0 &
        SERVER_PID=$!
        echo "✅ Server started with PID: $SERVER_PID"
        echo "   Access at: http://localhost:$DEPLOY_PORT/production-admin-interface.html"
        
        # Save PID for later shutdown
        echo $SERVER_PID > admin-server.pid
    else
        echo "❌ production-admin-interface.html not found"
        exit 1
    fi
}

# Option 2: Docker Deployment
deploy_docker() {
    echo "🐳 Building Docker container..."
    
    # Check if Dockerfile exists
    if [ ! -f "Dockerfile.prod" ]; then
        echo "❌ Dockerfile.prod not found"
        exit 1
    fi
    
    # Build container
    docker build -f Dockerfile.prod -t ai-orchestration-admin:latest .
    
    # Stop existing container if running
    docker stop ai-admin 2>/dev/null || true
    docker rm ai-admin 2>/dev/null || true
    
    # Run new container
    echo "🚢 Starting Docker container..."
    docker run -d \
        --name ai-admin \
        -p $DEPLOY_PORT:3000 \
        --restart unless-stopped \
        ai-orchestration-admin:latest
        
    echo "✅ Admin interface deployed via Docker"
    echo "   Access at: http://localhost:$DEPLOY_PORT"
}

# Option 3: Direct Nginx Deployment
deploy_nginx() {
    echo "🌐 Deploying to Nginx..."
    
    # Check if nginx is installed
    if ! command -v nginx &> /dev/null; then
        echo "⚠️  Nginx not found. Installing..."
        sudo apt-get update
        sudo apt-get install -y nginx
    fi
    
    # Copy files to nginx directory
    sudo mkdir -p /var/www/ai-orchestration-admin
    sudo cp production-admin-interface.html /var/www/ai-orchestration-admin/index.html
    sudo cp -r *.js *.css public/* /var/www/ai-orchestration-admin/ 2>/dev/null || true
    
    # Create nginx config
    sudo tee /etc/nginx/sites-available/ai-orchestration-admin > /dev/null << EOF
server {
    listen $DEPLOY_PORT;
    server_name _;
    root /var/www/ai-orchestration-admin;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Enable gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
EOF

    # Enable site
    sudo ln -sf /etc/nginx/sites-available/ai-orchestration-admin /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl reload nginx
    
    echo "✅ Admin interface deployed to Nginx"
    echo "   Access at: http://$DEPLOY_HOST:$DEPLOY_PORT"
}

# Option 4: Lambda Labs Production Deployment
deploy_lambda() {
    echo "☁️  Deploying to Lambda Labs..."
    
    # Get Lambda instance IP from environment or Pulumi
    if [ -z "$LAMBDA_INSTANCE_IP" ]; then
        echo "🔍 Getting Lambda instance IP from Pulumi..."
        LAMBDA_INSTANCE_IP=$(pulumi stack output instance_ip 2>/dev/null || echo "")
        
        if [ -z "$LAMBDA_INSTANCE_IP" ]; then
            echo "❌ Lambda instance IP not found. Deploy infrastructure first:"
            echo "   python3 lambda_labs_deployment.py"
            exit 1
        fi
    fi
    
    echo "📦 Preparing deployment package..."
    
    # Create deployment directory
    mkdir -p deploy-package
    cp production-admin-interface.html deploy-package/index.html
    cp -r *.js *.css public/* deploy-package/ 2>/dev/null || true
    
    # Create deployment script for remote
    cat > deploy-package/deploy-remote.sh << 'EOF'
#!/bin/bash
# Remote deployment script
sudo mkdir -p /var/www/ai-admin
sudo cp -r * /var/www/ai-admin/
sudo chown -R www-data:www-data /var/www/ai-admin

# Install nginx if needed
if ! command -v nginx &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y nginx
fi

# Configure nginx
sudo tee /etc/nginx/sites-available/ai-admin > /dev/null << NGINX_EOF
server {
    listen 80;
    server_name _;
    root /var/www/ai-admin;
    index index.html;
    
    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
NGINX_EOF

sudo ln -sf /etc/nginx/sites-available/ai-admin /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
EOF
    
    chmod +x deploy-package/deploy-remote.sh
    
    # Copy to Lambda instance
    echo "📤 Copying files to Lambda instance..."
    scp -r deploy-package/* ubuntu@$LAMBDA_INSTANCE_IP:/tmp/
    
    # Execute deployment
    echo "🚀 Executing remote deployment..."
    ssh ubuntu@$LAMBDA_INSTANCE_IP "cd /tmp && bash deploy-remote.sh"
    
    # Cleanup
    rm -rf deploy-package
    
    echo "✅ Admin interface deployed to Lambda Labs"
    echo "   Access at: http://$LAMBDA_INSTANCE_IP"
}

# Main menu
echo ""
echo "Select deployment method:"
echo "1. Local Development Server (Python)"
echo "2. Docker Container"
echo "3. Local Nginx"
echo "4. Lambda Labs Production"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        deploy_local
        ;;
    2)
        deploy_docker
        ;;
    3)
        deploy_nginx
        ;;
    4)
        deploy_lambda
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📊 Admin Interface Features:"
echo "   - Multi-persona support (Cherry, Sophia, Karen)"
echo "   - Infrastructure management dashboard"
echo "   - API and secrets management"
echo "   - Real-time system monitoring"
echo "   - AI agent factory controls"
echo "   - Creative tools integration"
echo ""
echo "🔗 API Backend: Ensure ai_agent_orchestrator.py is running"
echo "   python3 ../services/ai_agent_orchestrator.py"