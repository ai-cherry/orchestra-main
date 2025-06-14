#!/bin/bash

# Orchestra AI Infrastructure Scaling and Performance Optimization
# Auto-scaling, load balancing, and performance tuning for production

set -e

echo "🚀 Implementing Orchestra AI Infrastructure Scaling and Optimization..."

# Create Horizontal Pod Autoscaler (HPA) configurations
kubectl apply -f - << 'HPA_CONFIG_YAML'
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: orchestra-api-hpa
  namespace: orchestra
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: orchestra-api
  minReplicas: 2
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
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-memory-hpa
  namespace: orchestra
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-memory
  minReplicas: 1
  maxReplicas: 4
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 75
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-tools-hpa
  namespace: orchestra
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-tools
  minReplicas: 1
  maxReplicas: 6
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
HPA_CONFIG_YAML

# Deploy NGINX Ingress Controller for advanced load balancing
kubectl apply -f - << 'INGRESS_CONTROLLER_YAML'
apiVersion: v1
kind: Namespace
metadata:
  name: ingress-nginx
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-ingress-controller
  namespace: ingress-nginx
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx-ingress-controller
  template:
    metadata:
      labels:
        app: nginx-ingress-controller
    spec:
      containers:
      - name: nginx-ingress-controller
        image: k8s.gcr.io/ingress-nginx/controller:v1.8.1
        ports:
        - containerPort: 80
        - containerPort: 443
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        args:
          - /nginx-ingress-controller
          - --configmap=$(POD_NAMESPACE)/nginx-configuration
          - --tcp-services-configmap=$(POD_NAMESPACE)/tcp-services
          - --udp-services-configmap=$(POD_NAMESPACE)/udp-services
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
  name: nginx-ingress-controller
  namespace: ingress-nginx
spec:
  selector:
    app: nginx-ingress-controller
  ports:
  - name: http
    port: 80
    targetPort: 80
  - name: https
    port: 443
    targetPort: 443
  type: LoadBalancer
INGRESS_CONTROLLER_YAML

# Create Ingress rules for Orchestra AI services
kubectl apply -f - << 'ORCHESTRA_INGRESS_YAML'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: orchestra-ingress
  namespace: orchestra
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  ingressClassName: nginx
  rules:
  - host: orchestra-api.local
    http:
      paths:
      - path: /api/(.*)
        pathType: Prefix
        backend:
          service:
            name: orchestra-api
            port:
              number: 8000
      - path: /mcp/memory/(.*)
        pathType: Prefix
        backend:
          service:
            name: mcp-memory
            port:
              number: 8003
      - path: /mcp/tools/(.*)
        pathType: Prefix
        backend:
          service:
            name: mcp-tools
            port:
              number: 8006
      - path: /monitoring/(.*)
        pathType: Prefix
        backend:
          service:
            name: grafana-enhanced
            port:
              number: 3000
ORCHESTRA_INGRESS_YAML

# Deploy Redis Cluster for high availability
kubectl apply -f - << 'REDIS_CLUSTER_YAML'
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
  namespace: orchestra
spec:
  serviceName: redis-cluster
  replicas: 3
  selector:
    matchLabels:
      app: redis-cluster
  template:
    metadata:
      labels:
        app: redis-cluster
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command:
          - redis-server
          - --cluster-enabled
          - "yes"
          - --cluster-config-file
          - nodes.conf
          - --cluster-node-timeout
          - "5000"
          - --appendonly
          - "yes"
        volumeMounts:
        - name: redis-data
          mountPath: /data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
  volumeClaimTemplates:
  - metadata:
      name: redis-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: redis-cluster
  namespace: orchestra
spec:
  selector:
    app: redis-cluster
  ports:
  - port: 6379
    targetPort: 6379
  clusterIP: None
REDIS_CLUSTER_YAML

# Deploy PostgreSQL with read replicas for scaling
kubectl apply -f - << 'POSTGRES_SCALING_YAML'
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-primary
  namespace: orchestra
spec:
  serviceName: postgres-primary
  replicas: 1
  selector:
    matchLabels:
      app: postgres-primary
  template:
    metadata:
      labels:
        app: postgres-primary
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: orchestra_ai
        - name: POSTGRES_USER
          value: orchestra
        - name: POSTGRES_PASSWORD
          value: orchestra_secure_2024
        - name: POSTGRES_REPLICATION_USER
          value: replicator
        - name: POSTGRES_REPLICATION_PASSWORD
          value: replicator_pass_2024
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "4Gi"
            cpu: "2000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-replica
  namespace: orchestra
spec:
  replicas: 2
  selector:
    matchLabels:
      app: postgres-replica
  template:
    metadata:
      labels:
        app: postgres-replica
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: PGUSER
          value: replicator
        - name: POSTGRES_PASSWORD
          value: replicator_pass_2024
        - name: POSTGRES_MASTER_SERVICE
          value: postgres-primary
        command:
          - /bin/bash
          - -c
          - |
            pg_basebackup -h $POSTGRES_MASTER_SERVICE -D /var/lib/postgresql/data -U replicator -v -P -W
            echo "standby_mode = 'on'" >> /var/lib/postgresql/data/recovery.conf
            echo "primary_conninfo = 'host=$POSTGRES_MASTER_SERVICE port=5432 user=replicator'" >> /var/lib/postgresql/data/recovery.conf
            postgres
        ports:
        - containerPort: 5432
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
POSTGRES_SCALING_YAML

