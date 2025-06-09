#!/usr/bin/env python3
"""
Cherry AI Admin Interface API
Unified FastAPI application connecting database, authentication, and admin functionality
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

import asyncpg
import jwt
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import bcrypt
import uvicorn
from api.conversation_engine import ConversationEngine, ConversationMode
from config.cherry_ai_config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
config = get_config()
DATABASE_URL = config.get_database_url(async_driver=True)
JWT_SECRET_KEY = config.security.secret_key
JWT_ALGORITHM = config.security.jwt_algorithm
JWT_EXPIRATION_HOURS = config.security.access_token_expire_minutes / 60

logger.info(f"Loading configuration for environment: {config.environment}")

# Security
security = HTTPBearer()

# Database connection pool
db_pool: Optional[asyncpg.Pool] = None
conversation_engine: Optional[ConversationEngine] = None

# Models
class UserRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

class PersonaResponse(BaseModel):
    id: int
    persona_type: str
    name: str
    domain: str
    description: str
    configuration: Dict[str, Any]
    personality_traits: Dict[str, Any]
    skills: List[str]
    tools: List[str]
    voice_config: Dict[str, Any]
    is_active: bool
    created_at: datetime

class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    personality_traits: Optional[Dict[str, Any]] = None
    skills: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    voice_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class SupervisorAgentResponse(BaseModel):
    id: int
    persona_id: int
    agent_type: str
    name: str
    description: str
    capabilities: List[str]
    configuration: Dict[str, Any]
    status: str
    last_active: Optional[datetime]
    created_at: datetime

class SupervisorAgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    capabilities: Optional[List[str]] = None
    configuration: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class SystemMetrics(BaseModel):
    active_sessions: int
    total_requests_today: int
    average_response_time: float
    error_rate: float
    persona_performance: Dict[str, float]

class ConversationRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    persona_type: str = Field(..., pattern=r'^(cherry|sophia|karen)$')
    session_id: Optional[str] = None
    mode: str = Field(default="casual", pattern=r'^(casual|focused|coaching|analytical|supportive)$')

class ConversationResponse(BaseModel):
    response: str
    persona_type: str
    session_id: str
    mode: str
    response_time_ms: int
    relationship_context: Dict[str, Any]
    learning_applied: int

class ConversationHistory(BaseModel):
    message_type: str
    content: str
    context_data: Dict[str, Any]
    mood_score: float
    created_at: datetime
    effectiveness_score: Optional[float] = None

class RelationshipInsights(BaseModel):
    relationship_stage: str
    trust_score: float
    familiarity_score: float
    interaction_count: int
    communication_effectiveness: float
    learning_patterns_active: int
    personality_adaptations: int
    recent_mood_trend: float

# Utility functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # Get user from database
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM shared.users WHERE id = $1 AND is_active = true",
            user_id
        )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
    
    return dict(user)

# Database functions
async def init_database():
    """Initialize database connection and schema"""
    global db_pool, conversation_engine
    
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
        logger.info("Database connection pool created")
        
        # Initialize schema
        await setup_database_schema()
        
        # Initialize conversation engine with config
        conversation_engine = ConversationEngine(db_pool, config)
        await conversation_engine.initialize()
        logger.info("Conversation engine initialized with configuration")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def setup_database_schema():
    """Set up database schema"""
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
    
    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
    CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
    CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);
    CREATE INDEX IF NOT EXISTS idx_agents_persona ON supervisor_agents(persona_id);
    
    -- Insert default AI personas
    INSERT INTO ai_personas (persona_type, name, domain, description, configuration, personality_traits, skills, tools, voice_config)
    VALUES 
        ('cherry', 'Cherry', 'Personal Life', 
         'Personal life coach, friend, and lifestyle manager with a playful and flirty personality', 
         '{"role": "Life coach and personal assistant", "primary_focus": "personal_growth"}',
         '{"playful": 0.9, "flirty": 0.8, "creative": 0.9, "smart": 0.95, "empathetic": 0.9}',
         '["personal_development", "lifestyle_management", "relationship_advice", "health_wellness", "travel_planning"]',
         '["calendar", "fitness_tracker", "meal_planner", "travel_booking", "social_media"]',
         '{"tone": "warm_playful", "speech_rate": "medium", "voice_model": "cherry_v2"}'),
        ('sophia', 'Sophia', 'Pay Ready Business', 
         'Business strategist, client expert, and revenue advisor for apartment rental business',
         '{"role": "Business strategist and advisor", "primary_focus": "business_success", "domain": "apartment_rental"}',
         '{"strategic": 0.95, "professional": 0.9, "intelligent": 0.95, "confident": 0.9, "analytical": 0.9}',
         '["market_analysis", "client_management", "revenue_optimization", "business_strategy", "financial_planning"]',
         '["crm", "analytics_dashboard", "market_research", "financial_modeling", "client_portal"]',
         '{"tone": "professional_confident", "speech_rate": "medium", "voice_model": "sophia_v2"}'),
        ('karen', 'Karen', 'ParagonRX Healthcare', 
         'Healthcare expert, clinical trial specialist, and compliance advisor',
         '{"role": "Healthcare expert and compliance advisor", "primary_focus": "healthcare_excellence", "specialization": "clinical_research"}',
         '{"knowledgeable": 0.95, "trustworthy": 0.95, "patient_centered": 0.9, "detail_oriented": 0.95, "authoritative": 0.8}',
         '["clinical_research", "regulatory_compliance", "patient_recruitment", "clinical_operations", "healthcare_analytics"]',
         '["clinical_trial_management", "regulatory_database", "patient_portal", "compliance_tracker", "analytics_suite"]',
         '{"tone": "medical_professional", "speech_rate": "medium", "voice_model": "karen_v2"}')
    ON CONFLICT (persona_type) DO NOTHING;
    
    -- Insert default supervisor agents
    INSERT INTO supervisor_agents (persona_id, agent_type, name, description, capabilities, configuration, status)
    SELECT 
        p.id,
        agent_data.agent_type,
        agent_data.name,
        agent_data.description,
        agent_data.capabilities,
        agent_data.configuration,
        'active'
    FROM ai_personas p
    CROSS JOIN (
        VALUES
        -- Cherry's agents
        ('cherry', 'health_wellness', 'Health & Wellness Supervisor', 
         'Fitness tracking, nutrition management, medical coordination',
         '["fitness_planning", "nutrition_advice", "mental_wellness", "sleep_optimization"]'::jsonb,
         '{"expertise": "holistic_health", "focus_areas": ["physical", "mental", "emotional"]}'::jsonb),
        ('cherry', 'relationship_management', 'Relationship Management Supervisor',
         'Family coordination, friendship maintenance, social planning',
         '["family_coordination", "friendship_maintenance", "social_planning", "communication_advice"]'::jsonb,
         '{"expertise": "relationship_dynamics", "focus_areas": ["family", "friends", "social"]}'::jsonb),
        ('cherry', 'travel_planning', 'Travel Planning Supervisor',
         'Itinerary optimization, accommodation management, travel coordination',
         '["itinerary_creation", "booking_assistance", "local_recommendations", "travel_tips"]'::jsonb,
         '{"expertise": "travel_optimization", "focus_areas": ["planning", "booking", "experiences"]}'::jsonb),
        
        -- Sophia's agents
        ('sophia', 'client_relationship', 'Client Relationship Supervisor',
         'Client communication, satisfaction monitoring, retention strategies',
         '["client_communication", "satisfaction_monitoring", "retention_strategy", "relationship_growth"]'::jsonb,
         '{"expertise": "client_success", "focus_areas": ["communication", "satisfaction", "retention"]}'::jsonb),
        ('sophia', 'market_intelligence', 'Market Intelligence Supervisor',
         'Competitive analysis, trend monitoring, opportunity identification',
         '["market_analysis", "competitor_tracking", "trend_forecasting", "opportunity_identification"]'::jsonb,
         '{"expertise": "market_analysis", "focus_areas": ["competition", "trends", "opportunities"]}'::jsonb),
        ('sophia', 'financial_performance', 'Financial Performance Supervisor',
         'Revenue optimization, cost analysis, financial planning support',
         '["revenue_optimization", "cost_analysis", "profitability_improvement", "financial_planning"]'::jsonb,
         '{"expertise": "financial_optimization", "focus_areas": ["revenue", "costs", "profitability"]}'::jsonb),
        
        -- Karen's agents
        ('karen', 'regulatory_compliance', 'Regulatory Compliance Supervisor',
         'Regulation monitoring, compliance assessment, audit preparation',
         '["regulation_monitoring", "compliance_assessment", "audit_preparation", "regulatory_strategy"]'::jsonb,
         '{"expertise": "regulatory_affairs", "focus_areas": ["monitoring", "compliance", "audits"]}'::jsonb),
        ('karen', 'clinical_trial_management', 'Clinical Trial Management Supervisor',
         'Protocol optimization, operational efficiency, quality assurance',
         '["protocol_optimization", "operational_efficiency", "quality_assurance", "trial_performance"]'::jsonb,
         '{"expertise": "clinical_operations", "focus_areas": ["protocols", "operations", "quality"]}'::jsonb),
        ('karen', 'patient_recruitment', 'Patient Recruitment Supervisor',
         'Recruitment strategies, patient engagement, retention improvement',
         '["recruitment_strategy", "patient_engagement", "retention_improvement", "demographic_analysis"]'::jsonb,
         '{"expertise": "patient_recruitment", "focus_areas": ["strategy", "engagement", "retention"]}'::jsonb)
    ) AS agent_data(persona_type, agent_type, name, description, capabilities, configuration)
    WHERE p.persona_type = agent_data.persona_type
    ON CONFLICT (persona_id, agent_type) DO NOTHING;
    
    -- Create update timestamp trigger
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    
    -- Apply trigger to all tables with updated_at
    DROP TRIGGER IF EXISTS update_users_updated_at ON users;
    CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    DROP TRIGGER IF EXISTS update_personas_updated_at ON ai_personas;
    CREATE TRIGGER update_personas_updated_at BEFORE UPDATE ON ai_personas
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    DROP TRIGGER IF EXISTS update_agents_updated_at ON supervisor_agents;
    CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON supervisor_agents
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """
    
    async with db_pool.acquire() as conn:
        await conn.execute(schema_sql)
        logger.info("Database schema initialized successfully")

