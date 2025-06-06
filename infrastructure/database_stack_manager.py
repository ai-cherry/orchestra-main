import os
#!/usr/bin/env python3
"""
Database Stack Deployment Manager
Deploys PostgreSQL, Redis, Weaviate, and configures Pinecone integration
"""

import requests
import time
import subprocess
import json
from typing import Dict, List

class DatabaseStackManager:
    def __init__(self, LAMBDA_API_KEY: str):
        self.LAMBDA_API_KEY = LAMBDA_API_KEY
        self.headers = {
            "Authorization": f"Bearer {LAMBDA_API_KEY}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        
        # Database server configuration
        self.db_server_ip = "45.77.87.106"
        self.db_server_id = "42cb20f8-8297-4542-ba56-ac450a621292"
    
    def wait_for_server_ready(self, max_wait_minutes: int = 10) -> bool:
        """Wait for database server to be fully ready"""
        print(f"⏳ Waiting for database server to be ready (max {max_wait_minutes} minutes)...")
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while time.time() - start_time < max_wait_seconds:
            # Check server status
            response = requests.get(f"{self.base_url}/instances/{self.db_server_id}", headers=self.headers)
            
            if response.status_code == 200:
                instance = response.json()["instance"]
                server_status = instance.get("server_status", "unknown")
                power_status = instance.get("power_status", "unknown")
                
                print(f"   Status: {server_status}, Power: {power_status}")
                
                if server_status == "ok" and power_status == "running":
                    print("✅ Database server is ready!")
                    return True
                elif server_status in ["installingbooting", "pending"]:
                    print("   Still booting...")
                    # TODO: Replace with asyncio.sleep() for async code
                    time.sleep(30)
                else:
                    # TODO: Replace with asyncio.sleep() for async code
                    print(f"   Unexpected status: {server_status}")
                    time.sleep(15)
            # TODO: Replace with asyncio.sleep() for async code
            else:
                print(f"   API error: {response.status_code}")
                time.sleep(15)
        
        print("❌ Timeout waiting for server to be ready")
        return False
    
    def test_ssh_connectivity(self) -> bool:
        """Test SSH connectivity to database server"""
        print("🔌 Testing SSH connectivity...")
        
        try:
            # Try SSH with key authentication
            result = subprocess.run([
                'ssh', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=no',
                '-o', 'PasswordAuthentication=no', '-o', 'PubkeyAuthentication=yes',
                f'root@{self.db_server_ip}', 'echo "SSH key auth successful"'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                print("✅ SSH key authentication working")
                return True
            else:
                print("❌ SSH key authentication failed")
                print(f"   Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ SSH test failed: {e}")
            return False
    
    def deploy_database_stack_remote(self) -> bool:
        """Deploy database stack on remote server"""
        print("🗄️  DEPLOYING DATABASE STACK")
        print("=" * 40)
        
        # Create deployment script
        deployment_script = """#!/bin/bash
set -e

echo "🗄️  Orchestra-Main Database Stack Deployment"
echo "============================================="

# Update system
echo "📦 Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt update && apt upgrade -y

# Install PostgreSQL 16
echo "🐘 Installing PostgreSQL 16..."
apt install -y postgresql-16 postgresql-contrib-16

# Configure PostgreSQL
echo "⚙️  Configuring PostgreSQL..."
sudo -u postgres createuser orchestra 2>/dev/null || echo "User already exists"
sudo -u postgres createdb orchestra_main 2>/dev/null || echo "Database already exists"
sudo -u postgres psql -c "ALTER USER orchestra PASSWORD 'OrchAI_DB_2024!';"

# Configure PostgreSQL for remote connections
echo "🌐 Configuring PostgreSQL for remote access..."
echo "host all all 10.0.0.0/8 md5" >> /etc/postgresql/16/main/pg_hba.conf
echo "host all all 172.16.0.0/12 md5" >> /etc/postgresql/16/main/pg_hba.conf
echo "listen_addresses = '*'" >> /etc/postgresql/16/main/postgresql.conf
systemctl restart postgresql
systemctl enable postgresql

# Install Redis
echo "🔴 Installing Redis..."
apt install -y redis-server
sed -i 's/bind 127.0.0.1/bind 0.0.0.0/' /etc/redis/redis.conf
sed -i 's/protected-mode yes/protected-mode no/' /etc/redis/redis.conf
systemctl restart redis-server
systemctl enable redis-server

# Install Docker for Weaviate
echo "🐳 Installing Docker..."
apt install -y docker.io docker-compose-plugin
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
    restart: unless-stopped
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
docker compose up -d

# Install monitoring
echo "📊 Installing monitoring..."
apt install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter

# Install additional tools
echo "🛠️  Installing additional tools..."
apt install -y htop curl wget git vim nano

# Create health check script
cat > /root/health_check.sh << 'EOF'
#!/bin/bash
echo "🏥 Orchestra-Main Database Stack Health Check"
echo "============================================="
echo "PostgreSQL: $(systemctl is-active postgresql)"
echo "Redis: $(systemctl is-active redis-server)"
echo "Docker: $(systemctl is-active docker)"
echo "Weaviate: $(docker ps | grep weaviate | wc -l) containers running"
echo "Node Exporter: $(systemctl is-active prometheus-node-exporter)"
echo ""
echo "🔗 Connection endpoints:"
echo "   PostgreSQL: $(hostname -I | awk '{print $1}'):5432"
echo "   Redis: $(hostname -I | awk '{print $1}'):6379"
echo "   Weaviate: $(hostname -I | awk '{print $1}'):8080"
echo ""
echo "📊 System resources:"
echo "   CPU: $(nproc) cores"
echo "   RAM: $(free -h | grep Mem | awk '{print $2}') total, $(free -h | grep Mem | awk '{print $7}') available"
echo "   Disk: $(df -h / | tail -1 | awk '{print $4}') available"
EOF

chmod +x /root/health_check.sh

# Create database initialization script
cat > /root/init_orchestra_db.sql << 'EOF'
-- Orchestra-Main Database Initialization
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create main tables
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    config JSONB,
    status VARCHAR(50) DEFAULT 'inactive',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON tasks(agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_embeddings_metadata ON embeddings USING GIN(metadata);

-- Insert sample data
INSERT INTO agents (name, type, config, status) VALUES 
('Main Orchestrator', 'orchestrator', '{"max_concurrent_tasks": 10}', 'active'),
('Data Processor', 'processor', '{"batch_size": 100}', 'active'),
('AI Assistant', 'assistant', '{"model": "gpt-4", "temperature": 0.7}', 'active')
ON CONFLICT DO NOTHING;

EOF

# Initialize database
echo "🗃️  Initializing Orchestra database..."
sudo -u postgres psql -d orchestra_main -f /root/init_orchestra_db.sql

# Create connection test script
cat > /root/cleaned_reference << 'EOF'
#!/usr/bin/env python3
import psycopg2
import redis
import requests
import json

def test_postgresql():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="orchestra_main",
            user="orchestra",
password = os.getenv('ORCHESTRA_INFRA_PASSWORD')
        )
        cursor = conn.cursor()
        # TODO: Run EXPLAIN ANALYZE on this query
        cursor.execute("SELECT COUNT(*) FROM agents;")
        count = cursor.fetchone()[0]
        conn.close()
        return f"✅ PostgreSQL: {count} agents in database"
    except Exception as e:
        return f"❌ PostgreSQL: {e}"

def test_redis():
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.set('test_key', 'orchestra_test')
        value = r.get('test_key')
        r.delete('test_key')
        return f"✅ Redis: Connection successful, test value: {value}"
    except Exception as e:
        return f"❌ Redis: {e}"

def test_weaviate():
    try:
        response = requests.get('http://localhost:8080/v1/meta')
        if response.status_code == 200:
            meta = response.json()
            return f"✅ Weaviate: Version {meta.get('version', 'unknown')}"
        else:
            return f"❌ Weaviate: HTTP {response.status_code}"
    except Exception as e:
        return f"❌ Weaviate: {e}"

if __name__ == "__main__":
    print("🧪 Testing database connections...")
    print(test_postgresql())
    print(test_redis())
    print(test_weaviate())
EOF

chmod +x /root/cleaned_reference

# Install Python dependencies for testing
echo "🐍 Installing Python dependencies..."
apt install -y python3-pip
pip3 install psycopg2-binary redis requests

echo ""
echo "🎉 DATABASE STACK DEPLOYMENT COMPLETE!"
echo "======================================"
echo ""
echo "🔗 Services running on:"
echo "   PostgreSQL: $(hostname -I | awk '{print $1}'):5432"
echo "   Redis: $(hostname -I | awk '{print $1}'):6379"
echo "   Weaviate: $(hostname -I | awk '{print $1}'):8080"
echo ""
echo "🛠️  Management scripts:"
echo "   Health check: /root/health_check.sh"
echo ""
echo ""
echo "📊 Run health check now:"
/root/health_check.sh
echo ""
echo "🧪 Run connection tests:"
python3 /root/cleaned_reference
"""
        
        # Save deployment script
        with open("/home/ubuntu/deploy_database_stack.sh", "w") as f:
            f.write(deployment_script)
        
        print("✅ Database deployment script created")
        
        # Execute deployment script on remote server
        try:
            print("🚀 Executing deployment on database server...")
            
            # Copy script to server and execute
            copy_result = subprocess.run([
                'scp', '-o', 'StrictHostKeyChecking=no',
                '/home/ubuntu/deploy_database_stack.sh',
                f'root@{self.db_server_ip}:/root/deploy_database_stack.sh'
            ], capture_output=True, text=True, timeout=30)
            
            if copy_result.returncode == 0:
                print("✅ Script copied to server")
                
                # Execute script
                exec_result = subprocess.run([
                    'ssh', '-o', 'StrictHostKeyChecking=no',
                    f'root@{self.db_server_ip}',
                    'chmod +x /root/deploy_database_stack.sh && /root/deploy_database_stack.sh'
                ], capture_output=True, text=True, timeout=600)  # 10 minute timeout
                
                if exec_result.returncode == 0:
                    print("✅ Database stack deployed successfully!")
                    print("📋 Deployment output:")
                    print(exec_result.stdout)
                    return True
                else:
                    print("❌ Database deployment failed")
                    print(f"Error: {exec_result.stderr}")
                    return False
            else:
                print("❌ Failed to copy script to server")
                print(f"Error: {copy_result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Deployment execution failed: {e}")
            return False
    
    def create_pinecone_integration(self) -> Dict:
        """Create Pinecone integration configuration"""
        print("🌲 CONFIGURING PINECONE INTEGRATION")
        print("=" * 40)
        
        pinecone_config = {
            "api_key": "USER_PROVIDED",  # User needs to provide this
            "environment": "us-west1-gcp",
            "index_name": "orchestra-embeddings",
            "dimension": 1536,  # OpenAI embedding dimension
            "metric": "cosine",
            "pod_type": "p1.x1",
            "replicas": 1,
            "shards": 1
        }
        
        # Create Pinecone setup script
        pinecone_script = f"""#!/usr/bin/env python3
'''
Pinecone Integration Setup for Orchestra-Main
Run this script with your Pinecone API key
'''

import pinecone
import os
import sys

def setup_pinecone(api_key: str):
    try:
        # Initialize Pinecone
        pinecone.init(
            api_key=api_key,
            environment="{pinecone_config['environment']}"
        )
        
        # Create index if it doesn't exist
        index_name = "{pinecone_config['index_name']}"
        
        if index_name not in pinecone.list_indexes():
            print(f"Creating Pinecone index: {{index_name}}")
            pinecone.create_index(
                name=index_name,
                dimension={pinecone_config['dimension']},
                metric="{pinecone_config['metric']}",
                pod_type="{pinecone_config['pod_type']}",
                replicas={pinecone_config['replicas']},
                shards={pinecone_config['shards']}
            )
            print("✅ Pinecone index created successfully")
        else:
            print("✅ Pinecone index already exists")
        
        # Test connection
        index = pinecone.Index(index_name)
        stats = index.describe_index_stats()
        print(f"📊 Index stats: {{stats}}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pinecone setup failed: {{e}}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 setup_pinecone.py <API_KEY>")
        sys.exit(1)
    
    api_key = sys.argv[1]
    setup_pinecone(api_key)
"""
        
        with open("/home/ubuntu/setup_pinecone.py", "w") as f:
            f.write(pinecone_script)
        
        print("✅ Pinecone setup script created: setup_pinecone.py")
        print("📋 Pinecone configuration:")
        for key, value in pinecone_config.items():
            print(f"   {key}: {value}")
        
        return pinecone_config
    
    def generate_database_summary(self) -> Dict:
        """Generate database stack summary"""
        summary = {
            "deployment_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "database_server": {
                "ip": self.db_server_ip,
                "specs": "8 CPU, 32GB RAM, 640GB SSD",
                "location": "Los Angeles (LAX)"
            },
            "databases": {
                "postgresql": {
                    "version": "16",
                    "port": 5432,
                    "database": "orchestra_main",
                    "user": "orchestra",
                    "features": ["UUID extension", "Vector extension", "JSONB support"]
                },
                "redis": {
                    "version": "latest",
                    "port": 6379,
                    "configuration": "No authentication, bind all interfaces"
                },
                "weaviate": {
                    "version": "1.22.4",
                    "port": 8080,
                    "grpc_port": 50051,
                    "modules": ["text2vec-openai", "text2vec-cohere", "generative-openai"]
                },
                "pinecone": {
                    "type": "managed_service",
                    "index": "orchestra-embeddings",
                    "dimension": 1536,
                    "status": "requires_api_key"
                }
            },
            "management_scripts": {
                "health_check": "/root/health_check.sh",
                "",
                "database_init": "/root/init_orchestra_db.sql"
            },
            "connection_strings": {
                "postgresql": f"postgresql://orchestra:OrchAI_DB_2024!@{self.db_server_ip}:5432/orchestra_main",
                "redis": f"redis://{self.db_server_ip}:6379",
                "weaviate": f"http://{self.db_server_ip}:8080"
            }
        }
        
        return summary

def main():
LAMBDA_API_KEY = os.getenv("INFRA_DATABASE_STACK_MANAGER_API_KEY", "")
    manager = DatabaseStackManager(LAMBDA_API_KEY)
    
    print("🗄️  ORCHESTRA-MAIN DATABASE STACK DEPLOYMENT")
    print("=" * 55)
    
    # Wait for server to be ready
    if not manager.wait_for_server_ready():
        print("❌ Server not ready, cannot proceed with deployment")
        return
    
    # Test SSH connectivity
    if not manager.test_ssh_connectivity():
        print("❌ SSH connectivity failed, cannot proceed with deployment")
        return
    
    # Deploy database stack
    if manager.deploy_database_stack_remote():
        print("✅ Database stack deployment successful!")
    else:
        print("❌ Database stack deployment failed")
        return
    
    # Configure Pinecone integration
    pinecone_config = manager.create_pinecone_integration()
    
    # Generate summary
    summary = manager.generate_database_summary()
    
    # Save summary
    with open("/home/ubuntu/database_stack_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print("\n🎉 DATABASE STACK DEPLOYMENT COMPLETE!")
    print("=" * 45)
    print(f"📊 Database server: {manager.db_server_ip}")
    print("📄 Summary saved to: database_stack_summary.json")
    print("🌲 Pinecone setup: setup_pinecone.py")

if __name__ == "__main__":
    main()

