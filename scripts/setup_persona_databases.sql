-- Orchestra AI Persona Database Setup
-- Creates dedicated schemas and tables for Cherry, Sophia, and Karen
-- Run this script on PostgreSQL to set up persona-specific database sections

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- CHERRY SCHEMA - Personal Assistant & General AI Operations
-- ========================================

CREATE SCHEMA IF NOT EXISTS cherry;

-- Cherry conversations and interactions
CREATE TABLE IF NOT EXISTS cherry.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    message_count INTEGER DEFAULT 0,
    context_summary TEXT,
    personality_mode VARCHAR(50) DEFAULT 'friendly',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Cherry tasks and reminders
CREATE TABLE IF NOT EXISTS cherry.tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'pending',
    due_date TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    tags TEXT[]
);

-- Cherry personal data and preferences
CREATE TABLE IF NOT EXISTS cherry.user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    preference_category VARCHAR(100) NOT NULL,
    preference_key VARCHAR(100) NOT NULL,
    preference_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, preference_category, preference_key)
);

-- Cherry knowledge base
CREATE TABLE IF NOT EXISTS cherry.knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    tags TEXT[],
    source VARCHAR(255),
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- SOPHIA SCHEMA - Pay Ready Financial Operations
-- ========================================

CREATE SCHEMA IF NOT EXISTS sophia;

-- Financial transactions table (already defined in server, but ensuring it exists)
CREATE TABLE IF NOT EXISTS sophia.financial_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    transaction_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    merchant_id VARCHAR(255),
    customer_id VARCHAR(255),
    payment_method VARCHAR(50),
    processing_fee DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    metadata JSONB,
    risk_score DECIMAL(3,2),
    compliance_flags TEXT[],
    CONSTRAINT valid_amount CHECK (amount > 0),
    CONSTRAINT valid_risk_score CHECK (risk_score >= 0 AND risk_score <= 1)
);

-- Business intelligence metrics
CREATE TABLE IF NOT EXISTS sophia.business_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    dimension_1 VARCHAR(100),
    dimension_2 VARCHAR(100),
    dimension_3 VARCHAR(100),
    time_period VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(100),
    metadata JSONB,
    UNIQUE(metric_name, time_period, dimension_1, dimension_2, dimension_3)
);

-- Large data processing jobs
CREATE TABLE IF NOT EXISTS sophia.data_processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_name VARCHAR(255) NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    file_path TEXT,
    file_size_mb DECIMAL(10,2),
    records_total INTEGER,
    records_processed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    processing_config JSONB,
    results_summary JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Financial reports and analysis
CREATE TABLE IF NOT EXISTS sophia.financial_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_name VARCHAR(255) NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    report_period VARCHAR(20) NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_points INTEGER,
    key_insights TEXT[],
    recommendations TEXT[],
    risk_factors TEXT[],
    report_data JSONB,
    file_path TEXT,
    status VARCHAR(20) DEFAULT 'active'
);

-- Customer financial profiles
CREATE TABLE IF NOT EXISTS sophia.customer_financial_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(255) UNIQUE NOT NULL,
    total_transaction_volume DECIMAL(15,2) DEFAULT 0,
    average_transaction_amount DECIMAL(10,2) DEFAULT 0,
    transaction_count INTEGER DEFAULT 0,
    risk_rating VARCHAR(20) DEFAULT 'low',
    credit_score INTEGER,
    payment_history_score DECIMAL(3,2),
    last_transaction_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    profile_data JSONB
);

-- ========================================
-- KAREN SCHEMA - Healthcare & ParagonRX Operations
-- ========================================

CREATE SCHEMA IF NOT EXISTS karen;

-- Healthcare compliance tracking
CREATE TABLE IF NOT EXISTS karen.healthcare_compliance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    compliance_id VARCHAR(255) UNIQUE NOT NULL,
    regulation_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    due_date DATE,
    description TEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    assigned_to VARCHAR(255),
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    compliance_score DECIMAL(3,2)
);

-- ParagonRX operations
CREATE TABLE IF NOT EXISTS karen.paragonrx_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_id VARCHAR(255) UNIQUE NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    patient_id VARCHAR(255), -- HIPAA: Will be anonymized/hashed
    medication VARCHAR(255),
    dosage VARCHAR(100),
    quantity INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    pharmacist VARCHAR(255),
    physician VARCHAR(255),
    prescription_date DATE,
    fill_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Healthcare audit logs (HIPAA compliant)
