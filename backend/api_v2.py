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
from core.enhanced_policy_analyzer import EnhancedPolicyAnalyzer
from services.ai_validator import AIValidationService
from models.models import AIValidationResult, Policy, AuditRequirement


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


class AIValidationRequest(BaseModel):
    """Request model for AI validation"""
    policy_id: str
    requirement_id: str
    requirement_text: str
    regulation_reference: str


class AIValidationResponse(BaseModel):
    """Response model for AI validation"""
    validation_id: str
    policy_id: str
    requirement_id: str
    compliance_rating: str
    confidence_level: str
    confidence_score: float
    reasoning: str
    specific_findings: List[str]
    missing_elements: List[str]
    policy_strengths: List[str]
    recommendations: List[str]
    relevant_policy_excerpts: List[str]
    regulatory_interpretation: str
    risk_assessment: str
    priority_level: str
    validation_date: str
    is_human_reviewed: bool


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


@app.get("/api/v2/requirements/{requirement_id}/enhanced-analysis")
def get_enhanced_requirement_analysis(requirement_id: str, db: Session = Depends(get_db)):
    """
    Get enhanced policy analysis with semantic context understanding
    Uses the new EnhancedPolicyAnalyzer for better accuracy
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
    
    # Use the enhanced analyzer
    enhanced_analyzer = EnhancedPolicyAnalyzer(db)
    analyses = enhanced_analyzer.analyze_requirement_compliance(requirement_id)
    
    # Also get policy IDs for each analysis
    from models.models import Policy
    
    return {
        'requirement_id': requirement_id,
        'apl_code': req_result.apl_code,
        'apl_title': req_result.apl_title,
        'section_code': req_result.criteria_code or 'Main',
        'requirement_text': req_result.criteria_text,
        'validation_rule': req_result.validation_rule,
        'analyzer_version': 'enhanced',
        'total_policies_analyzed': len(analyses),
        'compliant_policies': sum(1 for a in analyses if a.is_compliant),
        'high_confidence_analyses': sum(1 for a in analyses if a.confidence_level > 0.8),
        'analyses': [
            {
                'policy_id': str(db.query(Policy).filter(Policy.policy_code == a.policy_code).first().id) if db.query(Policy).filter(Policy.policy_code == a.policy_code).first() else None,
                'policy_code': a.policy_code,
                'policy_title': a.policy_title,
                'compliance_score': a.compliance_score,
                'confidence_level': a.confidence_level,
                'is_compliant': a.is_compliant,
                'has_primary_reference': a.has_primary_reference,
                'has_cross_references': a.has_cross_references,
                'missing_elements': a.missing_elements,
                'found_elements': a.found_elements,
                'explanation': a.explanation,
                'recommendations': a.recommendations,
                'contextual_excerpts': [
                    {
                        'text': e.text,
                        'context': e.context,
                        'relevance_score': e.relevance_score,
                        'matched_elements': e.matched_elements,
                        'surrounding_keywords': e.surrounding_keywords
                    }
                    for e in a.contextual_excerpts[:5]  # Top 5 excerpts
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
    Get full policy details by ID or code
    """
    from models.models import Policy
    from sqlalchemy import text
    
    # First try to find by ID
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    
    # If not found, try by code
    if not policy:
        policy = db.query(Policy).filter(Policy.policy_code == policy_id).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy not found: {policy_id}")
    
    return {
        'policy_id': policy.id,
        'policy_code': policy.policy_code,
        'title': policy.title or policy.policy_code,  # Use clean title or policy code as fallback
        'filename': policy.file_path or f"{policy.policy_code}.pdf",  # Use file_path or generate filename
        'extracted_text': policy.extracted_text[:10000] if policy.extracted_text else "",  # Limit to 10KB
        'file_size': len(policy.extracted_text) if policy.extracted_text else 0,
        'created_at': policy.created_at.isoformat() if policy.created_at else None
    }


