"""
Migration: Add AI Validation Results table
Created: 2025-09-03
"""

from sqlalchemy import text

# Forward migration
UPGRADE_SQL = """
-- Create enum types for AI validation
CREATE TYPE ai_validation_compliance_rating AS ENUM (
    'fully_compliant', 
    'partially_compliant', 
    'non_compliant', 
    'unclear', 
    'not_applicable'
);

CREATE TYPE ai_validation_confidence_level AS ENUM (
    'high', 
    'medium', 
    'low'
);

-- Create AI validation results table
CREATE TABLE ai_validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL REFERENCES policies(id),
    audit_requirement_id UUID NOT NULL REFERENCES audit_requirements(id),
    requirement_text TEXT NOT NULL,
    regulation_reference VARCHAR(255) NOT NULL,
    
    -- AI Assessment Results
    compliance_rating ai_validation_compliance_rating NOT NULL,
    confidence_level ai_validation_confidence_level NOT NULL,
    confidence_score DECIMAL(5,2) NOT NULL,
    
    -- Detailed Analysis (stored as JSONB)
    reasoning TEXT,
    specific_findings JSONB,
    missing_elements JSONB,
    policy_strengths JSONB,
    recommendations JSONB,
    relevant_policy_excerpts JSONB,
    regulatory_interpretation TEXT,
    risk_assessment TEXT,
    priority_level VARCHAR(20),
    
    -- Metadata
    ai_model_version VARCHAR(50) DEFAULT 'gpt-4o',
    validation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processing_time_ms INTEGER,
    token_usage INTEGER,
    
    -- Review and Override
    is_human_reviewed BOOLEAN DEFAULT FALSE,
    human_review_notes TEXT,
    human_override_rating ai_validation_compliance_rating,
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit trail
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_ai_validation_policy_id ON ai_validation_results(policy_id);
CREATE INDEX idx_ai_validation_audit_requirement_id ON ai_validation_results(audit_requirement_id);
CREATE INDEX idx_ai_validation_compliance_rating ON ai_validation_results(compliance_rating);
CREATE INDEX idx_ai_validation_confidence_level ON ai_validation_results(confidence_level);
CREATE INDEX idx_ai_validation_priority_level ON ai_validation_results(priority_level);
CREATE INDEX idx_ai_validation_validation_date ON ai_validation_results(validation_date);
CREATE INDEX idx_ai_validation_human_reviewed ON ai_validation_results(is_human_reviewed);

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_ai_validation_results_updated_at 
    BEFORE UPDATE ON ai_validation_results 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add composite index for unique policy-requirement pairs
CREATE UNIQUE INDEX idx_ai_validation_unique_policy_requirement 
    ON ai_validation_results(policy_id, audit_requirement_id, requirement_text);
"""

# Reverse migration
DOWNGRADE_SQL = """
-- Drop table and related objects
DROP TRIGGER IF EXISTS update_ai_validation_results_updated_at ON ai_validation_results;
DROP TABLE IF EXISTS ai_validation_results;
DROP TYPE IF EXISTS ai_validation_compliance_rating;
DROP TYPE IF EXISTS ai_validation_confidence_level;
"""

def upgrade(connection):
    """Apply the migration"""
    connection.execute(text(UPGRADE_SQL))
    connection.commit()

def downgrade(connection):
    """Reverse the migration"""
    connection.execute(text(DOWNGRADE_SQL))
    connection.commit()