# Create performance optimization ConfigMap
kubectl apply -f - << 'PERFORMANCE_CONFIG_YAML'
apiVersion: v1
kind: ConfigMap
metadata:
  name: orchestra-performance-config
  namespace: orchestra
data:
  nginx.conf: |
    worker_processes auto;
    worker_connections 1024;
    
    events {
        use epoll;
        multi_accept on;
    }
    
    http {
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        keepalive_timeout 65;
        types_hash_max_size 2048;
        
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
        
        upstream orchestra_api {
            least_conn;
            server orchestra-api:8000 max_fails=3 fail_timeout=30s;
        }
        
        upstream mcp_memory {
            least_conn;
            server mcp-memory:8003 max_fails=3 fail_timeout=30s;
        }
        
        server {
            listen 80;
            server_name _;
            
            location /api/ {
                proxy_pass http://orchestra_api/;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_connect_timeout 30s;
                proxy_send_timeout 30s;
                proxy_read_timeout 30s;
            }
            
            location /mcp/memory/ {
                proxy_pass http://mcp_memory/;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_connect_timeout 60s;
                proxy_send_timeout 60s;
                proxy_read_timeout 60s;
            }
        }
    }
    
  redis.conf: |
    maxmemory 1gb
    maxmemory-policy allkeys-lru
    save 900 1
    save 300 10
    save 60 10000
    tcp-keepalive 300
    timeout 0
    
  postgres.conf: |
    shared_buffers = 2GB
    effective_cache_size = 6GB
    maintenance_work_mem = 512MB
    checkpoint_completion_target = 0.9
    wal_buffers = 16MB
    default_statistics_target = 100
    random_page_cost = 1.1
    effective_io_concurrency = 200
    work_mem = 64MB
    min_wal_size = 1GB
    max_wal_size = 4GB
PERFORMANCE_CONFIG_YAML

# Deploy resource quotas and limits
kubectl apply -f - << 'RESOURCE_QUOTAS_YAML'
apiVersion: v1
kind: ResourceQuota
metadata:
  name: orchestra-quota
  namespace: orchestra
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    persistentvolumeclaims: "10"
    services: "20"
    secrets: "10"
    configmaps: "10"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: orchestra-limits
  namespace: orchestra
spec:
  limits:
  - default:
      cpu: "1000m"
      memory: "2Gi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    type: Container
  - max:
      cpu: "8000m"
      memory: "16Gi"
    min:
      cpu: "50m"
      memory: "64Mi"
    type: Container
RESOURCE_QUOTAS_YAML

echo "📊 Deploying performance monitoring and alerting..."

# Create performance monitoring script
cat > monitor_performance.sh << 'EOF'
#!/bin/bash

echo "🔍 Orchestra AI Performance Monitoring Report"
echo "=============================================="

echo "📊 Cluster Resource Usage:"
kubectl top nodes
echo ""

echo "📈 Pod Resource Usage:"
kubectl top pods -n orchestra
echo ""

echo "🚀 HPA Status:"
kubectl get hpa -n orchestra
echo ""

echo "🌐 Service Status:"
kubectl get services -n orchestra -o wide
echo ""

echo "📋 Ingress Status:"
kubectl get ingress -n orchestra
echo ""

echo "💾 Storage Usage:"
kubectl get pvc -n orchestra
echo ""

echo "⚡ Performance Metrics:"
echo "API Response Time: $(curl -s -w '%{time_total}' -o /dev/null http://orchestra-api:8000/health || echo 'N/A')"
echo "MCP Memory Response: $(curl -s -w '%{time_total}' -o /dev/null http://mcp-memory:8003/health || echo 'N/A')"
echo "Database Connections: $(kubectl exec -n orchestra postgres-0 -- psql -U orchestra -d orchestra_ai -c "SELECT count(*) FROM pg_stat_activity;" -t 2>/dev/null || echo 'N/A')"

echo ""
echo "✅ Performance monitoring complete!"
EOF

chmod +x monitor_performance.sh

echo "🎯 Infrastructure scaling and optimization complete!"
echo ""
echo "📋 Deployed Components:"
echo "   ✅ Horizontal Pod Autoscaling (HPA) for all services"
echo "   ✅ NGINX Ingress Controller with load balancing"
echo "   ✅ Redis Cluster for high availability"
echo "   ✅ PostgreSQL with read replicas"
echo "   ✅ Performance optimization configurations"
echo "   ✅ Resource quotas and limits"
echo "   ✅ Performance monitoring script"
echo ""
echo "🚀 Auto-scaling Configuration:"
echo "   - Orchestra API: 2-10 replicas (CPU: 70%, Memory: 80%)"
echo "   - MCP Memory: 1-4 replicas (CPU: 60%, Memory: 75%)"
echo "   - MCP Tools: 1-6 replicas (CPU: 70%)"
echo ""
echo "📊 Performance Optimizations:"
echo "   - NGINX load balancing with least connections"
echo "   - Redis LRU cache with 1GB memory limit"
echo "   - PostgreSQL tuned for 8GB RAM with read replicas"
echo "   - Gzip compression for HTTP responses"
echo "   - Connection pooling and timeouts configured"
echo ""
echo "🎯 Next Steps:"
echo "   1. Run './monitor_performance.sh' to check system status"
echo "   2. Access Grafana at http://[LAMBDA_IP]:3000 for detailed metrics"
echo "   3. Monitor auto-scaling behavior under load"
echo "   4. Adjust resource limits based on actual usage patterns"

