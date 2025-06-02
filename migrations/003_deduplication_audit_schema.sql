-- Deduplication Audit Log Schema
-- This migration adds comprehensive audit logging for duplicate detection and resolution

-- Add deduplication audit log table
CREATE TABLE IF NOT EXISTS data_ingestion.deduplication_audit_log (
    id UUID PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    upload_channel VARCHAR(50),
    user_id UUID REFERENCES auth.users(id),
    session_id VARCHAR(255),
    content_id VARCHAR(255),
    duplicate_match JSONB,
    resolution_result JSONB,
    metadata JSONB DEFAULT '{}',
    error_details TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_event_type CHECK (
        event_type IN (
            'duplicate_check',
            'duplicate_detected',
            'resolution_applied',
            'manual_review_queued',
            'manual_review_completed',
            'bulk_operation',
            'error'
        )
    )
);

-- Add indexes for performance
CREATE INDEX idx_dedup_audit_timestamp ON data_ingestion.deduplication_audit_log(timestamp DESC);
CREATE INDEX idx_dedup_audit_event_type ON data_ingestion.deduplication_audit_log(event_type);
CREATE INDEX idx_dedup_audit_user_id ON data_ingestion.deduplication_audit_log(user_id);
CREATE INDEX idx_dedup_audit_content_id ON data_ingestion.deduplication_audit_log(content_id);
CREATE INDEX idx_dedup_audit_upload_channel ON data_ingestion.deduplication_audit_log(upload_channel);

-- Add duplicate resolution tracking to parsed_content
ALTER TABLE data_ingestion.parsed_content 
ADD COLUMN IF NOT EXISTS duplicate_of UUID REFERENCES data_ingestion.parsed_content(id),
ADD COLUMN IF NOT EXISTS duplicate_resolution VARCHAR(50),
ADD COLUMN IF NOT EXISTS duplicate_score NUMERIC(3,2);

-- Add index for duplicate tracking
CREATE INDEX idx_parsed_content_duplicate_of ON data_ingestion.parsed_content(duplicate_of) 
WHERE duplicate_of IS NOT NULL;

-- Manual review queue table
CREATE TABLE IF NOT EXISTS data_ingestion.manual_review_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL,
    existing_content_id UUID NOT NULL,
    duplicate_type VARCHAR(50) NOT NULL,
    similarity_score NUMERIC(3,2) NOT NULL,
    new_content JSONB NOT NULL,
    existing_content JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    assigned_to UUID REFERENCES auth.users(id),
    resolution_decision VARCHAR(50),
    resolution_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES auth.users(id),
    
    -- Constraints
    CONSTRAINT valid_status CHECK (
        status IN ('pending', 'in_review', 'resolved', 'expired')
    ),
    CONSTRAINT valid_resolution CHECK (
        resolution_decision IN ('keep_existing', 'replace', 'merge', 'keep_both')
    )
);

-- Indexes for manual review queue
CREATE INDEX idx_review_queue_status ON data_ingestion.manual_review_queue(status);
CREATE INDEX idx_review_queue_assigned ON data_ingestion.manual_review_queue(assigned_to);
CREATE INDEX idx_review_queue_created ON data_ingestion.manual_review_queue(created_at DESC);

-- Deduplication statistics materialized view
CREATE MATERIALIZED VIEW IF NOT EXISTS data_ingestion.deduplication_stats AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    upload_channel,
    COUNT(*) FILTER (WHERE event_type = 'duplicate_check') as total_checks,
    COUNT(*) FILTER (WHERE event_type = 'duplicate_detected') as duplicates_found,
    COUNT(*) FILTER (WHERE event_type = 'resolution_applied') as resolutions_applied,
    COUNT(*) FILTER (WHERE event_type = 'manual_review_queued') as manual_reviews,
    COUNT(*) FILTER (WHERE event_type = 'error') as errors,
    AVG((duplicate_match->>'similarity_score')::numeric) as avg_similarity_score,
    COUNT(DISTINCT user_id) as unique_users
FROM data_ingestion.deduplication_audit_log
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('hour', timestamp), upload_channel;

-- Create index on materialized view
CREATE INDEX idx_dedup_stats_hour ON data_ingestion.deduplication_stats(hour DESC);

