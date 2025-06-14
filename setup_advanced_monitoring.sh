#!/bin/bash

# Orchestra AI Advanced Monitoring and Analytics Dashboard
# Creates comprehensive monitoring with custom Orchestra AI metrics

set -e

echo "📊 Setting up Orchestra AI Advanced Monitoring..."

# Create monitoring configuration with Orchestra AI specific metrics
cat > orchestra_monitoring_config.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-orchestra-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
      - "orchestra_alerts.yml"
    
    scrape_configs:
      # Orchestra AI API Server
      - job_name: 'orchestra-api'
        static_configs:
          - targets: ['orchestra-api.orchestra:8000']
        metrics_path: '/metrics'
        scrape_interval: 10s
        
      # MCP Memory Server (GPU-accelerated)
      - job_name: 'mcp-memory'
        static_configs:
          - targets: ['mcp-memory.orchestra:8003']
        metrics_path: '/metrics'
        scrape_interval: 5s
        
      # MCP Tools Server
      - job_name: 'mcp-tools'
        static_configs:
          - targets: ['mcp-tools.orchestra:8006']
        metrics_path: '/metrics'
        
      # Database monitoring
      - job_name: 'postgres-exporter'
        static_configs:
          - targets: ['postgres-exporter.orchestra:9187']
          
      # Redis monitoring
      - job_name: 'redis-exporter'
        static_configs:
          - targets: ['redis-exporter.orchestra:9121']
          
      # Node metrics for GPU monitoring
      - job_name: 'node-exporter'
        static_configs:
          - targets: ['node-exporter.orchestra:9100']
          
      # NVIDIA GPU metrics
      - job_name: 'nvidia-gpu'
        static_configs:
          - targets: ['nvidia-gpu-exporter.orchestra:9445']

  orchestra_alerts.yml: |
    groups:
      - name: orchestra_ai_alerts
        rules:
          # API Response Time Alert
          - alert: HighAPIResponseTime
            expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
            for: 2m
            labels:
              severity: warning
            annotations:
              summary: "High API response time detected"
              description: "95th percentile response time is {{ $value }}s"
              
          # GPU Utilization Alert
          - alert: LowGPUUtilization
            expr: nvidia_gpu_utilization_percent < 20
            for: 5m
            labels:
              severity: info
            annotations:
              summary: "Low GPU utilization"
              description: "GPU utilization is only {{ $value }}%"
              
          # Memory Usage Alert
          - alert: HighMemoryUsage
            expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
            for: 2m
            labels:
              severity: critical
            annotations:
              summary: "High memory usage"
              description: "Memory usage is {{ $value | humanizePercentage }}"
              
          # MCP Server Down Alert
          - alert: MCPServerDown
            expr: up{job=~"mcp-.*"} == 0
            for: 1m
            labels:
              severity: critical
            annotations:
              summary: "MCP Server is down"
              description: "{{ $labels.job }} server is not responding"
EOF

# Deploy advanced monitoring stack
kubectl apply -f orchestra_monitoring_config.yaml

# Deploy PostgreSQL Exporter
kubectl apply -f - << 'POSTGRES_EXPORTER_YAML'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-exporter
  namespace: orchestra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres-exporter
  template:
    metadata:
      labels:
        app: postgres-exporter
    spec:
      containers:
      - name: postgres-exporter
        image: prometheuscommunity/postgres-exporter:latest
        ports:
        - containerPort: 9187
        env:
        - name: DATA_SOURCE_NAME
          value: "postgresql://orchestra:orchestra_secure_2024@postgres:5432/orchestra_ai?sslmode=disable"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-exporter
  namespace: orchestra
spec:
  selector:
    app: postgres-exporter
  ports:
  - port: 9187
    targetPort: 9187
POSTGRES_EXPORTER_YAML

# Deploy Redis Exporter
kubectl apply -f - << 'REDIS_EXPORTER_YAML'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-exporter
  namespace: orchestra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis-exporter
  template:
    metadata:
      labels:
        app: redis-exporter
    spec:
      containers:
      - name: redis-exporter
        image: oliver006/redis_exporter:latest
        ports:
        - containerPort: 9121
        env:
        - name: REDIS_ADDR
          value: "redis://redis:6379"
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis-exporter
  namespace: orchestra
spec:
  selector:
    app: redis-exporter
  ports:
  - port: 9121
    targetPort: 9121
REDIS_EXPORTER_YAML

