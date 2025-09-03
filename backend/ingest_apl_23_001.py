"""
Manually ingest APL 23-001 with its requirements
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

# Create APL 23-001 audit requirement
apl_23_001 = AuditRequirement(
    apl_code="APL 23-001",
    title="Network Certification Requirements",
    description="Requirements for Annual Network Certification (ANC), good faith contracting, and referral requirements with cancer centers",
    requirement_text="""APL 23-001 Network Certification Requirements (Supersedes APL 22-006)
    Policies and Procedures for Managed Care Health Plans' (MCPs) will provide guidance on:
    - Annual Network Certification requirements
    - Good faith contracting requirements with certain cancer centers
    - Network adequacy standards including time/distance requirements
    - Alternative Access Standard (AAS) requests
    - Telehealth utilization for network adequacy""",
    severity=AuditSeverity.HIGH,
    category="Network Management",
    effective_date=datetime(2023, 1, 1).date(),
    file_path="/mnt/c/Users/markv/Downloads/APL RTs/RT APL 23-001.pdf",
    file_hash=hashlib.md5("APL 23-001".encode()).hexdigest(),
    extracted_text="Full text extracted from PDF"
)

session.add(apl_23_001)
session.flush()

# Add key requirements - focusing on first few critical ones
criteria_list = [
    {
        "criteria_code": "23-001.1a",
        "criteria_text": """Does the P&Ps indicate MCP will submit complete and accurate data and information to 
DHCS that reflects the composition of the Network Providers subject to ANC requirements no 
later than 30 calendar days after receipt of DHCS ANC documents package, unless an extension 
is granted by DHCS?""",
        "validation_rule": "MUST_SUBMIT|30_CALENDAR_DAYS|COMPLETE_ACCURATE",
    },
    {
        "criteria_code": "23-001.1b", 
        "criteria_text": """Does the P&Ps indicate MCP will submit all required ANC exhibits as outlined in Attachment 
B and if applicable, alternative access (AAS) request in Attachment C, with the correct file 
labeling convention through the DHCS Secure File Transfer Protocol site?""",
        "validation_rule": "MUST_SUBMIT|ANC_EXHIBITS|ATTACHMENT_B|ATTACHMENT_C|SFTP",
    },
    {
        "criteria_code": "23-001.1c",
        "criteria_text": """Does the P&Ps indicate MCP must submit all complete and accurate exhibits, data and 
information for annual ANC requirements by the deadline or will be subject to a corrective action 
plan (CAP) or other enforcement actions?""",
        "validation_rule": "MUST_SUBMIT|DEADLINE|CAP|ENFORCEMENT",
    },
    {
        "criteria_code": "23-001.2a",
        "criteria_text": """Does the P&Ps indicate MCP will submit 274 Files for DHCS to verify the MCP's compliance 
with Provider to Member ratios, Mandatory Provider types, and timely access to standards for 
PCP for PCPs, core Specialists, Non-Specialty Mental Health providers, hospitals, and ancillary 
services?""",
        "validation_rule": "MUST_SUBMIT|274_FILES|PROVIDER_RATIOS|TIMELY_ACCESS",
    },
    {
        "criteria_code": "23-001.3a",
        "criteria_text": """Does the P&Ps indicate MCP will maintain an appropriate Network of specific Provider types 
to ensure the MCP's Network has the capacity to provide all Medically Necessary services for 
current and anticipated membership?""",
        "validation_rule": "MUST_MAINTAIN|NETWORK_CAPACITY|MEDICALLY_NECESSARY",
    },
    {
        "criteria_code": "23-001.3b",
        "criteria_text": """Does the P&Ps indicate MCP will comply with WIC section 14197.45 as set forth by SB 987 
and make good faith efforts to contract with at least one cancer center within their contracted 
Provider Networks and their subcontracted Provider Networks, if applicable, within each county in 
which the MCP operates, for provision of services to any eligible Member diagnosed with a 
complex cancer diagnosis?""",
        "validation_rule": "MUST_COMPLY|WIC_14197.45|SB_987|CANCER_CENTER|GOOD_FAITH",
    },
    {
        "criteria_code": "23-001.4a",
        "criteria_text": """Does the P&Ps indicate MCP met or exceeded the minimum Service Area capacity and ratio 
requirements as outlined in the MCP Contract for their model type ratios of one FTE PCP to 
every 2,000 Members and one FTE Physician to every 1,200 Members?""",
        "validation_rule": "MUST_MEET|PCP_RATIO_1:2000|PHYSICIAN_RATIO_1:1200",
    },
    {
        "criteria_code": "23-001.9a",
        "criteria_text": """Does the P&Ps indicate MCP must meet time or standards based on the population density 
of the county for designated Provider types set forth in Attachment A of this APL?""",
        "validation_rule": "MUST_MEET|TIME_DISTANCE_STANDARDS|ATTACHMENT_A",
    },
    {
        "criteria_code": "23-001.10a",
        "criteria_text": """Does the P&Ps indicate MCP is required to cover 100% of the population points in the ZIP 
code in order to be considered compliant with time or distance standards with any deficiencies 
accounted for through AAS requests?""",
        "validation_rule": "MUST_COVER|100_PERCENT_POPULATION|ZIP_CODE|AAS",
    },
    {
        "criteria_code": "23-001.10b",
        "criteria_text": """Does the P&Ps indicate when medically appropriate, if the MCP covers at least 85% of the 
population points in the ZIP code, DHCS permits MCP to use the synchronous mode of 
Telehealth instead of submitting an AAS request?""",
        "validation_rule": "MAY_USE|TELEHEALTH|85_PERCENT|SYNCHRONOUS",
    }
]

for idx, criteria_data in enumerate(criteria_list, 1):
    criteria = AuditCriteria(
        audit_requirement_id=apl_23_001.id,
        criteria_code=criteria_data["criteria_code"],
        criteria_text=criteria_data["criteria_text"],
        validation_rule=criteria_data["validation_rule"],
        weight=1.0,
        is_automated=False,
        metadata={
            "reference": "APL 23-001",
            "requirement_number": idx,
            "review_type": "yes_no_checkbox"
        }
    )
    session.add(criteria)

try:
    session.commit()
    print(f"✅ Successfully ingested APL 23-001 with {len(criteria_list)} requirements")
    
    # Verify it was added
    check = session.query(AuditCriteria).filter(
        AuditCriteria.audit_requirement_id == apl_23_001.id
    ).count()
    print(f"✅ Verified: {check} criteria added for APL 23-001")
    
except Exception as e:
    print(f"❌ Error: {e}")
    session.rollback()
finally:
    session.close()