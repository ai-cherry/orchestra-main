-- optimized_vector_indices.sql for AI Orchestra
-- Vector search optimization for AlloyDB PostgreSQL 
-- Apply to enhance vector search performance in AI Orchestra project

-- Check if pgvector extension is installed, if not install it
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    ) THEN
        CREATE EXTENSION vector;
        RAISE NOTICE 'pgvector extension installed';
    ELSE
        RAISE NOTICE 'pgvector extension already installed';
    END IF;
END
$$;

-- PostgreSQL performance parameters
-- Increase shared buffers for better caching
ALTER SYSTEM SET shared_buffers = '4GB';

-- Increase effective cache size assumption
ALTER SYSTEM SET effective_cache_size = '12GB';

-- Optimize work memory for vector operations
ALTER SYSTEM SET work_mem = '64MB';

-- Connection pooling optimization for Cloud Run dynamic scaling
ALTER SYSTEM SET max_connections = 500;
ALTER SYSTEM SET idle_in_transaction_session_timeout = '30s';
ALTER SYSTEM SET statement_timeout = '30s';

-- Optimize for parallel query execution
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers = 8;
ALTER SYSTEM SET parallel_tuple_cost = 0.1;
ALTER SYSTEM SET parallel_setup_cost = 100;

-- Vector-specific performance optimizations
-- Increase IVF lists for better search performance (default is 2000)
ALTER SYSTEM SET ivfflat.lists = 4000;

-- Enable vector executor for better performance
ALTER SYSTEM SET enable_vector_executor = on;

-- Apply settings without restarting
SELECT pg_reload_conf();

-- Create optimized vector storage table if it doesn't exist
-- This is an example schema - adapt to your actual needs
CREATE TABLE IF NOT EXISTS memory_vectors (
    id SERIAL PRIMARY KEY,
    content_id TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,  -- Matches model dimension (e.g., for OpenAI embeddings)
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for fast lookups by content_id
CREATE INDEX IF NOT EXISTS idx_memory_vectors_content_id 
ON memory_vectors(content_id);

-- Create vector index for similarity search
-- IVF flat index is a good balance of speed and accuracy
CREATE INDEX IF NOT EXISTS idx_memory_vectors_embedding 
ON memory_vectors USING ivfflat (embedding vector_l2_ops)
WITH (lists = 4000);  -- Optimized list count

-- Create GIN index for fast metadata searches (if you query on JSON fields)
CREATE INDEX IF NOT EXISTS idx_memory_vectors_metadata
ON memory_vectors USING GIN (metadata);

-- Create a hypertable for time-based partitioning (if using TimescaleDB)
-- This is optional but beneficial for time-series data
-- Uncomment if using TimescaleDB
/*
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
    ) THEN
        PERFORM create_hypertable('memory_vectors', 'created_at', 
                                 chunk_time_interval => INTERVAL '1 week',
                                 if_not_exists => TRUE);
        RAISE NOTICE 'Created hypertable for memory_vectors';
    END IF;
END
$$;
*/

-- Connection pooling functions
-- Create a function to monitor current connections
CREATE OR REPLACE FUNCTION get_connection_stats()
RETURNS TABLE (
    total_connections INT,
    active_connections INT,
    idle_connections INT,
    idle_in_transaction INT
) LANGUAGE SQL AS $$
    SELECT 
        count(*) AS total_connections,
        count(*) FILTER (WHERE state = 'active') AS active_connections,
        count(*) FILTER (WHERE state = 'idle') AS idle_connections,
        count(*) FILTER (WHERE state = 'idle in transaction') AS idle_in_transaction
    FROM pg_stat_activity
    WHERE backend_type = 'client backend';
$$;

-- Example of creating a view for common queries
CREATE OR REPLACE VIEW recent_memory_vectors AS
SELECT * FROM memory_vectors
WHERE created_at > (CURRENT_TIMESTAMP - INTERVAL '7 days')
ORDER BY created_at DESC;

-- Function for vector similarity search
CREATE OR REPLACE FUNCTION vector_search(
    query_embedding VECTOR(1536),
    similarity_threshold FLOAT,
    max_results INT
) 
RETURNS TABLE (
    id INT,
    content_id TEXT,
    similarity FLOAT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        mv.id,
        mv.content_id,
        1 - (mv.embedding <-> query_embedding) AS similarity,
        mv.metadata,
        mv.created_at
    FROM
        memory_vectors mv
    WHERE
        1 - (mv.embedding <-> query_embedding) > similarity_threshold
    ORDER BY
        mv.embedding <-> query_embedding
    LIMIT max_results;
END;
$$;

-- Performance monitoring functions
CREATE OR REPLACE FUNCTION check_vector_index_usage()
RETURNS TABLE (
    indexname TEXT,
    indexdef TEXT,
    idx_scan BIGINT,
    idx_tup_read BIGINT,
    idx_tup_fetch BIGINT
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.indexrelname AS indexname,
        pg_get_indexdef(i.indexrelid) AS indexdef,
        s.idx_scan,
        s.idx_tup_read,
        s.idx_tup_fetch
    FROM
        pg_stat_user_indexes s
        JOIN pg_index x ON s.indexrelid = x.indexrelid
        JOIN pg_indexes i ON i.indexname = s.indexrelname
    WHERE
        s.relname = 'memory_vectors'
    ORDER BY
        s.idx_scan DESC;
END;
$$;

-- Run ANALYZE to update statistics
ANALYZE memory_vectors;

-- Output confirmation
DO $$
BEGIN
    RAISE NOTICE 'Vector optimization complete - IVF lists set to 4000';
    RAISE NOTICE 'Created vector indexes and performance monitoring functions';
    RAISE NOTICE 'Connection pooling optimized for Cloud Run scaling';
    RAISE NOTICE 'Performance monitoring available through check_vector_index_usage() and get_connection_stats()';
END
$$;