
-- Create admin user for Orchestra AI
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    permissions JSONB DEFAULT '[]'::jsonb
);

-- Insert admin user
INSERT INTO users (username, password_hash, email, role, permissions) VALUES 
('scoobyjava', '$2b$12$3PQ71132oirPOvrZuW6TCeb3DM.pbRq3IHe0MZ6ujOmEdFMRjAMU2', 'admin@cherry-ai.me', 'admin', '["all"]'::jsonb)
ON CONFLICT (username) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    email = EXCLUDED.email,
    role = EXCLUDED.role,
    permissions = EXCLUDED.permissions;

-- Grant all permissions
UPDATE users SET permissions = '["all"]'::jsonb WHERE username = 'scoobyjava';
