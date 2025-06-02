-- LLM Orchestration Database Schema Migration
-- Version: 1.0.0
-- Date: 2024-06-02

BEGIN;

-- Create indexes for existing tables if not exists
CREATE INDEX IF NOT EXISTS idx_llm_providers_active ON llm_providers(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_llm_models_available ON llm_models(is_available, provider_id) WHERE is_available = true;
CREATE INDEX IF NOT EXISTS idx_llm_models_identifier ON llm_models(model_identifier);
CREATE INDEX IF NOT EXISTS idx_llm_model_assignments_use_case ON llm_model_assignments(use_case_id, tier);
CREATE INDEX IF NOT EXISTS idx_llm_metrics_date ON llm_metrics(date DESC);
CREATE INDEX IF NOT EXISTS idx_llm_metrics_model_date ON llm_metrics(model_id, date DESC);

-- Create workflow tracking tables
CREATE TABLE IF NOT EXISTS workflow_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_definition_id UUID REFERENCES workflow_definitions(id),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    context JSONB DEFAULT '{}'::jsonb,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workflow_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_execution_id UUID REFERENCES workflow_executions(id) ON DELETE CASCADE,
    task_id VARCHAR(255) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    retry_count INTEGER DEFAULT 0,
    task_data JSONB DEFAULT '{}'::jsonb,
    result JSONB,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workflow_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_execution_id UUID REFERENCES workflow_executions(id) ON DELETE CASCADE,
    checkpoint_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create agent preference tables
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    category VARCHAR(255) NOT NULL,
    weight DECIMAL(3,2) DEFAULT 1.0,
    positive_signals INTEGER DEFAULT 0,
    negative_signals INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, category)
);

CREATE TABLE IF NOT EXISTS user_search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    enhanced_query TEXT,
    results_count INTEGER,
    preferences_applied TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create apartment analysis cache
CREATE TABLE IF NOT EXISTS neighborhood_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    address TEXT NOT NULL UNIQUE,
    score DECIMAL(5,2),
    analysis_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP + INTERVAL '7 days'
);

-- Create clinical trial alerts
CREATE TABLE IF NOT EXISTS clinical_trial_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    alert_id VARCHAR(255) NOT NULL UNIQUE,
    criteria JSONB NOT NULL,
    notification_method VARCHAR(50) DEFAULT 'email',
    is_active BOOLEAN DEFAULT true,
    last_checked TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    matches_found INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for new tables
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status) WHERE status IN ('pending', 'running');
CREATE INDEX idx_workflow_executions_workflow_id ON workflow_executions(workflow_definition_id);
CREATE INDEX idx_workflow_tasks_execution_id ON workflow_tasks(workflow_execution_id);
CREATE INDEX idx_workflow_tasks_status ON workflow_tasks(status);
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_user_search_history_user_id ON user_search_history(user_id, created_at DESC);
CREATE INDEX idx_neighborhood_scores_expires ON neighborhood_scores(expires_at) WHERE expires_at > CURRENT_TIMESTAMP;
CREATE INDEX idx_clinical_trial_alerts_user_id ON clinical_trial_alerts(user_id) WHERE is_active = true;

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_workflow_definitions_updated_at BEFORE UPDATE ON workflow_definitions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clinical_trial_alerts_updated_at BEFORE UPDATE ON clinical_trial_alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create materialized view for routing analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS llm_routing_analytics AS
SELECT 
    date_trunc('hour', m.date) as hour,
    uc.use_case,
    p.name as provider,
    mo.model_identifier,
    COUNT(*) as request_count,
    SUM(m.success_count) as success_count,
    SUM(m.failure_count) as failure_count,
    AVG(m.avg_latency_ms) as avg_latency_ms,
    SUM(m.total_tokens) as total_tokens,
    SUM(m.total_cost) as total_cost
FROM llm_metrics m
JOIN llm_models mo ON m.model_id = mo.id
JOIN llm_providers p ON mo.provider_id = p.id
JOIN llm_use_cases uc ON m.use_case_id = uc.id
WHERE m.date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY 1, 2, 3, 4;

-- Create index on materialized view
CREATE INDEX idx_llm_routing_analytics_hour ON llm_routing_analytics(hour DESC);

-- Grant permissions (adjust based on your user setup)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO orchestra_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO orchestra_app;

-- Add comments for documentation
COMMENT ON TABLE workflow_definitions IS 'Stores workflow templates and definitions';
COMMENT ON TABLE workflow_executions IS 'Tracks individual workflow execution instances';
COMMENT ON TABLE workflow_tasks IS 'Stores tasks within workflow executions';
COMMENT ON TABLE workflow_checkpoints IS 'Checkpoint data for workflow recovery';
COMMENT ON TABLE user_preferences IS 'User preference learning for Personal Agent';
COMMENT ON TABLE user_search_history IS 'Search history for adaptive search refinement';
COMMENT ON TABLE neighborhood_scores IS 'Cached neighborhood analysis scores';
COMMENT ON TABLE clinical_trial_alerts IS 'Alert subscriptions for clinical trials';

COMMIT;

-- Refresh materialized view (run periodically)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY llm_routing_analytics;