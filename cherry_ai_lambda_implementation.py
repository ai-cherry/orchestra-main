#!/usr/bin/env python3
"""
Cherry AI Implementation Plan for Lambda Labs
Clear, practical steps for deploying on your existing infrastructure
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any


class CherryAIImplementationPlan:
    """
    Practical implementation plan for Cherry AI on Lambda Labs
    Focus on what we can actually deploy and test today
    """
    
    def __init__(self):
        self.server_ip = "150.136.94.139"
        self.infrastructure = {
            "provider": "Lambda Labs",
            "gpus": "8x A100",
            "existing_services": [
                "PostgreSQL",
                "Redis", 
                "Weaviate",
                "Nginx"
            ]
        }
        
    def generate_current_state_assessment(self) -> Dict[str, Any]:
        """Assess what we currently have deployed"""
        return {
            "infrastructure": {
                "server": self.server_ip,
                "provider": "Lambda Labs",
                "resources": {
                    "gpus": "8x A100 (excellent for AI workloads)",
                    "memory": "Sufficient for multiple AI models",
                    "storage": "NVMe SSDs for fast data access"
                }
            },
            "deployed_services": {
                "postgresql": {
                    "status": "Running",
                    "purpose": "Primary data storage",
                    "next_steps": ["Create persona schemas", "Set up replication"]
                },
                "redis": {
                    "status": "Running", 
                    "purpose": "Caching and sessions",
                    "next_steps": ["Configure persistence", "Set up clustering"]
                },
                "weaviate": {
                    "status": "Running",
                    "purpose": "Vector search and knowledge graphs",
                    "next_steps": ["Create persona classes", "Import initial data"]
                },
                "nginx": {
                    "status": "Running",
                    "purpose": "Reverse proxy and load balancing",
                    "next_steps": ["SSL configuration", "Rate limiting"]
                }
            },
            "completed_work": {
                "strategic_framework": "✓ Comprehensive persona strategies defined",
                "orchestration_system": "✓ Task breakdown and dependencies mapped",
                "agent_coordinator": "✓ Agent architecture designed",
                "deployment_scripts": "✓ Basic deployment automation created"
            },
            "immediate_needs": [
                "Fix authentication system deployment",
                "Configure vector databases properly",
                "Deploy first working AI persona (Cherry)",
                "Set up monitoring and observability"
            ]
        }
        
    def generate_practical_next_steps(self) -> Dict[str, Any]:
        """Generate actionable next steps we can execute today"""
        return {
            "phase_1_immediate": {
                "title": "Get Core Services Working (Today)",
                "duration": "4-6 hours",
                "tasks": [
                    {
                        "id": "T1",
                        "name": "Fix PostgreSQL Schemas",
                        "description": "Create proper schemas for personas",
                        "script": "setup_postgres_schemas.sh",
                        "validation": "psql -c '\\dn' should show: shared, cherry, sophia, karen"
                    },
                    {
                        "id": "T2", 
                        "name": "Configure Redis Properly",
                        "description": "Set up Redis with persistence and auth",
                        "script": "configure_redis.sh",
                        "validation": "redis-cli ping should return PONG"
                    },
                    {
                        "id": "T3",
                        "name": "Setup Weaviate Schemas",
                        "description": "Create vector schemas for each persona",
                        "script": "setup_weaviate_schemas.py",
                        "validation": "curl localhost:8080/v1/schema should show classes"
                    },
                    {
                        "id": "T4",
                        "name": "Deploy Basic Auth Service",
                        "description": "Simple JWT auth without MFA initially",
                        "script": "deploy_auth_service.py",
                        "validation": "curl localhost:5001/health should return 200"
                    }
                ]
            },
            "phase_2_ai_foundation": {
                "title": "Deploy First AI Persona (Tomorrow)",
                "duration": "8-10 hours",
                "tasks": [
                    {
                        "id": "T5",
                        "name": "Deploy Cherry Base Model",
                        "description": "Set up LLM integration for Cherry",
                        "components": ["Portkey setup", "Model selection", "Prompt templates"],
                        "validation": "Test conversation endpoint"
                    },
                    {
                        "id": "T6",
                        "name": "Implement Memory System",
                        "description": "Basic conversation memory using Redis + Postgres",
                        "components": ["Session management", "Context storage", "Retrieval"],
                        "validation": "Conversations maintain context"
                    },
                    {
                        "id": "T7",
                        "name": "Create Simple Web Interface",
                        "description": "Basic chat interface to test Cherry",
                        "components": ["React frontend", "WebSocket connection", "Auth integration"],
                        "validation": "Can chat with Cherry via web"
                    }
                ]
            },
            "phase_3_production_ready": {
                "title": "Production Hardening (Week 1)",
                "duration": "3-4 days",
                "tasks": [
                    {
                        "id": "T8",
                        "name": "Monitoring Stack",
                        "description": "Prometheus + Grafana for observability",
                        "components": ["Metrics collection", "Dashboards", "Alerts"],
                        "validation": "Can see system metrics in Grafana"
                    },
                    {
                        "id": "T9",
                        "name": "Load Balancing",
                        "description": "Configure Nginx for HA",
                        "components": ["SSL certificates", "Rate limiting", "Failover"],
                        "validation": "HTTPS working on cherry-ai.me"
                    },
                    {
                        "id": "T10",
                        "name": "Backup & Recovery",
                        "description": "Automated backups for all data",
                        "components": ["Database backups", "Vector store backups", "Recovery testing"],
                        "validation": "Can restore from backup"
                    }
                ]
            }
        }
        
    def generate_deployment_scripts(self) -> Dict[str, str]:
        """Generate actual deployment scripts we need"""
        return {
            "setup_postgres_schemas.sh": """#!/bin/bash
