#!/usr/bin/env python3
"""
Multi-Cloud Architecture Manager
Integrates Vultr and Paperspace for Orchestra-Main project
"""

import requests
import json
import time
import subprocess
from typing import Dict, List, Optional

class MultiCloudManager:
    def __init__(self, vultr_api_key: str, paperspace_api_key: str = None):
        self.vultr_api_key = vultr_api_key
        self.paperspace_api_key = paperspace_api_key
        
        # Vultr configuration
        self.vultr_base_url = "https://api.vultr.com/v2"
        self.vultr_headers = {
            "Authorization": f"Bearer {vultr_api_key}",
            "Content-Type": "application/json"
        }
        
        # Paperspace configuration (if available)
        if paperspace_api_key:
            self.paperspace_headers = {
                "Authorization": f"Bearer {paperspace_api_key}",
                "Content-Type": "application/json"
            }
        
        # Infrastructure mapping
        self.infrastructure = {
            "vultr": {
                "production": "45.32.69.157",
                "database": "45.77.87.106", 
                "staging": "207.246.108.201",
                "kubernetes_workers": [
                    "207.246.104.92",
                    "66.42.107.3", 
                    "45.32.68.4"
                ]
            },
            "paperspace": {
                "ai_workstation": None,  # To be discovered
                "gpu_instances": []
            }
        }
    
    def discover_paperspace_resources(self) -> Dict:
        """Discover existing Paperspace resources"""
        print("🔍 DISCOVERING PAPERSPACE RESOURCES")
        print("=" * 40)
        
        if not self.paperspace_api_key:
            print("⚠️  No Paperspace API key provided - checking via CLI")
            return self.discover_paperspace_cli()
        
        # Use API if available
        try:
            # Get machines
            response = requests.get(
                "https://api.paperspace.io/machines/getMachines",
                headers=self.paperspace_headers
            )
            
            if response.status_code == 200:
                machines = response.json()
                print(f"✅ Found {len(machines)} Paperspace machines")
                
                for machine in machines:
                    print(f"🖥️  {machine.get('name', 'Unknown')}: {machine.get('state', 'unknown')}")
                    print(f"   IP: {machine.get('publicIpAddress', 'N/A')}")
                    print(f"   GPU: {machine.get('machineType', 'N/A')}")
                
                return {"machines": machines}
            else:
                print(f"❌ Paperspace API error: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Paperspace discovery failed: {e}")
            return {}
    
    def discover_paperspace_cli(self) -> Dict:
        """Discover Paperspace resources via CLI"""
        try:
            # Check if paperspace CLI is available
            result = subprocess.run(['paperspace', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print("✅ Paperspace CLI found")
                
                # Get machines
                machines_result = subprocess.run(['paperspace', 'machines', 'list'], 
                                               capture_output=True, text=True, timeout=10)
                
                if machines_result.returncode == 0:
                    print("✅ Paperspace machines discovered via CLI")
                    print(machines_result.stdout)
                    return {"cli_output": machines_result.stdout}
                else:
                    print("❌ Failed to list Paperspace machines")
                    return {}
            else:
                print("⚠️  Paperspace CLI not available")
                return {}
                
        except Exception as e:
            print(f"⚠️  Paperspace CLI check failed: {e}")
            return {}
    
    def create_multi_cloud_network(self) -> Dict:
        """Create secure network connections between clouds"""
        print("🌐 CONFIGURING MULTI-CLOUD NETWORKING")
        print("=" * 45)
        
        network_config = {
            "vultr_private_network": None,
            "vpn_gateway": None,
            "security_groups": [],
            "load_balancer_config": None
        }
        
        # Create Vultr private network
        print("🔗 Creating Vultr private network...")
        
        private_network_data = {
            "region": "lax",
            "description": "Orchestra-Main Private Network",
            "v4_subnet": "10.99.0.0",
            "v4_subnet_mask": 24
        }
        
        response = requests.post(
            f"{self.vultr_base_url}/private-networks",
            headers=self.vultr_headers,
            json=private_network_data
        )
        
        if response.status_code == 201:
            network = response.json()["network"]
            network_config["vultr_private_network"] = network
            print(f"✅ Private network created: {network['id']}")
        else:
            print(f"❌ Private network creation failed: {response.status_code}")
        
        # Configure VPN gateway for Paperspace connection
        print("🔐 Setting up VPN gateway configuration...")
        
        vpn_config = {
            "type": "wireguard",
            "vultr_endpoint": "45.32.69.157",  # Main server as VPN gateway
            "paperspace_endpoint": "TBD",  # To be configured
            "shared_key": "orchestra-main-vpn-key",
            "vultr_subnet": "10.99.0.0/24",
            "paperspace_subnet": "10.100.0.0/24"
        }
        
        network_config["vpn_gateway"] = vpn_config
        print("✅ VPN gateway configuration prepared")
        
        return network_config
    
    def configure_ai_ml_workloads(self) -> Dict:
        """Configure AI/ML workload distribution"""
        print("🤖 CONFIGURING AI/ML WORKLOAD DISTRIBUTION")
        print("=" * 50)
        
        workload_config = {
            "vultr_services": {
                "web_api": "45.32.69.157",
                "database": "45.77.87.106",
                "redis_cache": "45.77.87.106",
                "kubernetes_orchestration": "kubernetes_cluster"
            },
            "paperspace_services": {
                "gpu_training": "paperspace_gpu",
                "model_inference": "paperspace_gpu", 
                "data_preprocessing": "paperspace_cpu"
            },
            "hybrid_services": {
                "vector_database": "both",  # Weaviate on Vultr, Pinecone managed
                "model_storage": "vultr_object_storage",
                "training_data": "paperspace_storage"
            }
        }
        
        print("📋 Workload distribution plan:")
        print("   🌐 Vultr: Web API, Database, Orchestration")
        print("   🎮 Paperspace: GPU Training, Model Inference")
        print("   🔄 Hybrid: Vector DB, Storage, Data Pipeline")
        
        return workload_config
    
    def deploy_database_stack(self) -> Dict:
        """Deploy the complete database stack"""
        print("🗄️  DEPLOYING DATABASE STACK")
        print("=" * 35)
        
        database_config = {
            "postgresql": {
                "host": "45.77.87.106",
                "port": 5432,
                "database": "orchestra_main",
                "user": "orchestra",
                "password": "OrchAI_DB_2024!"
            },
            "redis": {
                "host": "45.77.87.106", 
                "port": 6379,
                "password": None
            },
            "weaviate": {
                "host": "45.77.87.106",
                "port": 8080,
                "grpc_port": 50051
            },
            "pinecone": {
                "api_key": "user_provided",
                "environment": "us-west1-gcp",
                "index_name": "orchestra-embeddings"
            }
        }
        
        # Generate database setup script
        setup_script = self.generate_database_setup_script(database_config)
        
        with open("/home/ubuntu/setup_database_stack.sh", "w") as f:
            f.write(setup_script)
        
        print("✅ Database setup script created: setup_database_stack.sh")
        print("📋 Database configuration:")
        for db_type, config in database_config.items():
            print(f"   {db_type}: {config.get('host', 'managed')}:{config.get('port', 'N/A')}")
        
        return database_config
    
    def generate_database_setup_script(self, config: Dict) -> str:
        """Generate database setup script"""
        return f"""#!/bin/bash
# Orchestra-Main Database Stack Setup
# Run this on the database server: {config['postgresql']['host']}

echo "🗄️  Setting up Orchestra-Main Database Stack"
echo "=" * 50

# Update system
apt update && apt upgrade -y

# Install PostgreSQL 16
echo "📊 Installing PostgreSQL 16..."
apt install -y postgresql-16 postgresql-contrib-16

# Configure PostgreSQL
sudo -u postgres createuser {config['postgresql']['user']} 2>/dev/null || true
sudo -u postgres createdb {config['postgresql']['database']} 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER {config['postgresql']['user']} PASSWORD '{config['postgresql']['password']}';"

# Configure PostgreSQL for remote connections
echo "host all all 10.0.0.0/8 md5" >> /etc/postgresql/16/main/pg_hba.conf
echo "listen_addresses = '*'" >> /etc/postgresql/16/main/postgresql.conf
systemctl restart postgresql

# Install Redis
echo "🔴 Installing Redis..."
apt install -y redis-server
sed -i 's/bind 127.0.0.1/bind 0.0.0.0/' /etc/redis/redis.conf
systemctl restart redis-server

# Install Docker for Weaviate
echo "🐳 Installing Docker..."
apt install -y docker.io docker-compose
systemctl enable docker
systemctl start docker

# Deploy Weaviate
echo "🔍 Deploying Weaviate..."
mkdir -p /opt/weaviate
cat > /opt/weaviate/docker-compose.yml << 'EOF'
version: '3.4'
services:
  weaviate:
    command:
    - --host
    - 0.0.0.0
    - --port
    - '8080'
    - --scheme
    - http
    image: semitechnologies/weaviate:1.22.4
    ports:
    - "8080:8080"
    - "50051:50051"
    restart: on-failure:0
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      ENABLE_MODULES: 'text2vec-openai,text2vec-cohere,text2vec-huggingface,ref2vec-centroid,generative-openai,qna-openai'
      CLUSTER_HOSTNAME: 'node1'
    volumes:
    - weaviate_data:/var/lib/weaviate
volumes:
  weaviate_data:
EOF

cd /opt/weaviate
docker-compose up -d

# Install monitoring
echo "📊 Installing monitoring..."
apt install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter

# Create health check script
cat > /root/health_check.sh << 'EOF'
#!/bin/bash
echo "🏥 Database Stack Health Check"
echo "PostgreSQL: $(systemctl is-active postgresql)"
echo "Redis: $(systemctl is-active redis-server)"
echo "Docker: $(systemctl is-active docker)"
echo "Weaviate: $(docker ps | grep weaviate | wc -l) containers"
echo "Node Exporter: $(systemctl is-active prometheus-node-exporter)"
EOF

chmod +x /root/health_check.sh

echo "✅ Database stack setup complete!"
echo "🔗 Connection details:"
echo "   PostgreSQL: {config['postgresql']['host']}:5432"
echo "   Redis: {config['redis']['host']}:6379"
echo "   Weaviate: {config['weaviate']['host']}:8080"
echo ""
echo "🏥 Run health check: /root/health_check.sh"
"""
    
    def generate_infrastructure_summary(self) -> Dict:
        """Generate complete infrastructure summary"""
        print("📊 GENERATING INFRASTRUCTURE SUMMARY")
        print("=" * 45)
        
        summary = {
            "deployment_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "architecture": "Tier 2 Enterprise Multi-Cloud",
            "clouds": ["Vultr", "Paperspace"],
            "total_servers": 6,
            "estimated_monthly_cost": 455,
            "components": {
                "vultr": {
                    "production_server": {
                        "ip": "45.32.69.157",
                        "specs": "16 CPU, 64GB RAM",
                        "role": "Main application server",
                        "cost": "$75/month"
                    },
                    "database_server": {
                        "ip": "45.77.87.106", 
                        "specs": "8 CPU, 32GB RAM",
                        "role": "PostgreSQL, Redis, Weaviate",
                        "cost": "$160/month"
                    },
                    "staging_server": {
                        "ip": "207.246.108.201",
                        "specs": "8 CPU, 32GB RAM", 
                        "role": "Development and testing",
                        "cost": "$160/month"
                    },
                    "kubernetes_cluster": {
                        "nodes": 3,
                        "specs": "4 CPU, 8GB RAM per node",
                        "role": "Container orchestration",
                        "cost": "$120/month"
                    },
                    "load_balancer": {
                        "type": "Vultr Load Balancer",
                        "role": "Traffic distribution",
                        "cost": "$10/month"
                    }
                },
                "paperspace": {
                    "gpu_workstation": {
                        "role": "AI/ML training and inference",
                        "specs": "GPU-enabled instance",
                        "cost": "Variable based on usage"
                    }
                }
            },
            "databases": {
                "postgresql": "Primary application database",
                "redis": "Caching and session storage", 
                "weaviate": "Vector database for embeddings",
                "pinecone": "Managed vector database (backup)"
            },
            "networking": {
                "private_network": "10.99.0.0/24",
                "vpn_gateway": "Configured for multi-cloud",
                "load_balancing": "HTTP/HTTPS with health checks"
            },
            "monitoring": {
                "prometheus": "Metrics collection",
                "node_exporters": "System monitoring",
                "health_checks": "Automated service monitoring"
            }
        }
        
        return summary

def main():
    vultr_api_key = "7L34HOKF25HYDT7WHETR7QZTHQX6M5YP36MQ"
    
    manager = MultiCloudManager(vultr_api_key)
    
    print("🚀 ORCHESTRA-MAIN MULTI-CLOUD SETUP")
    print("=" * 50)
    
    # Discover Paperspace resources
    paperspace_resources = manager.discover_paperspace_resources()
    
    # Create multi-cloud network
    network_config = manager.create_multi_cloud_network()
    
    # Configure AI/ML workloads
    workload_config = manager.configure_ai_ml_workloads()
    
    # Deploy database stack
    database_config = manager.deploy_database_stack()
    
    # Generate summary
    summary = manager.generate_infrastructure_summary()
    
    # Save all configurations
    all_config = {
        "paperspace_resources": paperspace_resources,
        "network_config": network_config,
        "workload_config": workload_config,
        "database_config": database_config,
        "infrastructure_summary": summary
    }
    
    with open("/home/ubuntu/multi_cloud_config.json", "w") as f:
        json.dump(all_config, f, indent=2)
    
    print("\n🎉 MULTI-CLOUD CONFIGURATION COMPLETE!")
    print("📄 Configuration saved to: multi_cloud_config.json")
    print("🛠️  Database setup script: setup_database_stack.sh")
    print(f"💰 Estimated monthly cost: ${summary['estimated_monthly_cost']}")

if __name__ == "__main__":
    main()