CREATE TABLE IF NOT EXISTS karen.healthcare_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    log_id VARCHAR(255) UNIQUE NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255), -- Anonymized/hashed
    user_id VARCHAR(255),
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    action_details JSONB,
    compliance_flags TEXT[],
    severity VARCHAR(20) DEFAULT 'info'
);

-- Medical protocols and procedures
CREATE TABLE IF NOT EXISTS karen.medical_protocols (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_id VARCHAR(255) UNIQUE NOT NULL,
    protocol_name VARCHAR(255) NOT NULL,
    protocol_version VARCHAR(20) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    steps JSONB,
    compliance_requirements TEXT[],
    last_review_date DATE,
    next_review_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quality metrics and KPIs
CREATE TABLE IF NOT EXISTS karen.quality_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    measurement_period VARCHAR(20) NOT NULL,
    facility_id VARCHAR(100),
    department VARCHAR(100),
    target_value DECIMAL(10,4),
    threshold_min DECIMAL(10,4),
    threshold_max DECIMAL(10,4),
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- ========================================
-- SHARED TABLES - Cross-Persona Data
-- ========================================

CREATE SCHEMA IF NOT EXISTS shared;

-- System configuration
CREATE TABLE IF NOT EXISTS shared.system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    config_type VARCHAR(50) DEFAULT 'string',
    description TEXT,
    persona_scope TEXT[], -- Which personas can access this config
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inter-persona communication logs
CREATE TABLE IF NOT EXISTS shared.inter_persona_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_persona VARCHAR(20) NOT NULL,
    target_persona VARCHAR(20) NOT NULL,
    interaction_type VARCHAR(50) NOT NULL,
    message_content TEXT,
    context_data JSONB,
    response_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending'
);

-- Global analytics and insights
CREATE TABLE IF NOT EXISTS shared.global_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    persona VARCHAR(20),
    time_period VARCHAR(20) NOT NULL,
    aggregation_level VARCHAR(50) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- ========================================
-- INDEXES FOR PERFORMANCE
-- ========================================

-- Cherry indexes
CREATE INDEX IF NOT EXISTS idx_cherry_conversations_user ON cherry.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_cherry_conversations_created ON cherry.conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_cherry_tasks_status ON cherry.tasks(status);
CREATE INDEX IF NOT EXISTS idx_cherry_tasks_due_date ON cherry.tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_cherry_knowledge_category ON cherry.knowledge_base(category);

-- Sophia indexes  
CREATE INDEX IF NOT EXISTS idx_sophia_transactions_date ON sophia.financial_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_sophia_transactions_status ON sophia.financial_transactions(status);
CREATE INDEX IF NOT EXISTS idx_sophia_transactions_merchant ON sophia.financial_transactions(merchant_id);
CREATE INDEX IF NOT EXISTS idx_sophia_transactions_customer ON sophia.financial_transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_sophia_metrics_name_period ON sophia.business_metrics(metric_name, time_period);
CREATE INDEX IF NOT EXISTS idx_sophia_jobs_status ON sophia.data_processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_sophia_customers_risk ON sophia.customer_financial_profiles(risk_rating);

-- Karen indexes
CREATE INDEX IF NOT EXISTS idx_karen_compliance_status ON karen.healthcare_compliance(status);
CREATE INDEX IF NOT EXISTS idx_karen_compliance_due_date ON karen.healthcare_compliance(due_date);
CREATE INDEX IF NOT EXISTS idx_karen_operations_status ON karen.paragonrx_operations(status);
CREATE INDEX IF NOT EXISTS idx_karen_operations_date ON karen.paragonrx_operations(created_at);
CREATE INDEX IF NOT EXISTS idx_karen_audit_timestamp ON karen.healthcare_audit_logs(action_timestamp);
CREATE INDEX IF NOT EXISTS idx_karen_audit_resource ON karen.healthcare_audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_karen_protocols_status ON karen.medical_protocols(status);
CREATE INDEX IF NOT EXISTS idx_karen_metrics_period ON karen.quality_metrics(measurement_period);

-- Shared indexes
CREATE INDEX IF NOT EXISTS idx_shared_config_persona ON shared.system_config USING GIN(persona_scope);
CREATE INDEX IF NOT EXISTS idx_shared_inter_persona ON shared.inter_persona_logs(source_persona, target_persona);
CREATE INDEX IF NOT EXISTS idx_shared_analytics_persona_period ON shared.global_analytics(persona, time_period);

