-- Initialize PostgreSQL database for Emotional Wellness API
-- This script creates the necessary schema and tables with HIPAA compliance in mind

-- Enable pgAudit extension for comprehensive auditing
CREATE EXTENSION IF NOT EXISTS pgaudit;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create schema
CREATE SCHEMA IF NOT EXISTS emotional_wellness;

-- Set search path
SET search_path TO emotional_wellness, public;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    full_name VARCHAR(255),
    provider_id VARCHAR(255),
    password_hash VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    disabled BOOLEAN NOT NULL DEFAULT FALSE
);

-- Create user_roles table
CREATE TABLE IF NOT EXISTS user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, role)
);

-- Create consent_records table
CREATE TABLE IF NOT EXISTS consent_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    consent_version VARCHAR(50) NOT NULL,
    data_usage_approved BOOLEAN NOT NULL,
    crisis_protocol_approved BOOLEAN NOT NULL,
    data_retention_period INTEGER NOT NULL,
    ip_address_hash VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    revocable BOOLEAN NOT NULL DEFAULT TRUE,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    metadata JSONB
);

-- Create symbolic_mappings table
CREATE TABLE IF NOT EXISTS symbolic_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    primary_symbol VARCHAR(255) NOT NULL,
    alternative_symbols JSONB,
    archetype VARCHAR(255),
    valence FLOAT,
    arousal FLOAT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create encrypted_content table for PHI storage
CREATE TABLE IF NOT EXISTS encrypted_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL,
    encrypted_data BYTEA NOT NULL,
    iv VARCHAR(255) NOT NULL,
    hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Create safety_assessments table
CREATE TABLE IF NOT EXISTS safety_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    level INTEGER NOT NULL,
    risk_score FLOAT NOT NULL,
    triggers JSONB,
    recommended_actions JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create intervention_records table
CREATE TABLE IF NOT EXISTS intervention_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    safety_assessment_id UUID REFERENCES safety_assessments(id),
    level INTEGER NOT NULL,
    actions_taken JSONB,
    protocol_state VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    outcome VARCHAR(50),
    notes TEXT
);

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(255) NOT NULL,
    resource_id UUID,
    ip_address VARCHAR(255),
    user_agent TEXT,
    details JSONB
);

-- Create emotional_states table
CREATE TABLE IF NOT EXISTS emotional_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    valence FLOAT,
    arousal FLOAT,
    primary_symbol VARCHAR(255) NOT NULL,
    alternative_symbols JSONB,
    archetype VARCHAR(255),
    drift_index FLOAT,
    safety_level INTEGER NOT NULL,
    input_text_hash VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB
);

-- Create indices for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_emotional_states_user_id ON emotional_states(user_id);
CREATE INDEX IF NOT EXISTS idx_emotional_states_session_id ON emotional_states(session_id);
CREATE INDEX IF NOT EXISTS idx_emotional_states_timestamp ON emotional_states(timestamp);
CREATE INDEX IF NOT EXISTS idx_safety_assessments_user_id_level ON safety_assessments(user_id, level);
CREATE INDEX IF NOT EXISTS idx_intervention_records_user_id ON intervention_records(user_id);
CREATE INDEX IF NOT EXISTS idx_intervention_records_level ON intervention_records(level);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);

-- Create row level security policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE consent_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE emotional_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE encrypted_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE intervention_records ENABLE ROW LEVEL SECURITY;

-- Create functions for automatically updating timestamps
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for timestamp updates
CREATE TRIGGER users_update_timestamp
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

-- Audit logging functions
CREATE OR REPLACE FUNCTION audit_log()
RETURNS TRIGGER AS $$
DECLARE
    actor_id UUID;
BEGIN
    -- In a real app, we would get the actor_id from the application context
    -- For now, we'll set it to NULL
    actor_id := NULL;
    
    IF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_logs (actor_id, action, resource_type, resource_id, details)
        VALUES (actor_id, 'DELETE', TG_TABLE_NAME, OLD.id, 
                jsonb_build_object('old_data', row_to_json(OLD)));
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_logs (actor_id, action, resource_type, resource_id, details)
        VALUES (actor_id, 'UPDATE', TG_TABLE_NAME, NEW.id, 
                jsonb_build_object('old_data', row_to_json(OLD), 'new_data', row_to_json(NEW)));
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_logs (actor_id, action, resource_type, resource_id, details)
        VALUES (actor_id, 'INSERT', TG_TABLE_NAME, NEW.id, 
                jsonb_build_object('new_data', row_to_json(NEW)));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Add audit triggers to key tables (HIPAA compliance)
CREATE TRIGGER users_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE PROCEDURE audit_log();

CREATE TRIGGER consent_records_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON consent_records
FOR EACH ROW EXECUTE PROCEDURE audit_log();

CREATE TRIGGER sessions_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON sessions
FOR EACH ROW EXECUTE PROCEDURE audit_log();

CREATE TRIGGER emotional_states_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON emotional_states
FOR EACH ROW EXECUTE PROCEDURE audit_log();

CREATE TRIGGER intervention_records_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON intervention_records
FOR EACH ROW EXECUTE PROCEDURE audit_log();

-- Create a default admin user for development (remove in production)
INSERT INTO users (username, email, full_name, disabled)
VALUES ('admin', 'admin@example.com', 'System Administrator', FALSE)
ON CONFLICT (username) DO NOTHING;

-- Insert admin role for the admin user
INSERT INTO user_roles (user_id, role)
SELECT id, 'admin' FROM users WHERE username = 'admin'
ON CONFLICT (user_id, role) DO NOTHING;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA emotional_wellness TO wellness;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA emotional_wellness TO wellness;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA emotional_wellness TO wellness;

-- Enable row-level security policies
CREATE POLICY users_policy ON users 
    USING (id = current_setting('app.current_user_id', true)::UUID OR 
           current_setting('app.current_user_role', true) = 'admin');

CREATE POLICY consent_records_policy ON consent_records 
    USING (user_id = current_setting('app.current_user_id', true)::UUID OR 
           current_setting('app.current_user_role', true) = 'admin');

CREATE POLICY sessions_policy ON sessions 
    USING (user_id = current_setting('app.current_user_id', true)::UUID OR 
           current_setting('app.current_user_role', true) = 'admin');

CREATE POLICY emotional_states_policy ON emotional_states 
    USING (user_id = current_setting('app.current_user_id', true)::UUID OR 
           current_setting('app.current_user_role', true) = 'admin');

CREATE POLICY encrypted_content_policy ON encrypted_content 
    USING (user_id = current_setting('app.current_user_id', true)::UUID OR 
           current_setting('app.current_user_role', true) = 'admin');

COMMENT ON TABLE users IS 'User accounts for the Emotional Wellness API';
COMMENT ON TABLE consent_records IS 'HIPAA-compliant user consent records';
COMMENT ON TABLE sessions IS 'User interaction sessions';
COMMENT ON TABLE symbolic_mappings IS 'CANOPY symbolic metaphor mappings';
COMMENT ON TABLE safety_assessments IS 'MOSS safety assessments';
COMMENT ON TABLE intervention_records IS 'VELURIA intervention protocol records';
COMMENT ON TABLE audit_logs IS 'HIPAA-compliant audit logs for all system activity';
COMMENT ON TABLE emotional_states IS 'User emotional state records';
COMMENT ON TABLE encrypted_content IS 'Encrypted Protected Health Information (PHI)';
