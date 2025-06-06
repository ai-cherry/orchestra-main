import os
#!/usr/bin/env python3
"""
Orchestra-Main Tier 2 Enterprise Infrastructure Deployment (Fixed)
Multi-cloud architecture with Lambda + Paperspace integration
"""

import requests
import json
import time
import sys
import base64
from typing import Dict, List, Optional

class Tier2InfrastructureManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Infrastructure configuration
        self.ssh_key_id = "5e0549f8-d7cd-4ecd-9935-291d0965cc5b"  # orchestra-Lambda
        self.region = "lax"  # Los Angeles - same as main server
        self.main_server_ip = "45.32.69.157"
        
    def get_available_k8s_versions(self) -> List[str]:
        """Get available Kubernetes versions"""
        response = requests.get(f"{self.base_url}/kubernetes/versions", headers=self.headers)
        if response.status_code == 200:
            versions = response.json().get("versions", [])
            return [v["version"] for v in versions]
        return []
    
    def get_object_storage_clusters(self) -> List[Dict]:
        """Get available object storage clusters"""
        response = requests.get(f"{self.base_url}/object-storage/clusters", headers=self.headers)
        if response.status_code == 200:
            return response.json().get("clusters", [])
        return []
    
    def deploy_database_server(self) -> Dict:
        """Deploy dedicated PostgreSQL + Redis server"""
        print("🗄️  Deploying database server...")
        
        user_data = """#!/bin/bash
# Database Server Setup Script
apt update && apt upgrade -y

# Install PostgreSQL 16
apt install -y postgresql-16 postgresql-contrib-16

# Install Redis
apt install -y redis-server

# Install Docker for Weaviate
apt install -y docker.io docker-compose
systemctl enable docker
systemctl start docker

# Configure PostgreSQL
sudo -u postgres createuser orchestra
sudo -u postgres createdb orchestra_main
sudo -u postgres psql -c "ALTER USER orchestra PASSWORD 'OrchAI_DB_2024!';"

# Configure Redis
sed -i 's/bind 127.0.0.1/bind 0.0.0.0/' /etc/redis/redis.conf
systemctl restart redis-server

# Install monitoring
apt install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter

echo "Database server setup complete" > /root/setup_complete.txt
"""
        
        data = {
            "region": self.region,
            "plan": "vc2-8c-32gb",  # 8 CPU, 32GB RAM - $160/month
            "os_id": 1743,  # Ubuntu 24.04 LTS
            "label": "orchestra-database",
            "tag": "database",
            "hostname": "orchestra-db",
            "enable_ipv6": True,
            "enable_private_network": True,
            "sshkey_id": [self.ssh_key_id],
            "user_data": base64.b64encode(user_data.encode()).decode()
        }
        
        response = requests.post(f"{self.base_url}/instances", headers=self.headers, json=data)
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Database server created: {result['instance']['id']}")
            return result
        else:
            print(f"❌ Database server creation failed: {response.status_code} - {response.text}")
            return {}
    
    def deploy_staging_server(self) -> Dict:
        """Deploy staging/development server"""
        print("🧪 Deploying staging server...")
        
        user_data = """#!/bin/bash
# Staging Server Setup Script
apt update && apt upgrade -y

# Install Docker and Docker Compose
apt install -y docker.io docker-compose git nginx
systemctl enable docker nginx
systemctl start docker nginx

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Install Python 3.11 and pip
apt install -y python3.11 python3.11-pip python3.11-venv

# Install monitoring
apt install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter

# Clone orchestra-main repository (placeholder)
mkdir -p /opt/orchestra-staging
chown -R root:root /opt/orchestra-staging

echo "Staging server setup complete" > /root/setup_complete.txt
"""
        
        data = {
            "region": self.region,
            "plan": "vc2-8c-32gb",  # 8 CPU, 32GB RAM - $160/month
            "os_id": 1743,  # Ubuntu 24.04 LTS
            "label": "orchestra-staging",
            "tag": "staging",
            "hostname": "orchestra-staging",
            "enable_ipv6": True,
            "enable_private_network": True,
            "sshkey_id": [self.ssh_key_id],
            "user_data": base64.b64encode(user_data.encode()).decode()
        }
        
        response = requests.post(f"{self.base_url}/instances", headers=self.headers, json=data)
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Staging server created: {result['instance']['id']}")
            return result
        else:
            print(f"❌ Staging server creation failed: {response.status_code} - {response.text}")
            return {}
    
    def deploy_kubernetes_cluster(self) -> Dict:
        """Deploy Lambda Kubernetes Engine cluster"""
        print("☸️  Deploying Kubernetes cluster...")
        
        # Get available versions first
        versions = self.get_available_k8s_versions()
        if not versions:
            print("❌ Could not get Kubernetes versions")
            return {}
        
        latest_version = versions[0]  # Use the first (latest) version
        print(f"   Using Kubernetes version: {latest_version}")
        
        data = {
            "label": "orchestra-k8s",
            "region": self.region,
            "version": latest_version,
            "node_pools": [
                {
                    "node_quantity": 3,
                    "plan": "vc2-4c-8gb",  # 4 CPU, 8GB RAM per node
                    "label": "orchestra-workers",
                    "tag": "k8s-worker"
                }
            ]
        }
        
        response = requests.post(f"{self.base_url}/kubernetes/clusters", headers=self.headers, json=data)
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Kubernetes cluster created: {result['vke_cluster']['id']}")
            return result
        else:
            print(f"❌ Kubernetes cluster creation failed: {response.status_code} - {response.text}")
            return {}
    
    def deploy_load_balancer(self) -> Dict:
        """Deploy load balancer (HTTP only initially)"""
        print("⚖️  Deploying load balancer...")
        
        data = {
            "region": self.region,
            "label": "orchestra-lb",
            "balancing_algorithm": "roundrobin",
            "proxy_protocol": False,
            "health_check": {
                "protocol": "http",
                "port": 80,
                "path": "/health",
                "check_interval": 15,
                "response_timeout": 5,
                "unhealthy_threshold": 3,
                "healthy_threshold": 2
            },
            "forwarding_rules": [
                {
                    "frontend_protocol": "http",
                    "frontend_port": 80,
                    "backend_protocol": "http",
                    "backend_port": 80
                }
            ]
        }
        
        response = requests.post(f"{self.base_url}/load-balancers", headers=self.headers, json=data)
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Load balancer created: {result['load_balancer']['id']}")
            return result
        else:
            print(f"❌ Load balancer creation failed: {response.status_code} - {response.text}")
            return {}
    
    def deploy_object_storage(self) -> Dict:
        """Deploy object storage for backups and files"""
        print("🗂️  Deploying object storage...")
        
        # Get available clusters first
        clusters = self.get_object_storage_clusters()
        if not clusters:
            print("❌ Could not get object storage clusters")
            return {}
        
        # Find US cluster
        us_cluster = None
        for cluster in clusters:
            if "us" in cluster.get("region", "").lower() or "america" in cluster.get("region", "").lower():
                us_cluster = cluster
                break
        
        if not us_cluster:
            us_cluster = clusters[0]  # Use first available
        
        print(f"   Using cluster: {us_cluster.get('id')} in {us_cluster.get('region')}")
        
        data = {
            "cluster_id": us_cluster["id"],
            "label": "orchestra-storage"
        }
        
        response = requests.post(f"{self.base_url}/object-storage", headers=self.headers, json=data)
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Object storage created: {result['object_storage']['id']}")
            return result
        else:
            print(f"❌ Object storage creation failed: {response.status_code} - {response.text}")
            return {}
    
    def deploy_full_tier2(self) -> Dict:
        """Deploy complete Tier 2 infrastructure"""
        print("🚀 DEPLOYING TIER 2 ENTERPRISE INFRASTRUCTURE")
        print("=" * 60)
        
        results = {
            "deployment_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "components": {},
            "estimated_monthly_cost": 0
        }
        
        # Deploy database server
        db_result = self.deploy_database_server()
        if db_result:
            results["components"]["database"] = db_result
            results["estimated_monthly_cost"] += 160  # $160/month
        
        # TODO: Replace with asyncio.sleep() for async code
        time.sleep(2)  # Rate limiting
        
        # Deploy staging server
        staging_result = self.deploy_staging_server()
        if staging_result:
            results["components"]["staging"] = staging_result
            results["estimated_monthly_cost"] += 160  # $160/month
         # TODO: Replace with asyncio.sleep() for async code
        
        time.sleep(2)  # Rate limiting
        
        # Deploy Kubernetes cluster
        k8s_result = self.deploy_kubernetes_cluster()
        if k8s_result:
            results["components"]["kubernetes"] = k8s_result
            # TODO: Replace with asyncio.sleep() for async code
            results["estimated_monthly_cost"] += 120  # 3 nodes * $40/month
        
        time.sleep(2)  # Rate limiting
        
        # Deploy load balancer
        lb_result = self.deploy_load_balancer()
        if lb_result:
            # TODO: Replace with asyncio.sleep() for async code
            results["components"]["load_balancer"] = lb_result
            results["estimated_monthly_cost"] += 10  # $10/month
        
        time.sleep(2)  # Rate limiting
        
        # Deploy object storage
        storage_result = self.deploy_object_storage()
        if storage_result:
            results["components"]["object_storage"] = storage_result
            results["estimated_monthly_cost"] += 5  # ~$5/month for 100GB
        
        return results
    
    def get_infrastructure_status(self) -> Dict:
        """Get status of all infrastructure components"""
        print("📊 INFRASTRUCTURE STATUS")
        print("=" * 40)
        
        status = {"instances": [], "kubernetes": [], "load_balancers": [], "object_storage": []}
        
        # Get all instances
        response = requests.get(f"{self.base_url}/instances", headers=self.headers)
        if response.status_code == 200:
            instances = response.json().get("instances", [])
            for instance in instances:
                print(f"🖥️  {instance['label']}: {instance['power_status']} ({instance['main_ip']})")
                status["instances"].append({
                    "label": instance["label"],
                    "status": instance["power_status"],
                    "ip": instance["main_ip"],
                    "plan": instance["plan"]
                })
        
        # Get Kubernetes clusters
        response = requests.get(f"{self.base_url}/kubernetes/clusters", headers=self.headers)
        if response.status_code == 200:
            clusters = response.json().get("vke_clusters", [])
            for cluster in clusters:
                print(f"☸️  {cluster['label']}: {cluster['status']}")
                status["kubernetes"].append({
                    "label": cluster["label"],
                    "status": cluster["status"],
                    "version": cluster.get("version", "unknown")
                })
        
        # Get load balancers
        response = requests.get(f"{self.base_url}/load-balancers", headers=self.headers)
        if response.status_code == 200:
            lbs = response.json().get("load_balancers", [])
            for lb in lbs:
                print(f"⚖️  {lb['label']}: {lb['status']} ({lb.get('ipv4', 'pending')})")
                status["load_balancers"].append({
                    "label": lb["label"],
                    "status": lb["status"],
                    "ip": lb.get("ipv4", "pending")
                })
        
        # Get object storage
        response = requests.get(f"{self.base_url}/object-storage", headers=self.headers)
        if response.status_code == 200:
            storages = response.json().get("object_storages", [])
            for storage in storages:
                print(f"🗂️  {storage['label']}: {storage['status']}")
                status["object_storage"].append({
                    "label": storage["label"],
                    "status": storage["status"]
                })
        
        return status

def main():
api_key = os.getenv('ORCHESTRA_INFRA_API_KEY')
    manager = Tier2InfrastructureManager(api_key)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "deploy":
            results = manager.deploy_full_tier2()
            print("\n🎉 DEPLOYMENT RESULTS:")
            print(json.dumps(results, indent=2))
            
            # Save results to file
            with open("/home/ubuntu/tier2_deployment_results.json", "w") as f:
                json.dump(results, f, indent=2)
            print("\n📄 Results saved to: tier2_deployment_results.json")
            
        elif command == "status":
            status = manager.get_infrastructure_status()
            
            # Save status to file
            with open("/home/ubuntu/infrastructure_status.json", "w") as f:
                json.dump(status, f, indent=2)
            print("\n📄 Status saved to: infrastructure_status.json")
            
        else:
            print("Usage: python3 tier2_infrastructure_fixed.py [deploy|status]")
    else:
        print("Usage: python3 tier2_infrastructure_fixed.py [deploy|status]")

if __name__ == "__main__":
    main()

