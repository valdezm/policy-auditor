"""
Enhanced Coverage Analyzer V2
Distinguishes between reference mentions and actual compliance
"""
import re
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import text

from models.models import Policy, AuditRequirement, AuditCriteria

logger = logging.getLogger(__name__)


class CoverageType(Enum):
    """Different types of coverage relationships"""
    FULL_COMPLIANCE = "full_compliance"      # Policy fully satisfies requirement
    PARTIAL_COMPLIANCE = "partial_compliance" # Policy partially satisfies  
    REFERENCE_ONLY = "reference_only"        # Policy mentions regulation but doesn't satisfy
    RELATED = "related"                       # Policy is topically related
    NO_COVERAGE = "no_coverage"              # No relationship found
    MANUAL_REVIEW = "manual_review"          # Needs human verification


@dataclass
class RequirementDetail:
    """Detailed requirement with extracted components"""
    requirement_id: str
    apl_code: str
    section_number: str
    requirement_text: str
    regulation_references: List[str]  # WIC codes, CCR references, etc.
    key_obligations: List[str]        # "Must", "Shall" statements
    timeframes: List[str]             # "30 days", "annually", etc.
    definitions: Dict[str, str]       # Key terms that need definition


@dataclass
class CoverageAssessment:
    """Detailed coverage assessment for a requirement"""
    requirement: RequirementDetail
    coverage_type: CoverageType
    matching_policies: List[Dict]  # Each dict has policy info and match details
    confidence_score: float
    evidence: Dict[str, any]
    gaps: List[str]
    manual_review_needed: bool
    reviewer_notes: Optional[str] = None
    is_verified: bool = False