@app.post("/api/v2/ai-validation/validate", response_model=AIValidationResponse)
def validate_policy_with_ai(
    request: AIValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Validate a policy against a requirement using AI
    """
    import time
    import os
    from datetime import datetime
    from models.models import AuditCriteria
    
    # Get policy and requirement details
    policy = db.query(Policy).filter(Policy.id == request.policy_id).first()
    if not policy:
        # Try to find policy by code if ID fails
        policy = db.query(Policy).filter(Policy.policy_code == request.policy_id).first()
        if not policy:
            raise HTTPException(status_code=404, detail=f"Policy not found: {request.policy_id}")
    
    # First try to find as an AuditCriteria (which is what the frontend sends)
    audit_criteria = db.query(AuditCriteria).filter(AuditCriteria.id == request.requirement_id).first()
    if audit_criteria:
        # Get the parent AuditRequirement
        audit_req = db.query(AuditRequirement).filter(
            AuditRequirement.id == audit_criteria.audit_requirement_id
        ).first()
        # Use criteria text if available
        if audit_criteria.criteria_text:
            request.requirement_text = audit_criteria.criteria_text
    else:
        # Try direct AuditRequirement lookup
        audit_req = db.query(AuditRequirement).filter(AuditRequirement.id == request.requirement_id).first()
        
    if not audit_req:
        raise HTTPException(status_code=404, detail=f"Audit requirement not found: {request.requirement_id}")
    
    # Check if validation already exists
    existing_validation = db.query(AIValidationResult).filter(
        AIValidationResult.policy_id == policy.id,
        AIValidationResult.audit_requirement_id == audit_req.id,
        AIValidationResult.requirement_text == request.requirement_text
    ).first()
    
    if existing_validation:
        return _format_validation_response(existing_validation)
    
    # Initialize AI validation service
    ai_service = AIValidationService(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Perform AI validation
    start_time = time.time()
    try:
        validation_result = ai_service.validate_policy_compliance(
            policy_text=policy.extracted_text or "",
            requirement_text=request.requirement_text,
            regulation_reference=request.regulation_reference,
            requirement_context={
                'apl_code': audit_req.apl_code,
                'category': audit_req.category,
                'severity': audit_req.severity.value if audit_req.severity else None
            }
        )
        processing_time = int((time.time() - start_time) * 1000)
        
        # Save validation result to database
        db_validation = AIValidationResult(
            policy_id=policy.id,
            audit_requirement_id=audit_req.id,
            requirement_text=request.requirement_text,
            regulation_reference=request.regulation_reference,
            compliance_rating=validation_result.compliance_rating.value,
            confidence_level=validation_result.confidence_level.value,
            confidence_score=validation_result.confidence_score,
            reasoning=validation_result.reasoning,
            specific_findings=validation_result.specific_findings,
            missing_elements=validation_result.missing_elements,
            policy_strengths=validation_result.policy_strengths,
            recommendations=validation_result.recommendations,
            relevant_policy_excerpts=validation_result.relevant_policy_excerpts,
            regulatory_interpretation=validation_result.regulatory_interpretation,
            risk_assessment=validation_result.risk_assessment,
            priority_level=validation_result.priority_level,
            processing_time_ms=processing_time
        )
        
        db.add(db_validation)
        db.commit()
        db.refresh(db_validation)
        
        return _format_validation_response(db_validation)
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"AI validation failed: {str(e)}"
        )


@app.get("/api/v2/ai-validation/{validation_id}", response_model=AIValidationResponse)
def get_ai_validation(validation_id: str, db: Session = Depends(get_db)):
    """
    Get a specific AI validation result
    """
    validation = db.query(AIValidationResult).filter(AIValidationResult.id == validation_id).first()
    if not validation:
        raise HTTPException(status_code=404, detail="AI validation not found")
    
    return _format_validation_response(validation)


@app.get("/api/v2/ai-validation/policy/{policy_id}")
def get_policy_ai_validations(policy_id: str, db: Session = Depends(get_db)):
    """
    Get all AI validation results for a specific policy
    """
    validations = db.query(AIValidationResult).filter(
        AIValidationResult.policy_id == policy_id
    ).all()
    
    return {
        'policy_id': policy_id,
        'total_validations': len(validations),
        'validations': [_format_validation_response(v) for v in validations]
    }


@app.get("/api/v2/ai-validation/requirement/{requirement_id}")
def get_requirement_ai_validations(requirement_id: str, db: Session = Depends(get_db)):
    """
    Get all AI validation results for a specific requirement
    """
    validations = db.query(AIValidationResult).filter(
        AIValidationResult.audit_requirement_id == requirement_id
    ).all()
    
    return {
        'requirement_id': requirement_id,
        'total_validations': len(validations),
        'validations': [_format_validation_response(v) for v in validations]
    }


@app.post("/api/v2/ai-validation/{validation_id}/review")
def update_ai_validation_review(
    validation_id: str,
    review_notes: str,
    override_rating: Optional[str] = None,
    reviewer_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Add human review to an AI validation result
    """
    validation = db.query(AIValidationResult).filter(AIValidationResult.id == validation_id).first()
    if not validation:
        raise HTTPException(status_code=404, detail="AI validation not found")
    
    # Update review fields
    validation.is_human_reviewed = True
    validation.human_review_notes = review_notes
    validation.reviewed_by = reviewer_name
    validation.reviewed_at = datetime.utcnow()
    
    if override_rating:
        from models.models import AIValidationComplianceRating
        try:
            validation.human_override_rating = AIValidationComplianceRating(override_rating)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid override rating")
    
    db.commit()
    db.refresh(validation)
    
    return _format_validation_response(validation)


@app.get("/api/v2/ai-validation/stats")
def get_ai_validation_stats(db: Session = Depends(get_db)):
    """
    Get statistics about AI validations
    """
    from sqlalchemy import func
    from models.models import AIValidationComplianceRating, AIValidationConfidenceLevel
    
    total_validations = db.query(AIValidationResult).count()
    
    # Compliance rating distribution
    rating_stats = db.query(
        AIValidationResult.compliance_rating,
        func.count(AIValidationResult.id).label('count')
    ).group_by(AIValidationResult.compliance_rating).all()
    
    # Confidence level distribution
    confidence_stats = db.query(
        AIValidationResult.confidence_level,
        func.count(AIValidationResult.id).label('count')
    ).group_by(AIValidationResult.confidence_level).all()
    
    # Human review status
    human_reviewed = db.query(AIValidationResult).filter(
        AIValidationResult.is_human_reviewed == True
    ).count()
    
    return {
        'total_validations': total_validations,
        'human_reviewed': human_reviewed,
        'human_review_rate': round(human_reviewed / total_validations * 100, 2) if total_validations > 0 else 0,
        'compliance_distribution': {stat.compliance_rating: stat.count for stat in rating_stats},
        'confidence_distribution': {stat.confidence_level: stat.count for stat in confidence_stats}
    }


def _format_validation_response(validation: AIValidationResult) -> AIValidationResponse:
    """Helper function to format validation response"""
    return AIValidationResponse(
        validation_id=str(validation.id),
        policy_id=str(validation.policy_id),
        requirement_id=str(validation.audit_requirement_id),
        compliance_rating=validation.human_override_rating or validation.compliance_rating,
        confidence_level=validation.confidence_level,
        confidence_score=float(validation.confidence_score),
        reasoning=validation.reasoning or "",
        specific_findings=validation.specific_findings or [],
        missing_elements=validation.missing_elements or [],
        policy_strengths=validation.policy_strengths or [],
        recommendations=validation.recommendations or [],
        relevant_policy_excerpts=validation.relevant_policy_excerpts or [],
        regulatory_interpretation=validation.regulatory_interpretation or "",
        risk_assessment=validation.risk_assessment or "",
        priority_level=validation.priority_level or "medium",
        validation_date=validation.validation_date.isoformat() if validation.validation_date else "",
        is_human_reviewed=validation.is_human_reviewed
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)