-- ========================================
-- ROW LEVEL SECURITY (RLS) SETUP
-- ========================================

-- Enable RLS on sensitive tables
ALTER TABLE karen.paragonrx_operations ENABLE ROW LEVEL SECURITY;
ALTER TABLE karen.healthcare_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE sophia.customer_financial_profiles ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (examples - adjust based on your authentication system)
-- These would be configured based on your actual user roles and authentication

-- Example policy for healthcare data (HIPAA compliance)
-- CREATE POLICY karen_healthcare_access ON karen.paragonrx_operations
--     FOR ALL TO healthcare_staff
--     USING (true); -- Implement actual access logic here

-- Example policy for financial data (PCI compliance)
-- CREATE POLICY sophia_financial_access ON sophia.customer_financial_profiles
--     FOR ALL TO financial_staff
--     USING (true); -- Implement actual access logic here

-- ========================================
-- COMMENTS AND DOCUMENTATION
-- ========================================

COMMENT ON SCHEMA cherry IS 'Cherry persona - Personal assistant, general AI operations, and user interactions';
COMMENT ON SCHEMA sophia IS 'Sophia persona - Pay Ready financial operations, business intelligence, and large data processing';
COMMENT ON SCHEMA karen IS 'Karen persona - Healthcare operations, ParagonRX pharmacy management, and compliance';
COMMENT ON SCHEMA shared IS 'Shared data and cross-persona communication';

COMMENT ON TABLE cherry.conversations IS 'Cherry conversation history and context management';
COMMENT ON TABLE cherry.tasks IS 'Cherry task and reminder management';
COMMENT ON TABLE cherry.user_preferences IS 'User preferences and personalization settings';
COMMENT ON TABLE cherry.knowledge_base IS 'Cherry knowledge base and learned information';

COMMENT ON TABLE sophia.financial_transactions IS 'Financial transaction processing and analysis';
COMMENT ON TABLE sophia.business_metrics IS 'Business intelligence metrics and KPIs';
COMMENT ON TABLE sophia.data_processing_jobs IS 'Large-scale data processing job tracking';
COMMENT ON TABLE sophia.financial_reports IS 'Generated financial reports and analysis';
COMMENT ON TABLE sophia.customer_financial_profiles IS 'Customer financial behavior and risk profiles';

COMMENT ON TABLE karen.healthcare_compliance IS 'Healthcare compliance tracking and management';
COMMENT ON TABLE karen.paragonrx_operations IS 'ParagonRX pharmacy operations and prescription management';
COMMENT ON TABLE karen.healthcare_audit_logs IS 'HIPAA-compliant healthcare access audit logs';
COMMENT ON TABLE karen.medical_protocols IS 'Medical protocols and procedure documentation';
COMMENT ON TABLE karen.quality_metrics IS 'Healthcare quality metrics and performance indicators';

-- ========================================
-- INITIAL CONFIGURATION DATA
-- ========================================

-- Insert initial system configuration
INSERT INTO shared.system_config (config_key, config_value, config_type, description, persona_scope) VALUES
('database_version', '1.0.0', 'string', 'Database schema version', ARRAY['cherry', 'sophia', 'karen']),
('redis_db_cherry', '0', 'integer', 'Redis database number for Cherry', ARRAY['cherry']),
('redis_db_sophia', '1', 'integer', 'Redis database number for Sophia', ARRAY['sophia']),
('redis_db_karen', '2', 'integer', 'Redis database number for Karen', ARRAY['karen']),
('pinecone_namespace_cherry', 'cherry', 'string', 'Pinecone namespace for Cherry', ARRAY['cherry']),
('pinecone_namespace_sophia', 'sophia', 'string', 'Pinecone namespace for Sophia', ARRAY['sophia']),
('pinecone_namespace_karen', 'karen', 'string', 'Pinecone namespace for Karen', ARRAY['karen']),
('weaviate_class_prefix_cherry', 'Cherry', 'string', 'Weaviate class prefix for Cherry', ARRAY['cherry']),
('weaviate_class_prefix_sophia', 'Sophia', 'string', 'Weaviate class prefix for Sophia', ARRAY['sophia']),
('weaviate_class_prefix_karen', 'Karen', 'string', 'Weaviate class prefix for Karen', ARRAY['karen'])
ON CONFLICT (config_key) DO NOTHING;

-- Success message
-- SELECT 'Orchestra AI Persona Database Setup Complete!' as status; 