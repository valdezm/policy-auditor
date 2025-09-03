"""
Enhanced API v2 with detailed requirement coverage
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from models.database import get_db, init_db
from core.enhanced_coverage_analyzer import EnhancedCoverageAnalyzer, CoverageType
from core.policy_analyzer import PolicyAnalyzer, APL23012Analyzer


app = FastAPI(title="Policy Auditor API v2")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ManualReviewUpdate(BaseModel):
    """Manual review update request"""
    requirement_id: str
    coverage_type: str
    policy_references: List[str]
    reviewer_notes: str
    is_verified: bool


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/api/v2/coverage/detailed")
def get_detailed_coverage(
    apl_code: Optional[str] = None,
    coverage_type: Optional[str] = None,
    needs_review: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Get detailed coverage analysis with all requirements
    """
    analyzer = EnhancedCoverageAnalyzer(db)
    results = analyzer.analyze_corpus_coverage_v2()
    
    # Filter by APL code if provided
    if apl_code:
        if apl_code in results['by_apl']:
            filtered_results = {
                'total_requirements': len(results['by_apl'][apl_code]['requirements']),
                'coverage_summary': results['by_apl'][apl_code]['summary'],
                'assessments': results['by_apl'][apl_code]['requirements']
            }
            return filtered_results
        else:
            raise HTTPException(status_code=404, detail=f"APL {apl_code} not found")
    
    # Filter by coverage type
    if coverage_type:
        filtered = [a for a in results['assessments'] 
                   if a.coverage_type.value == coverage_type]
        results['assessments'] = filtered
        results['total_requirements'] = len(filtered)
    
    # Filter by needs review
    if needs_review is not None:
        filtered = [a for a in results['assessments'] 
                   if a.manual_review_needed == needs_review]
        results['assessments'] = filtered
        results['total_requirements'] = len(filtered)
    
    # Convert assessments to dict format
    results['assessments'] = [
        {
            'requirement_id': a.requirement.requirement_id,
            'apl_code': a.requirement.apl_code,
            'section': a.requirement.section_number,
            'requirement_text': a.requirement.requirement_text,
            'regulation_references': a.requirement.regulation_references,
            'key_obligations': a.requirement.key_obligations,
            'timeframes': a.requirement.timeframes,
            'coverage_type': a.coverage_type.value,
            'confidence_score': a.confidence_score,
            'matching_policies': a.matching_policies,
            'evidence': a.evidence,
            'gaps': a.gaps,
            'manual_review_needed': a.manual_review_needed,
            'is_verified': a.is_verified,
            'reviewer_notes': a.reviewer_notes
        }
        for a in results['assessments']
    ]
    
    return results


@app.get("/api/v2/requirements/{apl_code}")
def get_apl_requirements(apl_code: str, db: Session = Depends(get_db)):
    """
    Get all requirements for a specific APL with coverage status
    """
    from models.models import AuditRequirement
    
    audit_req = db.query(AuditRequirement).filter(
        AuditRequirement.apl_code == apl_code
    ).first()
    
    if not audit_req:
        raise HTTPException(status_code=404, detail=f"APL {apl_code} not found")
    
    analyzer = EnhancedCoverageAnalyzer(db)
    requirements = analyzer.extract_requirement_details(audit_req)
    
    # Get coverage for each requirement
    from models.models import Policy
    policies = db.query(Policy).all()
    
    detailed_requirements = []
    for req in requirements:
        # Find best coverage across all policies
        best_assessment = None
        all_matching_policies = []
        
        for policy in policies:
            assessment = analyzer.assess_policy_coverage(req, policy)
            if assessment.coverage_type != CoverageType.NO_COVERAGE:
                all_matching_policies.extend(assessment.matching_policies)
                if not best_assessment or analyzer._is_better_coverage(
                    assessment.coverage_type, best_assessment.coverage_type
                ):
                    best_assessment = assessment
        
        detailed_requirements.append({
            'requirement_id': req.requirement_id,
            'section': req.section_number,
            'text': req.requirement_text,
            'regulation_references': req.regulation_references,
            'obligations': req.key_obligations,
            'timeframes': req.timeframes,
            'definitions': req.definitions,
            'coverage': {
                'type': best_assessment.coverage_type.value if best_assessment else 'no_coverage',
                'confidence': best_assessment.confidence_score if best_assessment else 0,
                'matching_policies': all_matching_policies,
                'gaps': best_assessment.gaps if best_assessment else ['No coverage found']
            }
        })
    
    return {
        'apl_code': apl_code,
        'title': audit_req.title,
        'total_requirements': len(detailed_requirements),
        'requirements': detailed_requirements
    }


@app.post("/api/v2/requirements/{requirement_id}/review")
def update_manual_review(
    requirement_id: str,
    update: ManualReviewUpdate,
    db: Session = Depends(get_db)
):
    """
    Update manual review status for a requirement
    """
    # This would update a review table in production
    # For now, return success
    return {
        'success': True,
        'requirement_id': requirement_id,
        'updated': update.dict()
    }


