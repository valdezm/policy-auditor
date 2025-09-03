"""
Manually ingest APL 23-012 with its specific requirements
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import AuditRequirement, AuditCriteria, AuditSeverity
from datetime import datetime
import hashlib

DATABASE_URL = "postgresql://postgres:password@192.168.49.29:5432/policy_auditor"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Create APL 23-012 audit requirement
apl_23_012 = AuditRequirement(
    apl_code="APL 23-012",
    title="Policy and Procedure regarding Sanctions",
    description="Requirements for policies addressing DHCS sanctions under WIC 14197.7, including probability sampling and extrapolation procedures",
    requirement_text="""
    APL 23-012 requires Medi-Cal Managed Care Plans to have policies and procedures that:
    1. Reference 22 CCR 51458.2 for probability sampling methodology
    2. Specify DHCS's ability to use probability sampling to determine beneficiary harm
    3. Include definitions for probability sampling and extrapolation
    """,
    severity=AuditSeverity.HIGH,
    category="Compliance and Sanctions",
    effective_date=datetime(2023, 1, 1).date(),
    file_path="/mnt/c/Users/markv/Downloads/APL RTs/RT APL 23-012.pdf",
    file_hash=hashlib.md5("APL 23-012".encode()).hexdigest(),
    extracted_text="Full text would be extracted from PDF"
)

session.add(apl_23_012)
session.flush()

# Add the 3 specific criteria/requirements
criteria_list = [
    {
        "criteria_code": "23-012.1",
        "criteria_text": """Does the P&P include reference to 22 CCR 51458.2 and specify that DHCS may deploy the 
use of probability sampling to determine the potential harm or impact on beneficiaries due to the 
violation pursuant to WIC section 14197.7(g)(1)?""",
        "validation_rule": "MUST_REFERENCE|22_CCR_51458.2|WIC_14197.7",
    },
    {
        "criteria_code": "23-012.2", 
        "criteria_text": """Does the P&P include a reference to state that DHCS may use probability sampling to 
extrapolate and determine the number of beneficiaries impacted by sanctionable conduct, 
which is described under WIC section 14197.7(f)(1)?""",
        "validation_rule": "MUST_REFERENCE|PROBABILITY_SAMPLING|EXTRAPOLATION|WIC_14197.7",
    },
    {
        "criteria_code": "23-012.3",
        "criteria_text": """Does the P&P include the DHCS specified definitions for the terms Probability Sample and 
Extrapolation? 
• "Probability sampling" means the standard statistical methodology in which a sample 
is selected based on the theory of probability (a mathematical theory used to study the 
occurrence of random events).
• "Extrapolation" means the methodology whereby an unknown value can be estimated 
by projecting the results of a probability sample to the universe from which the sample 
was drawn with a calculated precision (margin of error).""",
        "validation_rule": "MUST_DEFINE|PROBABILITY_SAMPLING|EXTRAPOLATION",
    }
]

for idx, criteria_data in enumerate(criteria_list, 1):
    criteria = AuditCriteria(
        audit_requirement_id=apl_23_012.id,
        criteria_code=criteria_data["criteria_code"],
        criteria_text=criteria_data["criteria_text"],
        validation_rule=criteria_data["validation_rule"],
        weight=1.0,
        is_automated=False,
        metadata={
            "reference": "APL 23-012, Page 9",
            "requirement_number": idx,
            "review_type": "yes_no_checkbox"
        }
    )
    session.add(criteria)

try:
    session.commit()
    print("✅ Successfully ingested APL 23-012 with 3 requirements")
    
    # Verify it was added
    check = session.query(AuditCriteria).filter(
        AuditCriteria.audit_requirement_id == apl_23_012.id
    ).count()
    print(f"✅ Verified: {check} criteria added for APL 23-012")
    
except Exception as e:
    print(f"❌ Error: {e}")
    session.rollback()
finally:
    session.close()