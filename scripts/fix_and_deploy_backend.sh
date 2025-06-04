#!/bin/bash
# Comprehensive Backend Fix and Deploy Script

set -e

echo "🚀 Cherry AI Backend Fix and Deploy"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    case $1 in
        "error")
            echo -e "${RED}❌ $2${NC}"
            ;;
        "success")
            echo -e "${GREEN}✅ $2${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}⚠️  $2${NC}"
            ;;
        *)
            echo "$2"
            ;;
    esac
}

# 1. Fix Weaviate connection issue
print_status "info" "🔧 Starting Weaviate service..."
docker run -d \
  --name weaviate \
  --restart unless-stopped \
  -p 8080:8080 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  -e DEFAULT_VECTORIZER_MODULE=text2vec-openai \
  -e ENABLE_MODULES=text2vec-openai \
  -v weaviate_data:/var/lib/weaviate \
  semitechnologies/weaviate:latest 2>/dev/null || print_status "warning" "Weaviate already running"

# 2. Ensure all Docker services are running
print_status "info" "🐳 Starting Docker services..."
if [ -f "docker-compose.prod.yml" ]; then
    docker-compose -f docker-compose.prod.yml up -d
elif [ -f "docker-compose.yml" ]; then
    docker-compose up -d
else
    print_status "warning" "No docker-compose file found, starting services manually..."
    
    # Start PostgreSQL
    docker run -d \
        --name postgres \
        --restart unless-stopped \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_DB=cherry_ai \
        -p 5432:5432 \
        -v postgres_data:/var/lib/postgresql/data \
        postgres:15 2>/dev/null || print_status "warning" "PostgreSQL already running"
    
    # Start Redis
    docker run -d \
        --name redis \
        --restart unless-stopped \
        -p 6379:6379 \
        -v redis_data:/data \
        redis:7-alpine 2>/dev/null || print_status "warning" "Redis already running"
fi

# Wait for services to be ready
print_status "info" "⏳ Waiting for services to be ready..."
sleep 10

# 3. Create missing database tables
print_status "info" "📊 Creating database tables..."
python3 << 'EOF'
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

try:
    # Connect to database
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/cherry_ai")
    conn = psycopg2.connect(db_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
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
        """
    ]
    
    for table_sql in tables:
        cursor.execute(table_sql)
        
    # Insert default personas
    cursor.execute("""
        INSERT INTO personas (name, domain, description, traits)
        VALUES 
            ('Cherry', 'Personal', 'Personal AI assistant', '{"friendly": true, "helpful": true}'),
            ('Sophia', 'PayReady', 'Financial operations assistant', '{"professional": true, "accurate": true}'),
            ('Karen', 'ParagonRX', 'Healthcare assistant', '{"caring": true, "knowledgeable": true}')
        ON CONFLICT DO NOTHING
    """)
    
    # Create default admin user
    cursor.execute("""
        INSERT INTO users (username, email, password_hash)
        VALUES ('scoobyjava', 'admin@cherry-ai.me', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH1qQrjMnC')
        ON CONFLICT (username) DO NOTHING
    """)
    
    print("✅ Database tables created successfully")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Database setup error: {e}")
EOF

# 4. Install missing Python dependencies
print_status "info" "📦 Installing Python dependencies..."
pip install -q bcrypt psycopg2-binary redis requests python-dotenv pytest

# 5. Install security dependencies
if [ -f "requirements/security.txt" ]; then
    pip install -q -r requirements/security.txt
fi

# 6. Create API startup script if it doesn't exist
if [ ! -f "scripts/start_api.sh" ]; then
    print_status "info" "📝 Creating API startup script..."
    cat > scripts/start_api.sh << 'EOF'
#!/bin/bash
# Start cherry_ai API Server

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Find and start the API
if [ -d "api" ] && [ -f "api/main.py" ]; then
    cd api
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
elif [ -d "core/conductor/src" ] && [ -f "core/conductor/src/main.py" ]; then
    cd core/conductor/src
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
elif [ -f "main.py" ]; then
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "❌ Could not find API entry point"
    exit 1
fi
EOF
    chmod +x scripts/start_api.sh
fi

# 7. Start the API server
print_status "info" "🌐 Starting API server..."
# Kill any existing API process
pkill -f "uvicorn" 2>/dev/null || true

# Start API in background
nohup bash scripts/start_api.sh > api.log 2>&1 &
API_PID=$!
print_status "success" "API server started with PID: $API_PID"

# Wait for API to be ready
print_status "info" "⏳ Waiting for API to be ready..."
sleep 5

# 8. Verify everything is working
print_status "info" "🔍 Verifying deployment..."
python3 scripts/validate_and_deploy_backend.py

# 9. Create systemd service for production
if [ "$1" == "--production" ]; then
    print_status "info" "🚀 Setting up production services..."
    
    # Create systemd service
    sudo tee /etc/systemd/system/cherry_ai-api.service > /dev/null << EOF
[Unit]
Description=Cherry AI API Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/cherry_ai-main
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/local/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable cherry_ai-api
    sudo systemctl start cherry_ai-api
    
    print_status "success" "Production service configured"
fi

print_status "success" "🎉 Backend deployment complete!"
print_status "info" "📝 Next steps:"
echo "1. Check api.log for any errors"
echo "2. Access API at http://localhost:8000/docs"
echo "3. Run 'python3 scripts/validate_and_deploy_backend.py' to verify"
echo "4. For production: run this script with --production flag"