class EnhancedCoverageAnalyzer:
    """
    V2 Coverage Analyzer with multi-tier analysis
    """
    
    # Regulation patterns to extract
    REGULATION_PATTERNS = {
        'wic': r'WIC\s+(?:Section\s+)?(\d+(?:\.\d+)*)',
        'ccr': r'(?:22\s+)?CCR\s+(?:Section\s+)?(\d+(?:\.\d+)*)',
        'hsc': r'HSC\s+(?:Section\s+)?(\d+(?:\.\d+)*)',
        'apl': r'APL\s+(\d{2}-\d{3})',
        'cfr': r'42\s+CFR\s+(?:Section\s+)?(\d+(?:\.\d+)*)',
    }
    
    # Obligation keywords
    OBLIGATION_KEYWORDS = [
        'must', 'shall', 'required', 'mandatory', 'will',
        'responsible for', 'obligation', 'ensure', 'maintain'
    ]
    
    # Timeframe patterns
    TIMEFRAME_PATTERN = r'(\d+)\s*(business\s+)?(days?|hours?|months?|years?|calendar\s+days?|working\s+days?)'
    
    def __init__(self, db: Session):
        self.db = db
    
    def extract_requirement_details(self, audit_req: AuditRequirement) -> List[RequirementDetail]:
        """
        Extract detailed requirements from an RT APL document
        """
        requirements = []
        
        # Get all criteria for this audit requirement
        criteria = self.db.query(AuditCriteria).filter(
            AuditCriteria.audit_requirement_id == audit_req.id
        ).all()
        
        for criterion in criteria:
            detail = RequirementDetail(
                requirement_id=str(criterion.id),  # Use the actual database ID
                apl_code=audit_req.apl_code,
                section_number=criterion.criteria_code or f"Section_{criterion.id}",
                requirement_text=criterion.criteria_text,
                regulation_references=self._extract_regulations(criterion.criteria_text),
                key_obligations=self._extract_obligations(criterion.criteria_text),
                timeframes=self._extract_timeframes(criterion.criteria_text),
                definitions=self._extract_definitions(criterion.criteria_text)
            )
            requirements.append(detail)
        
        # If no criteria, create one from the main requirement
        if not requirements and audit_req.requirement_text:
            detail = RequirementDetail(
                requirement_id=str(audit_req.id),
                apl_code=audit_req.apl_code,
                section_number="Main",
                requirement_text=audit_req.requirement_text[:5000],
                regulation_references=self._extract_regulations(audit_req.requirement_text),
                key_obligations=self._extract_obligations(audit_req.requirement_text),
                timeframes=self._extract_timeframes(audit_req.requirement_text),
                definitions=self._extract_definitions(audit_req.requirement_text)
            )
            requirements.append(detail)
        
        return requirements
    
    def _extract_regulations(self, text: str) -> List[str]:
        """Extract regulation references from text"""
        regulations = []
        
        for reg_type, pattern in self.REGULATION_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                regulations.append(f"{reg_type.upper()} {match.group(1)}")
        
        return list(set(regulations))
    
    def _extract_obligations(self, text: str) -> List[str]:
        """Extract obligation statements"""
        obligations = []
        sentences = text.split('.')
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in self.OBLIGATION_KEYWORDS):
                # Extract the core obligation
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 10 and len(clean_sentence) < 500:
                    obligations.append(clean_sentence)
        
        return obligations[:10]  # Limit to top 10 obligations
    
    def _extract_timeframes(self, text: str) -> List[str]:
        """Extract timeframe requirements"""
        timeframes = []
        matches = re.finditer(self.TIMEFRAME_PATTERN, text, re.IGNORECASE)
        
        for match in matches:
            timeframes.append(match.group(0))
        
        return list(set(timeframes))
    
    def _extract_definitions(self, text: str) -> Dict[str, str]:
        """Extract key term definitions"""
        definitions = {}
        
        # Look for definition patterns
        def_patterns = [
            r'"([^"]+)"\s+means\s+([^.]+)',
            r'"([^"]+)"\s+is\s+defined\s+as\s+([^.]+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+means\s+([^.]+)'
        ]
        
        for pattern in def_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                term = match.group(1).strip()
                definition = match.group(2).strip()
                if len(term) < 100 and len(definition) < 500:
                    definitions[term] = definition
        
        return definitions
    
    def assess_policy_coverage(self, 
                               requirement: RequirementDetail, 
                               policy: Policy) -> CoverageAssessment:
        """
        Assess how well a policy covers a specific requirement
        """
        if not policy.extracted_text:
            return CoverageAssessment(
                requirement=requirement,
                coverage_type=CoverageType.NO_COVERAGE,
                matching_policies=[],
                confidence_score=0.0,
                evidence={},
                gaps=["Policy has no extracted text"],
                manual_review_needed=False
            )
        
        policy_text = policy.extracted_text.lower()
        evidence = {}
        gaps = []
        
        # Check 1: Regulation References
        reg_matches = []
        for reg in requirement.regulation_references:
            if reg.lower() in policy_text:
                reg_matches.append(reg)
        evidence['regulation_matches'] = reg_matches
        
        # Check 2: APL Code Reference
        apl_mentioned = requirement.apl_code.lower() in policy_text
        evidence['apl_mentioned'] = apl_mentioned
        
        # Check 3: Obligation Coverage
        obligation_coverage = []
        for obligation in requirement.key_obligations:
            # Simple keyword matching for now
            key_words = [w for w in obligation.lower().split() 
                        if len(w) > 4 and w not in ['that', 'this', 'with', 'from']]
            if key_words:
                matches = sum(1 for word in key_words if word in policy_text)
                coverage_pct = matches / len(key_words)
                if coverage_pct > 0.5:
                    obligation_coverage.append({
                        'obligation': obligation[:100],
                        'coverage': coverage_pct
                    })
        evidence['obligation_coverage'] = obligation_coverage
        
        # Check 4: Timeframe Matches
        timeframe_matches = []
        for timeframe in requirement.timeframes:
            if timeframe.lower() in policy_text:
                timeframe_matches.append(timeframe)
        evidence['timeframe_matches'] = timeframe_matches
        
        # Check 5: Definition Coverage
        definition_coverage = {}
        for term, definition in requirement.definitions.items():
            if term.lower() in policy_text:
                definition_coverage[term] = "Term found in policy"
        evidence['definition_coverage'] = definition_coverage
        
        # Determine coverage type
        coverage_type = self._determine_coverage_type(
            reg_matches, apl_mentioned, obligation_coverage, 
            timeframe_matches, requirement
        )
        
        # Calculate confidence score
        confidence = self._calculate_confidence(evidence, requirement)
        
        # Identify gaps
        if not reg_matches and requirement.regulation_references:
            gaps.append(f"Missing regulation references: {', '.join(requirement.regulation_references)}")
        if not obligation_coverage and requirement.key_obligations:
            gaps.append("Key obligations not addressed")
        if not timeframe_matches and requirement.timeframes:
            gaps.append(f"Missing timeframes: {', '.join(requirement.timeframes)}")
        
        # Determine if manual review needed
        manual_review_needed = (
            coverage_type in [CoverageType.PARTIAL_COMPLIANCE, CoverageType.REFERENCE_ONLY]
            or (coverage_type == CoverageType.RELATED and confidence > 0.3)
        )
        
        return CoverageAssessment(
            requirement=requirement,
            coverage_type=coverage_type,
            matching_policies=[{
                'policy_code': policy.policy_code,
                'policy_title': policy.title,
                'policy_id': policy.id,
                'match_details': evidence
            }] if coverage_type != CoverageType.NO_COVERAGE else [],
            confidence_score=confidence,
            evidence=evidence,
            gaps=gaps,
            manual_review_needed=manual_review_needed
        )
    
    def _determine_coverage_type(self, reg_matches, apl_mentioned, 
                                 obligation_coverage, timeframe_matches, 
                                 requirement) -> CoverageType:
        """Determine the type of coverage based on evidence"""
        
        # Full compliance: regulations match + obligations covered + timeframes match
        if (reg_matches and len(obligation_coverage) >= len(requirement.key_obligations) * 0.7 
            and (not requirement.timeframes or timeframe_matches)):
            return CoverageType.FULL_COMPLIANCE
        
        # Reference only: mentions regulation/APL but doesn't cover obligations
        if (reg_matches or apl_mentioned) and len(obligation_coverage) < len(requirement.key_obligations) * 0.3:
            return CoverageType.REFERENCE_ONLY
        
        # Partial compliance: some obligations covered
        if len(obligation_coverage) >= len(requirement.key_obligations) * 0.3:
            return CoverageType.PARTIAL_COMPLIANCE
        
        # Related: topically related but no direct coverage
        if len(obligation_coverage) > 0 or timeframe_matches:
            return CoverageType.RELATED
        
        return CoverageType.NO_COVERAGE
    
    def _calculate_confidence(self, evidence: Dict, requirement: RequirementDetail) -> float:
        """Calculate confidence score for the coverage assessment"""
        score = 0.0
        weights = {
            'regulation_matches': 0.3,
            'apl_mentioned': 0.1,
            'obligation_coverage': 0.4,
            'timeframe_matches': 0.1,
            'definition_coverage': 0.1
        }
        
        # Regulation matches
        if requirement.regulation_references:
            reg_score = len(evidence.get('regulation_matches', [])) / len(requirement.regulation_references)
            score += reg_score * weights['regulation_matches']
        
        # APL mention
        if evidence.get('apl_mentioned'):
            score += weights['apl_mentioned']
        
        # Obligation coverage
        if requirement.key_obligations:
            obligation_count = len(evidence.get('obligation_coverage', []))
            obligation_score = obligation_count / len(requirement.key_obligations)
            score += obligation_score * weights['obligation_coverage']
        
        # Timeframe matches
        if requirement.timeframes:
            time_score = len(evidence.get('timeframe_matches', [])) / len(requirement.timeframes)
            score += time_score * weights['timeframe_matches']
        
        # Definition coverage
        if requirement.definitions:
            def_score = len(evidence.get('definition_coverage', {})) / len(requirement.definitions)
            score += def_score * weights['definition_coverage']
        
        return min(score, 1.0)
    
    def analyze_corpus_coverage_v2(self) -> Dict:
        """
        Analyze entire corpus with enhanced coverage detection
        """
        # Get all audit requirements
        audit_reqs = self.db.query(AuditRequirement).all()
        policies = self.db.query(Policy).all()
        
        all_assessments = []
        
        for audit_req in audit_reqs:
            # Extract detailed requirements
            requirements = self.extract_requirement_details(audit_req)
            
            for requirement in requirements:
                best_coverage = None
                all_matches = []
                
                # Check each policy
                for policy in policies:
                    assessment = self.assess_policy_coverage(requirement, policy)
                    
                    if assessment.coverage_type != CoverageType.NO_COVERAGE:
                        all_matches.extend(assessment.matching_policies)
                        
                        # Keep track of best coverage
                        if (not best_coverage or 
                            self._is_better_coverage(assessment.coverage_type, best_coverage.coverage_type)):
                            best_coverage = assessment
                
                # Create final assessment with all matching policies
                if best_coverage:
                    best_coverage.matching_policies = all_matches
                    all_assessments.append(best_coverage)
                else:
                    # No coverage found
                    all_assessments.append(CoverageAssessment(
                        requirement=requirement,
                        coverage_type=CoverageType.NO_COVERAGE,
                        matching_policies=[],
                        confidence_score=0.0,
                        evidence={},
                        gaps=["No matching policies found"],
                        manual_review_needed=True
                    ))
        
        # Compile results
        results = {
            'total_requirements': len(all_assessments),
            'coverage_summary': self._compile_coverage_summary(all_assessments),
            'assessments': all_assessments,
            'by_apl': self._group_by_apl(all_assessments)
        }
        
        return results
    
    def _is_better_coverage(self, new_type: CoverageType, current_type: CoverageType) -> bool:
        """Determine if new coverage is better than current"""
        priority = {
            CoverageType.FULL_COMPLIANCE: 5,
            CoverageType.PARTIAL_COMPLIANCE: 4,
            CoverageType.REFERENCE_ONLY: 3,
            CoverageType.RELATED: 2,
            CoverageType.MANUAL_REVIEW: 1,
            CoverageType.NO_COVERAGE: 0
        }
        return priority.get(new_type, 0) > priority.get(current_type, 0)
    
    def _compile_coverage_summary(self, assessments: List[CoverageAssessment]) -> Dict:
        """Compile summary statistics"""
        summary = {
            'full_compliance': 0,
            'partial_compliance': 0,
            'reference_only': 0,
            'related': 0,
            'no_coverage': 0,
            'manual_review_needed': 0,
            'verified': 0
        }
        
        for assessment in assessments:
            summary[assessment.coverage_type.value] = summary.get(assessment.coverage_type.value, 0) + 1
            if assessment.manual_review_needed:
                summary['manual_review_needed'] += 1
            if assessment.is_verified:
                summary['verified'] += 1
        
        return summary
    
    def _group_by_apl(self, assessments: List[CoverageAssessment]) -> Dict:
        """Group assessments by APL code"""
        by_apl = {}
        
        for assessment in assessments:
            apl = assessment.requirement.apl_code
            if apl not in by_apl:
                by_apl[apl] = {
                    'apl_code': apl,
                    'requirements': [],
                    'summary': {
                        'full_compliance': 0,
                        'partial_compliance': 0,
                        'reference_only': 0,
                        'related': 0,
                        'no_coverage': 0
                    }
                }
            
            by_apl[apl]['requirements'].append(assessment)
            by_apl[apl]['summary'][assessment.coverage_type.value] += 1
        
        return by_apl