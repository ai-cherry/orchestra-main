#!/bin/bash

echo "🚀 Orchestra AI Simple Deployment"
echo "================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Lambda Labs servers
PROD_SERVER="150.136.94.139"
DEV_SERVER="192.9.142.8"

# Deploy function
deploy_to_server() {
    local server=$1
    local name=$2
    
    echo -e "\n📦 Deploying to $name ($server)..."
    
    # Test SSH connection
    if ssh -o ConnectTimeout=5 ubuntu@$server "echo 'Connected'" &>/dev/null; then
        echo -e "${GREEN}✅ SSH connection successful${NC}"
        
        # Deploy code
        ssh ubuntu@$server "
            cd /home/ubuntu
            
            # Remove old code
            rm -rf orchestra-main
            
            # Clone fresh code
            git clone https://github.com/ai-cherry/orchestra-main.git
            
            cd orchestra-main
            
            # Create .env file if needed
            if [ ! -f .env ]; then
                cp .env.example .env 2>/dev/null || echo 'No .env.example found'
            fi
            
            # Install dependencies
            if [ -f requirements.txt ]; then
                pip install -r requirements.txt --quiet
            fi
            
            # Stop old processes
            pkill -f 'python.*main_api.py' || true
            pkill -f 'python.*mcp_servers' || true
            
            # Start main API
            nohup python main_api.py > logs/api.log 2>&1 &
            
            echo 'Deployment complete!'
        "
        
        echo -e "${GREEN}✅ Deployed to $name${NC}"
        
        # Test the API
        sleep 3
        if curl -s http://$server:8000/health | grep -q "healthy"; then
            echo -e "${GREEN}✅ API is healthy at http://$server:8000${NC}"
        else
            echo -e "${RED}⚠️  API health check failed${NC}"
        fi
        
    else
        echo -e "${RED}❌ Cannot connect to $name ($server)${NC}"
    fi
}

# Main deployment
echo "Select deployment target:"
echo "1) Production only ($PROD_SERVER)"
echo "2) Development only ($DEV_SERVER)"
echo "3) Both servers"
echo -n "Enter choice (1-3): "
read choice

case $choice in
    1)
        deploy_to_server $PROD_SERVER "Production"
        ;;
    2)
        deploy_to_server $DEV_SERVER "Development"
        ;;
    3)
        deploy_to_server $PROD_SERVER "Production"
        deploy_to_server $DEV_SERVER "Development"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo -e "\n${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "📋 Service URLs:"
echo "   Production API: http://$PROD_SERVER:8000"
echo "   Development API: http://$DEV_SERVER:8000"
echo "   Frontend: https://modern-admin-4mzd6dkjb-lynn-musils-projects.vercel.app"
echo ""
echo "🔍 Check logs with:"
echo "   ssh ubuntu@$PROD_SERVER 'tail -f orchestra-main/logs/api.log'" 