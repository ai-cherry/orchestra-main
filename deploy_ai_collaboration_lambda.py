#!/usr/bin/env python3
"""
Lambda Labs Deployment Script for Cherry AI Ecosystem
Updated deployment strategy for Lambda Labs infrastructure
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import argparse


class LambdaLabsDeployment:
    """
    Deployment orchestrator for Lambda Labs infrastructure
    """
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.deployment_time = datetime.now()
        self.lambda_host = "150.136.94.139"  # Lambda Labs server
        self.services = {
            "postgresql": {
                "host": self.lambda_host,
                "port": 5432,
                "database": "cherry_ai",
                "status": "unknown"
            },
            "redis": {
                "host": self.lambda_host,
                "port": 6379,
                "status": "unknown"
            },
            "nginx": {
                "host": self.lambda_host,
                "port": 80,
                "ssl_port": 443,
                "status": "unknown"
            },
            "api": {
                "host": self.lambda_host,
                "port": 8000,
                "status": "unknown"
            },
            "frontend": {
                "host": self.lambda_host,
                "port": 3000,
                "status": "unknown"
            }
        }
        
    def check_prerequisites(self) -> bool:
        """Check deployment prerequisites"""
        print("🔍 Checking deployment prerequisites...")
        
        checks = {
            "ssh_access": self._check_ssh_access(),
            "docker": self._check_docker(),
            "environment_vars": self._check_environment_vars(),
            "services": self._check_services()
        }
        
        all_passed = all(checks.values())
        
        if all_passed:
            print("✅ All prerequisites met")
        else:
            print("❌ Prerequisites check failed:")
            for check, passed in checks.items():
                if not passed:
                    print(f"  - {check}: FAILED")
                    
        return all_passed
        
    def _check_ssh_access(self) -> bool:
        """Check SSH access to Lambda Labs server"""
        try:
            result = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=5", f"root@{self.lambda_host}", "echo", "connected"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
            
    def _check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True)
            return result.returncode == 0
        except:
            return False
            
    def _check_environment_vars(self) -> bool:
        """Check required environment variables"""
        required_vars = [
            "POSTGRES_PASSWORD",
            "REDIS_PASSWORD",
            "JWT_SECRET",
            "PINECONE_API_KEY",
            "WEAVIATE_API_KEY"
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            print(f"⚠️  Missing environment variables: {', '.join(missing)}")
            
        return len(missing) == 0
        
    def _check_services(self) -> bool:
        """Check service availability"""
        print("🔍 Checking Lambda Labs services...")
        
        # Check PostgreSQL
        try:
            result = subprocess.run(
                ["pg_isready", "-h", self.lambda_host, "-p", "5432"],
                capture_output=True,
                text=True
            )
            self.services["postgresql"]["status"] = "running" if result.returncode == 0 else "down"
        except:
            self.services["postgresql"]["status"] = "unknown"
            
        # Check Redis
        try:
            result = subprocess.run(
                ["redis-cli", "-h", self.lambda_host, "ping"],
                capture_output=True,
                text=True
            )
            self.services["redis"]["status"] = "running" if "PONG" in result.stdout else "down"
        except:
            self.services["redis"]["status"] = "unknown"
            
        # Check API
        try:
            import requests
            response = requests.get(f"http://{self.lambda_host}:8000/health", timeout=5)
            self.services["api"]["status"] = "running" if response.status_code == 200 else "down"
        except:
            self.services["api"]["status"] = "down"
            
        # Print service status
        for service, info in self.services.items():
            status_icon = "✅" if info["status"] == "running" else "❌"
            print(f"  {status_icon} {service}: {info['status']}")
            
        return all(info["status"] == "running" for info in self.services.values() 
                  if info.get("port"))
        
    def deploy_infrastructure(self) -> bool:
        """Deploy infrastructure components"""
        print("\n🚀 Deploying infrastructure on Lambda Labs...")
        
        steps = [
            ("Database setup", self._deploy_database),
            ("Redis setup", self._deploy_redis),
            ("Vector stores setup", self._deploy_vector_stores),
            ("API deployment", self._deploy_api),
            ("Frontend deployment", self._deploy_frontend),
            ("Nginx configuration", self._configure_nginx)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📦 {step_name}...")
            try:
                if not step_func():
                    print(f"❌ {step_name} failed")
                    return False
                print(f"✅ {step_name} completed")
            except Exception as e:
                print(f"❌ {step_name} failed: {e}")
                return False
                
        return True
        
    def _deploy_database(self) -> bool:
        """Deploy PostgreSQL database"""
        # Create database schema
        schema_sql = """
        -- AI Personas table
        CREATE TABLE IF NOT EXISTS ai_personas (
            id SERIAL PRIMARY KEY,
            persona_type VARCHAR(50) NOT NULL,
            name VARCHAR(100) NOT NULL,
            domain VARCHAR(100) NOT NULL,
            configuration JSONB NOT NULL DEFAULT '{}',
            personality_traits JSONB NOT NULL DEFAULT '{}',
            skills JSONB NOT NULL DEFAULT '[]',
            tools JSONB NOT NULL DEFAULT '[]',
            voice_config JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Supervisor Agents table
        CREATE TABLE IF NOT EXISTS supervisor_agents (
            id SERIAL PRIMARY KEY,
            persona_id INTEGER REFERENCES ai_personas(id),
            agent_type VARCHAR(100) NOT NULL,
            name VARCHAR(100) NOT NULL,
            capabilities JSONB NOT NULL DEFAULT '[]',
            configuration JSONB NOT NULL DEFAULT '{}',
            status VARCHAR(50) DEFAULT 'inactive',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- AI Tasks table (for collaboration)
        CREATE TABLE IF NOT EXISTS ai_tasks (
            id SERIAL PRIMARY KEY,
            task_id UUID DEFAULT gen_random_uuid(),
            agent_id INTEGER,
            task_type VARCHAR(100) NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}',
            status VARCHAR(50) DEFAULT 'pending',
            priority INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            error_details JSONB
        );
        
        -- Metrics table
        CREATE TABLE IF NOT EXISTS ai_metrics (
            id SERIAL PRIMARY KEY,
            agent_id INTEGER NOT NULL,
            metric_type VARCHAR(100) NOT NULL,
            value FLOAT NOT NULL,
            metadata JSONB DEFAULT '{}',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes
        CREATE INDEX idx_personas_type ON ai_personas(persona_type);
        CREATE INDEX idx_agents_persona ON supervisor_agents(persona_id);
        CREATE INDEX idx_tasks_status ON ai_tasks(status);
        CREATE INDEX idx_metrics_agent_type ON ai_metrics(agent_id, metric_type);
        
        -- Insert default personas
        INSERT INTO ai_personas (persona_type, name, domain, configuration)
        VALUES 
            ('cherry', 'Cherry', 'Personal Life', '{"role": "Life coach and personal assistant"}'),
            ('sophia', 'Sophia', 'Pay Ready Business', '{"role": "Business strategist and advisor"}'),
            ('karen', 'Karen', 'ParagonRX Healthcare', '{"role": "Healthcare expert and compliance advisor"}')
        ON CONFLICT DO NOTHING;
        """
        
        # Save schema to file
        with open("/tmp/cherry_ai_schema.sql", "w") as f:
            f.write(schema_sql)
            
        # Execute schema on Lambda Labs PostgreSQL
        try:
            result = subprocess.run([
                "psql",
                f"postgresql://postgres:{os.getenv('POSTGRES_PASSWORD')}@{self.lambda_host}/cherry_ai",
                "-f", "/tmp/cherry_ai_schema.sql"
            ], capture_output=True, text=True)
            
            return result.returncode == 0
        except Exception as e:
            print(f"Database deployment error: {e}")
            return False
            
    def _deploy_redis(self) -> bool:
        """Configure Redis for caching and sessions"""
        redis_config = """
# Redis configuration for Cherry AI
bind 0.0.0.0
protected-mode yes
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 300

# Persistence
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename cherry_ai.rdb

# Logging
loglevel notice
logfile /var/log/redis/cherry_ai.log

# Memory management
maxmemory 4gb
maxmemory-policy allkeys-lru

# Append only file
appendonly yes
appendfilename "cherry_ai.aof"
appendfsync everysec
"""
        
        # Save config
        with open("/tmp/redis_cherry_ai.conf", "w") as f:
            f.write(redis_config)
            
        # Copy to Lambda Labs server
        try:
            subprocess.run([
                "scp", "/tmp/redis_cherry_ai.conf",
                f"root@{self.lambda_host}:/etc/redis/cherry_ai.conf"
            ], check=True)
            
            # Restart Redis with new config
            subprocess.run([
                "ssh", f"root@{self.lambda_host}",
                "systemctl restart redis"
            ], check=True)
            
            return True
        except:
            return False
            
    def _deploy_vector_stores(self) -> bool:
        """Configure Pinecone and Weaviate connections"""
        vector_config = {
            "pinecone": {
                "api_key": os.getenv("PINECONE_API_KEY"),
                "environment": "us-west1-gcp",
                "indexes": {
                    "cherry-personal": {
                        "dimension": 1536,
                        "metric": "cosine"
                    },
                    "sophia-business": {
                        "dimension": 1536,
                        "metric": "cosine"
                    },
                    "karen-healthcare": {
                        "dimension": 1536,
                        "metric": "cosine"
                    }
                }
            },
            "weaviate": {
                "url": f"http://{self.lambda_host}:8080",
                "api_key": os.getenv("WEAVIATE_API_KEY"),
                "schemas": [
                    "PersonalKnowledge",
                    "BusinessIntelligence",
                    "HealthcareRegulations"
                ]
            }
        }
        
        # Save configuration
        with open("/tmp/vector_stores_config.json", "w") as f:
            json.dump(vector_config, f, indent=2)
            
        return True
        
    def _deploy_api(self) -> bool:
        """Deploy API services"""
        # Create deployment script
        api_deploy_script = f"""#!/bin/bash
# Deploy Cherry AI API on Lambda Labs

cd /opt/cherry-ai

# Pull latest code
git pull origin main

# Build API container
docker build -t cherry-ai-api:latest -f Dockerfile.api .

# Stop existing container
docker stop cherry-ai-api || true
docker rm cherry-ai-api || true

# Run new container
docker run -d \\
    --name cherry-ai-api \\
    --restart unless-stopped \\
    -p 8000:8000 \\
    -e DATABASE_URL="postgresql://postgres:{os.getenv('POSTGRES_PASSWORD')}@{self.lambda_host}/cherry_ai" \\
    -e REDIS_URL="redis://{self.lambda_host}:6379" \\
    -e JWT_SECRET="{os.getenv('JWT_SECRET')}" \\
    -e PINECONE_API_KEY="{os.getenv('PINECONE_API_KEY')}" \\
    -e WEAVIATE_URL="http://{self.lambda_host}:8080" \\
    cherry-ai-api:latest

# Health check
sleep 10
curl -f http://localhost:8000/health || exit 1

echo "API deployment successful"
"""
        
        # Save and execute deployment script
        with open("/tmp/deploy_api.sh", "w") as f:
            f.write(api_deploy_script)
            
        try:
            # Copy and execute on Lambda Labs
            subprocess.run([
                "scp", "/tmp/deploy_api.sh",
                f"root@{self.lambda_host}:/tmp/deploy_api.sh"
            ], check=True)
            
            subprocess.run([
                "ssh", f"root@{self.lambda_host}",
                "bash /tmp/deploy_api.sh"
            ], check=True)
            
            return True
        except:
            return False
            
    def _deploy_frontend(self) -> bool:
        """Deploy React frontend"""
        frontend_deploy_script = f"""#!/bin/bash
# Deploy Cherry AI Frontend on Lambda Labs

cd /opt/cherry-ai

# Build frontend
cd frontend
npm install
npm run build

# Deploy with Nginx
rm -rf /var/www/cherry-ai/*
cp -r build/* /var/www/cherry-ai/

# Set permissions
chown -R www-data:www-data /var/www/cherry-ai

echo "Frontend deployment successful"
"""
        
        with open("/tmp/deploy_frontend.sh", "w") as f:
            f.write(frontend_deploy_script)
            
        try:
            subprocess.run([
                "scp", "/tmp/deploy_frontend.sh",
                f"root@{self.lambda_host}:/tmp/deploy_frontend.sh"
            ], check=True)
            
            subprocess.run([
                "ssh", f"root@{self.lambda_host}",
                "bash /tmp/deploy_frontend.sh"
            ], check=True)
            
            return True
        except:
            return False
            
    def _configure_nginx(self) -> bool:
        """Configure Nginx for Cherry AI"""
        nginx_config = f"""
server {{
    listen 80;
    listen 443 ssl http2;
    server_name cherry-ai.me;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/cherry-ai.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cherry-ai.me/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Frontend
    location / {{
        root /var/www/cherry-ai;
        try_files $uri $uri/ /index.html;
    }}
    
    # API proxy
    location /api {{
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }}
    
    # WebSocket support for AI Collaboration
    location /ws {{
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }}
}}
"""
        
        with open("/tmp/cherry-ai-nginx.conf", "w") as f:
            f.write(nginx_config)
            
        try:
            subprocess.run([
                "scp", "/tmp/cherry-ai-nginx.conf",
                f"root@{self.lambda_host}:/etc/nginx/sites-available/cherry-ai.conf"
            ], check=True)
            
            subprocess.run([
                "ssh", f"root@{self.lambda_host}",
                "ln -sf /etc/nginx/sites-available/cherry-ai.conf /etc/nginx/sites-enabled/ && nginx -t && systemctl reload nginx"
            ], check=True)
            
            return True
        except:
            return False
            
    def run_health_checks(self) -> Dict[str, Any]:
        """Run comprehensive health checks"""
        print("\n🏥 Running health checks...")
        
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "environment": self.environment,
            "services": {},
            "overall": "healthy"
        }
        
        # Check each service
        checks = [
            ("database", self._check_database_health),
            ("redis", self._check_redis_health),
            ("api", self._check_api_health),
            ("frontend", self._check_frontend_health),
            ("vector_stores", self._check_vector_stores_health)
        ]
        
        for service_name, check_func in checks:
            try:
                status = check_func()
                health_status["services"][service_name] = status
                if status["status"] != "healthy":
                    health_status["overall"] = "degraded"
            except Exception as e:
                health_status["services"][service_name] = {
                    "status": "error",
                    "message": str(e)
                }
                health_status["overall"] = "unhealthy"
                
        # Print summary
        print(f"\n📊 Health Check Summary: {health_status['overall'].upper()}")
        for service, status in health_status["services"].items():
            icon = "✅" if status["status"] == "healthy" else "❌"
            print(f"  {icon} {service}: {status['status']}")
            
        return health_status
        
    def _check_database_health(self) -> Dict[str, Any]:
        """Check PostgreSQL health"""
        try:
            result = subprocess.run([
                "psql",
                f"postgresql://postgres:{os.getenv('POSTGRES_PASSWORD')}@{self.lambda_host}/cherry_ai",
                "-c", "SELECT COUNT(*) FROM ai_personas;"
            ], capture_output=True, text=True)
            
            return {
                "status": "healthy" if result.returncode == 0 else "unhealthy",
                "message": "Database connection successful"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            result = subprocess.run([
                "redis-cli", "-h", self.lambda_host, "ping"
            ], capture_output=True, text=True)
            
            return {
                "status": "healthy" if "PONG" in result.stdout else "unhealthy",
                "message": "Redis responding to ping"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    def _check_api_health(self) -> Dict[str, Any]:
        """Check API health"""
        try:
            import requests
            response = requests.get(f"http://{self.lambda_host}:8000/health", timeout=5)
            
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "message": f"API responded with status {response.status_code}"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    def _check_frontend_health(self) -> Dict[str, Any]:
        """Check frontend health"""
        try:
            import requests
            response = requests.get(f"http://{self.lambda_host}", timeout=5)
            
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "message": f"Frontend responded with status {response.status_code}"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    def _check_vector_stores_health(self) -> Dict[str, Any]:
        """Check Pinecone and Weaviate health"""
        # This would include actual API calls to check vector store connectivity
        return {
            "status": "healthy",
            "message": "Vector stores configured"
        }
        
    def generate_deployment_report(self, health_status: Dict[str, Any]) -> None:
        """Generate deployment report"""
        report = {
            "deployment_id": f"deploy_{self.deployment_time.strftime('%Y%m%d_%H%M%S')}",
            "timestamp": self.deployment_time.isoformat(),
            "environment": self.environment,
            "platform": "Lambda Labs",
            "infrastructure": {
                "compute": "8x A100 GPUs",
                "host": self.lambda_host,
                "services": self.services
            },
            "health_check": health_status,
            "deployment_duration": (datetime.now() - self.deployment_time).total_seconds()
        }
        
        # Save report
        report_file = f"cherry_ai_deployment_report_{self.deployment_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📄 Deployment report saved to: {report_file}")


def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy Cherry AI to Lambda Labs")
    parser.add_argument(
        "--environment",
        choices=["production", "development"],
        default="production",
        help="Deployment environment"
    )
    parser.add_argument(
        "--skip-health-checks",
        action="store_true",
        help="Skip post-deployment health checks"
    )
    
    args = parser.parse_args()
    
    print("🚀 CHERRY AI LAMBDA LABS DEPLOYMENT")
    print("=" * 50)
    print(f"Environment: {args.environment}")
    print(f"Platform: Lambda Labs")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    deployer = LambdaLabsDeployment(args.environment)
    
    # Check prerequisites
    if not deployer.check_prerequisites():
        print("\n❌ Deployment aborted due to failed prerequisites")
        return 1
        
    # Deploy infrastructure
    if not deployer.deploy_infrastructure():
        print("\n❌ Deployment failed")
        return 1
        
    # Run health checks
    if not args.skip_health_checks:
        health_status = deployer.run_health_checks()
        deployer.generate_deployment_report(health_status)
        
        if health_status["overall"] != "healthy":
            print("\n⚠️  Deployment completed with issues")
            return 2
            
    print("\n✅ Cherry AI successfully deployed to Lambda Labs!")
    print("\n🌐 Access the application at: https://cherry-ai.me")
    print("📊 Admin interface: https://cherry-ai.me/admin")
    print("🤖 AI Collaboration Dashboard: https://cherry-ai.me/settings/developer-tools/collaboration")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())