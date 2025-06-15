#!/bin/bash

# Orchestra AI Monitoring and Analytics Setup
# Deploys Prometheus, Grafana, and custom dashboards

set -e

echo "📊 Setting up Orchestra AI Monitoring and Analytics..."

# Create monitoring namespace and deploy Prometheus
kubectl create namespace monitoring || true

# Deploy Prometheus
kubectl apply -f - << 'PROMETHEUS_YAML'
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
      - job_name: 'orchestra-api'
        static_configs:
          - targets: ['orchestra-api.orchestra:8000']
      - job_name: 'mcp-memory'
        static_configs:
          - targets: ['mcp-memory.orchestra:8003']
      - job_name: 'mcp-tools'
        static_configs:
          - targets: ['mcp-tools.orchestra:8006']
      - job_name: 'postgres'
        static_configs:
          - targets: ['postgres.orchestra:5432']
      - job_name: 'redis'
        static_configs:
          - targets: ['redis.orchestra:6379']
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      volumes:
      - name: config
        configMap:
          name: prometheus-config
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: monitoring
spec:
  selector:
    app: prometheus
  ports:
  - port: 9090
    targetPort: 9090
  type: LoadBalancer
PROMETHEUS_YAML

# Deploy Grafana
kubectl apply -f - << 'GRAFANA_YAML'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          value: "orchestra_admin_2024"
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
  name: grafana
  namespace: monitoring
spec:
  selector:
    app: grafana
  ports:
  - port: 3000
    targetPort: 3000
  type: LoadBalancer
GRAFANA_YAML

echo "✅ Monitoring infrastructure deployed!"
echo "📊 Grafana will be available at the LoadBalancer IP on port 3000"
echo "🔐 Default login: admin / orchestra_admin_2024"

