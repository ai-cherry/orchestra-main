-- AlloyDB Schema for AGI Baby Cherry Project
-- This script defines the database structure for storing agent memory data
-- synchronized from Redis, including vector embeddings for hybrid search.

-- Create the memories table to store agent memory data
CREATE TABLE IF NOT EXISTS memories (
    id VARCHAR(255) PRIMARY KEY,
    vector VECTOR(1536) NOT NULL,  -- Vector embedding with dimension 1536 as per agent_memory.yaml
    data TEXT NOT NULL,            -- JSON or serialized data content
    version BIGINT NOT NULL DEFAULT 0,  -- Version for conflict resolution
    checksum BIGINT NOT NULL,      -- CRC32 checksum for data integrity
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create an index for vector similarity search using IVFFlat with L2 distance
CREATE INDEX IF NOT EXISTS agent_context ON memories 
USING ivfflat (vector vector_l2_ops) 
WITH (lists = 2000, quantizer='SQ8');

-- Create an index on version for faster conflict resolution queries
CREATE INDEX IF NOT EXISTS idx_memories_version ON memories (version);

-- Create an index on updated_at for efficient time-based queries
CREATE INDEX IF NOT EXISTS idx_memories_updated_at ON memories (updated_at);

-- Function to update the updated_at timestamp on row update
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update the updated_at timestamp
CREATE TRIGGER update_memories_timestamp
    BEFORE UPDATE ON memories
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Comment on the table for documentation
COMMENT ON TABLE memories IS 'Table storing agent memory data synchronized from Redis, with vector embeddings for similarity search and version control for conflict resolution.';

-- Comments on columns for clarity
COMMENT ON COLUMN memories.id IS 'Unique identifier for the memory record.';
COMMENT ON COLUMN memories.vector IS 'Vector embedding of dimension 1536 for similarity search.';
COMMENT ON COLUMN memories.data IS 'Serialized content of the memory item.';
COMMENT ON COLUMN memories.version IS 'Version number for conflict resolution during synchronization.';
COMMENT ON COLUMN memories.checksum IS 'CRC32 checksum for data integrity validation.';
COMMENT ON COLUMN memories.created_at IS 'Timestamp when the record was created.';
COMMENT ON COLUMN memories.updated_at IS 'Timestamp when the record was last updated.';