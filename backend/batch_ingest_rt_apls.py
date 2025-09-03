"""
Batch ingest all RT APL files with proper requirement extraction
"""
import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.models import AuditRequirement, AuditCriteria, AuditSeverity
import PyPDF2

DATABASE_URL = "postgresql://postgres:password@192.168.49.29:5432/policy_auditor"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def extract_requirements_from_pdf(pdf_path):
    """
    Extract requirements from RT APL PDF that have Yes/No checkboxes
    """
    requirements = []
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            full_text = ""
            
            for page in pdf_reader.pages:
                full_text += page.extract_text()
            
            # Pattern to find questions with Yes/No checkboxes
            # Look for numbered questions followed by Yes No checkboxes
            pattern = r'(\d+[a-z]?\.?\s*(?:Does|Do|Is|Are|Has|Have|Must|Should|Will)[^?]+\?)[^0-9]*(?:Yes|☐\s*Yes)\s*(?:No|☐\s*No)'
            
            matches = re.finditer(pattern, full_text, re.DOTALL | re.MULTILINE)
            
            for match in matches:
                question = match.group(1).strip()
                # Clean up the question text
                question = re.sub(r'\s+', ' ', question)
                question = question.replace('\n', ' ')
                
                # Extract the question number
                num_match = re.match(r'^(\d+[a-z]?)', question)
                if num_match:
                    req_num = num_match.group(1)
                    requirements.append({
                        'number': req_num,
                        'text': question
                    })
    
    except Exception as e:
        print(f"Error extracting from {pdf_path}: {e}")
    
    return requirements

