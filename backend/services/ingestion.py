"""
Policy and Audit Document Ingestion Service
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models.models import (
    Policy, AuditRequirement, PolicySection, AuditCriteria,
    Organization, PolicyStatus, AuditSeverity
)
from ..models.database import get_db
from ..utils.pdf_extractor import PDFExtractor, DocumentProcessor

logger = logging.getLogger(__name__)


class PolicyIngestionService:
    """Service for ingesting policy documents into the system"""
    
    def __init__(self, db: Session):
        self.db = db
        self.processor = DocumentProcessor()
        self.extractor = PDFExtractor()
    
    def ingest_policy_directory(self, directory_path: str) -> Dict[str, int]:
        """
        Ingest all policy documents from a directory
        
        Args:
            directory_path: Path to directory containing policy PDFs
            
        Returns:
            Dictionary with ingestion statistics
        """
        stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
        
        policy_dir = Path(directory_path)
        if not policy_dir.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        # Process each category directory
        for category_dir in policy_dir.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith('_'):
                continue
            
            logger.info(f"Processing category: {category_dir.name}")
            
            # Get or create organization
            org = self._get_or_create_organization(category_dir.name)
            
            # Process each PDF in the category
            for pdf_file in category_dir.glob("*.pdf"):
                stats['total_files'] += 1
                
                try:
                    if self._policy_exists(pdf_file):
                        logger.info(f"Policy already exists: {pdf_file.name}")
                        stats['skipped'] += 1
                        continue
                    
                    self.ingest_policy(str(pdf_file), org.id)
                    stats['successful'] += 1
                    logger.info(f"Successfully ingested: {pdf_file.name}")
                    
                except Exception as e:
                    stats['failed'] += 1
                    logger.error(f"Failed to ingest {pdf_file.name}: {e}")
        
        return stats
    
    def ingest_policy(self, file_path: str, organization_id: Optional[str] = None) -> Policy:
        """
        Ingest a single policy document
        
        Args:
            file_path: Path to policy PDF
            organization_id: Optional organization ID
            
        Returns:
            Created Policy object
        """
        # Process the document
        doc_data = self.processor.process_policy_document(file_path)
        
        # Create policy record
        policy = Policy(
            policy_code=doc_data['metadata'].get('policy_code') or Path(file_path).stem,
            title=doc_data['metadata'].get('title') or Path(file_path).name,
            description=self._extract_description(doc_data['extracted_text']),
            organization_id=organization_id,
            category=doc_data['metadata'].get('category'),
            subcategory=doc_data['metadata'].get('subcategory'),
            version=doc_data['metadata'].get('version'),
            effective_date=self._parse_date(doc_data['metadata'].get('effective_date')),
            status=PolicyStatus.ACTIVE,
            file_path=file_path,
            file_hash=doc_data['metadata'].get('file_hash'),
            extracted_text=doc_data['extracted_text'],
            metadata=doc_data['metadata']
        )
        
        self.db.add(policy)
        self.db.flush()  # Get the policy ID
        
        # Add policy sections
        for idx, section in enumerate(doc_data['sections']):
            policy_section = PolicySection(
                policy_id=policy.id,
                section_number=section.get('section_number'),
                section_title=section.get('section_title'),
                content=section.get('content'),
                order_index=idx,
                metadata={'original_section': section}
            )
            self.db.add(policy_section)
        
        self.db.commit()
        return policy
    
    def _policy_exists(self, file_path: Path) -> bool:
        """Check if policy already exists in database"""
        # Check by file hash would be more robust
        existing = self.db.query(Policy).filter(
            Policy.file_path == str(file_path)
        ).first()
        return existing is not None
    
    def _get_or_create_organization(self, code: str) -> Organization:
        """Get or create organization by code"""
        org = self.db.query(Organization).filter(
            Organization.code == code
        ).first()
        
        if not org:
            # Map codes to full names
            org_names = {
                'AA': 'Access and Availability',
                'CMC': 'Care Management and Coordination',
                'DD': 'Disease Management',
                'EE': 'Emergency and Urgent Care',
                'FF': 'Facility and Network',
                'GA': 'Grievance and Appeals',
                'GG': 'General Guidelines',
                'HH': 'Health Education',
                'MA': 'Member Services',
                'PA': 'Provider Administration'
            }
            
            org = Organization(
                code=code,
                name=org_names.get(code, code),
                description=f"Policies for {org_names.get(code, code)}"
            )
            self.db.add(org)
            self.db.commit()
        
        return org
    
    def _extract_description(self, text: str) -> str:
        """Extract description from document text"""
        lines = text.split('\n')[:50]
        description_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 50 and 'purpose' in line.lower():
                description_lines.append(line)
                # Get next few lines as well
                idx = lines.index(line)
                for i in range(1, 4):
                    if idx + i < len(lines):
                        description_lines.append(lines[idx + i].strip())
                break
        
        return ' '.join(description_lines)[:1000] if description_lines else ''
    
    def _parse_date(self, date_str: Optional[str]):
        """Parse date string to date object"""
        if not date_str:
            return None
        
        try:
            if isinstance(date_str, str):
                return datetime.fromisoformat(date_str).date()
        except:
            return None


class AuditIngestionService:
    """Service for ingesting audit requirement documents"""
    
    def __init__(self, db: Session):
        self.db = db
        self.processor = DocumentProcessor()
        self.extractor = PDFExtractor()
    
    def ingest_audit_directory(self, directory_path: str) -> Dict[str, int]:
        """
        Ingest all audit requirement documents from a directory
        
        Args:
            directory_path: Path to directory containing audit PDFs
            
        Returns:
            Dictionary with ingestion statistics
        """
        stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
        
        audit_dir = Path(directory_path)
        if not audit_dir.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        # Process each audit PDF
        for pdf_file in audit_dir.glob("*.pdf"):
            stats['total_files'] += 1
            
            try:
                if self._audit_exists(pdf_file):
                    logger.info(f"Audit requirement already exists: {pdf_file.name}")
                    stats['skipped'] += 1
                    continue
                
                self.ingest_audit(str(pdf_file))
                stats['successful'] += 1
                logger.info(f"Successfully ingested: {pdf_file.name}")
                
            except Exception as e:
                stats['failed'] += 1
                logger.error(f"Failed to ingest {pdf_file.name}: {e}")
        
        return stats
    
    def ingest_audit(self, file_path: str) -> AuditRequirement:
        """
        Ingest a single audit requirement document
        
        Args:
            file_path: Path to audit PDF
            
        Returns:
            Created AuditRequirement object
        """
        # Process the document
        doc_data = self.processor.process_audit_document(file_path)
        
        # Determine severity based on content
        severity = self._determine_severity(doc_data['extracted_text'])
        
        # Create audit requirement record
        audit_req = AuditRequirement(
            apl_code=doc_data['metadata'].get('apl_code') or Path(file_path).stem,
            title=doc_data['metadata'].get('title') or Path(file_path).name,
            description=self._extract_audit_description(doc_data['extracted_text']),
            requirement_text=doc_data['extracted_text'][:10000],  # Limit text size
            severity=severity,
            category=self._determine_category(doc_data['metadata'].get('apl_code')),
            effective_date=self._parse_date(doc_data['metadata'].get('effective_date')),
            file_path=file_path,
            file_hash=doc_data['metadata'].get('file_hash'),
            extracted_text=doc_data['extracted_text'],
            metadata=doc_data['metadata']
        )
        
        self.db.add(audit_req)
        self.db.flush()  # Get the audit requirement ID
        
        # Add audit criteria
        for criteria in doc_data['criteria']:
            audit_criteria = AuditCriteria(
                audit_requirement_id=audit_req.id,
                criteria_code=criteria.get('criteria_code'),
                criteria_text=criteria.get('criteria_text') or criteria.get('criteria_title', ''),
                validation_rule=self._generate_validation_rule(criteria),
                weight=1.0,  # Default weight
                is_automated=False,  # Manual review by default
                metadata={'original_criteria': criteria}
            )
            self.db.add(audit_criteria)
        
        self.db.commit()
        return audit_req
    
    def _audit_exists(self, file_path: Path) -> bool:
        """Check if audit requirement already exists in database"""
        existing = self.db.query(AuditRequirement).filter(
            AuditRequirement.file_path == str(file_path)
        ).first()
        return existing is not None
    
    def _determine_severity(self, text: str) -> AuditSeverity:
        """Determine audit severity based on content"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['critical', 'immediate', 'emergency']):
            return AuditSeverity.CRITICAL
        elif any(word in text_lower for word in ['high priority', 'urgent', 'mandatory']):
            return AuditSeverity.HIGH
        elif any(word in text_lower for word in ['low priority', 'optional', 'recommended']):
            return AuditSeverity.LOW
        elif any(word in text_lower for word in ['informational', 'guidance', 'best practice']):
            return AuditSeverity.INFORMATIONAL
        
        return AuditSeverity.MEDIUM
    
    def _determine_category(self, apl_code: Optional[str]) -> str:
        """Determine category based on APL code"""
        if not apl_code:
            return 'General'
        
        # Parse APL code pattern (e.g., APL 23-001)
        if '23-0' in apl_code:
            code_num = int(apl_code.split('-')[-1])
            
            if code_num <= 5:
                return 'Access and Eligibility'
            elif code_num <= 10:
                return 'Quality Management'
            elif code_num <= 15:
                return 'Network Management'
            elif code_num <= 20:
                return 'Member Services'
            else:
                return 'Administrative'
        
        return 'General'
    
    def _extract_audit_description(self, text: str) -> str:
        """Extract description from audit document text"""
        lines = text.split('\n')[:100]
        description_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 50 and any(word in line.lower() for word in ['purpose', 'objective', 'requirement']):
                description_lines.append(line)
                # Get next few lines as well
                idx = lines.index(line)
                for i in range(1, 5):
                    if idx + i < len(lines):
                        next_line = lines[idx + i].strip()
                        if next_line:
                            description_lines.append(next_line)
                break
        
        return ' '.join(description_lines)[:2000] if description_lines else ''
    
    def _generate_validation_rule(self, criteria: Dict) -> str:
        """Generate a validation rule for the criteria"""
        # This could be enhanced with NLP to create actual validation rules
        criteria_text = criteria.get('criteria_text', '').lower()
        
        rules = []
        if 'must' in criteria_text or 'shall' in criteria_text:
            rules.append('MANDATORY')
        if 'within' in criteria_text and 'days' in criteria_text:
            rules.append('TIME_BOUND')
        if 'document' in criteria_text or 'record' in criteria_text:
            rules.append('DOCUMENTATION_REQUIRED')
        if 'review' in criteria_text:
            rules.append('REVIEW_REQUIRED')
        
        return '|'.join(rules) if rules else 'MANUAL_REVIEW'
    
    def _parse_date(self, date_str: Optional[str]):
        """Parse date string to date object"""
        if not date_str:
            return None
        
        try:
            if isinstance(date_str, str):
                return datetime.fromisoformat(date_str).date()
        except:
            return None