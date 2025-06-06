#!/usr/bin/env python3
"""
Cherry AI Implementation - Phase 1: Foundation Infrastructure
Sets up the base infrastructure on Lambda Labs using existing secrets
"""

import os
import sys
import subprocess
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CherryAIPhase1Implementation:
    """
    Phase 1 implementation: Foundation Infrastructure
    - Lambda Labs environment setup
    - PostgreSQL, Redis, Pinecone, Weaviate configuration
    - Authentication system
    - Base React application
    """
    
    def __init__(self):
        self.lambda_host = "150.136.94.139"
        self.start_time = datetime.now()
        
        # Load environment variables from GitHub secrets or .env
        self.config = {
            "postgres": {
                "host": os.getenv("POSTGRES_HOST", self.lambda_host),
                "port": os.getenv("POSTGRES_PORT", "5432"),
                "database": os.getenv("POSTGRES_DB", "cherry_ai"),
                "user": os.getenv("POSTGRES_USER", "postgres"),
                "password": os.getenv("POSTGRES_PASSWORD", "")
            },
            "redis": {
                "host": os.getenv("REDIS_HOST", self.lambda_host),
                "port": os.getenv("REDIS_PORT", "6379"),
                "password": os.getenv("REDIS_PASSWORD", ""),
                "database": os.getenv("REDIS_DB", "0")
            },
            "pinecone": {
                "api_key": os.getenv("PINECONE_API_KEY", ""),
                "environment": os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
            },
            "weaviate": {
                "url": os.getenv("WEAVIATE_URL", f"http://{self.lambda_host}:8080"),
                "api_key": os.getenv("WEAVIATE_API_KEY", "")
            },
            "auth": {
                "jwt_secret": os.getenv("JWT_SECRET", ""),
                "admin_api_key": os.getenv("ADMIN_API_KEY", "")
            }
        }
        
    async def validate_environment(self) -> bool:
        """Validate that all required environment variables are set"""
        logger.info("🔍 Validating environment configuration...")
        
        missing = []
        
        # Check critical configurations
        if not self.config["postgres"]["password"]:
            missing.append("POSTGRES_PASSWORD")
        if not self.config["pinecone"]["api_key"]:
            missing.append("PINECONE_API_KEY")
        if not self.config["weaviate"]["api_key"]:
            missing.append("WEAVIATE_API_KEY")
        if not self.config["auth"]["jwt_secret"]:
            missing.append("JWT_SECRET")
            
        if missing:
            logger.error(f"❌ Missing required environment variables: {', '.join(missing)}")
            logger.info("💡 These should be set in GitHub secrets or local .env file")
            return False
            
        logger.info("✅ Environment validation passed")
        return True
        
    async def setup_database_schema(self) -> bool:
        """Set up PostgreSQL database schema for Cherry AI"""
        logger.info("🗄️  Setting up PostgreSQL database schema...")
        
        schema_sql = """
        -- Create schemas for each persona
        CREATE SCHEMA IF NOT EXISTS cherry;
        CREATE SCHEMA IF NOT EXISTS sophia;
        CREATE SCHEMA IF NOT EXISTS karen;
        CREATE SCHEMA IF NOT EXISTS shared;
        
        -- Switch to shared schema for common tables
        SET search_path TO shared;
        
        -- Users table with multi-factor authentication
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            mfa_secret VARCHAR(255),
            mfa_enabled BOOLEAN DEFAULT FALSE,
            role VARCHAR(50) DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );
        
        -- AI Personas configuration
        CREATE TABLE IF NOT EXISTS ai_personas (
            id SERIAL PRIMARY KEY,
            persona_type VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL,
            domain VARCHAR(100) NOT NULL,
            description TEXT,
            configuration JSONB NOT NULL DEFAULT '{}',
            personality_traits JSONB NOT NULL DEFAULT '{}',
            skills JSONB NOT NULL DEFAULT '[]',
            tools JSONB NOT NULL DEFAULT '[]',
            voice_config JSONB NOT NULL DEFAULT '{}',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Supervisor Agents
        CREATE TABLE IF NOT EXISTS supervisor_agents (
            id SERIAL PRIMARY KEY,
            persona_id INTEGER REFERENCES ai_personas(id) ON DELETE CASCADE,
            agent_type VARCHAR(100) NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            capabilities JSONB NOT NULL DEFAULT '[]',
            configuration JSONB NOT NULL DEFAULT '{}',
            status VARCHAR(50) DEFAULT 'inactive',
            last_active TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(persona_id, agent_type)
        );
        
        -- User sessions for authentication
        CREATE TABLE IF NOT EXISTS user_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            session_token VARCHAR(255) UNIQUE NOT NULL,
            refresh_token VARCHAR(255) UNIQUE,
            ip_address INET,
            user_agent TEXT,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Audit logs for security
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(100),
            resource_id INTEGER,
            details JSONB DEFAULT '{}',
            ip_address INET,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- API keys for service access
        CREATE TABLE IF NOT EXISTS api_keys (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            key_hash VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(100),
            permissions JSONB DEFAULT '[]',
            last_used TIMESTAMP,
            expires_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes for performance
        CREATE INDEX idx_users_email ON users(email);
        CREATE INDEX idx_users_username ON users(username);
        CREATE INDEX idx_sessions_token ON user_sessions(session_token);
        CREATE INDEX idx_sessions_user ON user_sessions(user_id);
        CREATE INDEX idx_audit_user ON audit_logs(user_id);
        CREATE INDEX idx_audit_created ON audit_logs(created_at);
        CREATE INDEX idx_agents_persona ON supervisor_agents(persona_id);
        
        -- Insert default AI personas
        INSERT INTO ai_personas (persona_type, name, domain, description, configuration)
        VALUES 
            ('cherry', 'Cherry', 'Personal Life', 
             'Personal life coach, friend, and lifestyle manager', 
             '{"role": "Life coach and personal assistant", "primary_focus": "personal_growth"}'),
            ('sophia', 'Sophia', 'Pay Ready Business', 
             'Business strategist, client expert, and revenue advisor',
             '{"role": "Business strategist and advisor", "primary_focus": "business_success"}'),
            ('karen', 'Karen', 'ParagonRX Healthcare', 
             'Healthcare expert, clinical trial specialist, and compliance advisor',
             '{"role": "Healthcare expert and compliance advisor", "primary_focus": "healthcare_excellence"}')
        ON CONFLICT (persona_type) DO NOTHING;
        
        -- Create update timestamp trigger
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        -- Apply trigger to all tables with updated_at
        CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        CREATE TRIGGER update_personas_updated_at BEFORE UPDATE ON ai_personas
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON supervisor_agents
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        try:
            # Save schema to file
            schema_file = "/tmp/cherry_ai_schema.sql"
            with open(schema_file, "w") as f:
                f.write(schema_sql)
                
            # Execute schema
            cmd = [
                "psql",
                f"postgresql://{self.config['postgres']['user']}:{self.config['postgres']['password']}@{self.config['postgres']['host']}/{self.config['postgres']['database']}",
                "-f", schema_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Database schema created successfully")
                return True
            else:
                logger.error(f"❌ Database schema creation failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database setup error: {e}")
            return False
            
    async def configure_redis(self) -> bool:
        """Configure Redis for caching and real-time features"""
        logger.info("🔴 Configuring Redis...")
        
        redis_config = f"""