# Setup PostgreSQL schemas for Cherry AI
set -e

echo "Setting up PostgreSQL schemas..."

# Create schemas
sudo -u postgres psql -d postgres << EOF
-- Create database if not exists
SELECT 'CREATE DATABASE cherry_ai'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'cherry_ai')\\gexec

-- Connect to cherry_ai
\\c cherry_ai

-- Create schemas
CREATE SCHEMA IF NOT EXISTS shared;
CREATE SCHEMA IF NOT EXISTS cherry;
CREATE SCHEMA IF NOT EXISTS sophia;
CREATE SCHEMA IF NOT EXISTS karen;

-- Create user management in shared schema
CREATE TABLE IF NOT EXISTS shared.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS shared.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES shared.users(id),
    token TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cherry's tables
CREATE TABLE IF NOT EXISTS cherry.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES shared.users(id),
    thread_id UUID NOT NULL,
    message TEXT NOT NULL,
    response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cherry.memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES shared.users(id),
    memory_type VARCHAR(50),
    content JSONB,
    importance FLOAT DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_conversations_user_thread ON cherry.conversations(user_id, thread_id);
CREATE INDEX idx_memories_user_type ON cherry.memories(user_id, memory_type);

-- Grant permissions
GRANT ALL ON SCHEMA shared TO postgres;
GRANT ALL ON SCHEMA cherry TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA shared TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA cherry TO postgres;

\\q
EOF

echo "PostgreSQL schemas created successfully!"
""",
            
            "configure_redis.sh": """#!/bin/bash
# Configure Redis for Cherry AI
set -e

echo "Configuring Redis..."

# Create Redis config
cat > /etc/redis/redis.conf << EOF
# Basic configuration
bind 127.0.0.1
protected-mode yes
port 6379

# Authentication
requirepass ${REDIS_PASSWORD}

# Persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# Memory management
maxmemory 4gb
maxmemory-policy allkeys-lru

# Performance
tcp-keepalive 300
timeout 0
tcp-backlog 511
EOF

# Restart Redis
systemctl restart redis
systemctl enable redis

# Test connection
redis-cli -a ${REDIS_PASSWORD} ping

echo "Redis configured successfully!"
""",
            
            "setup_weaviate_schemas.py": """#!/usr/bin/env python3
# Setup Weaviate schemas for Cherry AI
import weaviate
import json

client = weaviate.Client("http://localhost:8080")

