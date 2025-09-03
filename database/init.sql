-- Policy Auditor Database Schema
-- Version 1.0.0

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create enum types
CREATE TYPE policy_status AS ENUM ('active', 'superseded', 'draft', 'archived');
CREATE TYPE compliance_status AS ENUM ('compliant', 'non_compliant', 'partial', 'pending_review', 'not_applicable');
CREATE TYPE audit_severity AS ENUM ('critical', 'high', 'medium', 'low', 'informational');

-- Organizations table
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Policies table
CREATE TABLE policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_code VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    organization_id UUID REFERENCES organizations(id),
    category VARCHAR(50),
    subcategory VARCHAR(50),
    version VARCHAR(50),
    effective_date DATE,
    expiry_date DATE,
    status policy_status DEFAULT 'active',
    file_path VARCHAR(500),
    file_hash VARCHAR(64),
    extracted_text TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit Requirements table
CREATE TABLE audit_requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    apl_code VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    requirement_text TEXT,
    severity audit_severity DEFAULT 'medium',
    category VARCHAR(100),
    subcategory VARCHAR(100),
    effective_date DATE,
    file_path VARCHAR(500),
    file_hash VARCHAR(64),
    extracted_text TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Policy Sections table (for granular policy content)
CREATE TABLE policy_sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    section_number VARCHAR(50),
    section_title VARCHAR(500),
    content TEXT,
    parent_section_id UUID REFERENCES policy_sections(id),
    order_index INTEGER,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit Criteria table (specific checkpoints from audit requirements)
CREATE TABLE audit_criteria (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audit_requirement_id UUID REFERENCES audit_requirements(id) ON DELETE CASCADE,
    criteria_code VARCHAR(100),
    criteria_text TEXT NOT NULL,
    validation_rule TEXT,
    weight DECIMAL(3,2) DEFAULT 1.0,
    is_automated BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Compliance Checks table
CREATE TABLE compliance_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id UUID REFERENCES policies(id),
    audit_requirement_id UUID REFERENCES audit_requirements(id),
    audit_criteria_id UUID REFERENCES audit_criteria(id),
    check_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status compliance_status DEFAULT 'pending_review',
    score DECIMAL(5,2),
    findings TEXT,
    evidence JSONB,
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    automated_check BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Violations table
CREATE TABLE violations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    compliance_check_id UUID REFERENCES compliance_checks(id) ON DELETE CASCADE,
    policy_id UUID REFERENCES policies(id),
    audit_requirement_id UUID REFERENCES audit_requirements(id),
    violation_type VARCHAR(100),
    description TEXT NOT NULL,
    severity audit_severity DEFAULT 'medium',
    remediation_required TEXT,
    remediation_deadline DATE,
    status VARCHAR(50) DEFAULT 'open',
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255),
    resolution_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Policy Mappings table (maps policies to audit requirements)
CREATE TABLE policy_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    audit_requirement_id UUID REFERENCES audit_requirements(id) ON DELETE CASCADE,
    mapping_confidence DECIMAL(3,2),
    mapping_notes TEXT,
    is_manual BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(policy_id, audit_requirement_id)
);

-- Audit History table
CREATE TABLE audit_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,
    changes JSONB,
    performed_by VARCHAR(255),
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Reports table
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_name VARCHAR(255) NOT NULL,
    report_type VARCHAR(50),
    parameters JSONB,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    generated_by VARCHAR(255),
    file_path VARCHAR(500),
    file_format VARCHAR(20),
    metadata JSONB
);

-- Create indexes for better query performance
CREATE INDEX idx_policies_code ON policies(policy_code);
CREATE INDEX idx_policies_status ON policies(status);
CREATE INDEX idx_policies_category ON policies(category);
CREATE INDEX idx_policies_effective_date ON policies(effective_date);

CREATE INDEX idx_audit_requirements_code ON audit_requirements(apl_code);
CREATE INDEX idx_audit_requirements_severity ON audit_requirements(severity);
CREATE INDEX idx_audit_requirements_category ON audit_requirements(category);

CREATE INDEX idx_compliance_checks_policy ON compliance_checks(policy_id);
CREATE INDEX idx_compliance_checks_requirement ON compliance_checks(audit_requirement_id);
CREATE INDEX idx_compliance_checks_status ON compliance_checks(status);
CREATE INDEX idx_compliance_checks_date ON compliance_checks(check_date);

CREATE INDEX idx_violations_policy ON violations(policy_id);
CREATE INDEX idx_violations_requirement ON violations(audit_requirement_id);
CREATE INDEX idx_violations_status ON violations(status);
CREATE INDEX idx_violations_severity ON violations(severity);

-- Full-text search indexes
CREATE INDEX idx_policies_text_search ON policies USING gin(to_tsvector('english', extracted_text));
CREATE INDEX idx_audit_requirements_text_search ON audit_requirements USING gin(to_tsvector('english', extracted_text));

-- Create update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to relevant tables
CREATE TRIGGER update_policies_updated_at BEFORE UPDATE ON policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_audit_requirements_updated_at BEFORE UPDATE ON audit_requirements
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_compliance_checks_updated_at BEFORE UPDATE ON compliance_checks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_violations_updated_at BEFORE UPDATE ON violations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial organization data
INSERT INTO organizations (name, code, description) VALUES
('Access and Availability', 'AA', 'Policies related to member access and service availability'),
('Care Management and Coordination', 'CMC', 'Care management and coordination policies'),
('Disease Management', 'DD', 'Disease and condition management policies'),
('Emergency and Urgent Care', 'EE', 'Emergency and urgent care service policies'),
('Facility and Network', 'FF', 'Facility standards and network policies'),
('Grievance and Appeals', 'GA', 'Member grievance and appeals procedures'),
('General Guidelines', 'GG', 'General operational guidelines and standards'),
('Health Education', 'HH', 'Health education and wellness program policies'),
('Member Services', 'MA', 'Member services and support policies'),
('Provider Administration', 'PA', 'Provider network administration policies');