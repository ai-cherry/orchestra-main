-- Enhanced conversations table for Sophia
CREATE TABLE IF NOT EXISTS enhanced_conversations (
    id SERIAL PRIMARY KEY,
    gong_call_id VARCHAR(255) UNIQUE,
    title TEXT,
    duration INTEGER,
    apartment_relevance DECIMAL(5,2),
    business_value DECIMAL(12,2),
    call_outcome VARCHAR(100),
    competitive_mentions JSONB,
    sophia_insights JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_apartment_relevance ON enhanced_conversations(apartment_relevance);
CREATE INDEX IF NOT EXISTS idx_business_value ON enhanced_conversations(business_value);
CREATE INDEX IF NOT EXISTS idx_call_outcome ON enhanced_conversations(call_outcome);
