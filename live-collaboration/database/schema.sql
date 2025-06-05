-- Live Collaboration Database Schema
-- Purpose: Enable real-time file sync between Cursor IDE and Manus AI

-- Sessions table to track active collaboration sessions
CREATE TABLE collaboration_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_name VARCHAR(200) NOT NULL,
    cursor_session_id VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    workspace_path TEXT,
    manus_connected BOOLEAN DEFAULT false
);

-- Live files being tracked in real-time
CREATE TABLE live_files (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES collaboration_sessions(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    relative_path VARCHAR(500) NOT NULL, -- Path relative to workspace root
    content TEXT,
    content_hash VARCHAR(64), -- SHA256 hash for change detection
    file_size INTEGER,
    last_modified TIMESTAMP DEFAULT NOW(),
    cursor_last_edit TIMESTAMP,
    manus_visible BOOLEAN DEFAULT true,
    sync_status VARCHAR(20) DEFAULT 'synced', -- 'synced', 'pending', 'conflict'
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(session_id, relative_path)
);

-- Real-time changes stream for live collaboration
CREATE TABLE live_changes (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES live_files(id) ON DELETE CASCADE,
    session_id UUID REFERENCES collaboration_sessions(id) ON DELETE CASCADE,
    change_type VARCHAR(50) NOT NULL, -- 'insert', 'delete', 'modify', 'create', 'rename', 'delete_file'
    line_number INTEGER,
    column_number INTEGER,
    content_delta TEXT, -- JSON with change details
    content_before TEXT, -- Previous content for rollback
    content_after TEXT,  -- New content
    change_size INTEGER, -- Size of change in characters
    timestamp TIMESTAMP DEFAULT NOW(),
    cursor_user VARCHAR(100) DEFAULT 'cursor_user',
    is_applied BOOLEAN DEFAULT false
);

-- Manus activity tracking
CREATE TABLE manus_activity (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES collaboration_sessions(id) ON DELETE CASCADE,
    activity_type VARCHAR(50), -- 'view_file', 'request_explanation', 'suggest_change'
    file_id INTEGER REFERENCES live_files(id) ON DELETE SET NULL,
    activity_data JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Real-time cursors/selections for advanced collaboration
CREATE TABLE live_cursors (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES collaboration_sessions(id) ON DELETE CASCADE,
    file_id INTEGER REFERENCES live_files(id) ON DELETE CASCADE,
    user_type VARCHAR(20) NOT NULL, -- 'cursor', 'manus'
    user_id VARCHAR(100),
    cursor_line INTEGER,
    cursor_column INTEGER,
    selection_start_line INTEGER,
    selection_start_column INTEGER,
    selection_end_line INTEGER,
    selection_end_column INTEGER,
    last_updated TIMESTAMP DEFAULT NOW(),
    UNIQUE(session_id, file_id, user_type, user_id)
);

-- Indexes for performance
CREATE INDEX idx_live_files_session_id ON live_files(session_id);
CREATE INDEX idx_live_files_path ON live_files(relative_path);
CREATE INDEX idx_live_changes_file_id ON live_changes(file_id);
CREATE INDEX idx_live_changes_timestamp ON live_changes(timestamp DESC);
CREATE INDEX idx_collaboration_sessions_active ON collaboration_sessions(is_active) WHERE is_active = true;
CREATE INDEX idx_live_cursors_session_file ON live_cursors(session_id, file_id);

-- Function to update session activity
CREATE OR REPLACE FUNCTION update_session_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE collaboration_sessions 
    SET last_active = NOW() 
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers to auto-update session activity
CREATE TRIGGER update_session_on_file_change
    AFTER INSERT OR UPDATE ON live_files
    FOR EACH ROW EXECUTE FUNCTION update_session_activity();

CREATE TRIGGER update_session_on_change_log
    AFTER INSERT ON live_changes
    FOR EACH ROW EXECUTE FUNCTION update_session_activity();

-- Function to clean up old sessions (older than 24 hours inactive)
CREATE OR REPLACE FUNCTION cleanup_old_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    UPDATE collaboration_sessions 
    SET is_active = false 
    WHERE last_active < NOW() - INTERVAL '24 hours' 
    AND is_active = true;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- View for active collaboration overview
CREATE VIEW active_collaboration_overview AS
SELECT 
    cs.id,
    cs.session_name,
    cs.workspace_path,
    cs.created_at,
    cs.last_active,
    cs.manus_connected,
    COUNT(lf.id) as file_count,
    COUNT(CASE WHEN lf.sync_status != 'synced' THEN 1 END) as pending_syncs,
    MAX(lc.timestamp) as last_change
FROM collaboration_sessions cs
LEFT JOIN live_files lf ON cs.id = lf.session_id
LEFT JOIN live_changes lc ON cs.id = lc.session_id
WHERE cs.is_active = true
GROUP BY cs.id, cs.session_name, cs.workspace_path, cs.created_at, cs.last_active, cs.manus_connected
ORDER BY cs.last_active DESC;

-- View for file change activity
CREATE VIEW file_change_activity AS
SELECT 
    lf.relative_path,
    lf.last_modified,
    lf.sync_status,
    COUNT(lc.id) as change_count,
    MAX(lc.timestamp) as last_change_time,
    lc.change_type as last_change_type
FROM live_files lf
LEFT JOIN live_changes lc ON lf.id = lc.file_id
WHERE lf.session_id IN (SELECT id FROM collaboration_sessions WHERE is_active = true)
GROUP BY lf.id, lf.relative_path, lf.last_modified, lf.sync_status, lc.change_type
ORDER BY MAX(lc.timestamp) DESC NULLS LAST; 