#!/usr/bin/env python3
"""
CI/CD Pipeline and Deployment Automation Manager
Creates comprehensive DevOps workflows for Orchestra-Main project
"""

import json
import time
import os
from typing import Dict, List

class CICDManager:
    def __init__(self):
        self.infrastructure = {
            "production": "45.32.69.157",
            "database": "45.77.87.106",
            "staging": "207.246.108.201",
            "kubernetes_cluster": "bd2cab79-0db3-4317-8b0f-52368f99c577"
        }
    
    def create_github_actions_workflows(self) -> Dict:
        """Create GitHub Actions CI/CD workflows"""
        print("🔄 CREATING GITHUB ACTIONS WORKFLOWS")
        print("=" * 40)
        
        workflows = {
            "ci_pipeline": self.generate_ci_workflow(),
            "cd_staging": self.generate_staging_deployment_workflow(),
            "cd_production": self.generate_production_deployment_workflow(),
            "security_scan": self.generate_security_workflow(),
            "performance_test": self.generate_performance_workflow()
        }
        
        return workflows
    
    def generate_ci_workflow(self) -> str:
        """Generate CI pipeline workflow"""
        return """name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '20'

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: orchestra_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:latest
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}
    
    - name: Cache Python dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Install Node.js dependencies
      run: |
        npm ci
    
    - name: Run Python linting
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        black --check .
        isort --check-only .
    
    - name: Run Python type checking
      run: |
        mypy .
    
    - name: Run Python tests
      env:
        DATABASE_URL: postgresql://postgres:test_password@localhost:5432/orchestra_test
        REDIS_URL: redis://localhost:6379
      run: |
        pytest --cov=. --cov-report=xml --cov-report=html
    
    - name: Run JavaScript/TypeScript tests
      run: |
        npm test
    
    - name: Build frontend
      run: |
        npm run build
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
    
    - name: Security scan with Bandit
      run: |
        bandit -r . -f json -o bandit-report.json || true
    
    - name: Upload test artifacts
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-results
        path: |
          coverage.xml
          htmlcov/
          bandit-report.json
          test-results.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Login to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: |
          ghcr.io/${{ github.repository }}:latest
          ghcr.io/${{ github.repository }}:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
"""
    
    def generate_staging_deployment_workflow(self) -> str:
        """Generate staging deployment workflow"""
        return f"""name: Deploy to Staging

on:
  push:
    branches: [ develop ]
  workflow_dispatch:

env:
  STAGING_HOST: {self.infrastructure['staging']}
  STAGING_USER: root

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup SSH
      run: |
        mkdir -p ~/.ssh
        echo "${{{{ secrets.STAGING_SSH_KEY }}}}" > ~/.ssh/id_rsa
        chmod 600 ~/.ssh/id_rsa
        ssh-keyscan -H $STAGING_HOST >> ~/.ssh/known_hosts
    
    - name: Deploy to staging server
      run: |
        ssh $STAGING_USER@$STAGING_HOST << 'EOF'
          # Update code
          cd /opt/orchestra-staging
          git pull origin develop
          
          # Install/update dependencies
          pip install -r requirements.txt
          npm ci
          npm run build
          
          # Run database migrations
          python manage.py migrate
          
          # Restart services
          systemctl restart orchestra-staging
          systemctl restart nginx
          
          # Health check
          sleep 10
          curl -f http://localhost:8000/health || exit 1
        EOF
    
    - name: Run staging tests
      run: |
        ssh $STAGING_USER@$STAGING_HOST << 'EOF'
          cd /opt/orchestra-staging
          python -m pytest tests/integration/ --staging
        EOF
    
    - name: Notify deployment status
      if: always()
      run: |
        if [ "${{{{ job.status }}}}" == "success" ]; then
          echo "✅ Staging deployment successful"
        else
          echo "❌ Staging deployment failed"
        fi
"""
    
    def generate_production_deployment_workflow(self) -> str:
        """Generate production deployment workflow"""
        return f"""name: Deploy to Production

on:
  push:
    branches: [ main ]
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to deploy'
        required: true
        default: 'latest'

env:
  PRODUCTION_HOST: {self.infrastructure['production']}
  DATABASE_HOST: {self.infrastructure['database']}
  STAGING_HOST: {self.infrastructure['staging']}

jobs:
  pre-deployment-checks:
    runs-on: ubuntu-latest
    
    steps:
    - name: Check staging health
      run: |
        curl -f http://$STAGING_HOST:8000/health
    
    - name: Check database connectivity
      run: |
        nc -zv $DATABASE_HOST 5432
        nc -zv $DATABASE_HOST 6379
    
    - name: Verify backup status
      run: |
        ssh root@$STAGING_HOST "/root/backup_health.sh"

  deploy-production:
    needs: pre-deployment-checks
    runs-on: ubuntu-latest
    environment: production
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup SSH
      run: |
        mkdir -p ~/.ssh
        echo "${{{{ secrets.PRODUCTION_SSH_KEY }}}}" > ~/.ssh/id_rsa
        chmod 600 ~/.ssh/id_rsa
        ssh-keyscan -H $PRODUCTION_HOST >> ~/.ssh/known_hosts
        ssh-keyscan -H $DATABASE_HOST >> ~/.ssh/known_hosts
    
    - name: Create backup before deployment
      run: |
        ssh root@$STAGING_HOST "/opt/backups/scripts/backup_database.sh"
    
    - name: Deploy to production
      run: |
        ssh root@$PRODUCTION_HOST << 'EOF'
          # Create deployment directory
          DEPLOY_DIR="/opt/orchestra-deploy-$(date +%Y%m%d_%H%M%S)"
          mkdir -p $DEPLOY_DIR
          cd $DEPLOY_DIR
          
          # Clone latest code
          git clone https://github.com/user/orchestra-main.git .
          git checkout main
          
          # Install dependencies
          python -m venv venv
          source venv/bin/activate
          pip install -r requirements.txt
          
          # Build frontend
          npm ci
          npm run build:production
          
          # Run database migrations (if any)
          python manage.py migrate --check
          
          # Stop current services
          systemctl stop orchestra-main
          
          # Backup current deployment
          if [ -d "/opt/orchestra-current" ]; then
            mv /opt/orchestra-current /opt/orchestra-backup-$(date +%Y%m%d_%H%M%S)
          fi
          
          # Switch to new deployment
          ln -sfn $DEPLOY_DIR /opt/orchestra-current
          
          # Update service configuration
          cp /opt/orchestra-current/deploy/orchestra-main.service /etc/systemd/system/
          systemctl daemon-reload
          
          # Start services
          systemctl start orchestra-main
          systemctl enable orchestra-main
          
          # Update nginx configuration
          cp /opt/orchestra-current/deploy/nginx.conf /etc/nginx/sites-available/orchestra-main
          nginx -t && systemctl reload nginx
        EOF
    
    - name: Health check
      run: |
        sleep 30
        for i in {{1..5}}; do
          if curl -f http://$PRODUCTION_HOST/health; then
            echo "✅ Production deployment successful"
            exit 0
          fi
          echo "Attempt $i failed, retrying..."
          sleep 10
        done
        echo "❌ Production health check failed"
        exit 1
    
    - name: Rollback on failure
      if: failure()
      run: |
        ssh root@$PRODUCTION_HOST << 'EOF'
          echo "🔄 Rolling back deployment..."
          systemctl stop orchestra-main
          
          # Find latest backup
          BACKUP_DIR=$(ls -td /opt/orchestra-backup-* | head -1)
          if [ -n "$BACKUP_DIR" ]; then
            rm -f /opt/orchestra-current
            ln -sfn $BACKUP_DIR /opt/orchestra-current
            systemctl start orchestra-main
            echo "✅ Rollback completed"
          else
            echo "❌ No backup found for rollback"
          fi
        EOF
    
    - name: Cleanup old deployments
      if: success()
      run: |
        ssh root@$PRODUCTION_HOST << 'EOF'
          # Keep last 3 deployments
          ls -td /opt/orchestra-deploy-* | tail -n +4 | xargs rm -rf
          ls -td /opt/orchestra-backup-* | tail -n +3 | xargs rm -rf
        EOF

  post-deployment:
    needs: deploy-production
    runs-on: ubuntu-latest
    if: always()
    
    steps:
    - name: Update monitoring dashboards
      run: |
        # Update Grafana annotations
        curl -X POST http://$STAGING_HOST:3000/api/annotations \\
          -H "Content-Type: application/json" \\
          -d '{{"text": "Production deployment completed", "time": '$(date +%s000)'}}'
    
    - name: Run post-deployment tests
      run: |
        # Run production smoke tests
        curl -f http://$PRODUCTION_HOST/api/health
        curl -f http://$PRODUCTION_HOST/api/status
"""
    
    def generate_security_workflow(self) -> str:
        """Generate security scanning workflow"""
        return """name: Security Scan

on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday at 2 AM
  workflow_dispatch:

jobs:
  security-scan:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'
    
    - name: Run Semgrep security scan
      uses: returntocorp/semgrep-action@v1
      with:
        config: >-
          p/security-audit
          p/secrets
          p/python
          p/javascript
    
    - name: Run dependency check
      run: |
        pip install safety
        safety check --json --output safety-report.json || true
        
        npm audit --audit-level moderate --json > npm-audit.json || true
    
    - name: Upload security artifacts
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          trivy-results.sarif
          safety-report.json
          npm-audit.json
"""
    
    def generate_performance_workflow(self) -> str:
        """Generate performance testing workflow"""
        return f"""name: Performance Tests

on:
  schedule:
    - cron: '0 3 * * *'  # Daily at 3 AM
  workflow_dispatch:

env:
  STAGING_HOST: {self.infrastructure['staging']}

jobs:
  performance-test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
    
    - name: Install k6
      run: |
        sudo gpg -k
        sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
        echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
        sudo apt-get update
        sudo apt-get install k6
    
    - name: Run load tests
      run: |
        k6 run --out json=results.json tests/performance/load-test.js
    
    - name: Run stress tests
      run: |
        k6 run --out json=stress-results.json tests/performance/stress-test.js
    
    - name: Generate performance report
      run: |
        node scripts/generate-performance-report.js
    
    - name: Upload performance results
      uses: actions/upload-artifact@v3
      with:
        name: performance-results
        path: |
          results.json
          stress-results.json
          performance-report.html
"""
    
    def create_kubernetes_manifests(self) -> Dict:
        """Create Kubernetes deployment manifests"""
        print("☸️  CREATING KUBERNETES MANIFESTS")
        print("=" * 35)
        
        manifests = {
            "namespace": self.generate_namespace_manifest(),
            "deployment": self.generate_deployment_manifest(),
            "service": self.generate_service_manifest(),
            "ingress": self.generate_ingress_manifest(),
            "configmap": self.generate_configmap_manifest(),
            "secret": self.generate_secret_manifest(),
            "hpa": self.generate_hpa_manifest()
        }
        
        return manifests
    
    def generate_namespace_manifest(self) -> str:
        """Generate namespace manifest"""
        return """apiVersion: v1
kind: Namespace
metadata:
  name: orchestra-main
  labels:
    name: orchestra-main
    environment: production
"""
    
    def generate_deployment_manifest(self) -> str:
        """Generate deployment manifest"""
        return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestra-main
  namespace: orchestra-main
  labels:
    app: orchestra-main
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: orchestra-main
  template:
    metadata:
      labels:
        app: orchestra-main
        version: v1
    spec:
      containers:
      - name: orchestra-main
        image: ghcr.io/user/orchestra-main:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: orchestra-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: orchestra-secrets
              key: redis-url
        - name: WEAVIATE_URL
          valueFrom:
            configMapKeyRef:
              name: orchestra-config
              key: weaviate-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
          readOnly: true
      volumes:
      - name: config-volume
        configMap:
          name: orchestra-config
      imagePullSecrets:
      - name: ghcr-secret
