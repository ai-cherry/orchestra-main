-- Roo Mode Executions Table
CREATE TABLE IF NOT EXISTS roo_mode_executions (
    id SERIAL PRIMARY KEY,
    mode VARCHAR(50) NOT NULL,
    task TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    result TEXT,
    model VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Mode Transitions Table
CREATE TABLE IF NOT EXISTS mode_transitions (
    id VARCHAR(100) PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    from_mode VARCHAR(50) NOT NULL,
    to_mode VARCHAR(50) NOT NULL,
    transition_type VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    context JSONB DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_roo_executions_mode ON roo_mode_executions(mode);
CREATE INDEX IF NOT EXISTS idx_roo_executions_created ON roo_mode_executions(created_at);
CREATE INDEX IF NOT EXISTS idx_transitions_session ON mode_transitions(session_id);
CREATE INDEX IF NOT EXISTS idx_transitions_states ON mode_transitions(from_mode, to_mode);
CREATE INDEX IF NOT EXISTS idx_transitions_created ON mode_transitions(created_at);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_roo_executions_updated_at BEFORE UPDATE
    ON roo_mode_executions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transitions_updated_at BEFORE UPDATE
    ON mode_transitions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();