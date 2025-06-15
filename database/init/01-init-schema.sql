-- Orchestra AI Database Schema
-- Initialize PostgreSQL database for Orchestra AI

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Personas table
CREATE TABLE IF NOT EXISTS personas (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    avatar VARCHAR(10),
    color VARCHAR(20),
    gradient VARCHAR(100),
    communication_style JSONB,
    expertise TEXT[],
    knowledge_domains TEXT[],
    capabilities TEXT[],
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    persona_id VARCHAR(50) REFERENCES personas(id),
    title VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    response TEXT,
    persona_id VARCHAR(50) REFERENCES personas(id),
    sources TEXT[],
    search_results JSONB,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Search queries table
CREATE TABLE IF NOT EXISTS search_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query TEXT NOT NULL,
    search_mode VARCHAR(50) DEFAULT 'normal',
    user_id UUID REFERENCES users(id),
    results_count INTEGER,
    processing_time_ms INTEGER,
    sources_used TEXT[],
    cost_estimate DECIMAL(10,4) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- System metrics table
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4),
    metric_unit VARCHAR(20),
    metadata JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API usage table
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    user_id UUID REFERENCES users(id),
    response_status INTEGER,
    response_time_ms INTEGER,
    request_size INTEGER,
    response_size INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_search_queries_user_id ON search_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_search_queries_created_at ON search_queries(created_at);
CREATE INDEX IF NOT EXISTS idx_system_metrics_name_time ON system_metrics(metric_name, recorded_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint_time ON api_usage(endpoint, created_at);

-- Create full-text search indexes
CREATE INDEX IF NOT EXISTS idx_chat_messages_message_fts ON chat_messages USING gin(to_tsvector('english', message));
CREATE INDEX IF NOT EXISTS idx_search_queries_query_fts ON search_queries USING gin(to_tsvector('english', query));

-- Insert default personas
INSERT INTO personas (id, name, description, avatar, color, gradient, communication_style, expertise, knowledge_domains, capabilities) VALUES
('cherry', 'Cherry', 'Creative AI specialized in content creation, design, and innovation', 'C', '#ef4444', 'from-red-500 to-pink-500', 
 '{"tone": "friendly and enthusiastic", "approach": "creative and innovative", "greeting": "Hi there! I''m Cherry, and I''m excited to help you with this creative challenge!"}',
 ARRAY['Content Creation', 'Design & Visual Arts', 'Innovation & Brainstorming', 'Creative Writing', 'Brand Development', 'Marketing Campaigns'],
 ARRAY['Art & Design', 'Content Marketing', 'Creative Industries', 'Innovation Management', 'Brand Strategy', 'Digital Media'],
 ARRAY['Generate creative content', 'Design concepts and mockups', 'Brainstorm innovative solutions', 'Create marketing materials', 'Develop brand strategies', 'Write compelling copy']),

('sophia', 'Sophia', 'Strategic AI focused on analysis, planning, and complex problem-solving', 'S', '#3b82f6', 'from-blue-500 to-indigo-500',
 '{"tone": "analytical and comprehensive", "approach": "strategic and data-driven", "greeting": "As your strategic AI assistant, I''ve conducted a comprehensive analysis and gathered relevant information."}',
 ARRAY['Strategic Analysis', 'Data Insights', 'Problem Solving', 'Research & Analysis', 'Business Intelligence', 'Decision Support'],
 ARRAY['Business Strategy', 'Data Analytics', 'Market Research', 'Competitive Intelligence', 'Risk Assessment', 'Performance Metrics'],
 ARRAY['Analyze complex data', 'Develop strategic plans', 'Conduct market research', 'Assess risks and opportunities', 'Create business intelligence reports', 'Provide decision support']),

('karen', 'Karen', 'Operational AI focused on execution, automation, and workflow management', 'K', '#10b981', 'from-green-500 to-emerald-500',
 '{"tone": "organized and efficient", "approach": "practical and systematic", "greeting": "I''m Karen, your operational AI. Let me provide you with structured, actionable information."}',
 ARRAY['Workflow Automation', 'Process Optimization', 'Project Management', 'Operations Excellence', 'System Integration', 'Quality Assurance'],
 ARRAY['Operations Management', 'Process Engineering', 'Automation Technologies', 'Quality Management', 'Project Management', 'System Administration'],
 ARRAY['Optimize workflows', 'Automate processes', 'Manage projects', 'Ensure quality standards', 'Integrate systems', 'Monitor performance'])
ON CONFLICT (id) DO NOTHING;

