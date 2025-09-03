"""
SQLAlchemy ORM Models for Policy Auditor
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4
import enum

from sqlalchemy import (
    Column, String, Text, Date, DateTime, ForeignKey, 
    Boolean, DECIMAL, Integer, Enum, JSON, TIMESTAMP
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class PolicyStatus(str, enum.Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    DRAFT = "draft"
    ARCHIVED = "archived"


class ComplianceStatus(str, enum.Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    PENDING_REVIEW = "pending_review"
    NOT_APPLICABLE = "not_applicable"


class AuditSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    policies = relationship("Policy", back_populates="organization")


class Policy(Base):
    __tablename__ = "policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    policy_code = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    category = Column(String(50), index=True)
    subcategory = Column(String(50))
    version = Column(String(50))
    effective_date = Column(Date, index=True)
    expiry_date = Column(Date)
    status = Column(Enum(PolicyStatus), default=PolicyStatus.ACTIVE, index=True)
    file_path = Column(String(500))
    file_hash = Column(String(64))
    extracted_text = Column(Text)
    metadata = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="policies")
    sections = relationship("PolicySection", back_populates="policy", cascade="all, delete-orphan")
    compliance_checks = relationship("ComplianceCheck", back_populates="policy")
    violations = relationship("Violation", back_populates="policy")
    mappings = relationship("PolicyMapping", back_populates="policy", cascade="all, delete-orphan")


class AuditRequirement(Base):
    __tablename__ = "audit_requirements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    apl_code = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    requirement_text = Column(Text)
    severity = Column(Enum(AuditSeverity), default=AuditSeverity.MEDIUM, index=True)
    category = Column(String(100), index=True)
    subcategory = Column(String(100))
    effective_date = Column(Date)
    file_path = Column(String(500))
    file_hash = Column(String(64))
    extracted_text = Column(Text)
    metadata = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    criteria = relationship("AuditCriteria", back_populates="audit_requirement", cascade="all, delete-orphan")
    compliance_checks = relationship("ComplianceCheck", back_populates="audit_requirement")
    violations = relationship("Violation", back_populates="audit_requirement")
    mappings = relationship("PolicyMapping", back_populates="audit_requirement", cascade="all, delete-orphan")


class PolicySection(Base):
    __tablename__ = "policy_sections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"))
    section_number = Column(String(50))
    section_title = Column(String(500))
    content = Column(Text)
    parent_section_id = Column(UUID(as_uuid=True), ForeignKey("policy_sections.id"))
    order_index = Column(Integer)
    metadata = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    policy = relationship("Policy", back_populates="sections")
    parent = relationship("PolicySection", remote_side=[id])


class AuditCriteria(Base):
    __tablename__ = "audit_criteria"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    audit_requirement_id = Column(UUID(as_uuid=True), ForeignKey("audit_requirements.id", ondelete="CASCADE"))
    criteria_code = Column(String(100))
    criteria_text = Column(Text, nullable=False)
    validation_rule = Column(Text)
    weight = Column(DECIMAL(3, 2), default=1.0)
    is_automated = Column(Boolean, default=False)
    metadata = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    audit_requirement = relationship("AuditRequirement", back_populates="criteria")
    compliance_checks = relationship("ComplianceCheck", back_populates="audit_criteria")


class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), index=True)
    audit_requirement_id = Column(UUID(as_uuid=True), ForeignKey("audit_requirements.id"), index=True)
    audit_criteria_id = Column(UUID(as_uuid=True), ForeignKey("audit_criteria.id"))
    check_date = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    status = Column(Enum(ComplianceStatus), default=ComplianceStatus.PENDING_REVIEW, index=True)
    score = Column(DECIMAL(5, 2))
    findings = Column(Text)
    evidence = Column(JSONB)
    reviewed_by = Column(String(255))
    reviewed_at = Column(TIMESTAMP(timezone=True))
    automated_check = Column(Boolean, default=False)
    metadata = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    policy = relationship("Policy", back_populates="compliance_checks")
    audit_requirement = relationship("AuditRequirement", back_populates="compliance_checks")
    audit_criteria = relationship("AuditCriteria", back_populates="compliance_checks")
    violations = relationship("Violation", back_populates="compliance_check", cascade="all, delete-orphan")


class Violation(Base):
    __tablename__ = "violations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    compliance_check_id = Column(UUID(as_uuid=True), ForeignKey("compliance_checks.id", ondelete="CASCADE"))
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), index=True)
    audit_requirement_id = Column(UUID(as_uuid=True), ForeignKey("audit_requirements.id"), index=True)
    violation_type = Column(String(100))
    description = Column(Text, nullable=False)
    severity = Column(Enum(AuditSeverity), default=AuditSeverity.MEDIUM, index=True)
    remediation_required = Column(Text)
    remediation_deadline = Column(Date)
    status = Column(String(50), default="open", index=True)
    resolved_at = Column(TIMESTAMP(timezone=True))
    resolved_by = Column(String(255))
    resolution_notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    compliance_check = relationship("ComplianceCheck", back_populates="violations")
    policy = relationship("Policy", back_populates="violations")
    audit_requirement = relationship("AuditRequirement", back_populates="violations")


class PolicyMapping(Base):
    __tablename__ = "policy_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"))
    audit_requirement_id = Column(UUID(as_uuid=True), ForeignKey("audit_requirements.id", ondelete="CASCADE"))
    mapping_confidence = Column(DECIMAL(3, 2))
    mapping_notes = Column(Text)
    is_manual = Column(Boolean, default=False)
    created_by = Column(String(255))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    policy = relationship("Policy", back_populates="mappings")
    audit_requirement = relationship("AuditRequirement", back_populates="mappings")


class AuditHistory(Base):
    __tablename__ = "audit_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(50), nullable=False)
    changes = Column(JSONB)
    performed_by = Column(String(255))
    performed_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    ip_address = Column(INET)
    user_agent = Column(Text)


class Report(Base):
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    report_name = Column(String(255), nullable=False)
    report_type = Column(String(50))
    parameters = Column(JSONB)
    generated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    generated_by = Column(String(255))
    file_path = Column(String(500))
    file_format = Column(String(20))
    metadata = Column(JSONB)