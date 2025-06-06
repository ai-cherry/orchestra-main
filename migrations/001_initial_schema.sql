
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
    