async def close_database():
    """Close database connection pool"""
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")

# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    logger.info("Starting Cherry AI Admin Interface API...")
    
    # Initialize database
    await init_database()
    
    yield
    
    # Cleanup
    logger.info("Shutting down Cherry AI Admin Interface API...")
    await close_database()

# FastAPI application
app = FastAPI(
    title="Cherry AI Admin Interface API",
    description="Complete API for managing AI personas, supervisor agents, and authentication",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "https://cherry-ai.me"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse)
async def register_user(user_data: UserRegistration):
    """Register a new user"""
    async with db_pool.acquire() as conn:
        # Check if user exists
        existing = await conn.fetchrow(
            "SELECT id FROM shared.users WHERE username = $1 OR email = $2",
            user_data.username, user_data.email
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists"
            )
        
        # Hash password and create user
        password_hash = hash_password(user_data.password)
        user = await conn.fetchrow("""
            INSERT INTO shared.users (username, email, password_hash)
            VALUES ($1, $2, $3)
            RETURNING id, username, email, role, is_active, created_at
        """, user_data.username, user_data.email, password_hash)
        
        return UserResponse(**dict(user))

@app.post("/auth/login")
async def login_user(credentials: UserLogin):
    """Login user and return JWT token"""
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM shared.users WHERE username = $1 AND is_active = true",
            credentials.username
        )
        
        if not user or not verify_password(credentials.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Update last login
        await conn.execute(
            "UPDATE shared.users SET last_login = CURRENT_TIMESTAMP WHERE id = $1",
            user['id']
        )
        
        # Create access token
        access_token = create_access_token({"user_id": user['id'], "username": user['username']})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse(**dict(user))
        }

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(**current_user)

