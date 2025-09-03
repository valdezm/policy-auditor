#!/usr/bin/env python3
"""
Improved RT APL Ingestor
Properly extracts all requirements from RT APL PDFs using consistent patterns
"""
import os
import sys
import re
import PyPDF2
import pdfplumber
from typing import List, Dict, Optional
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from models.database import SessionLocal
from models.models import AuditRequirement, AuditCriteria


class ImprovedRTAPLIngestor:
    def __init__(self):
        self.session = SessionLocal()
        
    def close(self):
        if self.session:
            self.session.close()
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using multiple methods"""
        text = ""
        
        # Try pdfplumber first (better for structured documents)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"pdfplumber failed for {pdf_path}: {e}")
            
        # Fallback to PyPDF2 if pdfplumber fails
        if not text.strip():
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            except Exception as e:
                print(f"PyPDF2 also failed for {pdf_path}: {e}")
                return ""
        
        return text
    
    def parse_apl_code(self, filename: str, text: str) -> str:
        """Extract APL code from filename or text"""
        # First try filename
        apl_match = re.search(r'APL[\s_-]?(\d{2}-\d{3})', filename, re.IGNORECASE)
        if apl_match:
            return f"APL {apl_match.group(1)}"
        
        # Try text content
        apl_match = re.search(r'APL[\s_-]?(\d{2}-\d{3})', text, re.IGNORECASE)
        if apl_match:
            return f"APL {apl_match.group(1)}"
            
        return "Unknown APL"
    
    def parse_title(self, text: str, apl_code: str) -> str:
        """Extract title from RT APL text"""
        lines = text.split('\n')
        
        # Look for submission item line
        for line in lines:
            if 'SUBMISSION ITEM:' in line.upper():
                # Extract everything after "Policy and Procedure (P&P) regarding"
                match = re.search(r'regarding\s+(.+?)(?:\s*$)', line, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    # Clean up title
                    title = re.sub(r'\s+', ' ', title)
                    return title
        
        # Fallback patterns
        for line in lines:
            if 'policy and procedure' in line.lower() and 'regarding' in line.lower():
                match = re.search(r'regarding\s+(.+?)(?:\s*$)', line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        
        return f"Policy and Procedure Requirements for {apl_code}"
    
    def extract_requirements(self, text: str, apl_code: str) -> List[Dict]:
        """Extract numbered requirements from RT APL text"""
        requirements = []
        
        # Split text into lines for processing
        lines = text.split('\n')
        
        # Look for numbered requirements pattern: "1. Does the MCP's P&P..."
        current_requirement = None
        collecting_requirement = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Look for numbered requirement start (1., 2., 3., etc.)
            req_match = re.match(r'^(\d+)\.\s*(.+)', line)
            if req_match:
                # Save previous requirement if exists
                if current_requirement:
                    requirements.append(current_requirement)
                
                # Start new requirement
                req_number = req_match.group(1)
                req_text = req_match.group(2)
                
                current_requirement = {
                    'number': int(req_number),
                    'section_code': f"{apl_code.split()[-1]}.{req_number}",
                    'text': req_text,
                    'full_text': req_text
                }
                collecting_requirement = True
                
            elif collecting_requirement and current_requirement:
                # Continue collecting text for current requirement
                if line.startswith('Yes') or line.startswith('No') or line.startswith('Citation:'):
                    # End of requirement text
                    collecting_requirement = False
                elif not line.startswith('REVIEWER:') and not line.startswith('DATE:') and len(line) > 10:
                    # Add to requirement text if it's meaningful content
                    current_requirement['full_text'] += ' ' + line
        
        # Don't forget the last requirement
        if current_requirement:
            requirements.append(current_requirement)
        
        # Clean up requirement texts
        for req in requirements:
            req['full_text'] = re.sub(r'\s+', ' ', req['full_text']).strip()
            
        return requirements
    
    def create_validation_rules(self, requirement_text: str) -> str:
        """Create validation rules based on requirement text patterns"""
        text_lower = requirement_text.lower()
        rules = []
        
        # Common patterns to look for
        if 'clearly state' in text_lower or 'state' in text_lower:
            rules.append('MUST_STATE')
        if 'report' in text_lower or 'reporting' in text_lower:
            rules.append('MUST_REPORT')
        if 'notify' in text_lower or 'notification' in text_lower:
            rules.append('MUST_NOTIFY')
        if 'retain' in text_lower or 'retention' in text_lower:
            rules.append('MUST_RETAIN')
        if 'process' in text_lower:
            rules.append('MUST_HAVE_PROCESS')
        if 'within' in text_lower and ('days' in text_lower or 'hours' in text_lower):
            rules.append('TIMEFRAME_REQUIRED')
        
        # Specific amounts or thresholds
        if '$25 million' in requirement_text:
            rules.append('THRESHOLD_25M')
        if '60 days' in requirement_text:
            rules.append('TIMEFRAME_60_DAYS')
        if '10 days' in requirement_text:
            rules.append('TIMEFRAME_10_DAYS')
        if 'bi-annually' in text_lower or 'annually' in text_lower:
            rules.append('PERIODIC_REVIEW')
            
        return '|'.join(rules) if rules else 'COMPLIANCE_CHECK'
    
    def ingest_rt_apl(self, pdf_path: str) -> bool:
        """Ingest a single RT APL PDF"""
        try:
            print(f"\nProcessing: {pdf_path}")
            
            # Extract text
            text = self.extract_text_from_pdf(pdf_path)
            if not text.strip():
                print(f"  ❌ No text extracted from {pdf_path}")
                return False
            
            filename = os.path.basename(pdf_path)
            apl_code = self.parse_apl_code(filename, text)
            title = self.parse_title(text, apl_code)
            
            print(f"  📋 APL: {apl_code}")
            print(f"  📄 Title: {title}")
            
            # Check if already exists
            existing = self.session.query(AuditRequirement).filter_by(apl_code=apl_code).first()
            if existing:
                print(f"  ⚠️  APL {apl_code} already exists, updating...")
                # Delete existing criteria first
                existing_criteria = self.session.query(AuditCriteria).filter_by(audit_requirement_id=existing.id).all()
                for criteria in existing_criteria:
                    self.session.delete(criteria)
                    
                audit_req = existing
                audit_req.title = title
                audit_req.extracted_text = text
            else:
                # Create new audit requirement
                audit_req = AuditRequirement(
                    apl_code=apl_code,
                    title=title,
                    extracted_text=text,
                    source_file=filename
                )
                self.session.add(audit_req)
            
            # Flush to get the ID
            self.session.flush()
            
            # Extract requirements
            requirements = self.extract_requirements(text, apl_code)
            print(f"  📝 Found {len(requirements)} requirements")
            
            if not requirements:
                print(f"  ⚠️  No structured requirements found, creating generic entry")
                # Create a single generic requirement
                criteria = AuditCriteria(
                    audit_requirement_id=audit_req.id,
                    criteria_code="Main",
                    criteria_text=f"Review compliance with {apl_code} requirements",
                    validation_rule="COMPLIANCE_CHECK"
                )
                self.session.add(criteria)
            else:
                # Create criteria for each requirement
                for req in requirements:
                    validation_rule = self.create_validation_rules(req['full_text'])
                    
                    criteria = AuditCriteria(
                        audit_requirement_id=audit_req.id,
                        criteria_code=req['section_code'],
                        criteria_text=req['full_text'],
                        validation_rule=validation_rule
                    )
                    self.session.add(criteria)
                    
                    print(f"    ✓ {req['section_code']}: {req['full_text'][:60]}...")
            
            self.session.commit()
            print(f"  ✅ Successfully ingested {apl_code}")
            return True
            
        except Exception as e:
            print(f"  ❌ Error processing {pdf_path}: {e}")
            self.session.rollback()
            return False
    
    def ingest_all_rt_apls(self, directory: str) -> Dict[str, int]:
        """Ingest all RT APL PDFs from directory"""
        rt_apl_dir = Path(directory)
        if not rt_apl_dir.exists():
            print(f"Directory not found: {directory}")
            return {'success': 0, 'failed': 0}
        
        pdf_files = list(rt_apl_dir.glob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files in {directory}")
        
        stats = {'success': 0, 'failed': 0}
        
        for pdf_file in pdf_files:
            if self.ingest_rt_apl(str(pdf_file)):
                stats['success'] += 1
            else:
                stats['failed'] += 1
        
        return stats


def main():
    ingestor = ImprovedRTAPLIngestor()
    try:
        directory = "/mnt/c/Users/markv/Downloads/APL RTs"
        stats = ingestor.ingest_all_rt_apls(directory)
        
        print(f"\n🎯 Ingestion Complete!")
        print(f"   ✅ Success: {stats['success']} APLs")
        print(f"   ❌ Failed: {stats['failed']} APLs")
        
    finally:
        ingestor.close()


if __name__ == "__main__":
    main()