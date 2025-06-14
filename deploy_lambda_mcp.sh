#!/bin/bash

# Orchestra AI Lambda Labs MCP Deployment Script
# Deploys MCP servers to GPU instances for production AI workloads

set -e

echo "🚀 Deploying Orchestra AI MCP Servers to Lambda Labs..."

# Lambda Labs Configuration
LAMBDA_API_KEY="secret_pulumi_87a092f03b5e4896a56542ed6e07d249.bHCTOCe4mkvm9jiT53DWZpnewReAoGic"
PROD_INSTANCE="150.136.94.139"  # 8x A100 - Production
DEV_INSTANCE="192.9.142.8"      # 1x A10 - Development

echo "📋 Checking Lambda Labs instances status..."
curl -u "$LAMBDA_API_KEY:" https://cloud.lambda.ai/api/v1/instances | jq '.data[] | {name: .name, ip: .ip, status: .status, instance_type: .instance_type.name}'

echo "🔧 Setting up SSH connection to production instance..."
# Test SSH connectivity
ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no ubuntu@$PROD_INSTANCE "echo 'SSH connection successful to production instance'"

echo "🐳 Installing Docker and K3s on production instance..."
ssh ubuntu@$PROD_INSTANCE << 'REMOTE_SCRIPT'
    # Update system
    sudo apt-get update -y
    sudo apt-get install -y curl wget jq git
    
    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker ubuntu
        sudo systemctl start docker
        sudo systemctl enable docker
    fi
    
    # Install K3s if not present
    if ! command -v k3s &> /dev/null; then
        curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
        sudo systemctl enable k3s
        sudo systemctl start k3s
        
        # Setup kubectl
        sudo cp /usr/local/bin/k3s /usr/local/bin/kubectl
        mkdir -p ~/.kube
        sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
        sudo chown ubuntu:ubuntu ~/.kube/config
    fi
    
    echo "✅ Docker and K3s installation complete"
    docker --version
    kubectl version --client
REMOTE_SCRIPT

echo "📦 Building and deploying MCP server containers..."

# Create deployment script for remote execution
cat > deploy_mcp_remote.sh << 'EOF'
#!/bin/bash
set -e

echo "🏗️ Building Orchestra AI MCP containers..."

# Create namespace
kubectl create namespace orchestra || true

# Deploy PostgreSQL
kubectl apply -f - << 'POSTGRES_YAML'
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-config
  namespace: orchestra
data:
  POSTGRES_DB: orchestra_ai
  POSTGRES_USER: orchestra
  POSTGRES_PASSWORD: orchestra_secure_2024
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: orchestra
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: orchestra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        envFrom:
        - configMapRef:
            name: postgres-config
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: orchestra
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
POSTGRES_YAML

# Deploy Redis
kubectl apply -f - << 'REDIS_YAML'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: orchestra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: orchestra
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
REDIS_YAML

# Deploy MCP Memory Server (GPU-accelerated)
kubectl apply -f - << 'MCP_MEMORY_YAML'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-memory
  namespace: orchestra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mcp-memory
  template:
    metadata:
      labels:
        app: mcp-memory
    spec:
      containers:
      - name: mcp-memory
        image: python:3.11-slim
        command: ["/bin/bash", "-c"]
        args:
          - |
            apt-get update && apt-get install -y git curl
            pip install fastapi uvicorn sqlalchemy asyncpg redis aiohttp structlog
            pip install torch transformers sentence-transformers faiss-cpu
            git clone https://github.com/ai-cherry/orchestra-main.git /app
            cd /app
            python main_mcp.py --port 8003
        ports:
        - containerPort: 8003
        env:
        - name: DATABASE_URL
          value: "postgresql://orchestra:orchestra_secure_2024@postgres:5432/orchestra_ai"
        - name: REDIS_URL
          value: "redis://redis:6379"
        resources:
          requests:
            memory: "4Gi"
            cpu: "2000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-memory
  namespace: orchestra