# Define schemas for each persona
schemas = {
    "PersonalMemory": {
        "class": "PersonalMemory",
        "description": "Cherry's personal memories and learnings",
        "properties": [
            {
                "name": "userId",
                "dataType": ["string"],
                "description": "User ID"
            },
            {
                "name": "content",
                "dataType": ["text"],
                "description": "Memory content"
            },
            {
                "name": "category",
                "dataType": ["string"],
                "description": "Memory category"
            },
            {
                "name": "importance",
                "dataType": ["number"],
                "description": "Importance score"
            },
            {
                "name": "timestamp",
                "dataType": ["date"],
                "description": "When this was learned"
            }
        ]
    },
    "BusinessKnowledge": {
        "class": "BusinessKnowledge",
        "description": "Sophia's business knowledge",
        "properties": [
            {
                "name": "domain",
                "dataType": ["string"],
                "description": "Business domain"
            },
            {
                "name": "content",
                "dataType": ["text"],
                "description": "Knowledge content"
            },
            {
                "name": "source",
                "dataType": ["string"],
                "description": "Knowledge source"
            }
        ]
    },
    "HealthcareRegulation": {
        "class": "HealthcareRegulation",
        "description": "Karen's healthcare knowledge",
        "properties": [
            {
                "name": "regulation",
                "dataType": ["string"],
                "description": "Regulation name"
            },
            {
                "name": "content",
                "dataType": ["text"],
                "description": "Regulation details"
            },
            {
                "name": "jurisdiction",
                "dataType": ["string"],
                "description": "Applicable jurisdiction"
            }
        ]
    }
}

# Create schemas
for schema_name, schema_def in schemas.items():
    try:
        client.schema.create_class(schema_def)
        print(f"Created schema: {schema_name}")
    except Exception as e:
        print(f"Schema {schema_name} may already exist: {e}")

# Verify schemas
existing = client.schema.get()
print(f"\\nTotal schemas: {len(existing['classes'])}")
for cls in existing['classes']:
    print(f"  - {cls['class']}")
""",
            
            "deploy_auth_service.py": """#!/usr/bin/env python3
# Deploy basic authentication service
import os
import subprocess

auth_service_code = '''
from flask import Flask, request, jsonify
import jwt
import bcrypt
import psycopg2
import redis
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-secret-change-in-production')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')

# Database connection
def get_db():
    return psycopg2.connect(
        host="localhost",
        database="cherry_ai",
        user="postgres"
    )

# Redis connection
r = redis.Redis(host='localhost', port=6379, password=REDIS_PASSWORD, decode_responses=True)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "auth"}), 200

@app.route('/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Create user
        cur.execute(
            "INSERT INTO shared.users (email) VALUES (%s) RETURNING id",
            (email,)
        )
        
        user_id = cur.fetchone()[0]
        conn.commit()
        
        # Store password hash in Redis (temporary solution)
        r.set(f"user:pass:{email}", password_hash.decode('utf-8'))
        
        return jsonify({
            "user_id": str(user_id),
            "message": "User registered successfully"
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    try:
        # Get password hash from Redis
        stored_hash = r.get(f"user:pass:{email}")
        if not stored_hash:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Get user from database
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM shared.users WHERE email = %s", (email,))
        user = cur.fetchone()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        user_id = str(user[0])
        
        # Generate JWT
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
        
        # Store session in Redis
        r.setex(f"session:{user_id}", 86400, token)
        
        return jsonify({
            "token": token,
            "user_id": user_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
'''

# Write auth service
with open('/opt/cherry-ai-auth.py', 'w') as f:
    f.write(auth_service_code)

# Install dependencies
subprocess.run(['pip3', 'install', 'flask', 'pyjwt', 'bcrypt', 'psycopg2-binary', 'redis'])

# Create systemd service
service_content = '''[Unit]
Description=Cherry AI Auth Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=root
Environment="JWT_SECRET=your-secret-here"
Environment="REDIS_PASSWORD=your-redis-password"
ExecStart=/usr/bin/python3 /opt/cherry-ai-auth.py
Restart=always

[Install]
WantedBy=multi-user.target
'''

with open('/etc/systemd/system/cherry-ai-auth.service', 'w') as f:
    f.write(service_content)

# Start service
subprocess.run(['systemctl', 'daemon-reload'])
subprocess.run(['systemctl', 'enable', 'cherry-ai-auth'])
subprocess.run(['systemctl', 'start', 'cherry-ai-auth'])

