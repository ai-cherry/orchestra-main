-- Cherry AI Orchestrator Database Schema
-- Complete database strategy for PostgreSQL integration
-- Supports all three domains: Cherry (Personal), Sophia (Pay Ready), Karen (ParagonRX)

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Cherry Domain Tables (Personal Assistant & Ranch Management)
CREATE TABLE IF NOT EXISTS cherry_personal_tasks (
    id VARCHAR(255) PRIMARY KEY,
    description TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    category VARCHAR(100) DEFAULT 'general',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    due_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS cherry_ranch_operations (
    id VARCHAR(255) PRIMARY KEY,
    description TEXT NOT NULL,
    livestock_type VARCHAR(100),
    location VARCHAR(200),
    operation_type VARCHAR(100) DEFAULT 'general',
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    scheduled_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS cherry_health_wellness (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255),
    metric_type VARCHAR(100) NOT NULL, -- weight, blood_pressure, exercise, etc.
    value DECIMAL(10,2),
    unit VARCHAR(20),
    notes TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Sophia Domain Tables (Pay Ready Business Intelligence)
CREATE TABLE IF NOT EXISTS sophia_debt_recovery_cases (
    id VARCHAR(255) PRIMARY KEY,
    client_name VARCHAR(255) NOT NULL,
    debtor_name VARCHAR(255) NOT NULL,
    original_amount DECIMAL(12,2) NOT NULL,
    current_balance DECIMAL(12,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'written_off', 'in_litigation')),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    assigned_agent VARCHAR(255),
    last_contact_date TIMESTAMP,
    next_action_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS sophia_sales_records (
    id VARCHAR(255) PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    product_service VARCHAR(255) NOT NULL,
    revenue DECIMAL(12,2) NOT NULL,
    commission DECIMAL(12,2),
    sales_rep VARCHAR(255),
    sale_date TIMESTAMP NOT NULL,
    payment_status VARCHAR(50) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'partial', 'overdue')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS sophia_business_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(15,2),
    metric_type VARCHAR(100), -- revenue, conversion_rate, recovery_rate, etc.
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    department VARCHAR(100),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Karen Domain Tables (ParagonRX Healthcare Operations)
CREATE TABLE IF NOT EXISTS karen_patient_records (
    id VARCHAR(255) PRIMARY KEY,
    patient_id VARCHAR(255) NOT NULL, -- Anonymized patient identifier
    condition_summary TEXT,
    treatment_plan TEXT,
    pharmacy_location VARCHAR(255),
    prescribing_physician VARCHAR(255),
    medication_list JSONB,
    last_visit_date TIMESTAMP,
    next_appointment TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'transferred', 'deceased')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS karen_pharmacy_operations (
    id VARCHAR(255) PRIMARY KEY,
    operation_type VARCHAR(100) NOT NULL, -- dispensing, inventory, ordering, etc.
    medication_name VARCHAR(255),
    quantity INTEGER,
    unit VARCHAR(50),
    pharmacy_location VARCHAR(255) NOT NULL,
    staff_member VARCHAR(255),
    patient_id VARCHAR(255), -- Links to patient_records
    prescription_id VARCHAR(255),
    operation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'cancelled', 'error')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS karen_healthcare_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(15,2),
    metric_type VARCHAR(100), -- patient_satisfaction, medication_adherence, etc.
    pharmacy_location VARCHAR(255),
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Cross-Domain Tables
CREATE TABLE IF NOT EXISTS orchestrator_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    active_persona VARCHAR(50) CHECK (active_persona IN ('cherry', 'sophia', 'karen')),
    session_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orchestrator_chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES orchestrator_sessions(id),
    persona VARCHAR(50) NOT NULL CHECK (persona IN ('cherry', 'sophia', 'karen')),
    message_type VARCHAR(20) CHECK (message_type IN ('user', 'assistant')),
    content TEXT NOT NULL,
    search_mode VARCHAR(20) DEFAULT 'creative' CHECK (search_mode IN ('creative', 'deep', 'super-deep')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS orchestrator_system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    log_level VARCHAR(20) CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    component VARCHAR(100), -- cherry_server, sophia_server, karen_server, infrastructure, etc.
    message TEXT NOT NULL,
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_cherry_tasks_status ON cherry_personal_tasks(status);
CREATE INDEX IF NOT EXISTS idx_cherry_tasks_priority ON cherry_personal_tasks(priority);
CREATE INDEX IF NOT EXISTS idx_cherry_tasks_category ON cherry_personal_tasks(category);
CREATE INDEX IF NOT EXISTS idx_cherry_tasks_created_at ON cherry_personal_tasks(created_at);

CREATE INDEX IF NOT EXISTS idx_cherry_ranch_location ON cherry_ranch_operations(location);
CREATE INDEX IF NOT EXISTS idx_cherry_ranch_livestock ON cherry_ranch_operations(livestock_type);
CREATE INDEX IF NOT EXISTS idx_cherry_ranch_created_at ON cherry_ranch_operations(created_at);

CREATE INDEX IF NOT EXISTS idx_sophia_debt_status ON sophia_debt_recovery_cases(status);
CREATE INDEX IF NOT EXISTS idx_sophia_debt_priority ON sophia_debt_recovery_cases(priority);
CREATE INDEX IF NOT EXISTS idx_sophia_debt_client ON sophia_debt_recovery_cases(client_name);
CREATE INDEX IF NOT EXISTS idx_sophia_debt_created_at ON sophia_debt_recovery_cases(created_at);

CREATE INDEX IF NOT EXISTS idx_sophia_sales_date ON sophia_sales_records(sale_date);
CREATE INDEX IF NOT EXISTS idx_sophia_sales_customer ON sophia_sales_records(customer_name);
CREATE INDEX IF NOT EXISTS idx_sophia_sales_rep ON sophia_sales_records(sales_rep);

CREATE INDEX IF NOT EXISTS idx_karen_patient_status ON karen_patient_records(status);
CREATE INDEX IF NOT EXISTS idx_karen_patient_pharmacy ON karen_patient_records(pharmacy_location);
CREATE INDEX IF NOT EXISTS idx_karen_patient_created_at ON karen_patient_records(created_at);

CREATE INDEX IF NOT EXISTS idx_karen_pharmacy_location ON karen_pharmacy_operations(pharmacy_location);
CREATE INDEX IF NOT EXISTS idx_karen_pharmacy_medication ON karen_pharmacy_operations(medication_name);
CREATE INDEX IF NOT EXISTS idx_karen_pharmacy_date ON karen_pharmacy_operations(operation_date);

CREATE INDEX IF NOT EXISTS idx_sessions_token ON orchestrator_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON orchestrator_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_persona ON orchestrator_sessions(active_persona);

CREATE INDEX IF NOT EXISTS idx_chat_session ON orchestrator_chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_persona ON orchestrator_chat_history(persona);
CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON orchestrator_chat_history(timestamp);

CREATE INDEX IF NOT EXISTS idx_logs_level ON orchestrator_system_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_logs_component ON orchestrator_system_logs(component);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON orchestrator_system_logs(timestamp);

-- Insert initial test data
INSERT INTO cherry_personal_tasks (id, description, priority, category) VALUES
('task_001', 'Check cattle feed levels in north pasture', 'high', 'ranch'),
('task_002', 'Schedule annual vet checkup for livestock', 'medium', 'ranch'),
('task_003', 'Review personal budget and expenses', 'medium', 'finance'),
('task_004', 'Plan weekend family activities', 'low', 'personal')
ON CONFLICT (id) DO NOTHING;

INSERT INTO cherry_ranch_operations (id, description, livestock_type, location) VALUES
('ranch_001', 'Morning cattle count - 47 head present', 'cattle', 'north_pasture'),
('ranch_002', 'Repair fence section near water trough', 'general', 'south_field'),
('ranch_003', 'Administer vaccinations to new calves', 'cattle', 'barn_area')
ON CONFLICT (id) DO NOTHING;

INSERT INTO sophia_debt_recovery_cases (id, client_name, debtor_name, original_amount, current_balance, status, priority) VALUES
('debt_001', 'ABC Collections', 'John Smith', 5000.00, 4200.00, 'active', 'high'),
('debt_002', 'XYZ Recovery', 'Jane Doe', 2500.00, 2500.00, 'active', 'medium'),
('debt_003', 'Pay Ready Client', 'Bob Johnson', 8000.00, 6500.00, 'active', 'high')
ON CONFLICT (id) DO NOTHING;

INSERT INTO sophia_sales_records (id, customer_name, product_service, revenue, sales_rep, sale_date) VALUES
('sale_001', 'TechCorp Inc', 'Debt Recovery Services', 15000.00, 'Sarah Wilson', '2024-06-01'),
('sale_002', 'HealthSystem LLC', 'Business Intelligence Package', 25000.00, 'Mike Chen', '2024-06-02'),
('sale_003', 'Local Business Group', 'Analytics Consulting', 8000.00, 'Sarah Wilson', '2024-06-03')
ON CONFLICT (id) DO NOTHING;

INSERT INTO karen_patient_records (id, patient_id, condition_summary, pharmacy_location, status) VALUES
('patient_001', 'PT_12345', 'Hypertension management with ACE inhibitors', 'ParagonRX Main', 'active'),
('patient_002', 'PT_12346', 'Diabetes Type 2 with metformin therapy', 'ParagonRX North', 'active'),
('patient_003', 'PT_12347', 'Chronic pain management protocol', 'ParagonRX Main', 'active')
ON CONFLICT (id) DO NOTHING;

INSERT INTO karen_pharmacy_operations (id, operation_type, medication_name, quantity, pharmacy_location, status) VALUES
('pharm_001', 'dispensing', 'Lisinopril 10mg', 30, 'ParagonRX Main', 'completed'),
('pharm_002', 'dispensing', 'Metformin 500mg', 60, 'ParagonRX North', 'completed'),
('pharm_003', 'inventory', 'Gabapentin 300mg', 100, 'ParagonRX Main', 'completed')
ON CONFLICT (id) DO NOTHING;

-- Create views for common queries
CREATE OR REPLACE VIEW cherry_active_tasks AS
SELECT * FROM cherry_personal_tasks 
WHERE status IN ('pending', 'in_progress')
ORDER BY priority DESC, created_at ASC;

CREATE OR REPLACE VIEW sophia_high_priority_cases AS
SELECT * FROM sophia_debt_recovery_cases
WHERE status = 'active' AND priority IN ('high', 'urgent')
ORDER BY priority DESC, current_balance DESC;

CREATE OR REPLACE VIEW karen_recent_operations AS
SELECT * FROM karen_pharmacy_operations
WHERE operation_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY operation_date DESC;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO orchestra;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO orchestra;

COMMENT ON DATABASE orchestra IS 'Cherry AI Orchestrator - Complete database for three-domain AI system';
COMMENT ON TABLE cherry_personal_tasks IS 'Personal tasks and reminders for Cherry domain';
COMMENT ON TABLE cherry_ranch_operations IS 'Ranch management operations and livestock tracking';
COMMENT ON TABLE sophia_debt_recovery_cases IS 'Pay Ready debt recovery case management';
COMMENT ON TABLE sophia_sales_records IS 'Sales tracking and revenue management';
COMMENT ON TABLE karen_patient_records IS 'ParagonRX patient management (anonymized)';
COMMENT ON TABLE karen_pharmacy_operations IS 'Pharmacy operations and medication dispensing';
COMMENT ON TABLE orchestrator_sessions IS 'User sessions and persona state management';
COMMENT ON TABLE orchestrator_chat_history IS 'Natural language interaction history';
COMMENT ON TABLE orchestrator_system_logs IS 'System-wide logging and monitoring';