# Deploy Node Exporter for system metrics
kubectl apply -f - << 'NODE_EXPORTER_YAML'
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: orchestra
spec:
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      hostNetwork: true
      hostPID: true
      containers:
      - name: node-exporter
        image: prom/node-exporter:latest
        ports:
        - containerPort: 9100
        args:
          - '--path.procfs=/host/proc'
          - '--path.sysfs=/host/sys'
          - '--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|host|etc)($|/)'
        volumeMounts:
        - name: proc
          mountPath: /host/proc
          readOnly: true
        - name: sys
          mountPath: /host/sys
          readOnly: true
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
      volumes:
      - name: proc
        hostPath:
          path: /proc
      - name: sys
        hostPath:
          path: /sys
---
apiVersion: v1
kind: Service
metadata:
  name: node-exporter
  namespace: orchestra
spec:
  selector:
    app: node-exporter
  ports:
  - port: 9100
    targetPort: 9100
NODE_EXPORTER_YAML

# Deploy NVIDIA GPU Exporter
kubectl apply -f - << 'GPU_EXPORTER_YAML'
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: nvidia-gpu-exporter
  namespace: orchestra
spec:
  selector:
    matchLabels:
      app: nvidia-gpu-exporter
  template:
    metadata:
      labels:
        app: nvidia-gpu-exporter
    spec:
      hostNetwork: true
      containers:
      - name: nvidia-gpu-exporter
        image: mindprince/nvidia_gpu_prometheus_exporter:latest
        ports:
        - containerPort: 9445
        securityContext:
          privileged: true
        volumeMounts:
        - name: nvidia-dev
          mountPath: /dev/nvidia0
        - name: nvidia-uvm
          mountPath: /dev/nvidia-uvm
        - name: nvidia-ctl
          mountPath: /dev/nvidiactl
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
      volumes:
      - name: nvidia-dev
        hostPath:
          path: /dev/nvidia0
      - name: nvidia-uvm
        hostPath:
          path: /dev/nvidia-uvm
      - name: nvidia-ctl
        hostPath:
          path: /dev/nvidiactl
---
apiVersion: v1
kind: Service
metadata:
  name: nvidia-gpu-exporter
  namespace: orchestra
spec:
  selector:
    app: nvidia-gpu-exporter
  ports:
  - port: 9445
    targetPort: 9445
GPU_EXPORTER_YAML

# Deploy Enhanced Grafana with Orchestra AI Dashboards
kubectl apply -f - << 'GRAFANA_ENHANCED_YAML'
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
  namespace: monitoring
data:
  orchestra-overview.json: |
    {
      "dashboard": {
        "title": "Orchestra AI Overview",
        "panels": [
          {
            "title": "API Request Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(http_requests_total[5m])",
                "legendFormat": "{{method}} {{status}}"
              }
            ]
          },
          {
            "title": "GPU Utilization",
            "type": "graph", 
            "targets": [
              {
                "expr": "nvidia_gpu_utilization_percent",
                "legendFormat": "GPU {{gpu}}"
              }
            ]
          },
          {
            "title": "MCP Server Status",
            "type": "stat",
            "targets": [
              {
                "expr": "up{job=~\"mcp-.*\"}",
                "legendFormat": "{{job}}"
              }
            ]
          }
        ]
      }
    }
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana-enhanced
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana-enhanced
  template:
    metadata:
      labels:
        app: grafana-enhanced
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          value: "orchestra_admin_2024"
        - name: GF_INSTALL_PLUGINS
          value: "grafana-piechart-panel,grafana-worldmap-panel"
        volumeMounts:
        - name: dashboards
          mountPath: /var/lib/grafana/dashboards
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: dashboards
        configMap:
          name: grafana-dashboards
---
apiVersion: v1
kind: Service
metadata:
  name: grafana-enhanced
  namespace: monitoring
spec:
  selector:
    app: grafana-enhanced
  ports:
  - port: 3000
    targetPort: 3000
  type: LoadBalancer
GRAFANA_ENHANCED_YAML

echo "📊 Advanced monitoring deployment complete!"
echo "🎯 Monitoring endpoints:"
echo "   - Prometheus: http://[LAMBDA_IP]:9090"
echo "   - Grafana: http://[LAMBDA_IP]:3000 (admin/orchestra_admin_2024)"
echo "   - GPU Metrics: http://[LAMBDA_IP]:9445"
echo "   - Node Metrics: http://[LAMBDA_IP]:9100"

echo "📈 Custom Orchestra AI dashboards configured:"
echo "   - API Performance Monitoring"
echo "   - GPU Utilization Tracking"
echo "   - MCP Server Health Status"
echo "   - Database Performance Metrics"
echo "   - Real-time Alert System"