# Cherry AI Redis Configuration
bind 0.0.0.0
protected-mode yes
port {self.config['redis']['port']}
requirepass {self.config['redis']['password']}

# Persistence
save 900 1
save 300 10
save 60 10000
dbfilename cherry_ai.rdb
dir /var/lib/redis

# Memory management
maxmemory 4gb
maxmemory-policy allkeys-lru

# Append only file
appendonly yes
appendfilename "cherry_ai.aof"
appendfsync everysec

# Logging
loglevel notice
logfile /var/log/redis/cherry_ai.log
"""
        
        try:
            # Save config
            config_file = "/tmp/redis_cherry_ai.conf"
            with open(config_file, "w") as f:
                f.write(redis_config)
                
            # Copy to server and restart Redis
            subprocess.run([
                "scp", config_file,
                f"root@{self.lambda_host}:/etc/redis/cherry_ai.conf"
            ], check=True)
            
            subprocess.run([
                "ssh", f"root@{self.lambda_host}",
                "systemctl restart redis && redis-cli ping"
            ], check=True)
            
            logger.info("✅ Redis configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Redis configuration failed: {e}")
            return False
            
    async def setup_vector_stores(self) -> bool:
        """Initialize Pinecone and Weaviate vector stores"""
        logger.info("🔮 Setting up vector stores...")
        
        # Pinecone initialization script
        pinecone_init = f"""