-- Function to get duplicate chain
CREATE OR REPLACE FUNCTION data_ingestion.get_duplicate_chain(content_id UUID)
RETURNS TABLE (
    id UUID,
    content TEXT,
    source_type VARCHAR,
    created_at TIMESTAMPTZ,
    duplicate_score NUMERIC,
    level INTEGER
) AS $$
WITH RECURSIVE duplicate_chain AS (
    -- Base case: start with the given content
    SELECT 
        pc.id,
        pc.content,
        fi.source_type,
        pc.created_at,
        pc.duplicate_score,
        0 as level
    FROM data_ingestion.parsed_content pc
    JOIN data_ingestion.file_imports fi ON pc.file_import_id = fi.id
    WHERE pc.id = content_id
    
    UNION ALL
    
    -- Recursive case: find all duplicates
    SELECT 
        pc.id,
        pc.content,
        fi.source_type,
        pc.created_at,
        pc.duplicate_score,
        dc.level + 1
    FROM data_ingestion.parsed_content pc
    JOIN data_ingestion.file_imports fi ON pc.file_import_id = fi.id
    JOIN duplicate_chain dc ON pc.duplicate_of = dc.id
    WHERE dc.level < 10  -- Prevent infinite recursion
)
SELECT * FROM duplicate_chain
ORDER BY level, created_at;
$$ LANGUAGE sql;

-- Function to merge duplicate content
CREATE OR REPLACE FUNCTION data_ingestion.merge_duplicate_content(
    keep_id UUID,
    merge_id UUID,
    merge_metadata JSONB DEFAULT '{}'
)
RETURNS UUID AS $$
DECLARE
    merged_metadata JSONB;
    result_id UUID;
BEGIN
    -- Get existing metadata from both records
    SELECT 
        COALESCE(k.metadata, '{}') || COALESCE(m.metadata, '{}') || merge_metadata
    INTO merged_metadata
    FROM data_ingestion.parsed_content k
    CROSS JOIN data_ingestion.parsed_content m
    WHERE k.id = keep_id AND m.id = merge_id;
    
    -- Update the kept record with merged metadata
    UPDATE data_ingestion.parsed_content
    SET 
        metadata = merged_metadata,
        updated_at = NOW()
    WHERE id = keep_id
    RETURNING id INTO result_id;
    
    -- Mark the merged record as duplicate
    UPDATE data_ingestion.parsed_content
    SET 
        duplicate_of = keep_id,
        duplicate_resolution = 'merged',
        updated_at = NOW()
    WHERE id = merge_id;
    
    RETURN result_id;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-expire old manual review items
CREATE OR REPLACE FUNCTION data_ingestion.expire_old_reviews()
RETURNS trigger AS $$
BEGIN
    UPDATE data_ingestion.manual_review_queue
    SET status = 'expired'
    WHERE status = 'pending' 
    AND created_at < NOW() - INTERVAL '7 days';
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_expire_reviews
    AFTER INSERT ON data_ingestion.manual_review_queue
    FOR EACH STATEMENT
    EXECUTE FUNCTION data_ingestion.expire_old_reviews();

-- Grant permissions
GRANT SELECT, INSERT ON data_ingestion.deduplication_audit_log TO authenticated;
GRANT SELECT, INSERT, UPDATE ON data_ingestion.manual_review_queue TO authenticated;
GRANT SELECT ON data_ingestion.deduplication_stats TO authenticated;
GRANT EXECUTE ON FUNCTION data_ingestion.get_duplicate_chain TO authenticated;
GRANT EXECUTE ON FUNCTION data_ingestion.merge_duplicate_content TO authenticated;

-- Comments for documentation
COMMENT ON TABLE data_ingestion.deduplication_audit_log IS 'Comprehensive audit trail for all duplicate detection and resolution operations';
COMMENT ON TABLE data_ingestion.manual_review_queue IS 'Queue for duplicates requiring manual review and resolution';
COMMENT ON MATERIALIZED VIEW data_ingestion.deduplication_stats IS 'Aggregated statistics for deduplication operations';
COMMENT ON FUNCTION data_ingestion.get_duplicate_chain IS 'Retrieves the complete chain of duplicate relationships for a content item';
COMMENT ON FUNCTION data_ingestion.merge_duplicate_content IS 'Merges metadata from duplicate content items';