spec:
  selector:
    app: mcp-memory
  ports:
  - port: 8003
    targetPort: 8003
  type: LoadBalancer
MCP_MEMORY_YAML

# Deploy MCP Tools Server
kubectl apply -f - << 'MCP_TOOLS_YAML'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-tools
  namespace: orchestra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mcp-tools
  template:
    metadata:
      labels:
        app: mcp-tools
    spec:
      containers:
      - name: mcp-tools
        image: python:3.11-slim
        command: ["/bin/bash", "-c"]
        args:
          - |
            apt-get update && apt-get install -y git curl
            pip install fastapi uvicorn sqlalchemy asyncpg redis aiohttp structlog
            git clone https://github.com/ai-cherry/orchestra-main.git /app
            cd /app
            python -c "
import asyncio
from fastapi import FastAPI
import uvicorn

app = FastAPI(title='MCP Tools Server')

@app.get('/health')
async def health():
    return {'status': 'healthy', 'service': 'mcp-tools'}

@app.get('/tools')
async def list_tools():
    return {'tools': ['file_processor', 'code_analyzer', 'git_manager']}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8006)
            "
        ports:
        - containerPort: 8006
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-tools
  namespace: orchestra
spec:
  selector:
    app: mcp-tools
  ports:
  - port: 8006
    targetPort: 8006
  type: LoadBalancer
MCP_TOOLS_YAML

# Deploy Orchestra AI API Server
kubectl apply -f - << 'API_SERVER_YAML'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestra-api
  namespace: orchestra
spec:
  replicas: 2
  selector:
    matchLabels:
      app: orchestra-api
  template:
    metadata:
      labels:
        app: orchestra-api
    spec:
      containers:
      - name: orchestra-api
        image: python:3.11-slim
        command: ["/bin/bash", "-c"]
        args:
          - |
            apt-get update && apt-get install -y git curl
            pip install fastapi uvicorn sqlalchemy asyncpg redis aiohttp structlog python-multipart
            git clone https://github.com/ai-cherry/orchestra-main.git /app
            cd /app
            uvicorn main_api:app --host 0.0.0.0 --port 8000
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://orchestra:orchestra_secure_2024@postgres:5432/orchestra_ai"
        - name: REDIS_URL
          value: "redis://redis:6379"
        - name: MCP_MEMORY_URL
          value: "http://mcp-memory:8003"
        - name: MCP_TOOLS_URL
          value: "http://mcp-tools:8006"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
---
apiVersion: v1
kind: Service
metadata:
  name: orchestra-api
  namespace: orchestra
spec:
  selector:
    app: orchestra-api
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
API_SERVER_YAML

echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n orchestra
kubectl wait --for=condition=available --timeout=300s deployment/redis -n orchestra
kubectl wait --for=condition=available --timeout=300s deployment/mcp-memory -n orchestra
kubectl wait --for=condition=available --timeout=300s deployment/mcp-tools -n orchestra
kubectl wait --for=condition=available --timeout=300s deployment/orchestra-api -n orchestra

echo "📊 Checking deployment status..."
kubectl get pods -n orchestra
kubectl get services -n orchestra

echo "🌐 Getting external IPs..."
kubectl get services -n orchestra -o wide

echo "✅ Orchestra AI MCP deployment complete!"
EOF

# Copy and execute deployment script on remote instance
scp deploy_mcp_remote.sh ubuntu@$PROD_INSTANCE:/tmp/
ssh ubuntu@$PROD_INSTANCE "chmod +x /tmp/deploy_mcp_remote.sh && /tmp/deploy_mcp_remote.sh"

echo "🎯 Getting service endpoints..."
ssh ubuntu@$PROD_INSTANCE "kubectl get services -n orchestra -o wide"

echo "✅ Lambda Labs MCP deployment complete!"
echo "📋 Next steps:"
echo "   1. Configure GPU acceleration for MCP Memory server"
echo "   2. Set up monitoring dashboards"
echo "   3. Scale infrastructure based on load"