@app.get("/api/v2/coverage/matrix")
def get_coverage_matrix(db: Session = Depends(get_db)):
    """
    Get a matrix view of all APLs vs coverage types
    """
    analyzer = EnhancedCoverageAnalyzer(db)
    results = analyzer.analyze_corpus_coverage_v2()
    
    matrix = []
    for apl_code, apl_data in results['by_apl'].items():
        row = {
            'apl_code': apl_code,
            'total': len(apl_data['requirements']),
            **apl_data['summary']
        }
        matrix.append(row)
    
    return {
        'matrix': matrix,
        'coverage_types': [ct.value for ct in CoverageType]
    }


@app.get("/api/v2/requirements/{requirement_id}/analysis")
def get_requirement_analysis(requirement_id: str, db: Session = Depends(get_db)):
    """
    Get detailed policy analysis for a specific requirement
    Shows which policies comply and why/why not with excerpts
    """
    # First get the requirement details
    from sqlalchemy import text
    
    req_query = text("""
        SELECT 
            ar.apl_code,
            ar.title as apl_title,
            ac.criteria_code,
            ac.criteria_text,
            ac.validation_rule
        FROM audit_criteria ac
        JOIN audit_requirements ar ON ar.id = ac.audit_requirement_id
        WHERE ac.id = :req_id
    """)
    
    req_result = db.execute(req_query, {"req_id": requirement_id}).fetchone()
    if not req_result:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    analyzer = PolicyAnalyzer(db)
    analyses = analyzer.analyze_requirement_compliance(requirement_id)
    
    return {
        'requirement_id': requirement_id,
        'apl_code': req_result.apl_code,
        'apl_title': req_result.apl_title,
        'section_code': req_result.criteria_code or 'Main',
        'requirement_text': req_result.criteria_text,
        'validation_rule': req_result.validation_rule,
        'total_policies_analyzed': len(analyses),
        'compliant_policies': sum(1 for a in analyses if a.is_compliant),
        'analyses': [
            {
                'policy_code': a.policy_code,
                'policy_title': a.policy_title,
                'compliance_score': a.compliance_score,
                'is_compliant': a.is_compliant,
                'has_reference': a.has_reference,
                'missing_elements': a.missing_elements,
                'found_elements': a.found_elements,
                'explanation': a.explanation,
                'recommendations': a.recommendations,
                'excerpts': [
                    {
                        'text': e.text,
                        'context': e.context
                    }
                    for e in a.relevant_excerpts[:3]  # Limit excerpts
                ]
            }
            for a in analyses
        ]
    }


@app.get("/api/v2/apl/23-012/detailed-analysis")
def get_apl_23012_analysis(db: Session = Depends(get_db)):
    """
    Get specialized analysis for APL 23-012 sanctions requirements
    """
    analyzer = APL23012Analyzer(db)
    return analyzer.analyze_23012_compliance()



@app.get("/api/v2/policies/{policy_code}/coverage")
def get_policy_coverage(policy_code: str, db: Session = Depends(get_db)):
    """
    Get all requirements that a specific policy covers
    """
    from models.models import Policy, AuditRequirement
    
    policy = db.query(Policy).filter(Policy.policy_code == policy_code).first()
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {policy_code} not found")
    
    analyzer = EnhancedCoverageAnalyzer(db)
    audit_reqs = db.query(AuditRequirement).all()
    
    covered_requirements = []
    
    for audit_req in audit_reqs:
        requirements = analyzer.extract_requirement_details(audit_req)
        for req in requirements:
            assessment = analyzer.assess_policy_coverage(req, policy)
            if assessment.coverage_type != CoverageType.NO_COVERAGE:
                covered_requirements.append({
                    'requirement_id': req.requirement_id,
                    'apl_code': req.apl_code,
                    'requirement_text': req.requirement_text[:200],
                    'coverage_type': assessment.coverage_type.value,
                    'confidence': assessment.confidence_score,
                    'evidence': assessment.evidence
                })
    
    return {
        'policy_code': policy_code,
        'policy_title': policy.title,
        'total_covered': len(covered_requirements),
        'covered_requirements': covered_requirements
    }


@app.get("/api/v2/policies/{policy_id}")
def get_policy_by_id(policy_id: str, db: Session = Depends(get_db)):
    """
    Get full policy details by ID
    """
    from models.models import Policy
    from sqlalchemy import text
    
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return {
        'policy_id': policy.id,
        'policy_code': policy.policy_code,
        'title': policy.title or policy.policy_code,  # Use clean title or policy code as fallback
        'filename': policy.file_path or f"{policy.policy_code}.pdf",  # Use file_path or generate filename
        'extracted_text': policy.extracted_text[:10000] if policy.extracted_text else "",  # Limit to 10KB
        'file_size': len(policy.extracted_text) if policy.extracted_text else 0,
        'created_at': policy.created_at.isoformat() if policy.created_at else None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)