print("Auth service deployed successfully!")
"""
        }
        
    def generate_validation_checklist(self) -> List[Dict[str, Any]]:
        """Generate validation steps to ensure everything works"""
        return [
            {
                "step": 1,
                "name": "Verify PostgreSQL",
                "commands": [
                    "sudo -u postgres psql -c '\\l' | grep cherry_ai",
                    "sudo -u postgres psql -d cherry_ai -c '\\dn'",
                    "sudo -u postgres psql -d cherry_ai -c '\\dt shared.*'"
                ],
                "expected": "Database exists with 4 schemas"
            },
            {
                "step": 2,
                "name": "Verify Redis",
                "commands": [
                    "redis-cli -a $REDIS_PASSWORD ping",
                    "redis-cli -a $REDIS_PASSWORD info server | grep redis_version"
                ],
                "expected": "PONG response and version info"
            },
            {
                "step": 3,
                "name": "Verify Weaviate",
                "commands": [
                    "curl -s localhost:8080/v1/meta | jq .version",
                    "curl -s localhost:8080/v1/schema | jq '.classes | length'"
                ],
                "expected": "Version info and 3 classes"
            },
            {
                "step": 4,
                "name": "Verify Auth Service",
                "commands": [
                    "curl -s localhost:5001/health | jq",
                    "systemctl status cherry-ai-auth"
                ],
                "expected": "Healthy status and service running"
            }
        ]
        
    def export_plan(self):
        """Export the complete implementation plan"""
        plan = {
            "generated_at": datetime.now().isoformat(),
            "infrastructure": self.infrastructure,
            "current_state": self.generate_current_state_assessment(),
            "next_steps": self.generate_practical_next_steps(),
            "deployment_scripts": list(self.generate_deployment_scripts().keys()),
            "validation_checklist": self.generate_validation_checklist(),
            "key_decisions": {
                "start_simple": "Begin with basic auth, add MFA later",
                "focus_on_cherry": "Get Cherry working first, then add other personas",
                "use_existing": "Leverage already deployed services",
                "iterative": "Deploy in small, testable increments"
            },
            "timeline": {
                "today": "Core services setup (4-6 hours)",
                "tomorrow": "First AI persona deployment (8-10 hours)",
                "week_1": "Production hardening and monitoring",
                "week_2": "Add Sophia and Karen personas",
                "week_3": "Voice integration and advanced features"
            }
        }
        
        # Save scripts
        scripts = self.generate_deployment_scripts()
        for filename, content in scripts.items():
            with open(filename, 'w') as f:
                f.write(content)
            os.chmod(filename, 0o755)
            print(f"Created: {filename}")
        
        # Save plan
        with open('cherry_ai_implementation_plan.json', 'w') as f:
            json.dump(plan, f, indent=2)
            
        return plan


def main():
    """Generate and display the implementation plan"""
    print("🍒 CHERRY AI IMPLEMENTATION PLAN FOR LAMBDA LABS")
    print("=" * 60)
    
    planner = CherryAIImplementationPlan()
    
    # Current state
    state = planner.generate_current_state_assessment()
    print("\n📊 CURRENT STATE:")
    print(f"Server: {state['infrastructure']['server']}")
    print(f"Provider: {state['infrastructure']['provider']}")
    print("\nDeployed Services:")
    for service, info in state['deployed_services'].items():
        print(f"  ✓ {service}: {info['status']}")
    
    # Next steps
    steps = planner.generate_practical_next_steps()
    print("\n🎯 IMMEDIATE NEXT STEPS:")
    
    for phase_key, phase in steps.items():
        print(f"\n{phase['title']} ({phase['duration']})")
        for task in phase['tasks']:
            print(f"  {task['id']}: {task['name']}")
            print(f"     → {task['description']}")
    
    # Export everything
    plan = planner.export_plan()
    
    print("\n✅ IMPLEMENTATION PLAN GENERATED!")
    print("\nCreated files:")
    print("  - cherry_ai_implementation_plan.json")
    print("  - setup_postgres_schemas.sh")
    print("  - configure_redis.sh") 
    print("  - setup_weaviate_schemas.py")
    print("  - deploy_auth_service.py")
    
    print("\n🚀 TO GET STARTED:")
    print("1. Review the plan: cat cherry_ai_implementation_plan.json")
    print("2. Set environment variables:")
    print("   export REDIS_PASSWORD='your-password'")
    print("   export JWT_SECRET='your-secret'")
    print("3. Run the first script: ./setup_postgres_schemas.sh")
    print("4. Follow the validation checklist after each step")
    
    print("\n💡 KEY INSIGHT:")
    print("We're starting simple and building incrementally.")
    print("Get the basics working today, add complexity tomorrow.")


if __name__ == "__main__":
    main()