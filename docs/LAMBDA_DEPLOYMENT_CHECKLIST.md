# Lambda Labs Deployment Checklist

## Pre-Deployment Verification
- [ ] Access Jupyter terminal: https://161b3292a006449cb3dcf794b2bd5d4e-0.lambdaspaces.com/
- [ ] Verify Lambda server IP: 150.136.94.139
- [ ] Confirm DNS points cherry-ai.me → 150.136.94.139

## Deployment Steps

### 1. Clean Slate Setup
```bash
cd /home/ubuntu
rm -rf orchestra-main  # Remove old deployment
git clone https://github.com/ai-cherry/orchestra-main.git
cd orchestra-main
git log --oneline -5  # Verify commit 4882588
```

### 2. Environment Configuration
```bash
# Create production config
cat > .env.production << EOF
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cherry_ai_production
POSTGRES_DB=cherry_ai_production
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis Stack (upgraded)
REDIS_URL=redis://localhost:6379

# Vector Stores
WEAVIATE_URL=http://localhost:8080
PINECONE_API_KEY=<your-pinecone-key>
PINECONE_ENV=us-east1-gcp

# AI Bridge & Context Server
AI_BRIDGE_PORT=8766
AI_CONTEXT_PORT=8765

# Domain
DOMAIN=cherry-ai.me
SERVER_IP=150.136.94.139

# API Keys
SECRET_KEY=c6NbaFwcC3UcBJNzJcZm9sNjdFV1sQKg3VBcCLLbDiQ=
EOF
```

### 3. Docker Compose Updates
```yaml
# Ensure docker-compose.production.yml includes:
services:
  redis:
    image: redis/redis-stack:latest  # Upgrade from redis:7-alpine
    ports:
      - "6379:6379"
      - "8001:8001"  # RedisInsight UI
    
  ai_context_server:
    build:
      context: .
      dockerfile: Dockerfile.context
    ports:
      - "8765:8765"
    environment:
      - CONTEXT_SERVER_PORT=8765
```

### 4. Service Deployment
```bash
# Stop any existing services
docker-compose down -v

# Deploy with production config
docker-compose -f docker-compose.production.yml --env-file .env.production up -d

# Verify all services
docker-compose ps
```

### 5. Nginx Configuration
```nginx
# Update nginx/production.conf for both endpoints:
location /bridge/ws {
    proxy_pass http://ai_bridge:8766/ws;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}

location /context/ws {
    proxy_pass http://ai_context_server:8765/context/ws;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### 6. SSL Setup
```bash
# Install certbot if needed
sudo apt update
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d cherry-ai.me -d www.cherry-ai.me
```

### 7. Testing Endpoints
```bash
# API Health
curl https://cherry-ai.me/api/health

# AI Bridge WebSocket
wscat -c wss://cherry-ai.me/bridge/ws

# AI Context Server
wscat -c wss://cherry-ai.me/context/ws
```

## Multi-Domain Architecture (Future)

### Container Isolation Strategy
```yaml
# docker-compose.multi-domain.yml
networks:
  cherry_network:
    driver: bridge
  sophia_network:
    driver: bridge
  karen_network:
    driver: bridge

services:
  # Cherry AI Services
  cherry_nginx:
    networks:
      - cherry_network
    environment:
      - DOMAIN=cherry-ai.me
  
  # Sophia AI Services  
  sophia_nginx:
    networks:
      - sophia_network
    environment:
      - DOMAIN=sophia-ai.me
  
  # Karen AI Services
  karen_nginx:
    networks:
      - karen_network
    environment:
      - DOMAIN=karen-ai.me
```

## Performance Optimizations

### PostgreSQL with pgvector
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create embeddings table
CREATE TABLE code_embeddings (
    id SERIAL PRIMARY KEY,
    file_path TEXT,
    embedding vector(1536),
    metadata JSONB
);
```

### Redis Stack Features
```python
# Use Redis for both caching and vector search
import redis
from redis.commands.search.field import VectorField, TextField

# Create vector index
schema = [
    TextField("file_path"),
    VectorField("embedding", "FLAT", {
        "TYPE": "FLOAT32",
        "DIM": 1536,
        "DISTANCE_METRIC": "COSINE"
    })
]
```

## Monitoring & Logs

### Real-time Monitoring
```bash
# Watch all services
docker-compose logs -f

# Monitor specific service
docker logs -f cherry_ai_bridge_prod

# System resources
htop

# GPU usage (if needed)
nvidia-smi
```

## Success Metrics
- [ ] All services show "healthy" status
- [ ] WebSocket connections work without 1011 errors
- [ ] SSL certificates valid for cherry-ai.me
- [ ] AI Bridge accepts connections from Manus AI
- [ ] Context Server indexes all code files
- [ ] Redis Stack operational with vector search 