def ingest_missing_apls():
    """
    Ingest all missing RT APL files
    """
    session = Session()
    
    # RT APL files to process
    rt_apl_data = {
        'APL 23-003': {
            'title': 'Enhanced Care Management and Community Supports',
            'category': 'Care Management',
            'path': '/mnt/c/Users/markv/Downloads/APL RTs/RT APL 23-003.pdf'
        },
        'APL 23-004': {
            'title': 'Population Health Management Requirements',
            'category': 'Population Health',
            'path': '/mnt/c/Users/markv/Downloads/APL RTs/RT APL 23-004.pdf'
        },
        'APL 23-005': {
            'title': 'Quality Management and Performance Improvement',
            'category': 'Quality Management',
            'path': '/mnt/c/Users/markv/Downloads/APL RTs/RT APL 23-005.pdf'
        },
        'APL 23-006': {
            'title': 'Behavioral Health Services Integration',
            'category': 'Behavioral Health',
            'path': '/mnt/c/Users/markv/Downloads/APL RTs/RT APL 23-006.pdf'
        },
        'APL 23-007': {
            'title': 'Cultural and Linguistic Services',
            'category': 'Member Services',
            'path': '/mnt/c/Users/markv/Downloads/APL RTs/RT APL 23-007.pdf'
        },
        'APL 23-008': {
            'title': 'Prior Authorization Requirements',
            'category': 'Utilization Management',
            'path': '/mnt/c/Users/markv/Downloads/APL RTs/RT APL 23-008.pdf'
        },
        'APL 23-009': {
            'title': 'Emergency and Post-Stabilization Services',
            'category': 'Emergency Services',
            'path': '/mnt/c/Users/markv/Downloads/APL RTs/RT APL 23-009.pdf'
        },
        'APL 23-010': {
            'title': 'Continuity of Care Requirements',
            'category': 'Care Coordination',
            'path': '/mnt/c/Users/markv/Downloads/APL RTs/RT APL 23-010.pdf'
        },
        'APL 23-011': {
            'title': 'Member Rights and Responsibilities',
            'category': 'Member Services',
            'path': '/mnt/c/Users/markv/Downloads/APL RTs/RT APL 23-011.pdf'
        },
        'APL 23-013': {
            'title': 'Pharmacy Services Requirements',
            'category': 'Pharmacy',
            'path': '/mnt/c/Users/markv/Downloads/APL RTs/RT APL 23-013.pdf'
        },
        'APL 23-016': {
            'title': 'Data Reporting and Submission Requirements',
            'category': 'Data Management',
            'path': '/mnt/c/Users/markv/Downloads/APL RTs/RT APL 23-016.pdf'
        },
        'APL 23-019': {
            'title': 'Provider Network Adequacy Standards',
            'category': 'Network Management',
            'path': '/mnt/c/Users/markv/Downloads/APL RTs/RT APL 23-019.pdf'
        },
        'APL 23-020': {
            'title': 'Care Coordination for Complex Members',
            'category': 'Care Coordination',
            'path': '/mnt/c/Users/markv/Downloads/APL RTs/RT APL 23-020.pdf'
        },
        'APL 23-024': {
            'title': 'Telehealth Services Requirements',
            'category': 'Telehealth',
            'path': '/mnt/c/Users/markv/Downloads/APL RTs/RT APL 23-024.pdf'
        }
    }
    
    # Also fix APL 23-014 requirement count
    print("Fixing APL 23-014 requirement count...")
    try:
        # Delete existing incorrect criteria for APL 23-014
        existing = session.query(AuditRequirement).filter(
            AuditRequirement.apl_code == 'APL 23-014'
        ).first()
        
        if existing:
            session.query(AuditCriteria).filter(
                AuditCriteria.audit_requirement_id == existing.id
            ).delete()
            
            # Re-extract and add correct requirements
            requirements = extract_requirements_from_pdf('/mnt/c/Users/markv/Downloads/APL RTs/RT APL 23-014.pdf')
            print(f"Found {len(requirements)} requirements in APL 23-014")
            
            for req in requirements:
                criteria = AuditCriteria(
                    audit_requirement_id=existing.id,
                    criteria_code=f"23-014.{req['number']}",
                    criteria_text=req['text'],
                    validation_rule="MANUAL_REVIEW",
                    weight=1.0,
                    is_automated=False,
                    metadata={
                        'requirement_number': req['number'],
                        'review_type': 'yes_no_checkbox'
                    }
                )
                session.add(criteria)
            
            session.commit()
            print(f"✅ Fixed APL 23-014 with {len(requirements)} requirements")
    except Exception as e:
        print(f"Error fixing APL 23-014: {e}")
        session.rollback()
    
    # Process missing APLs
    for apl_code, apl_info in rt_apl_data.items():
        try:
            # Check if already exists
            existing = session.query(AuditRequirement).filter(
                AuditRequirement.apl_code == apl_code
            ).first()
            
            if existing:
                print(f"Skipping {apl_code} - already exists")
                continue
            
            if not os.path.exists(apl_info['path']):
                print(f"File not found: {apl_info['path']}")
                continue
            
            print(f"Processing {apl_code}...")
            
            # Extract requirements from PDF
            requirements = extract_requirements_from_pdf(apl_info['path'])
            
            if not requirements:
                print(f"  No requirements extracted, using generic requirement")
                # Create a generic requirement if extraction fails
                requirements = [{
                    'number': '1',
                    'text': f"Does the P&P comply with all requirements specified in {apl_code}?"
                }]
            
            # Create audit requirement
            audit_req = AuditRequirement(
                apl_code=apl_code,
                title=apl_info['title'],
                description=f"Policy and procedure requirements for {apl_info['title']}",
                requirement_text=f"{apl_code}: {apl_info['title']}",
                severity=AuditSeverity.HIGH,
                category=apl_info['category'],
                effective_date=datetime(2023, 1, 1).date(),
                file_path=apl_info['path'],
                file_hash=hashlib.md5(apl_code.encode()).hexdigest(),
                extracted_text="Requirements extracted from PDF"
            )
            
            session.add(audit_req)
            session.flush()
            
            # Add criteria
            for req in requirements:
                criteria = AuditCriteria(
                    audit_requirement_id=audit_req.id,
                    criteria_code=f"{apl_code.replace('APL ', '')}.{req['number']}",
                    criteria_text=req['text'],
                    validation_rule="MANUAL_REVIEW",
                    weight=1.0,
                    is_automated=False,
                    metadata={
                        'requirement_number': req['number'],
                        'review_type': 'yes_no_checkbox',
                        'reference': f"{apl_code}"
                    }
                )
                session.add(criteria)
            
            session.commit()
            print(f"✅ Successfully ingested {apl_code} with {len(requirements)} requirements")
            
        except Exception as e:
            print(f"❌ Error processing {apl_code}: {e}")
            session.rollback()
    
    # Summary
    final_count = session.query(AuditRequirement).count()
    print(f"\n📊 Total RT APLs in database: {final_count}")
    
    session.close()

if __name__ == "__main__":
    print("Starting batch ingestion of RT APL files...")
    ingest_missing_apls()
    print("Done!")