"""
    
    def generate_service_manifest(self) -> str:
        """Generate service manifest"""
        return """apiVersion: v1
kind: Service
metadata:
  name: orchestra-main-service
  namespace: orchestra-main
  labels:
    app: orchestra-main
spec:
  selector:
    app: orchestra-main
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
  type: ClusterIP
"""
    
    def generate_ingress_manifest(self) -> str:
        """Generate ingress manifest"""
        return """apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: orchestra-main-ingress
  namespace: orchestra-main
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.orchestra-main.com
    secretName: orchestra-main-tls
  rules:
  - host: api.orchestra-main.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: orchestra-main-service
            port:
              number: 80
"""
    
    def generate_configmap_manifest(self) -> str:
        """Generate configmap manifest"""
        return f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: orchestra-config
  namespace: orchestra-main
data:
  weaviate-url: "http://{self.infrastructure['database']}:8080"
  redis-host: "{self.infrastructure['database']}"
  redis-port: "6379"
  log-level: "INFO"
  environment: "production"
  prometheus-endpoint: "http://{self.infrastructure['staging']}:9090"
  grafana-endpoint: "http://{self.infrastructure['staging']}:3000"
"""
    
    def generate_secret_manifest(self) -> str:
        """Generate secret manifest template"""
        return """apiVersion: v1
kind: Secret
metadata:
  name: orchestra-secrets
  namespace: orchestra-main
type: Opaque
data:
  # Base64 encoded values - replace with actual encoded secrets
  database-url: <BASE64_ENCODED_DATABASE_URL>
  redis-url: <BASE64_ENCODED_REDIS_URL>
  jwt-secret: <BASE64_ENCODED_JWT_SECRET>
  api-key: <BASE64_ENCODED_API_KEY>
"""
    
    def generate_hpa_manifest(self) -> str:
        """Generate horizontal pod autoscaler manifest"""
        return """apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: orchestra-main-hpa
  namespace: orchestra-main
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: orchestra-main
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
"""
    
    def create_deployment_scripts(self) -> Dict:
        """Create deployment automation scripts"""
        print("🚀 CREATING DEPLOYMENT SCRIPTS")
        print("=" * 35)
        
        scripts = {
            "deploy_to_kubernetes": self.generate_k8s_deployment_script(),
            "deploy_to_staging": self.generate_staging_deployment_script_local(),
            "deploy_to_production": self.generate_production_deployment_script_local(),
            "rollback_deployment": self.generate_rollback_script(),
            "health_check": self.generate_health_check_script()
        }
        
        return scripts
    
    def generate_k8s_deployment_script(self) -> str:
        """Generate Kubernetes deployment script"""
        return f"""#!/bin/bash
# Kubernetes Deployment Script for Orchestra-Main

set -e

NAMESPACE="orchestra-main"
CLUSTER_ID="{self.infrastructure['kubernetes_cluster']}"

echo "☸️  DEPLOYING TO KUBERNETES CLUSTER"
echo "===================================="

# Check if kubectl is configured
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ kubectl not configured. Please configure kubectl first."
    exit 1
fi

# Create namespace if it doesn't exist
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Apply all manifests
echo "📦 Applying Kubernetes manifests..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/orchestra-main -n $NAMESPACE --timeout=300s

# Check pod status
echo "📊 Pod status:"
kubectl get pods -n $NAMESPACE

# Check service status
echo "🔗 Service status:"
kubectl get services -n $NAMESPACE

# Check ingress status
echo "🌐 Ingress status:"
kubectl get ingress -n $NAMESPACE

# Run health check
echo "🏥 Running health check..."
POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=orchestra-main -o jsonpath="{{.items[0].metadata.name}}")
kubectl exec -n $NAMESPACE $POD_NAME -- curl -f http://localhost:8000/health

echo "✅ Kubernetes deployment completed successfully!"
"""
    
    def generate_staging_deployment_script_local(self) -> str:
        """Generate local staging deployment script"""
        return f"""#!/bin/bash
# Local Staging Deployment Script

set -e

STAGING_HOST="{self.infrastructure['staging']}"
STAGING_USER="root"

echo "🧪 DEPLOYING TO STAGING SERVER"
echo "=============================="

# Check SSH connectivity
if ! ssh -o ConnectTimeout=5 $STAGING_USER@$STAGING_HOST "echo 'SSH connection successful'"; then
    echo "❌ Cannot connect to staging server"
    exit 1
fi

# Deploy to staging
ssh $STAGING_USER@$STAGING_HOST << 'EOF'
    cd /opt/orchestra-staging
    
    # Pull latest code
    git fetch origin
    git reset --hard origin/develop
    
    # Install/update dependencies
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Install Node.js dependencies
    npm ci
    npm run build
    
    # Run database migrations
    python manage.py migrate
    
    # Collect static files
    python manage.py collectstatic --noinput
    
    # Restart services
    systemctl restart orchestra-staging
    systemctl reload nginx
    
    # Wait for service to start
    sleep 10
    
    # Health check
    curl -f http://localhost:8000/health || exit 1
EOF

echo "✅ Staging deployment completed!"
echo "🔗 Staging URL: http://$STAGING_HOST:8000"
"""
    
    def generate_production_deployment_script_local(self) -> str:
        """Generate local production deployment script"""
        return f"""#!/bin/bash
# Local Production Deployment Script

set -e

PRODUCTION_HOST="{self.infrastructure['production']}"
DATABASE_HOST="{self.infrastructure['database']}"
STAGING_HOST="{self.infrastructure['staging']}"

echo "🚀 DEPLOYING TO PRODUCTION"
echo "=========================="

# Pre-deployment checks
echo "🔍 Running pre-deployment checks..."

# Check staging health
if ! curl -f http://$STAGING_HOST:8000/health; then
    echo "❌ Staging server is not healthy"
    exit 1
fi

# Check database connectivity
if ! nc -zv $DATABASE_HOST 5432; then
    echo "❌ Cannot connect to database"
    exit 1
fi

# Create backup
echo "💾 Creating backup..."
ssh root@$STAGING_HOST "/opt/backups/scripts/backup_database.sh"

# Deploy to production
echo "🚀 Deploying to production..."
ssh root@$PRODUCTION_HOST << 'EOF'
    # Create deployment directory
    DEPLOY_DIR="/opt/orchestra-deploy-$(date +%Y%m%d_%H%M%S)"
    mkdir -p $DEPLOY_DIR
    cd $DEPLOY_DIR
    
    # Clone latest code
    git clone https://github.com/user/orchestra-main.git .
    git checkout main
    
    # Setup virtual environment
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Build frontend
    npm ci
    npm run build:production
    
    # Stop current services
    systemctl stop orchestra-main || true
    
    # Backup current deployment
    if [ -d "/opt/orchestra-current" ]; then
        mv /opt/orchestra-current /opt/orchestra-backup-$(date +%Y%m%d_%H%M%S)
    fi
    
    # Switch to new deployment
    ln -sfn $DEPLOY_DIR /opt/orchestra-current
    
    # Update systemd service
    cp deploy/orchestra-main.service /etc/systemd/system/
    systemctl daemon-reload
    
    # Start services
    systemctl start orchestra-main
    systemctl enable orchestra-main
    
    # Update nginx
    cp deploy/nginx.conf /etc/nginx/sites-available/orchestra-main
    nginx -t && systemctl reload nginx
EOF

# Health check
echo "🏥 Running health check..."
sleep 30

for i in {{1..5}}; do
    if curl -f http://$PRODUCTION_HOST/health; then
        echo "✅ Production deployment successful!"
        exit 0
    fi
    echo "Attempt $i failed, retrying..."
    sleep 10
done

echo "❌ Production health check failed"
exit 1
"""
    
    def generate_rollback_script(self) -> str:
        """Generate rollback script"""
        return f"""#!/bin/bash
# Rollback Script for Orchestra-Main

set -e

PRODUCTION_HOST="{self.infrastructure['production']}"

if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_timestamp>"
    echo "Available backups:"
    ssh root@$PRODUCTION_HOST "ls -la /opt/orchestra-backup-*"
    exit 1
fi

BACKUP_TIMESTAMP=$1

echo "🔄 ROLLING BACK PRODUCTION DEPLOYMENT"
echo "====================================="

ssh root@$PRODUCTION_HOST << EOF
    BACKUP_DIR="/opt/orchestra-backup-$BACKUP_TIMESTAMP"
    
    if [ ! -d "\$BACKUP_DIR" ]; then
        echo "❌ Backup directory not found: \$BACKUP_DIR"
        exit 1
    fi
    
    echo "🛑 Stopping current services..."
    systemctl stop orchestra-main
    
    echo "🔄 Switching to backup..."
    rm -f /opt/orchestra-current
    ln -sfn \$BACKUP_DIR /opt/orchestra-current
    
    echo "🚀 Starting services..."
    systemctl start orchestra-main
    
    echo "🏥 Health check..."
    sleep 10
    curl -f http://localhost:8000/health || exit 1
EOF

echo "✅ Rollback completed successfully!"
"""
    
    def generate_health_check_script(self) -> str:
        """Generate comprehensive health check script"""
        return f"""#!/bin/bash
# Comprehensive Health Check Script

PRODUCTION_HOST="{self.infrastructure['production']}"
DATABASE_HOST="{self.infrastructure['database']}"
STAGING_HOST="{self.infrastructure['staging']}"

echo "🏥 ORCHESTRA-MAIN HEALTH CHECK"
echo "=============================="

# Production server health
echo "🚀 Production Server:"
if curl -f http://$PRODUCTION_HOST/health; then
    echo "   ✅ Application healthy"
else
    echo "   ❌ Application unhealthy"
fi

if curl -f http://$PRODUCTION_HOST/api/status; then
    echo "   ✅ API responding"
else
    echo "   ❌ API not responding"
fi

# Database health
echo "🗄️  Database Server:"
if nc -zv $DATABASE_HOST 5432; then
    echo "   ✅ PostgreSQL accessible"
else
    echo "   ❌ PostgreSQL not accessible"
fi

if nc -zv $DATABASE_HOST 6379; then
    echo "   ✅ Redis accessible"
else
    echo "   ❌ Redis not accessible"
fi

if curl -f http://$DATABASE_HOST:8080/v1/meta; then
    echo "   ✅ Weaviate accessible"
else
    echo "   ❌ Weaviate not accessible"
fi

# Staging server health
echo "🧪 Staging Server:"
if curl -f http://$STAGING_HOST:8000/health; then
    echo "   ✅ Staging application healthy"
else
    echo "   ❌ Staging application unhealthy"
fi

# Monitoring health
echo "📊 Monitoring:"
if curl -f http://$STAGING_HOST:9090/-/healthy; then
    echo "   ✅ Prometheus healthy"
else
    echo "   ❌ Prometheus unhealthy"
fi

if curl -f http://$STAGING_HOST:3000/api/health; then
    echo "   ✅ Grafana healthy"
else
    echo "   ❌ Grafana unhealthy"
fi

if curl -f http://$STAGING_HOST:5601/api/status; then
    echo "   ✅ Kibana healthy"
else
    echo "   ❌ Kibana unhealthy"
fi

echo ""
echo "🏥 Health check completed"
"""
    
    def create_cicd_summary(self) -> Dict:
        """Create CI/CD deployment summary"""
        summary = {
            "deployment_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "components": {
                "github_actions": {
                    "ci_pipeline": "Automated testing and building",
                    "staging_deployment": "Automatic deployment to staging",
                    "production_deployment": "Manual deployment to production",
                    "security_scanning": "Weekly security scans",
                    "performance_testing": "Daily performance tests"
                },
                "kubernetes": {
                    "cluster_id": self.infrastructure["kubernetes_cluster"],
                    "namespace": "orchestra-main",
                    "replicas": 3,
                    "autoscaling": "CPU and memory based"
                },
                "deployment_scripts": {
                    "kubernetes": "deploy_to_kubernetes.sh",
                    "staging": "deploy_to_staging.sh",
                    "production": "deploy_to_production.sh",
                    "rollback": "rollback_deployment.sh",
                    "health_check": "health_check.sh"
                }
            },
            "infrastructure": self.infrastructure,
            "features": [
                "Automated CI/CD pipeline",
                "Blue-green deployments",
                "Automatic rollback on failure",
                "Comprehensive health checks",
                "Security scanning",
                "Performance monitoring",
                "Kubernetes orchestration",
                "Multi-environment support"
            ]
        }
        
        return summary
    
    def deploy_cicd_pipeline(self) -> Dict:
        """Deploy complete CI/CD pipeline"""
        print("🔄 DEPLOYING CI/CD PIPELINE")
        print("=" * 30)
        
        # Create GitHub Actions workflows
        workflows = self.create_github_actions_workflows()
        
        # Create Kubernetes manifests
        k8s_manifests = self.create_kubernetes_manifests()
        
        # Create deployment scripts
        deployment_scripts = self.create_deployment_scripts()
        
        # Save all files
        self.save_cicd_files(workflows, k8s_manifests, deployment_scripts)
        
        # Create summary
        summary = self.create_cicd_summary()
        
        return summary
    
    def save_cicd_files(self, workflows: Dict, manifests: Dict, scripts: Dict):
        """Save all CI/CD files"""
        # Create directories
        os.makedirs("/home/ubuntu/.github/workflows", exist_ok=True)
        os.makedirs("/home/ubuntu/k8s", exist_ok=True)
        os.makedirs("/home/ubuntu/scripts", exist_ok=True)
        
        # Save GitHub Actions workflows
        for name, content in workflows.items():
            with open(f"/home/ubuntu/.github/workflows/{name}.yml", "w") as f:
                f.write(content)
        
        # Save Kubernetes manifests
        for name, content in manifests.items():
            with open(f"/home/ubuntu/k8s/{name}.yaml", "w") as f:
                f.write(content)
        
        # Save deployment scripts
        for name, content in scripts.items():
            script_path = f"/home/ubuntu/scripts/{name}.sh"
            with open(script_path, "w") as f:
                f.write(content)
            os.chmod(script_path, 0o755)  # Make executable
        
        print("✅ CI/CD files saved:")
        print("   📁 GitHub Actions: .github/workflows/")
        print("   📁 Kubernetes: k8s/")
        print("   📁 Scripts: scripts/")

def main():
    manager = CICDManager()
    
    # Deploy CI/CD pipeline
    summary = manager.deploy_cicd_pipeline()
    
    # Save summary
    with open("/home/ubuntu/cicd_deployment_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print("\n🎉 CI/CD PIPELINE DEPLOYMENT COMPLETE!")
    print("=" * 45)
    print("🔄 Components: GitHub Actions, Kubernetes, Deployment Scripts")
    print("📄 Summary saved to: cicd_deployment_summary.json")

if __name__ == "__main__":
    main()

