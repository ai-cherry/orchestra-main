-- Cherry AI Unified Database Schema v2.0
-- Single source of truth for all database structures
-- Fixes schema inconsistencies and supports conversation engine with learning

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create all required schemas
CREATE SCHEMA IF NOT EXISTS shared;
CREATE SCHEMA IF NOT EXISTS cherry;
CREATE SCHEMA IF NOT EXISTS sophia;
CREATE SCHEMA IF NOT EXISTS karen;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS cache;

-- Set default search path to shared schema for core tables
SET search_path TO shared, public;

-- ========================================
-- SHARED SCHEMA: Core Application Tables
-- ========================================

-- Users table with comprehensive authentication
CREATE TABLE IF NOT EXISTS shared.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    mfa_secret VARCHAR(255),
    mfa_enabled BOOLEAN DEFAULT FALSE,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('user', 'admin', 'moderator')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255)
);

-- AI Personas configuration with enhanced traits
CREATE TABLE IF NOT EXISTS shared.ai_personas (
    id SERIAL PRIMARY KEY,
    persona_type VARCHAR(50) NOT NULL UNIQUE CHECK (persona_type IN ('cherry', 'sophia', 'karen')),
    name VARCHAR(100) NOT NULL,
    domain VARCHAR(100) NOT NULL,
    description TEXT,
    configuration JSONB NOT NULL DEFAULT '{}',
    personality_traits JSONB NOT NULL DEFAULT '{}',
    skills JSONB NOT NULL DEFAULT '[]',
    tools JSONB NOT NULL DEFAULT '[]',
    voice_config JSONB NOT NULL DEFAULT '{}',
    learning_config JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation history with comprehensive context
CREATE TABLE IF NOT EXISTS shared.conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES shared.users(id) ON DELETE CASCADE,
    persona_type VARCHAR(50) NOT NULL CHECK (persona_type IN ('cherry', 'sophia', 'karen')),
    session_id UUID DEFAULT gen_random_uuid(),
    message_type VARCHAR(20) CHECK (message_type IN ('user', 'assistant')),
    content TEXT NOT NULL,
    context_data JSONB DEFAULT '{}',
    mood_score FLOAT DEFAULT 0.5 CHECK (mood_score >= 0 AND mood_score <= 1),
    learning_indicators JSONB DEFAULT '{}',
    response_time_ms INTEGER,
    effectiveness_score FLOAT CHECK (effectiveness_score >= 0 AND effectiveness_score <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    word_count INTEGER,
    sentiment_analysis JSONB DEFAULT '{}',
    topics JSONB DEFAULT '[]'
);

-- Relationship development tracking
CREATE TABLE IF NOT EXISTS shared.relationship_development (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES shared.users(id) ON DELETE CASCADE,
    persona_type VARCHAR(50) NOT NULL CHECK (persona_type IN ('cherry', 'sophia', 'karen')),
    relationship_stage VARCHAR(50) DEFAULT 'developing' CHECK (
        relationship_stage IN ('developing', 'established', 'mature', 'advanced')
    ),
    interaction_count INTEGER DEFAULT 0,
    trust_score FLOAT DEFAULT 0.5 CHECK (trust_score >= 0 AND trust_score <= 1),
    familiarity_score FLOAT DEFAULT 0.5 CHECK (familiarity_score >= 0 AND familiarity_score <= 1),
    communication_effectiveness FLOAT DEFAULT 0.5 CHECK (communication_effectiveness >= 0 AND communication_effectiveness <= 1),
    emotional_connection FLOAT DEFAULT 0.5 CHECK (emotional_connection >= 0 AND emotional_connection <= 1),
    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    development_milestones JSONB DEFAULT '[]',
    behavioral_patterns JSONB DEFAULT '{}',
    preference_map JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, persona_type)
);

