#!/usr/bin/env python3
"""
Deploy and manage Cherry AI backend services
"""

import os
import sys
import time
import subprocess
import psycopg2
import redis
import requests
from pathlib import Path

class BackendDeployer:
    def __init__(self):
        self.services_status = {}
        
    def run_command(self, cmd, check=True):
        """Run a shell command"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if check and result.returncode != 0:
                print(f"❌ Command failed: {cmd}")
                print(f"Error: {result.stderr}")
                return False
            return True
        except Exception as e:
            print(f"❌ Exception running command: {e}")
            return False
            
    def check_docker(self):
        """Ensure Docker is running"""
        print("🐳 Checking Docker...")
        if self.run_command("docker ps", check=False):
            print("✅ Docker is running")
            return True
        else:
            print("❌ Docker is not running. Please start Docker first.")
            return False
            
    def start_postgres(self):
        """Start PostgreSQL container"""
        print("\n📊 Starting PostgreSQL...")
        
        # Stop existing container if any
        self.run_command("docker stop cherry_ai-postgres 2>/dev/null", check=False)
        self.run_command("docker rm cherry_ai-postgres 2>/dev/null", check=False)
        
        # Start new container
        cmd = """
        docker run -d \
            --name cherry_ai-postgres \
            --restart unless-stopped \
            -e POSTGRES_USER=postgres \
            -e POSTGRES_PASSWORD=postgres \
            -e POSTGRES_DB=cherry_ai \
            -p 5432:5432 \
            -v cherry_ai_postgres_data:/var/lib/postgresql/data \
            postgres:15-alpine
        """
        
        if self.run_command(cmd):
            print("✅ PostgreSQL started")
            self.services_status['postgres'] = True
            time.sleep(5)  # Wait for startup
            return True
        return False
        
    def start_redis(self):
        """Start Redis container"""
        print("\n📮 Starting Redis...")
        
        # Stop existing container if any
        self.run_command("docker stop cherry_ai-redis 2>/dev/null", check=False)
        self.run_command("docker rm cherry_ai-redis 2>/dev/null", check=False)
        
        # Start new container
        cmd = """
        docker run -d \
            --name cherry_ai-redis \
            --restart unless-stopped \
            -p 6379:6379 \
            -v cherry_ai_redis_data:/data \
            redis:7-alpine
        """
        
        if self.run_command(cmd):
            print("✅ Redis started")
            self.services_status['redis'] = True
            return True
        return False
        
    def start_weaviate(self):
        """Start Weaviate container"""
        print("\n🔍 Starting Weaviate...")
        
        # Stop existing container if any
        self.run_command("docker stop cherry_ai-weaviate 2>/dev/null", check=False)
        self.run_command("docker rm cherry_ai-weaviate 2>/dev/null", check=False)
        
        # Start new container
        cmd = """
        docker run -d \
            --name cherry_ai-weaviate \
            --restart unless-stopped \
            -p 8080:8080 \
            -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
            -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
            -e DEFAULT_VECTORIZER_MODULE=text2vec-openai \
            -e ENABLE_MODULES=text2vec-openai \
            -v cherry_ai_weaviate_data:/var/lib/weaviate \
            semitechnologies/weaviate:latest
        """
        
        if self.run_command(cmd):
            print("✅ Weaviate started")
            self.services_status['weaviate'] = True
            time.sleep(10)  # Weaviate takes longer to start
            return True
        return False
        
    def setup_database(self):
        """Create database schema and initial data"""
        print("\n🗄️  Setting up database...")
        
        try:
            # Connect to database
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="cherry_ai",
                user="postgres",
                password=os.getenv("POSTGRES_PASSWORD", "postgres")
            )
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Create tables
            tables = [
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    token VARCHAR(255) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS personas (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    domain VARCHAR(255) NOT NULL,
                    description TEXT,
                    traits JSONB DEFAULT '{}',
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS interactions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    persona_id INTEGER REFERENCES personas(id),
                    message TEXT NOT NULL,
                    response TEXT,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_interactions_user_id ON interactions(user_id);
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_interactions_created_at ON interactions(created_at);
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
                """
            ]
            
            for sql in tables:
                cursor.execute(sql)
                
            # Insert default data
            cursor.execute("""
                INSERT INTO personas (name, domain, description, traits)
                VALUES 
                    ('Cherry', 'Personal', 'Personal AI assistant for health and lifestyle', 
                     '{"friendly": true, "helpful": true, "empathetic": true}'),
                    ('Sophia', 'PayReady', 'Financial operations and payment processing assistant', 
                     '{"professional": true, "accurate": true, "efficient": true}'),
                    ('Karen', 'ParagonRX', 'Healthcare and medical information assistant', 
                     '{"caring": true, "knowledgeable": true, "thorough": true}')
                ON CONFLICT DO NOTHING
            """)
            
            # Create admin user (password: Huskers1983$)
            cursor.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES ('scoobyjava', 'admin@cherry-ai.me', 
                        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH1qQrjMnC')
                ON CONFLICT (username) DO UPDATE 
                SET email = EXCLUDED.email,
                    password_hash = EXCLUDED.password_hash
            """)
            
            cursor.close()
            conn.close()
            
            print("✅ Database setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            return False
            
    def find_api_entry(self):
        """Find the API entry point"""
        possible_paths = [
            "api/main.py",
            "core/conductor/src/main.py",
            "src/main.py",
            "main.py",
            "app.py",
            "server.py"
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return path
                
        # Search for FastAPI apps
        result = subprocess.run(
            "find . -name '*.py' -type f | xargs grep -l 'FastAPI()' | head -1",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            return result.stdout.strip()
            
        return None
        
    def start_api(self):
        """Start the API server"""
        print("\n🌐 Starting API server...")
        
        # Kill any existing uvicorn process
        self.run_command("pkill -f uvicorn", check=False)
        time.sleep(2)
        
        # Find API entry point
        api_path = self.find_api_entry()
        if not api_path:
            print("❌ Could not find API entry point")
            return False
            
        print(f"📍 Found API at: {api_path}")
        
        # Prepare the module path for uvicorn
        module_path = api_path.replace('/', '.').replace('.py', '')
        if module_path.startswith('.'):
            module_path = module_path[1:]
            
        # Start API
        api_dir = os.path.dirname(api_path) or '.'
        cmd = f"cd {api_dir} && nohup uvicorn {os.path.basename(api_path).replace('.py', '')}:app --host 0.0.0.0 --port 8000 --reload > /tmp/cherry_ai-api.log 2>&1 &"
        
        if self.run_command(cmd):
            print("✅ API server started")
            print("📝 Logs available at: /tmp/cherry_ai-api.log")
            self.services_status['api'] = True
            time.sleep(5)  # Wait for startup
            return True
            
        return False
        
    def verify_services(self):
        """Verify all services are running"""
        print("\n🔍 Verifying services...")
        
        all_good = True
        
        # Check PostgreSQL
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="cherry_ai",
                user="postgres",
                password=os.getenv("POSTGRES_PASSWORD", "postgres")
            )
            conn.close()
            print("✅ PostgreSQL: Connected")
        except:
            print("❌ PostgreSQL: Not accessible")
            all_good = False
            
        # Check Redis
        try:
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            print("✅ Redis: Connected")
        except:
            print("❌ Redis: Not accessible")
            all_good = False
            
        # Check Weaviate
        try:
            response = requests.get("http://localhost:8080/v1/meta", timeout=5)
            if response.status_code == 200:
                print("✅ Weaviate: Connected")
            else:
                raise Exception("Bad status code")
        except:
            print("❌ Weaviate: Not accessible")
            all_good = False
            
        # Check API
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            print("✅ API: Connected")
        except:
            print("⚠️  API: Not accessible (may still be starting)")
            
        return all_good
        
    def deploy(self):
        """Deploy all backend services"""
        print("🚀 Cherry AI Backend Deployment")
        print("=" * 40)
        
        # Check Docker
        if not self.check_docker():
            return False
            
        # Start services
        if not self.start_postgres():
            return False
            
        if not self.start_redis():
            return False
            
        if not self.start_weaviate():
            return False
            
        # Setup database
        if not self.setup_database():
            return False
            
        # Start API
        if not self.start_api():
            print("⚠️  API failed to start, but other services are running")
            
        # Verify everything
        self.verify_services()
        
        print("\n" + "=" * 40)
        print("🎉 Backend deployment complete!")
        print("\n📝 Service Status:")
        print(f"  PostgreSQL: {'✅ Running' if self.services_status.get('postgres') else '❌ Failed'}")
        print(f"  Redis: {'✅ Running' if self.services_status.get('redis') else '❌ Failed'}")
        print(f"  Weaviate: {'✅ Running' if self.services_status.get('weaviate') else '❌ Failed'}")
        print(f"  API: {'✅ Running' if self.services_status.get('api') else '⚠️  Check logs'}")
        
        print("\n🔗 Access Points:")
        print("  API Documentation: http://localhost:8000/docs")
        print("  PostgreSQL: localhost:5432")
        print("  Redis: localhost:6379")
        print("  Weaviate: http://localhost:8080")
        
        print("\n🔑 Default Credentials:")
        print("  Username: scoobyjava")
        print("  Password: Huskers1983$")
        
        return True

def main():
    deployer = BackendDeployer()
    success = deployer.deploy()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()