# Persona management endpoints
@app.get("/api/personas", response_model=List[PersonaResponse])
async def get_personas(current_user: dict = Depends(get_current_user)):
    """Get all AI personas"""
    async with db_pool.acquire() as conn:
        personas = await conn.fetch("SELECT * FROM shared.ai_personas ORDER BY created_at")
        return [PersonaResponse(**dict(persona)) for persona in personas]

@app.get("/api/personas/{persona_id}", response_model=PersonaResponse)
async def get_persona(persona_id: int, current_user: dict = Depends(get_current_user)):
    """Get specific persona by ID"""
    async with db_pool.acquire() as conn:
        persona = await conn.fetchrow("SELECT * FROM shared.ai_personas WHERE id = $1", persona_id)
        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found")
        return PersonaResponse(**dict(persona))

@app.put("/api/personas/{persona_id}", response_model=PersonaResponse)
async def update_persona(
    persona_id: int, 
    updates: PersonaUpdate, 
    current_user: dict = Depends(get_current_user)
):
    """Update persona configuration"""
    update_fields = []
    values = []
    param_count = 1
    
    for field, value in updates.dict(exclude_unset=True).items():
        if field in ['configuration', 'personality_traits', 'skills', 'tools', 'voice_config']:
            update_fields.append(f"{field} = ${param_count}")
            values.append(json.dumps(value) if not isinstance(value, str) else value)
        else:
            update_fields.append(f"{field} = ${param_count}")
            values.append(value)
        param_count += 1
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    values.append(persona_id)
    
    async with db_pool.acquire() as conn:
        query = f"""
            UPDATE shared.ai_personas 
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            RETURNING *
        """
        
        persona = await conn.fetchrow(query, *values)
        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found")
        
        return PersonaResponse(**dict(persona))