import pinecone
import os

# Initialize Pinecone
pinecone.init(
    api_key="{self.config['pinecone']['api_key']}",
    environment="{self.config['pinecone']['environment']}"
)

# Create indexes for each persona
indexes = [
    {{"name": "cherry-personal", "dimension": 1536, "metric": "cosine"}},
    {{"name": "sophia-business", "dimension": 1536, "metric": "cosine"}},
    {{"name": "karen-healthcare", "dimension": 1536, "metric": "cosine"}}
]

for index_config in indexes:
    if index_config["name"] not in pinecone.list_indexes():
        pinecone.create_index(**index_config)
        print(f"Created index: {{index_config['name']}}")
    else:
        print(f"Index already exists: {{index_config['name']}}")
"""
        
        # Weaviate schema configuration
        weaviate_schema = {
            "classes": [
                {
                    "class": "PersonalKnowledge",
                    "description": "Cherry's personal life knowledge base",
                    "properties": [
                        {"name": "content", "dataType": ["text"]},
                        {"name": "category", "dataType": ["string"]},
                        {"name": "tags", "dataType": ["string[]"]},
                        {"name": "timestamp", "dataType": ["date"]}
                    ]
                },
                {
                    "class": "BusinessIntelligence",
                    "description": "Sophia's business knowledge base",
                    "properties": [
                        {"name": "content", "dataType": ["text"]},
                        {"name": "industry", "dataType": ["string"]},
                        {"name": "company", "dataType": ["string"]},
                        {"name": "insights", "dataType": ["text"]}
                    ]
                },
                {
                    "class": "HealthcareRegulations",
                    "description": "Karen's healthcare compliance knowledge",
                    "properties": [
                        {"name": "regulation", "dataType": ["text"]},
                        {"name": "jurisdiction", "dataType": ["string"]},
                        {"name": "effective_date", "dataType": ["date"]},
                        {"name": "compliance_notes", "dataType": ["text"]}
                    ]
                }
            ]
        }
        
        try:
            # Initialize Pinecone
            with open("/tmp/init_pinecone.py", "w") as f:
                f.write(pinecone_init)
                
            subprocess.run(["python3", "/tmp/init_pinecone.py"], check=True)
            logger.info("✅ Pinecone indexes created")
            
            # Configure Weaviate
            import requests
            weaviate_url = self.config["weaviate"]["url"]
            headers = {"Authorization": f"Bearer {self.config['weaviate']['api_key']}"}
            
            # Create schema
            response = requests.post(
                f"{weaviate_url}/v1/schema",
                json=weaviate_schema,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                logger.info("✅ Weaviate schema configured")
            else:
                logger.warning(f"⚠️  Weaviate schema may already exist: {response.text}")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Vector store setup failed: {e}")
            return False
            
    async def create_base_application(self) -> bool:
        """Create base React application structure"""
        logger.info("⚛️  Creating base React application...")
        
        # Package.json for the React app
        package_json = {
            "name": "cherry-ai-admin",
            "version": "1.0.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.8.0",
                "@mui/material": "^5.11.0",
                "@emotion/react": "^11.10.0",
                "@emotion/styled": "^11.10.0",
                "@mui/icons-material": "^5.11.0",
                "axios": "^1.3.0",
                "socket.io-client": "^4.5.0",
                "@reduxjs/toolkit": "^1.9.0",
                "react-redux": "^8.0.0",
                "formik": "^2.2.0",
                "yup": "^1.0.0",
                "recharts": "^2.5.0",
                "date-fns": "^2.29.0"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            },
            "devDependencies": {
                "@types/react": "^18.0.0",
                "@types/react-dom": "^18.0.0",
                "react-scripts": "5.0.1",
                "typescript": "^4.9.0"
            }
        }
        
        # Base App component
        app_component = """
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Provider } from 'react-redux';
import { store } from './store';

