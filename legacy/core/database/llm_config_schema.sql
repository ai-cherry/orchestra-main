-- LLM Configuration Schema for Dynamic Model Routing
-- This schema allows admin users to configure model routing without code changes

-- Table for storing LLM provider configurations
CREATE TABLE IF NOT EXISTS llm_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL, -- 'portkey', 'openrouter'
    api_key_env_var VARCHAR(100), -- Environment variable name for API key
    base_url VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0, -- Lower number = higher priority
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for available models from providers
CREATE TABLE IF NOT EXISTS llm_models (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES llm_providers(id) ON DELETE CASCADE,
    model_identifier VARCHAR(255) NOT NULL, -- e.g., 'anthropic/claude-3-opus'
    display_name VARCHAR(255),
    capabilities JSONB DEFAULT '{}', -- {"supports_tools": true, "max_tokens": 4096}
    cost_per_1k_tokens DECIMAL(10, 6), -- For cost tracking
    is_available BOOLEAN DEFAULT true,
    last_checked TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider_id, model_identifier)
);

-- Table for use case configurations
CREATE TABLE IF NOT EXISTS llm_use_cases (
    id SERIAL PRIMARY KEY,
    use_case VARCHAR(50) UNIQUE NOT NULL, -- 'code_generation', 'debugging', etc.
    display_name VARCHAR(255),
    description TEXT,
    default_temperature DECIMAL(3, 2) DEFAULT 0.5,
    default_max_tokens INTEGER DEFAULT 2048,
    default_system_prompt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for model assignments per use case and tier
CREATE TABLE IF NOT EXISTS llm_model_assignments (
    id SERIAL PRIMARY KEY,
    use_case_id INTEGER REFERENCES llm_use_cases(id) ON DELETE CASCADE,
    tier VARCHAR(20) NOT NULL, -- 'premium', 'standard', 'economy'
    primary_model_id INTEGER REFERENCES llm_models(id) ON DELETE SET NULL,
    temperature_override DECIMAL(3, 2),
    max_tokens_override INTEGER,
    system_prompt_override TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(use_case_id, tier)
);

-- Table for fallback models
CREATE TABLE IF NOT EXISTS llm_fallback_models (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER REFERENCES llm_model_assignments(id) ON DELETE CASCADE,
    model_id INTEGER REFERENCES llm_models(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0, -- Order of fallback
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(assignment_id, model_id)
);

-- Table for tracking model performance metrics
CREATE TABLE IF NOT EXISTS llm_metrics (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES llm_models(id) ON DELETE CASCADE,
    use_case_id INTEGER REFERENCES llm_use_cases(id) ON DELETE CASCADE,
    request_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost DECIMAL(10, 4) DEFAULT 0,
    avg_latency_ms DECIMAL(10, 2),
    date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_id, use_case_id, date)
);

-- Indexes for performance
CREATE INDEX idx_llm_models_provider ON llm_models(provider_id);
CREATE INDEX idx_llm_models_available ON llm_models(is_available);
CREATE INDEX idx_llm_assignments_use_case ON llm_model_assignments(use_case_id);
CREATE INDEX idx_llm_metrics_date ON llm_metrics(date);
CREATE INDEX idx_llm_metrics_model_use_case ON llm_metrics(model_id, use_case_id);

-- Trigger to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_llm_providers_updated_at BEFORE UPDATE ON llm_providers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_llm_models_updated_at BEFORE UPDATE ON llm_models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_llm_use_cases_updated_at BEFORE UPDATE ON llm_use_cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_llm_model_assignments_updated_at BEFORE UPDATE ON llm_model_assignments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default providers
INSERT INTO llm_providers (name, api_key_env_var, base_url, priority) VALUES
    ('portkey', 'PORTKEY_API_KEY', 'https://api.portkey.ai/v1', 0),
    ('openrouter', 'OPENROUTER_API_KEY', 'https://openrouter.ai/api/v1', 1)
ON CONFLICT (name) DO NOTHING;

-- Insert default use cases
INSERT INTO llm_use_cases (use_case, display_name, description, default_temperature, default_max_tokens) VALUES
    ('code_generation', 'Code Generation', 'Generate clean, efficient code', 0.2, 4096),
    ('architecture_design', 'Architecture Design', 'Design system architectures', 0.7, 8192),
    ('debugging', 'Debugging', 'Debug code and fix errors', 0.1, 4096),
    ('documentation', 'Documentation', 'Create technical documentation', 0.5, 4096),
    ('chat_conversation', 'Chat Conversation', 'General conversational AI', 0.7, 2048),
    ('memory_processing', 'Memory Processing', 'Process and structure memories', 0.3, 2048),
    ('workflow_orchestration', 'Workflow Orchestration', 'Orchestrate complex workflows', 0.4, 8192),
    ('general_purpose', 'General Purpose', 'General AI tasks', 0.5, 2048)
ON CONFLICT (use_case) DO NOTHING;