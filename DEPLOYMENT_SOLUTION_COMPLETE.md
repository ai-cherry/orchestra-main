# Orchestra AI - Complete Deployment Solution

## 🎯 Based on Comprehensive Analysis

### Current State Summary:
- ❌ Lambda Labs instances NOT running Orchestra AI (returning "Not Found")
- ❌ Vercel trying to run complex FastAPI as serverless (FUNCTION_INVOCATION_FAILED)
- ❌ Database models file is empty (breaking imports)
- ❌ Fundamental architecture mismatch

## 🚀 RECOMMENDED SOLUTION: Option 1 - Lambda Labs Full Deployment

### Phase 1: Fix Local Codebase

#### 1.1 Restore Database Models
First, we need to fix the empty models file:

```python
# api/database/models.py
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Integer, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    sessions = relationship("Session", back_populates="user")
    personas = relationship("Persona", back_populates="user")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="sessions")

class Persona(Base):
    __tablename__ = "personas"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    description = Column(Text)
    configuration = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="personas")
```

#### 1.2 Create Deployment Script for Lambda Labs
```bash
#!/bin/bash
# deploy_to_lambda.sh

# Configuration
LAMBDA_HOST="150.136.94.139"
LAMBDA_USER="ubuntu"
SSH_KEY="~/.ssh/lambda_labs_key"

# Step 1: Connect to Lambda Labs
echo "Connecting to Lambda Labs..."
ssh -i $SSH_KEY $LAMBDA_USER@$LAMBDA_HOST << 'ENDSSH'

# Step 2: Clone/Update Repository
cd /home/ubuntu
if [ -d "orchestra-main" ]; then
    cd orchestra-main
    git pull
else
    git clone https://github.com/ai-cherry/orchestra-main.git
    cd orchestra-main
fi

# Step 3: Install System Dependencies
sudo apt-get update
sudo apt-get install -y docker.io docker-compose python3.11 python3.11-venv

# Step 4: Set up Environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Step 5: Start Services with Docker Compose
docker-compose -f docker-compose.yml up -d

# Step 6: Verify Services
sleep 10
curl http://localhost:8000/health
curl http://localhost:8003/health

ENDSSH
```

### Phase 2: Vercel Configuration (Frontend Only)

#### 2.1 Update vercel.json for Frontend-Only Deployment
```json
{
  "version": 2,
  "buildCommand": "cd modern-admin && pnpm install && pnpm run build",
  "outputDirectory": "modern-admin/dist",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://150.136.94.139:8000/api/:path*"
    }
  ]
}
```

#### 2.2 Remove Python Functions from Vercel
- Delete any Python files in api/ that Vercel is trying to run
- Keep only the frontend build

### Phase 3: Infrastructure Setup on Lambda Labs

#### 3.1 Docker Compose Configuration
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: orchestra
      POSTGRES_USER: orchestra
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  weaviate:
    image: semitechnologies/weaviate:latest
    environment:
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
    volumes:
      - weaviate_data:/var/lib/weaviate
    ports:
      - "8080:8080"

  api:
    build: .
    environment:
      DATABASE_URL: postgresql://orchestra:${DB_PASSWORD}@postgres:5432/orchestra
      REDIS_URL: redis://redis:6379
      WEAVIATE_URL: http://weaviate:8080
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - weaviate
    command: uvicorn main_api:app --host 0.0.0.0 --port 8000

volumes:
  postgres_data:
  weaviate_data:
```

#### 3.2 Nginx Configuration for Lambda Labs
```nginx
server {
    listen 80;
    server_name 150.136.94.139;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Phase 4: Deployment Steps

1. **Fix Local Code**
   ```bash
   # Restore models.py with the content above
   # Test locally
   python -m api.main
   ```

2. **Deploy to Lambda Labs**
   ```bash
   # Copy deployment script
   scp deploy_to_lambda.sh ubuntu@150.136.94.139:~/
   
   # Run deployment
   ssh ubuntu@150.136.94.139 'bash deploy_to_lambda.sh'
   ```

3. **Deploy Frontend to Vercel**
   ```bash
   # Remove Python functions
   rm -rf api/*.py  # Keep only proxy.js if needed
   
   # Deploy
   vercel --prod
   ```

## 🎯 Alternative: Option 2 - Simplified Serverless

If Lambda Labs deployment is not feasible, create a simplified API:

### Simplified API (api/simple.py)
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "orchestra-api-simple"}

@app.get("/api/personas")
async def get_personas():
    # Return mock data without database
    return [
        {"id": "1", "name": "Assistant", "role": "helper"},
        {"id": "2", "name": "Expert", "role": "advisor"}
    ]
```

### Vercel Serverless Configuration
```json
{
  "functions": {
    "api/simple.py": {
      "runtime": "python3.9"
    }
  },
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api/simple"
    }
  ]
}
```

## 🚨 Immediate Actions

1. **Choose deployment strategy**:
   - Full Lambda Labs (recommended for full functionality)
   - Simplified Serverless (quick but limited)

2. **Fix the broken code**:
   - Restore models.py
   - Fix import chains
   - Test locally first

3. **Deploy properly**:
   - Stop mixing architectures
   - Use appropriate infrastructure

## 📊 Decision Matrix

| Feature | Lambda Labs Full | Serverless Simple |
|---------|-----------------|-------------------|
| Database Support | ✅ Full | ❌ None |
| Vector Search | ✅ Weaviate | ❌ None |
| File Processing | ✅ Full | ❌ Limited |
| Background Tasks | ✅ Full | ❌ None |
| WebSockets | ✅ Full | ❌ None |
| Cost | 💰 Higher | 💰 Lower |
| Complexity | 🔧 High | 🔧 Low |
| Scalability | 📈 Manual | 📈 Automatic |

Choose based on your requirements! 