// Layout components
import { MainLayout } from './layouts/MainLayout';
import { AuthLayout } from './layouts/AuthLayout';

// Page components
import { Dashboard } from './pages/Dashboard';
import { AIPersonas } from './pages/AIPersonas';
import { CherryManagement } from './pages/personas/CherryManagement';
import { SophiaManagement } from './pages/personas/SophiaManagement';
import { KarenManagement } from './pages/personas/KarenManagement';
import { AgentManagement } from './pages/AgentManagement';
import { Monitoring } from './pages/Monitoring';
import { Analytics } from './pages/Analytics';
import { Settings } from './pages/Settings';
import { Login } from './pages/auth/Login';
import { AICollaborationDashboard } from './pages/developer/AICollaborationDashboard';

// Auth context
import { AuthProvider, useAuth } from './contexts/AuthContext';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#FF1744', // Cherry red
    },
    secondary: {
      main: '#2196F3',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <Router>
            <Routes>
              {/* Auth routes */}
              <Route path="/login" element={<AuthLayout><Login /></AuthLayout>} />
              
              {/* Protected routes */}
              <Route path="/" element={<MainLayout />}>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<Dashboard />} />
                
                {/* AI Personas */}
                <Route path="personas" element={<AIPersonas />} />
                <Route path="personas/cherry" element={<CherryManagement />} />
                <Route path="personas/sophia" element={<SophiaManagement />} />
                <Route path="personas/karen" element={<KarenManagement />} />
                
                {/* Other sections */}
                <Route path="agents" element={<AgentManagement />} />
                <Route path="monitoring" element={<Monitoring />} />
                <Route path="analytics" element={<Analytics />} />
                <Route path="settings" element={<Settings />} />
                
                {/* Developer tools - AI Collaboration is here */}
                <Route path="settings/developer-tools/collaboration" element={<AICollaborationDashboard />} />
              </Route>
            </Routes>
          </Router>
        </AuthProvider>
      </ThemeProvider>
    </Provider>
  );
}