# Supervisor agents endpoints
@app.get("/api/personas/{persona_id}/agents", response_model=List[SupervisorAgentResponse])
async def get_persona_agents(persona_id: int, current_user: dict = Depends(get_current_user)):
    """Get all supervisor agents for a persona"""
    async with db_pool.acquire() as conn:
        agents = await conn.fetch(
            "SELECT * FROM shared.supervisor_agents WHERE persona_id = $1 ORDER BY created_at",
            persona_id
        )
        return [SupervisorAgentResponse(**dict(agent)) for agent in agents]

@app.get("/api/agents", response_model=List[SupervisorAgentResponse])
async def get_all_agents(current_user: dict = Depends(get_current_user)):
    """Get all supervisor agents across all personas"""
    async with db_pool.acquire() as conn:
        agents = await conn.fetch("""
            SELECT sa.*, ap.name as persona_name, ap.persona_type
            FROM shared.supervisor_agents sa
            JOIN shared.ai_personas ap ON sa.persona_id = ap.id
            ORDER BY ap.persona_type, sa.created_at
        """)
        return [SupervisorAgentResponse(**dict(agent)) for agent in agents]

@app.put("/api/agents/{agent_id}", response_model=SupervisorAgentResponse)
async def update_agent(
    agent_id: int, 
    updates: SupervisorAgentUpdate, 
    current_user: dict = Depends(get_current_user)
):
    """Update supervisor agent configuration"""
    update_fields = []
    values = []
    param_count = 1
    
    for field, value in updates.dict(exclude_unset=True).items():
        if field in ['capabilities', 'configuration']:
            update_fields.append(f"{field} = ${param_count}")
            values.append(json.dumps(value))
        else:
            update_fields.append(f"{field} = ${param_count}")
            values.append(value)
        param_count += 1
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    values.append(agent_id)
    
    async with db_pool.acquire() as conn:
        query = f"""
            UPDATE shared.supervisor_agents 
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            RETURNING *
        """
        
        agent = await conn.fetchrow(query, *values)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return SupervisorAgentResponse(**dict(agent))

# System monitoring endpoints
@app.get("/api/system/metrics", response_model=SystemMetrics)
async def get_system_metrics(current_user: dict = Depends(get_current_user)):
    """Get system performance metrics"""
    async with db_pool.acquire() as conn:
        # Get basic metrics (mock data for now)
        active_sessions = await conn.fetchval(
            "SELECT COUNT(*) FROM shared.user_sessions WHERE expires_at > CURRENT_TIMESTAMP"
        ) or 0
        
        # Mock other metrics - would be replaced with real data in production
        return SystemMetrics(
            active_sessions=active_sessions,
            total_requests_today=147,
            average_response_time=245.5,
            error_rate=0.01,
            persona_performance={
                "cherry": 85.2,
                "sophia": 92.1,
                "karen": 88.7
            }
        )

