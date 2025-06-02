-- Data Ingestion System Schema
-- This migration creates the schema and tables for the data ingestion system

-- Create schema for data ingestion
CREATE SCHEMA IF NOT EXISTS data_ingestion;

-- Set search path
SET search_path TO data_ingestion, public;

-- Create enum types
CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled');
CREATE TYPE source_type AS ENUM ('slack', 'gong', 'salesforce', 'looker', 'hubspot', 'unknown');

-- File imports table - tracks all uploaded files
CREATE TABLE file_imports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    source_type source_type NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    upload_timestamp TIMESTAMPTZ DEFAULT NOW(),
    processing_status processing_status DEFAULT 'pending',
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    processing_duration_ms INTEGER,
    error_message TEXT,
    s3_key VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT file_size_positive CHECK (file_size > 0)
);

-- Parsed content table - stores processed data from files
CREATE TABLE parsed_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_import_id UUID REFERENCES file_imports(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL,
    source_id VARCHAR(255),
    content TEXT NOT NULL,
    content_hash VARCHAR(64) GENERATED ALWAYS AS (encode(sha256(content::bytea), 'hex')) STORED,
    metadata JSONB DEFAULT '{}',
    vector_id VARCHAR(255),
    tokens_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    -- Ensure no duplicate content within the same file
    UNIQUE(file_import_id, content_hash)
);

-- Query cache table - caches search results
CREATE TABLE query_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR(64) NOT NULL,
    query_text TEXT NOT NULL,
    sources_searched TEXT[] NOT NULL,
    result_data JSONB NOT NULL,
    result_count INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    hit_count INTEGER DEFAULT 1,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(query_hash)
);

-- Processing queue table - manages file processing tasks
CREATE TABLE processing_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_import_id UUID REFERENCES file_imports(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 5,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    locked_at TIMESTAMPTZ,
    locked_by VARCHAR(255),
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT priority_range CHECK (priority >= 1 AND priority <= 10)
);

-- API sync configuration table
CREATE TABLE api_sync_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type source_type NOT NULL UNIQUE,
    enabled BOOLEAN DEFAULT false,
    sync_interval_minutes INTEGER DEFAULT 60,
    last_sync_at TIMESTAMPTZ,
    next_sync_at TIMESTAMPTZ,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT sync_interval_positive CHECK (sync_interval_minutes > 0)
);

-- Create indexes for performance
CREATE INDEX idx_file_imports_status_created ON file_imports(processing_status, created_at DESC);
CREATE INDEX idx_file_imports_source_type ON file_imports(source_type);
CREATE INDEX idx_file_imports_created_by ON file_imports(created_by);
CREATE INDEX idx_file_imports_s3_key ON file_imports(s3_key) WHERE s3_key IS NOT NULL;

CREATE INDEX idx_parsed_content_file_import ON parsed_content(file_import_id);
CREATE INDEX idx_parsed_content_vector ON parsed_content(vector_id) WHERE vector_id IS NOT NULL;
CREATE INDEX idx_parsed_content_content_type ON parsed_content(content_type);
CREATE INDEX idx_parsed_content_source_id ON parsed_content(source_id) WHERE source_id IS NOT NULL;
-- Full text search index
CREATE INDEX idx_parsed_content_search ON parsed_content USING gin(to_tsvector('english', content));

CREATE INDEX idx_query_cache_expires ON query_cache(expires_at) WHERE expires_at > NOW();
CREATE INDEX idx_query_cache_hash ON query_cache(query_hash);
CREATE INDEX idx_query_cache_last_accessed ON query_cache(last_accessed_at DESC);

CREATE INDEX idx_processing_queue_scheduled ON processing_queue(scheduled_at) 
    WHERE completed_at IS NULL AND locked_at IS NULL;
CREATE INDEX idx_processing_queue_file_import ON processing_queue(file_import_id);

-- Create partitioned tables for scale
-- Partition parsed_content by month
CREATE TABLE parsed_content_2025_01 PARTITION OF parsed_content
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE parsed_content_2025_02 PARTITION OF parsed_content
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
-- Add more partitions as needed

-- Create update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_file_imports_updated_at BEFORE UPDATE ON file_imports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_sync_config_updated_at BEFORE UPDATE ON api_sync_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to clean expired cache entries
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM query_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to get processing statistics
CREATE OR REPLACE FUNCTION get_processing_stats()
RETURNS TABLE (
    status processing_status,
    count BIGINT,
    avg_duration_ms NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        fi.processing_status,
        COUNT(*) as count,
        AVG(fi.processing_duration_ms)::NUMERIC as avg_duration_ms
    FROM file_imports fi
    GROUP BY fi.processing_status;
END;
$$ LANGUAGE plpgsql;

-- Create view for active processing tasks
CREATE VIEW active_processing_tasks AS
SELECT 
    pq.id as queue_id,
    fi.id as file_id,
    fi.filename,
    fi.source_type,
    fi.file_size,
    pq.priority,
    pq.retry_count,
    pq.scheduled_at,
    pq.locked_at,
    pq.locked_by
FROM processing_queue pq
JOIN file_imports fi ON pq.file_import_id = fi.id
WHERE pq.completed_at IS NULL
ORDER BY pq.priority DESC, pq.scheduled_at ASC;

-- Create materialized view for source statistics
CREATE MATERIALIZED VIEW source_statistics AS
SELECT 
    source_type,
    COUNT(DISTINCT file_import_id) as file_count,
    COUNT(*) as record_count,
    SUM(tokens_count) as total_tokens,
    MAX(created_at) as last_updated
FROM parsed_content pc
JOIN file_imports fi ON pc.file_import_id = fi.id
GROUP BY source_type;

-- Create index on materialized view
CREATE INDEX idx_source_statistics_source ON source_statistics(source_type);

-- Grant permissions (adjust based on your user roles)
GRANT USAGE ON SCHEMA data_ingestion TO authenticated;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA data_ingestion TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA data_ingestion TO authenticated;

-- Add comments for documentation
COMMENT ON SCHEMA data_ingestion IS 'Schema for multi-source data ingestion system';
COMMENT ON TABLE file_imports IS 'Tracks all uploaded files and their processing status';
COMMENT ON TABLE parsed_content IS 'Stores parsed and processed content from imported files';
COMMENT ON TABLE query_cache IS 'Caches search query results for performance';
COMMENT ON TABLE processing_queue IS 'Manages asynchronous file processing tasks';
COMMENT ON TABLE api_sync_config IS 'Configuration for automated API data synchronization';