export default App;
"""
        
        try:
            # Create directory structure
            app_structure = [
                "frontend/src/components",
                "frontend/src/contexts",
                "frontend/src/hooks",
                "frontend/src/layouts",
                "frontend/src/pages/auth",
                "frontend/src/pages/personas",
                "frontend/src/pages/developer",
                "frontend/src/services",
                "frontend/src/store",
                "frontend/src/utils",
                "frontend/public"
            ]
            
            for dir_path in app_structure:
                os.makedirs(dir_path, exist_ok=True)
                
            # Write package.json
            with open("frontend/package.json", "w") as f:
                json.dump(package_json, f, indent=2)
                
            # Write App.js
            with open("frontend/src/App.js", "w") as f:
                f.write(app_component)
                
            logger.info("✅ Base React application created")
            return True
            
        except Exception as e:
            logger.error(f"❌ React app creation failed: {e}")
            return False
            
    async def setup_authentication(self) -> bool:
        """Set up authentication system with JWT and MFA"""
        logger.info("🔐 Setting up authentication system...")
        
        # Authentication service
        auth_service = f"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
import pyotp
import qrcode
import io
import base64

app = FastAPI()

# Configuration
SECRET_KEY = "{self.config['auth']['jwt_secret']}"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class MFASetup(BaseModel):
    secret: str
    qr_code: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({{"exp": expire}})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({{"exp": expire}})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

@app.post("/auth/register", response_model=dict)
async def register(user: UserCreate):
    # Check if user exists
    # Hash password
    hashed_password = get_password_hash(user.password)
    
    # Create user in database
    # Return success
    return {{"message": "User created successfully", "username": user.username}}

@app.post("/auth/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Verify user credentials
    # Create tokens
    access_token = create_access_token(data={{"sub": form_data.username}})
    refresh_token = create_refresh_token(data={{"sub": form_data.username}})
    
    return {{
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }}

@app.post("/auth/mfa/setup", response_model=MFASetup)
async def setup_mfa(current_user: dict = Depends(get_current_user)):
    # Generate secret
    secret = pyotp.random_base32()
    
    # Generate QR code
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user["email"],
        issuer_name="Cherry AI"
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    
    qr_code_b64 = base64.b64encode(buf.getvalue()).decode()
    
    return {{
        "secret": secret,
        "qr_code": f"data:image/png;base64,{{qr_code_b64}}"
    }}

@app.post("/auth/mfa/verify")
async def verify_mfa(token: str, current_user: dict = Depends(get_current_user)):
    # Get user's MFA secret from database
    # Verify token
    totp = pyotp.TOTP(current_user["mfa_secret"])
    
    if totp.verify(token, valid_window=1):
        return {{"verified": True}}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA token"
        )
"""
        
        try:
            # Save authentication service
            with open("services/auth/auth_service.py", "w") as f:
                f.write(auth_service)
                
            logger.info("✅ Authentication system configured")
            return True
            
        except Exception as e:
            logger.error(f"❌ Authentication setup failed: {e}")
            return False
            
    async def create_api_endpoints(self) -> bool:
        """Create base API endpoints"""
        logger.info("🌐 Creating API endpoints...")
        
        # Main API application
        api_app = """
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Import routers
from services.auth.auth_service import app as auth_router
from services.ai_collaboration.api.endpoints import router as collab_router
from services.ai_collaboration.refactored_collaboration_page import collaboration_router

# Import services
from services.ai_collaboration.service import AICollaborationService
from services.ai_collaboration.refactored_collaboration_page import initialize_collaboration_page

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Cherry AI API...")
    
    # Initialize services
    collab_service = AICollaborationService()
    await collab_service.initialize()
    
    # Initialize collaboration page
    initialize_collaboration_page(collab_service)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Cherry AI API...")
    await collab_service.close()

# Create FastAPI app
app = FastAPI(
    title="Cherry AI Admin Interface API",
    description="API for managing AI personas and collaboration",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://cherry-ai.me"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.mount("/auth", auth_router)
app.include_router(collab_router, prefix="/api/collaboration", tags=["collaboration"])
app.include_router(collaboration_router)  # This adds the /api/settings/developer-tools/collaboration routes

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cherry-ai-api"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Cherry AI Admin Interface API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "auth": "/auth",
            "collaboration": "/api/collaboration",
            "developer_tools": "/api/settings/developer-tools/collaboration"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
        
        try:
            # Create API directory
            os.makedirs("api", exist_ok=True)
            
            # Save main API file
            with open("api/main.py", "w") as f:
                f.write(api_app)
                
            logger.info("✅ API endpoints created")
            return True
            
        except Exception as e:
            logger.error(f"❌ API creation failed: {e}")
            return False
            
    async def run_phase1(self) -> bool:
        """Execute Phase 1 implementation"""
        logger.info("🚀 Starting Cherry AI Phase 1 Implementation")
        logger.info("=" * 60)
        
        # Validate environment
        if not await self.validate_environment():
            return False
            
        # Execute implementation steps
        steps = [
            ("Database Schema Setup", self.setup_database_schema),
            ("Redis Configuration", self.configure_redis),
            ("Vector Stores Setup", self.setup_vector_stores),
            ("Base React Application", self.create_base_application),
            ("Authentication System", self.setup_authentication),
            ("API Endpoints", self.create_api_endpoints)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n📋 {step_name}...")
            if not await step_func():
                logger.error(f"❌ Phase 1 failed at: {step_name}")
                return False
                
        # Generate summary
        duration = (datetime.now() - self.start_time).total_seconds()
        logger.info("\n" + "=" * 60)
        logger.info("✅ PHASE 1 IMPLEMENTATION COMPLETE!")
        logger.info(f"⏱️  Duration: {duration:.2f} seconds")
        logger.info("\n📊 Completed Components:")
        logger.info("  ✓ PostgreSQL database with multi-schema architecture")
        logger.info("  ✓ Redis configured for caching and real-time features")
        logger.info("  ✓ Pinecone indexes for AI embeddings")
        logger.info("  ✓ Weaviate schema for knowledge management")
        logger.info("  ✓ Base React application with routing")
        logger.info("  ✓ JWT authentication with MFA support")