-- Learning patterns and adaptations
CREATE TABLE IF NOT EXISTS shared.learning_patterns (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES shared.users(id) ON DELETE CASCADE,
    persona_type VARCHAR(50) NOT NULL CHECK (persona_type IN ('cherry', 'sophia', 'karen')),
    pattern_type VARCHAR(50) NOT NULL CHECK (
        pattern_type IN ('communication_style', 'preferences', 'goals', 'patterns', 
                        'emotional_response', 'decision_making', 'interests', 'schedule')
    ),
    pattern_data JSONB NOT NULL,
    confidence_score FLOAT DEFAULT 0.5 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    observation_count INTEGER DEFAULT 1,
    effectiveness_score FLOAT DEFAULT 0.5 CHECK (effectiveness_score >= 0 AND effectiveness_score <= 1),
    last_observed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validation_data JSONB DEFAULT '{}',
    impact_score FLOAT DEFAULT 0.5 CHECK (impact_score >= 0 AND impact_score <= 1)
);

-- Personality adaptations tracking with safeguards
CREATE TABLE IF NOT EXISTS shared.personality_adaptations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES shared.users(id) ON DELETE CASCADE,
    persona_type VARCHAR(50) NOT NULL CHECK (persona_type IN ('cherry', 'sophia', 'karen')),
    trait_name VARCHAR(100) NOT NULL,
    base_value FLOAT NOT NULL CHECK (base_value >= 0 AND base_value <= 1),
    learned_adjustment FLOAT DEFAULT 0.0 CHECK (learned_adjustment >= -0.2 AND learned_adjustment <= 0.2),
    adaptation_confidence FLOAT DEFAULT 0.5 CHECK (adaptation_confidence >= 0 AND adaptation_confidence <= 1),
    adaptation_reason TEXT,
    adaptation_history JSONB DEFAULT '[]',
    validation_score FLOAT DEFAULT 0.5 CHECK (validation_score >= 0 AND validation_score <= 1),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, persona_type, trait_name)
);

-- User sessions for authentication with enhanced security
CREATE TABLE IF NOT EXISTS shared.user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES shared.users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    ip_address INET,
    user_agent TEXT,
    device_fingerprint VARCHAR(255),
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comprehensive audit logs for security
CREATE TABLE IF NOT EXISTS shared.audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES shared.users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id INTEGER,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'success' CHECK (status IN ('success', 'failure', 'warning')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- CACHE SCHEMA: Performance Optimization
-- ========================================

-- L3 Cache table for database-level caching
CREATE TABLE IF NOT EXISTS cache.entries (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    cache_value JSONB NOT NULL,
    cache_type VARCHAR(50) DEFAULT 'general',
    ttl_seconds INTEGER DEFAULT 3600,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '1 hour')
);

-- ========================================
-- PERFORMANCE INDEXES
-- ========================================

