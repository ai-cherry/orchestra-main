-- Pay Ready Domain Database Schema
-- =================================
-- This script creates all necessary database objects for the Pay Ready ETL orchestration system

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS pay_ready;

-- Set search path
SET search_path TO pay_ready, public;

-- Data Sources Configuration
CREATE TABLE IF NOT EXISTS pay_ready.data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('gong', 'slack', 'hubspot', 'salesforce')),
    connection_id VARCHAR(255) UNIQUE NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    last_sync_at TIMESTAMP,
    sync_status VARCHAR(50) CHECK (sync_status IN ('pending', 'running', 'succeeded', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Entity Mappings for Resolution
CREATE TABLE IF NOT EXISTS pay_ready.entity_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN ('person', 'company')),
    unified_id UUID NOT NULL,
    source_system VARCHAR(50) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    confidence_score FLOAT DEFAULT 1.0 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_system, source_id)
);

-- Sync State for Checkpointing
CREATE TABLE IF NOT EXISTS pay_ready.sync_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(50) NOT NULL,
    stream_name VARCHAR(100) NOT NULL,
    last_processed_timestamp TIMESTAMP,
    last_processed_id VARCHAR(255),
    checkpoint_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_type, stream_name)
);

-- Interactions Storage
CREATE TABLE IF NOT EXISTS pay_ready.interactions (
    id VARCHAR(255) PRIMARY KEY,
    type VARCHAR(50) NOT NULL CHECK (type IN ('slack_message', 'gong_call_segment', 'hubspot_note', 'salesforce_note')),
    text TEXT,
    metadata JSONB DEFAULT '{}',
    unified_person_id UUID,
    unified_company_id UUID,
    source_system VARCHAR(50),
    source_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics Cache
CREATE TABLE IF NOT EXISTS pay_ready.analytics_cache (
    metric_name VARCHAR(255) PRIMARY KEY,
    metric_value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workflow Execution History
CREATE TABLE IF NOT EXISTS pay_ready.workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_name VARCHAR(100) NOT NULL,
    execution_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    context JSONB DEFAULT '{}',
    error_details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_entity_mappings_unified ON pay_ready.entity_mappings(unified_id);
CREATE INDEX IF NOT EXISTS idx_entity_mappings_source ON pay_ready.entity_mappings(source_system, source_id);
CREATE INDEX IF NOT EXISTS idx_entity_mappings_type ON pay_ready.entity_mappings(entity_type);

CREATE INDEX IF NOT EXISTS idx_sync_state_source ON pay_ready.sync_state(source_type, stream_name);

CREATE INDEX IF NOT EXISTS idx_interactions_person ON pay_ready.interactions(unified_person_id);
CREATE INDEX IF NOT EXISTS idx_interactions_company ON pay_ready.interactions(unified_company_id);
CREATE INDEX IF NOT EXISTS idx_interactions_type ON pay_ready.interactions(type);
CREATE INDEX IF NOT EXISTS idx_interactions_created ON pay_ready.interactions(created_at);
CREATE INDEX IF NOT EXISTS idx_interactions_source ON pay_ready.interactions(source_system, source_id);

CREATE INDEX IF NOT EXISTS idx_workflow_executions_name ON pay_ready.workflow_executions(workflow_name);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON pay_ready.workflow_executions(status);

-- Create update timestamp trigger function
CREATE OR REPLACE FUNCTION pay_ready.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update timestamp triggers
CREATE TRIGGER update_data_sources_updated_at BEFORE UPDATE ON pay_ready.data_sources
    FOR EACH ROW EXECUTE FUNCTION pay_ready.update_updated_at_column();

CREATE TRIGGER update_entity_mappings_updated_at BEFORE UPDATE ON pay_ready.entity_mappings
    FOR EACH ROW EXECUTE FUNCTION pay_ready.update_updated_at_column();

CREATE TRIGGER update_sync_state_updated_at BEFORE UPDATE ON pay_ready.sync_state
    FOR EACH ROW EXECUTE FUNCTION pay_ready.update_updated_at_column();

CREATE TRIGGER update_interactions_updated_at BEFORE UPDATE ON pay_ready.interactions
    FOR EACH ROW EXECUTE FUNCTION pay_ready.update_updated_at_column();

-- Create views for common queries
CREATE OR REPLACE VIEW pay_ready.v_recent_interactions AS
SELECT 
    i.*,
    em_person.metadata->>'name' as person_name,
    em_company.metadata->>'name' as company_name
FROM pay_ready.interactions i
LEFT JOIN pay_ready.entity_mappings em_person 
    ON i.unified_person_id = em_person.unified_id 
    AND em_person.entity_type = 'person'
LEFT JOIN pay_ready.entity_mappings em_company 
    ON i.unified_company_id = em_company.unified_id 
    AND em_company.entity_type = 'company'
WHERE i.created_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY i.created_at DESC;

CREATE OR REPLACE VIEW pay_ready.v_sync_status AS
SELECT 
    ds.source_type,
    ds.connection_id,
    ds.sync_status,
    ds.last_sync_at,
    ss.last_processed_timestamp,
    ss.checkpoint_data,
    CASE 
        WHEN ds.sync_status = 'running' THEN 'Syncing'
        WHEN ss.last_processed_timestamp IS NULL THEN 'Never Processed'
        WHEN ss.last_processed_timestamp < CURRENT_TIMESTAMP - INTERVAL '1 hour' THEN 'Stale'
        ELSE 'Current'
    END as data_freshness
FROM pay_ready.data_sources ds
LEFT JOIN pay_ready.sync_state ss 
    ON ds.source_type = ss.source_type 
    AND ss.stream_name = ds.source_type || '_processing';

-- Grant permissions (adjust as needed)
GRANT USAGE ON SCHEMA pay_ready TO orchestra_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA pay_ready TO orchestra_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA pay_ready TO orchestra_app;

-- Insert initial configuration (example)
INSERT INTO pay_ready.data_sources (source_type, connection_id, config) 
VALUES 
    ('gong', 'gong_connection_placeholder', '{"start_date": "2024-01-01", "region": "us"}'),
    ('slack', 'slack_connection_placeholder', '{"start_date": "2024-01-01", "channels": ["all"]}'),
    ('hubspot', 'hubspot_connection_placeholder', '{"start_date": "2024-01-01", "objects": ["contacts", "companies", "engagements"]}'),
    ('salesforce', 'salesforce_connection_placeholder', '{"start_date": "2024-01-01", "objects": ["Contact", "Account", "Task"]}')
ON CONFLICT (connection_id) DO NOTHING;

-- Add comments for documentation
COMMENT ON SCHEMA pay_ready IS 'Pay Ready domain ETL and orchestration schema';
COMMENT ON TABLE pay_ready.data_sources IS 'Configuration for Airbyte data source connections';
COMMENT ON TABLE pay_ready.entity_mappings IS 'Unified entity resolution mappings across systems';
COMMENT ON TABLE pay_ready.sync_state IS 'Checkpoint state for ETL processing';
COMMENT ON TABLE pay_ready.interactions IS 'Processed and unified interaction data';
COMMENT ON TABLE pay_ready.analytics_cache IS 'Pre-computed analytics metrics for performance';
COMMENT ON TABLE pay_ready.workflow_executions IS 'Prefect workflow execution history and status';