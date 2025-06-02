-- Factory AI Integration Schema
-- This schema supports the unified context management system

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Context metadata table
CREATE TABLE IF NOT EXISTS factory_context_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_id VARCHAR(255) UNIQUE NOT NULL,
    parent_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    source VARCHAR(50) NOT NULL CHECK (source IN ('factory', 'mcp')),
    data JSONB NOT NULL,
    embeddings VECTOR(1536), -- For Weaviate sync
    CONSTRAINT fk_parent_context 
        FOREIGN KEY (parent_id) 
        REFERENCES factory_context_metadata(context_id)
        ON DELETE SET NULL
);

-- Indexes for context metadata
CREATE INDEX IF NOT EXISTS idx_context_parent ON factory_context_metadata(parent_id);
CREATE INDEX IF NOT EXISTS idx_context_updated ON factory_context_metadata(updated_at);
CREATE INDEX IF NOT EXISTS idx_context_source ON factory_context_metadata(source);
CREATE INDEX IF NOT EXISTS idx_context_embeddings ON factory_context_metadata USING ivfflat (embeddings vector_cosine_ops);

-- Context version history
CREATE TABLE IF NOT EXISTS factory_context_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_id VARCHAR(255) NOT NULL,
    version INTEGER NOT NULL,
    data JSONB NOT NULL,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_type VARCHAR(50) CHECK (change_type IN ('create', 'update', 'merge')),
    UNIQUE(context_id, version),
    FOREIGN KEY (context_id) REFERENCES factory_context_metadata(context_id) ON DELETE CASCADE
);

-- Indexes for version history
CREATE INDEX IF NOT EXISTS idx_version_context ON factory_context_versions(context_id);
CREATE INDEX IF NOT EXISTS idx_version_changed ON factory_context_versions(changed_at);

-- Cache entries table
CREATE TABLE IF NOT EXISTS factory_cache_entries (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for cache entries
CREATE INDEX IF NOT EXISTS idx_cache_expires ON factory_cache_entries(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_cache_accessed ON factory_cache_entries(last_accessed);
CREATE INDEX IF NOT EXISTS idx_cache_access_count ON factory_cache_entries(access_count DESC);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_factory_context_metadata_updated_at 
    BEFORE UPDATE ON factory_context_metadata 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache_entries()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM factory_cache_entries
    WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- View for cache statistics
CREATE OR REPLACE VIEW factory_cache_stats AS
SELECT 
    COUNT(*) as total_entries,
    COUNT(CASE WHEN expires_at IS NULL THEN 1 END) as permanent_entries,
    COUNT(CASE WHEN expires_at IS NOT NULL THEN 1 END) as expiring_entries,
    COUNT(CASE WHEN expires_at < CURRENT_TIMESTAMP THEN 1 END) as expired_entries,
    AVG(access_count) as avg_access_count,
    MAX(access_count) as max_access_count,
    MIN(created_at) as oldest_entry,
    MAX(created_at) as newest_entry
FROM factory_cache_entries;

-- View for context statistics
CREATE OR REPLACE VIEW factory_context_stats AS
SELECT 
    COUNT(DISTINCT fcm.context_id) as total_contexts,
    COUNT(DISTINCT fcm.parent_id) as contexts_with_children,
    AVG(fcm.version) as avg_version,
    MAX(fcm.version) as max_version,
    COUNT(DISTINCT fcv.id) as total_versions,
    COUNT(CASE WHEN fcm.source = 'factory' THEN 1 END) as factory_contexts,
    COUNT(CASE WHEN fcm.source = 'mcp' THEN 1 END) as mcp_contexts,
    MIN(fcm.created_at) as oldest_context,
    MAX(fcm.created_at) as newest_context
FROM factory_context_metadata fcm
LEFT JOIN factory_context_versions fcv ON fcm.context_id = fcv.context_id;

-- Permissions (adjust as needed for your database users)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;