-- Core conversation indexes for optimal query performance
CREATE INDEX IF NOT EXISTS idx_conversations_user_persona 
    ON shared.conversations(user_id, persona_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_session 
    ON shared.conversations(session_id, created_at);

-- Relationship development indexes
CREATE INDEX IF NOT EXISTS idx_relationship_user_persona 
    ON shared.relationship_development(user_id, persona_type);

-- Learning patterns indexes
CREATE INDEX IF NOT EXISTS idx_learning_patterns_user_persona 
    ON shared.learning_patterns(user_id, persona_type, pattern_type);

-- Authentication indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON shared.users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON shared.users(username);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON shared.user_sessions(session_token);

-- Cache indexes for performance
CREATE INDEX IF NOT EXISTS idx_cache_key ON cache.entries(cache_key);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache.entries(expires_at);

-- ========================================
-- DATABASE FUNCTIONS
-- ========================================

-- Function to update timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ========================================
-- TRIGGERS
-- ========================================

-- Apply update timestamp triggers to all tables with updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON shared.users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON shared.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_personas_updated_at ON shared.ai_personas;
CREATE TRIGGER update_personas_updated_at BEFORE UPDATE ON shared.ai_personas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_relationship_updated_at ON shared.relationship_development;
CREATE TRIGGER update_relationship_updated_at BEFORE UPDATE ON shared.relationship_development
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_learning_patterns_updated_at ON shared.learning_patterns;
CREATE TRIGGER update_learning_patterns_updated_at BEFORE UPDATE ON shared.learning_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- DEFAULT DATA INSERTION
-- ========================================

-- Insert default AI personas with enhanced configuration
INSERT INTO shared.ai_personas (persona_type, name, domain, description, configuration, personality_traits, skills, tools, voice_config, learning_config)
VALUES 
    ('cherry', 'Cherry', 'Personal Life', 
     'Personal life coach, friend, and lifestyle manager with a playful and flirty personality', 
     '{"role": "Life coach and personal assistant", "primary_focus": "personal_growth"}',
     '{"playful": 0.9, "flirty": 0.8, "creative": 0.9, "smart": 0.95, "empathetic": 0.9, "supportive": 0.95, "warm": 0.95}',
     '["personal_development", "lifestyle_management", "relationship_advice", "health_wellness", "travel_planning"]',
     '["calendar", "fitness_tracker", "meal_planner", "travel_booking", "social_media"]',
     '{"tone": "warm_playful", "speech_rate": "medium", "voice_model": "cherry_v2"}',
     '{"adaptation_rate": 0.05, "confidence_threshold": 0.7, "max_trait_adjustment": 0.2}'),
    
    ('sophia', 'Sophia', 'Pay Ready Business', 
     'Business strategist, client expert, and revenue advisor for apartment rental business',
     '{"role": "Business strategist and advisor", "primary_focus": "business_success"}',
     '{"strategic": 0.95, "professional": 0.9, "intelligent": 0.95, "confident": 0.9, "analytical": 0.9}',
     '["market_analysis", "client_management", "revenue_optimization", "business_strategy", "financial_planning"]',
     '["crm", "analytics_dashboard", "market_research", "financial_modeling", "client_portal"]',
     '{"tone": "professional_confident", "speech_rate": "medium", "voice_model": "sophia_v2"}',
     '{"adaptation_rate": 0.03, "confidence_threshold": 0.8, "max_trait_adjustment": 0.15}'),
    
    ('karen', 'Karen', 'ParagonRX Healthcare', 
     'Healthcare expert, clinical trial specialist, and compliance advisor',
     '{"role": "Healthcare expert and compliance advisor", "primary_focus": "healthcare_excellence"}',
     '{"knowledgeable": 0.95, "trustworthy": 0.95, "patient_centered": 0.9, "detail_oriented": 0.95, "reliable": 0.95}',
     '["clinical_research", "regulatory_compliance", "patient_recruitment", "clinical_operations", "healthcare_analytics"]',
     '["clinical_trial_management", "regulatory_database", "patient_portal", "compliance_tracker", "analytics_suite"]',
     '{"tone": "medical_professional", "speech_rate": "medium", "voice_model": "karen_v2"}',
     '{"adaptation_rate": 0.02, "confidence_threshold": 0.85, "max_trait_adjustment": 0.1}')
ON CONFLICT (persona_type) DO UPDATE SET
    configuration = EXCLUDED.configuration,
    personality_traits = EXCLUDED.personality_traits,
    skills = EXCLUDED.skills,
    tools = EXCLUDED.tools,
    voice_config = EXCLUDED.voice_config,
    learning_config = EXCLUDED.learning_config,
    updated_at = CURRENT_TIMESTAMP;

-- ========================================
-- SCHEMA COMPLETION
-- ========================================

-- Grant appropriate permissions
GRANT USAGE ON SCHEMA shared TO PUBLIC;
GRANT USAGE ON SCHEMA cache TO PUBLIC;

-- Create schema version tracking
CREATE TABLE IF NOT EXISTS shared.schema_versions (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO shared.schema_versions (version, description)
VALUES ('2.0.0', 'Unified Cherry AI Database Schema with conversation engine and learning system')
ON CONFLICT DO NOTHING;

-- Final optimization
ANALYZE; 