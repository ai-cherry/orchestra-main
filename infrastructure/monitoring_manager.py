#!/usr/bin/env python3
"""
Monitoring, Logging, and Backup Systems Manager
Deploys comprehensive observability and backup infrastructure
"""

import requests
import json
import time
import subprocess
from typing import Dict, List

class MonitoringManager:
    def __init__(self, vultr_api_key: str):
        self.vultr_api_key = vultr_api_key
        self.headers = {
            "Authorization": f"Bearer {vultr_api_key}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.vultr.com/v2"
        
        # Infrastructure IPs
        self.servers = {
            "production": "45.32.69.157",
            "database": "45.77.87.106",
            "staging": "207.246.108.201",
            "kubernetes_workers": [
                "207.246.104.92",
                "66.42.107.3",
                "45.32.68.4"
            ]
        }
    
    def create_monitoring_stack(self) -> Dict:
        """Create comprehensive monitoring stack"""
        print("📊 CREATING MONITORING STACK")
        print("=" * 35)
        
        # Prometheus configuration
        prometheus_config = self.generate_prometheus_config()
        
        # Grafana configuration
        grafana_config = self.generate_grafana_config()
        
        # AlertManager configuration
        alertmanager_config = self.generate_alertmanager_config()
        
        monitoring_stack = {
            "prometheus": prometheus_config,
            "grafana": grafana_config,
            "alertmanager": alertmanager_config,
            "deployment_server": self.servers["staging"]  # Deploy on staging server
        }
        
        return monitoring_stack
    
    def generate_prometheus_config(self) -> Dict:
        """Generate Prometheus configuration"""
        config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "scrape_configs": [
                {
                    "job_name": "prometheus",
                    "static_configs": [{"targets": ["localhost:9090"]}]
                },
                {
                    "job_name": "node-exporter",
                    "static_configs": [
                        {"targets": [f"{ip}:9100" for ip in [
                            self.servers["production"],
                            self.servers["database"],
                            self.servers["staging"]
                        ] + self.servers["kubernetes_workers"]]}
                    ]
                },
                {
                    "job_name": "postgresql",
                    "static_configs": [{"targets": [f"{self.servers['database']}:9187"]}]
                },
                {
                    "job_name": "redis",
                    "static_configs": [{"targets": [f"{self.servers['database']}:9121"]}]
                },
                {
                    "job_name": "nginx",
                    "static_configs": [{"targets": [f"{self.servers['production']}:9113"]}]
                }
            ],
            "rule_files": ["alerts.yml"],
            "alerting": {
                "alertmanagers": [
                    {"static_configs": [{"targets": ["localhost:9093"]}]}
                ]
            }
        }
        
        return config
    
    def generate_grafana_config(self) -> Dict:
        """Generate Grafana configuration"""
        config = {
            "server": {
                "http_port": 3000,
                "domain": self.servers["staging"],
                "root_url": f"http://{self.servers['staging']}:3000"
            },
            "security": {
                "admin_user": "admin",
                "admin_password": "OrchAI_Grafana_2024!"
            },
            "datasources": [
                {
                    "name": "Prometheus",
                    "type": "prometheus",
                    "url": f"http://{self.servers['staging']}:9090",
                    "access": "proxy",
                    "isDefault": True
                }
            ],
            "dashboards": [
                "node-exporter-full",
                "postgresql-database",
                "redis-dashboard",
                "kubernetes-cluster-monitoring",
                "nginx-overview"
            ]
        }
        
        return config
    
    def generate_alertmanager_config(self) -> Dict:
        """Generate AlertManager configuration"""
        config = {
            "global": {
                "smtp_smarthost": "localhost:587",
                "smtp_from": "alerts@orchestra-main.com"
            },
            "route": {
                "group_by": ["alertname"],
                "group_wait": "10s",
                "group_interval": "10s",
                "repeat_interval": "1h",
                "receiver": "web.hook"
            },
            "receivers": [
                {
                    "name": "web.hook",
                    "webhook_configs": [
                        {
                            "url": f"http://{self.servers['production']}/api/alerts",
                            "send_resolved": True
                        }
                    ]
                }
            ]
        }
        
        return config
    
    def create_logging_system(self) -> Dict:
        """Create centralized logging system"""
        print("📝 CREATING LOGGING SYSTEM")
        print("=" * 30)
        
        logging_config = {
            "elasticsearch": {
                "host": self.servers["staging"],
                "port": 9200,
                "cluster_name": "orchestra-logs"
            },
            "logstash": {
                "host": self.servers["staging"],
                "port": 5044,
                "beats_port": 5044
            },
            "kibana": {
                "host": self.servers["staging"],
                "port": 5601,
                "elasticsearch_url": f"http://{self.servers['staging']}:9200"
            },
            "filebeat_configs": {
                "production": {
                    "paths": [
                        "/var/log/nginx/*.log",
                        "/var/log/orchestra/*.log",
                        "/var/log/syslog"
                    ]
                },
                "database": {
                    "paths": [
                        "/var/log/postgresql/*.log",
                        "/var/log/redis/*.log",
                        "/var/log/docker/*.log"
                    ]
                }
            }
        }
        
        return logging_config
    
    def create_backup_system(self) -> Dict:
        """Create automated backup system"""
        print("💾 CREATING BACKUP SYSTEM")
        print("=" * 28)
        
        backup_config = {
            "schedule": {
                "database_backup": "0 2 * * *",  # Daily at 2 AM
                "config_backup": "0 3 * * 0",   # Weekly on Sunday at 3 AM
                "full_backup": "0 1 * * 0"      # Weekly on Sunday at 1 AM
            },
            "retention": {
                "daily": 7,
                "weekly": 4,
                "monthly": 12
            },
            "storage": {
                "local": "/opt/backups",
                "remote": "vultr_object_storage",
                "encryption": True
            },
            "backup_targets": {
                "postgresql": {
                    "host": self.servers["database"],
                    "databases": ["orchestra_main"],
                    "method": "pg_dump"
                },
                "redis": {
                    "host": self.servers["database"],
                    "method": "redis_save"
                },
                "weaviate": {
                    "host": self.servers["database"],
                    "method": "docker_volume"
                },
                "configurations": {
                    "nginx": "/etc/nginx",
                    "prometheus": "/etc/prometheus",
                    "grafana": "/etc/grafana"
                }
            }
        }
        
        return backup_config
    
    def generate_monitoring_deployment_script(self, monitoring_config: Dict) -> str:
        """Generate monitoring stack deployment script"""
        script = f"""#!/bin/bash
# Orchestra-Main Monitoring Stack Deployment
# Deploy on staging server: {self.servers['staging']}

set -e

echo "📊 DEPLOYING MONITORING STACK"
echo "=============================="

# Update system
export DEBIAN_FRONTEND=noninteractive
apt update && apt upgrade -y

# Install Docker and Docker Compose
echo "🐳 Installing Docker..."
apt install -y docker.io docker-compose-plugin
systemctl enable docker
systemctl start docker

# Create monitoring directory
mkdir -p /opt/monitoring
cd /opt/monitoring

# Create Prometheus configuration
cat > prometheus.yml << 'EOF'
{json.dumps(monitoring_config['prometheus'], indent=2)}
EOF

# Create Grafana configuration
mkdir -p grafana/provisioning/datasources
mkdir -p grafana/provisioning/dashboards

cat > grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

# Create AlertManager configuration
cat > alertmanager.yml << 'EOF'
{json.dumps(monitoring_config['alertmanager'], indent=2)}
EOF

# Create alerts configuration
cat > alerts.yml << 'EOF'
groups:
  - name: orchestra-main-alerts
    rules:
      - alert: InstanceDown
        expr: up == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Instance {{{{ $labels.instance }}}} down"
          description: "{{{{ $labels.instance }}}} has been down for more than 5 minutes."
      
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{{mode="idle"}}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{{{ $labels.instance }}}}"
          description: "CPU usage is above 80% for more than 5 minutes."
      
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage on {{{{ $labels.instance }}}}"
          description: "Memory usage is above 90% for more than 5 minutes."
      
      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space on {{{{ $labels.instance }}}}"
          description: "Disk space is below 10% on {{{{ $labels.mountpoint }}}}."
      
      - alert: PostgreSQLDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"
          description: "PostgreSQL database is not responding."
      
      - alert: RedisDown
        expr: redis_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis is down"
          description: "Redis server is not responding."
EOF

# Create Docker Compose file
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerts.yml:/etc/prometheus/alerts.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=OrchAI_Grafana_2024!
      - GF_USERS_ALLOW_SIGN_UP=false
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:
EOF

# Start monitoring stack
echo "🚀 Starting monitoring stack..."
docker compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Check service status
echo "📊 Checking service status..."
docker compose ps

# Create health check script
cat > /root/monitoring_health.sh << 'EOF'
#!/bin/bash
echo "📊 Monitoring Stack Health Check"
echo "================================"
echo "Prometheus: $(curl -s http://localhost:9090/-/healthy || echo 'DOWN')"
echo "Grafana: $(curl -s http://localhost:3000/api/health | jq -r '.database' 2>/dev/null || echo 'DOWN')"
echo "AlertManager: $(curl -s http://localhost:9093/-/healthy || echo 'DOWN')"
echo "Node Exporter: $(curl -s http://localhost:9100/metrics | head -1 | grep -o 'node_' || echo 'DOWN')"
echo ""
echo "🔗 Access URLs:"
echo "   Prometheus: http://{self.servers['staging']}:9090"
echo "   Grafana: http://{self.servers['staging']}:3000 (admin/OrchAI_Grafana_2024!)"
echo "   AlertManager: http://{self.servers['staging']}:9093"
EOF

chmod +x /root/monitoring_health.sh

echo ""
echo "✅ MONITORING STACK DEPLOYED!"
echo "============================="
echo "🔗 Access URLs:"
echo "   Prometheus: http://{self.servers['staging']}:9090"
echo "   Grafana: http://{self.servers['staging']}:3000"
echo "   AlertManager: http://{self.servers['staging']}:9093"
echo ""
echo "🔐 Grafana Login:"
echo "   Username: admin"
echo "   Password: OrchAI_Grafana_2024!"
echo ""
echo "🏥 Health check: /root/monitoring_health.sh"
"""
        
        return script
    
    def generate_logging_deployment_script(self, logging_config: Dict) -> str:
        """Generate logging system deployment script"""
        script = f"""#!/bin/bash
# Orchestra-Main Logging System Deployment (ELK Stack)
# Deploy on staging server: {self.servers['staging']}

set -e

echo "📝 DEPLOYING LOGGING SYSTEM (ELK STACK)"
echo "======================================="

# Create logging directory
mkdir -p /opt/logging
cd /opt/logging

# Create ELK Stack Docker Compose
cat > docker-compose-elk.yml << 'EOF'
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    restart: unless-stopped

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: logstash
    ports:
      - "5044:5044"
      - "9600:9600"
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch
    restart: unless-stopped

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: kibana
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch
    restart: unless-stopped

volumes:
  elasticsearch_data:
EOF

# Create Logstash configuration
cat > logstash.conf << 'EOF'
input {{
  beats {{
    port => 5044
  }}
}}

filter {{
  if [fileset][module] == "nginx" {{
    if [fileset][name] == "access" {{
      grok {{
        match => {{ "message" => "%{{NGINXACCESS}}" }}
      }}
    }}
    else if [fileset][name] == "error" {{
      grok {{
        match => {{ "message" => "%{{NGINXERROR}}" }}
      }}
    }}
  }}
  
  if [fileset][module] == "postgresql" {{
    grok {{
      match => {{ "message" => "%{{POSTGRESQL}}" }}
    }}
  }}
  
  date {{
    match => [ "timestamp", "dd/MMM/yyyy:HH:mm:ss Z" ]
  }}
}}

output {{
  elasticsearch {{
    hosts => ["elasticsearch:9200"]
    index => "orchestra-logs-%{{+YYYY.MM.dd}}"
  }}
}}
EOF

# Start ELK stack
echo "🚀 Starting ELK stack..."
docker compose -f docker-compose-elk.yml up -d

# Wait for Elasticsearch to be ready
echo "⏳ Waiting for Elasticsearch..."
until curl -s http://localhost:9200/_cluster/health | grep -q '"status":"green"\\|"status":"yellow"'; do
  sleep 5
done

echo "✅ ELK stack is running!"

# Create Filebeat configuration for each server
mkdir -p filebeat-configs

# Production server Filebeat config
cat > filebeat-configs/filebeat-production.yml << 'EOF'
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/nginx/*.log
    - /var/log/orchestra/*.log
    - /var/log/syslog
  fields:
    server: production
    environment: prod

output.logstash:
  hosts: ["{self.servers['staging']}:5044"]

processors:
- add_host_metadata:
    when.not.contains.tags: forwarded
EOF

# Database server Filebeat config
cat > filebeat-configs/filebeat-database.yml << 'EOF'
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/postgresql/*.log
    - /var/log/redis/*.log
    - /var/log/docker/*.log
  fields:
    server: database
    environment: prod

output.logstash:
  hosts: ["{self.servers['staging']}:5044"]

processors:
- add_host_metadata:
    when.not.contains.tags: forwarded
EOF

echo "📄 Filebeat configurations created in filebeat-configs/"

# Create logging health check
cat > /root/logging_health.sh << 'EOF'
#!/bin/bash
echo "📝 Logging System Health Check"
echo "=============================="
echo "Elasticsearch: $(curl -s http://localhost:9200/_cluster/health | jq -r '.status' 2>/dev/null || echo 'DOWN')"
echo "Logstash: $(curl -s http://localhost:9600/_node/stats | jq -r '.pipeline.events.in' 2>/dev/null || echo 'DOWN')"
echo "Kibana: $(curl -s http://localhost:5601/api/status | jq -r '.status.overall.state' 2>/dev/null || echo 'DOWN')"
echo ""
echo "🔗 Access URLs:"
echo "   Elasticsearch: http://{self.servers['staging']}:9200"
echo "   Kibana: http://{self.servers['staging']}:5601"
echo ""
echo "📊 Index status:"
curl -s http://localhost:9200/_cat/indices?v
EOF

chmod +x /root/logging_health.sh

echo ""
echo "✅ LOGGING SYSTEM DEPLOYED!"
echo "=========================="
echo "🔗 Access URLs:"
echo "   Elasticsearch: http://{self.servers['staging']}:9200"
echo "   Kibana: http://{self.servers['staging']}:5601"
echo ""
echo "📄 Filebeat configs: /opt/logging/filebeat-configs/"
echo "🏥 Health check: /root/logging_health.sh"
"""
        
        return script
    
    def generate_backup_deployment_script(self, backup_config: Dict) -> str:
        """Generate backup system deployment script"""
        script = f"""#!/bin/bash
# Orchestra-Main Backup System Deployment
# Deploy on staging server: {self.servers['staging']}

set -e

echo "💾 DEPLOYING BACKUP SYSTEM"
echo "=========================="

# Create backup directory structure
mkdir -p /opt/backups/{{daily,weekly,monthly}}
mkdir -p /opt/backups/scripts

# Install backup tools
apt update
apt install -y postgresql-client redis-tools rsync rclone

# Create database backup script
cat > /opt/backups/scripts/backup_database.sh << 'EOF'
#!/bin/bash
# Database backup script

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/daily"
DB_HOST="{self.servers['database']}"

echo "💾 Starting database backup - $BACKUP_DATE"

# PostgreSQL backup
echo "🐘 Backing up PostgreSQL..."
PGPASSWORD="OrchAI_DB_2024!" pg_dump -h $DB_HOST -U orchestra -d orchestra_main > $BACKUP_DIR/postgresql_$BACKUP_DATE.sql
gzip $BACKUP_DIR/postgresql_$BACKUP_DATE.sql

# Redis backup
echo "🔴 Backing up Redis..."
redis-cli -h $DB_HOST --rdb $BACKUP_DIR/redis_$BACKUP_DATE.rdb

# Weaviate backup (Docker volume)
echo "🔍 Backing up Weaviate..."
ssh root@$DB_HOST "docker run --rm -v weaviate_weaviate_data:/data -v /tmp:/backup alpine tar czf /backup/weaviate_$BACKUP_DATE.tar.gz -C /data ."
scp root@$DB_HOST:/tmp/weaviate_$BACKUP_DATE.tar.gz $BACKUP_DIR/

echo "✅ Database backup completed - $BACKUP_DATE"
EOF

# Create configuration backup script
cat > /opt/backups/scripts/backup_configs.sh << 'EOF'
#!/bin/bash
# Configuration backup script

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/weekly"

echo "⚙️  Starting configuration backup - $BACKUP_DATE"

# Create config backup directory
mkdir -p $BACKUP_DIR/configs_$BACKUP_DATE

# Backup from production server
echo "📦 Backing up production configs..."
rsync -avz root@{self.servers['production']}:/etc/nginx/ $BACKUP_DIR/configs_$BACKUP_DATE/nginx/
rsync -avz root@{self.servers['production']}:/etc/ssl/ $BACKUP_DIR/configs_$BACKUP_DATE/ssl/

# Backup from database server
echo "🗄️  Backing up database configs..."
rsync -avz root@{self.servers['database']}:/etc/postgresql/ $BACKUP_DIR/configs_$BACKUP_DATE/postgresql/
rsync -avz root@{self.servers['database']}:/etc/redis/ $BACKUP_DIR/configs_$BACKUP_DATE/redis/

# Backup monitoring configs
echo "📊 Backing up monitoring configs..."
cp -r /opt/monitoring $BACKUP_DIR/configs_$BACKUP_DATE/
cp -r /opt/logging $BACKUP_DIR/configs_$BACKUP_DATE/

# Compress configuration backup
tar czf $BACKUP_DIR/configs_$BACKUP_DATE.tar.gz -C $BACKUP_DIR configs_$BACKUP_DATE
rm -rf $BACKUP_DIR/configs_$BACKUP_DATE

echo "✅ Configuration backup completed - $BACKUP_DATE"
EOF

# Create cleanup script
cat > /opt/backups/scripts/cleanup_backups.sh << 'EOF'
#!/bin/bash
# Backup cleanup script

echo "🧹 Cleaning up old backups..."

# Keep last 7 daily backups
find /opt/backups/daily -name "*.sql.gz" -mtime +7 -delete
find /opt/backups/daily -name "*.rdb" -mtime +7 -delete
find /opt/backups/daily -name "*.tar.gz" -mtime +7 -delete

# Keep last 4 weekly backups
find /opt/backups/weekly -name "*.tar.gz" -mtime +28 -delete

# Keep last 12 monthly backups
find /opt/backups/monthly -name "*.tar.gz" -mtime +365 -delete

echo "✅ Backup cleanup completed"
EOF

# Create restore script
cat > /opt/backups/scripts/restore_database.sh << 'EOF'
#!/bin/bash
# Database restore script

if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_date>"
    echo "Example: $0 20241204_143000"
    exit 1
fi

BACKUP_DATE=$1
BACKUP_DIR="/opt/backups/daily"
DB_HOST="{self.servers['database']}"

echo "🔄 Starting database restore - $BACKUP_DATE"

# Restore PostgreSQL
if [ -f "$BACKUP_DIR/postgresql_$BACKUP_DATE.sql.gz" ]; then
    echo "🐘 Restoring PostgreSQL..."
    gunzip -c $BACKUP_DIR/postgresql_$BACKUP_DATE.sql.gz | PGPASSWORD="OrchAI_DB_2024!" psql -h $DB_HOST -U orchestra -d orchestra_main
    echo "✅ PostgreSQL restored"
else
    echo "❌ PostgreSQL backup not found: postgresql_$BACKUP_DATE.sql.gz"
fi

# Restore Redis
if [ -f "$BACKUP_DIR/redis_$BACKUP_DATE.rdb" ]; then
    echo "🔴 Restoring Redis..."
    scp $BACKUP_DIR/redis_$BACKUP_DATE.rdb root@$DB_HOST:/tmp/
    ssh root@$DB_HOST "systemctl stop redis-server && cp /tmp/redis_$BACKUP_DATE.rdb /var/lib/redis/dump.rdb && chown redis:redis /var/lib/redis/dump.rdb && systemctl start redis-server"
    echo "✅ Redis restored"
else
    echo "❌ Redis backup not found: redis_$BACKUP_DATE.rdb"
fi

echo "✅ Database restore completed - $BACKUP_DATE"
EOF

# Make scripts executable
chmod +x /opt/backups/scripts/*.sh

# Create cron jobs
cat > /tmp/backup_crontab << 'EOF'
# Orchestra-Main Backup Schedule
0 2 * * * /opt/backups/scripts/backup_database.sh >> /var/log/backup.log 2>&1
0 3 * * 0 /opt/backups/scripts/backup_configs.sh >> /var/log/backup.log 2>&1
0 4 * * 0 /opt/backups/scripts/cleanup_backups.sh >> /var/log/backup.log 2>&1
EOF

crontab /tmp/backup_crontab

# Create backup health check
cat > /root/backup_health.sh << 'EOF'
#!/bin/bash
echo "💾 Backup System Health Check"
echo "============================"
echo "Backup directory: $(du -sh /opt/backups)"
echo "Last daily backup: $(ls -t /opt/backups/daily/*.sql.gz 2>/dev/null | head -1 | xargs ls -lh 2>/dev/null || echo 'None')"
echo "Last weekly backup: $(ls -t /opt/backups/weekly/*.tar.gz 2>/dev/null | head -1 | xargs ls -lh 2>/dev/null || echo 'None')"
echo ""
echo "📅 Cron jobs:"
crontab -l | grep backup
echo ""
echo "📊 Backup log (last 10 lines):"
tail -10 /var/log/backup.log 2>/dev/null || echo "No backup log yet"
EOF

chmod +x /root/backup_health.sh

# Test backup system
echo "🧪 Testing backup system..."
/opt/backups/scripts/backup_database.sh

echo ""
echo "✅ BACKUP SYSTEM DEPLOYED!"
echo "========================="
echo "📁 Backup directory: /opt/backups"
echo "🛠️  Scripts: /opt/backups/scripts/"
echo "📅 Schedule:"
echo "   Daily DB backup: 2:00 AM"
echo "   Weekly config backup: 3:00 AM Sunday"
echo "   Cleanup: 4:00 AM Sunday"
echo ""
echo "🏥 Health check: /root/backup_health.sh"
echo "🔄 Manual restore: /opt/backups/scripts/restore_database.sh <date>"
"""
        
        return script
    
    def deploy_monitoring_systems(self) -> Dict:
        """Deploy all monitoring, logging, and backup systems"""
        print("🚀 DEPLOYING COMPLETE MONITORING INFRASTRUCTURE")
        print("=" * 55)
        
        # Create configurations
        monitoring_config = self.create_monitoring_stack()
        logging_config = self.create_logging_system()
        backup_config = self.create_backup_system()
        
        # Generate deployment scripts
        monitoring_script = self.generate_monitoring_deployment_script(monitoring_config)
        logging_script = self.generate_logging_deployment_script(logging_config)
        backup_script = self.generate_backup_deployment_script(backup_config)
        
        # Save scripts
        with open("/home/ubuntu/deploy_monitoring.sh", "w") as f:
            f.write(monitoring_script)
        
        with open("/home/ubuntu/deploy_logging.sh", "w") as f:
            f.write(logging_script)
        
        with open("/home/ubuntu/deploy_backup.sh", "w") as f:
            f.write(backup_script)
        
        print("✅ Deployment scripts created:")
        print("   📊 Monitoring: deploy_monitoring.sh")
        print("   📝 Logging: deploy_logging.sh")
        print("   💾 Backup: deploy_backup.sh")
        
        # Create combined deployment summary
        deployment_summary = {
            "deployment_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "target_server": self.servers["staging"],
            "monitoring": monitoring_config,
            "logging": logging_config,
            "backup": backup_config,
            "access_urls": {
                "prometheus": f"http://{self.servers['staging']}:9090",
                "grafana": f"http://{self.servers['staging']}:3000",
                "alertmanager": f"http://{self.servers['staging']}:9093",
                "kibana": f"http://{self.servers['staging']}:5601",
                "elasticsearch": f"http://{self.servers['staging']}:9200"
            },
            "credentials": {
                "grafana": {
                    "username": "admin",
                    "password": "OrchAI_Grafana_2024!"
                }
            }
        }
        
        return deployment_summary

def main():
    vultr_api_key = "7L34HOKF25HYDT7WHETR7QZTHQX6M5YP36MQ"
    manager = MonitoringManager(vultr_api_key)
    
    # Deploy monitoring systems
    summary = manager.deploy_monitoring_systems()
    
    # Save summary
    with open("/home/ubuntu/monitoring_deployment_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print("\n🎉 MONITORING INFRASTRUCTURE READY!")
    print("=" * 40)
    print(f"🎯 Target server: {summary['target_server']}")
    print("📊 Components: Prometheus, Grafana, AlertManager, ELK Stack, Backup System")
    print("📄 Summary saved to: monitoring_deployment_summary.json")

if __name__ == "__main__":
    main()