@app.get("/api/system/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        return {
            "status": "healthy",
            "service": "cherry-ai-admin-api",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "cherry-ai-admin-api",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Conversation endpoints
@app.post("/api/conversation", response_model=ConversationResponse)
async def chat_with_persona(
    request: ConversationRequest, 
    current_user: dict = Depends(get_current_user)
):
    """Send message to AI persona and get response with learning integration"""
    try:
        if not conversation_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Conversation engine not available"
            )
        
        # Convert string mode to ConversationMode enum
        mode = ConversationMode(request.mode)
        
        response = await conversation_engine.generate_response(
            user_id=current_user['id'],
            persona_type=request.persona_type,
            user_message=request.message,
            session_id=request.session_id,
            mode=mode
        )
        
        return ConversationResponse(**response)
        
    except Exception as e:
        logger.error(f"Conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate response"
        )

@app.get("/api/conversation/history/{persona_type}", response_model=List[ConversationHistory])
async def get_conversation_history(
    persona_type: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get conversation history with specific persona"""
    if persona_type not in ['cherry', 'sophia', 'karen']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid persona type"
        )
    
    try:
        if not conversation_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Conversation engine not available"
            )
        
        history = await conversation_engine.get_conversation_history(
            user_id=current_user['id'],
            persona_type=persona_type,
            limit=min(limit, 100)  # Cap at 100 messages
        )
        
        return [ConversationHistory(**conv) for conv in history]
        
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation history"
        )

@app.get("/api/relationship/insights/{persona_type}", response_model=RelationshipInsights)
async def get_relationship_insights(
    persona_type: str,
    current_user: dict = Depends(get_current_user)
):
    """Get relationship development insights for specific persona"""
    if persona_type not in ['cherry', 'sophia', 'karen']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid persona type"
        )
    
    try:
        if not conversation_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Conversation engine not available"
            )
        
        insights = await conversation_engine.get_relationship_insights(
            user_id=current_user['id'],
            persona_type=persona_type
        )
        
        return RelationshipInsights(**insights)
        
    except Exception as e:
        logger.error(f"Insights retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve relationship insights"
        )

@app.get("/api/conversation/active-sessions")
async def get_active_sessions(current_user: dict = Depends(get_current_user)):
    """Get user's active conversation sessions"""
    try:
        async with db_pool.acquire() as conn:
            sessions = await conn.fetch("""
                SELECT DISTINCT 
                    persona_type,
                    session_id,
                    MAX(created_at) as last_activity,
                    COUNT(*) as message_count
                FROM shared.conversations 
                WHERE user_id = $1 
                AND created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
                GROUP BY persona_type, session_id
                ORDER BY last_activity DESC
                LIMIT 10
            """, current_user['id'])
            
            return [
                {
                    "persona_type": session['persona_type'],
                    "session_id": session['session_id'],
                    "last_activity": session['last_activity'],
                    "message_count": session['message_count']
                }
                for session in sessions
            ]
            
    except Exception as e:
        logger.error(f"Active sessions retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active sessions"
        )

# t endpoint
@app.get("/")
    """t endpoint with API information"""
    return {
        "name": "Cherry AI Admin Interface API",
        "version": "1.0.0",
        "description": "Complete API for managing AI personas and conversations with learning",
        "endpoints": {
            "authentication": "/auth",
            "personas": "/api/personas",
            "agents": "/api/agents",
            "conversations": "/api/conversation",
            "system": "/api/system",
            "docs": "/docs"
        },
        "features": {
            "ai_conversations": "Real-time AI persona interactions",
            "relationship_learning": "Progressive personality adaptation",
            "conversation_memory": "Context-aware conversation history",
            "multi_persona": "Three distinct AI personalities (Cherry, Sophia, Karen)"
        },
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 