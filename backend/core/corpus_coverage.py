"""
Corpus Coverage Analyzer
Simplified approach: Check if the entire corpus of policies covers all RT APL requirements
"""
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session

from ..models.models import Policy, AuditRequirement, AuditCriteria

logger = logging.getLogger(__name__)


class CoverageStatus(Enum):
    COVERED = "covered"           # At least one policy fully covers this
    PARTIAL = "partial"           # Some policies partially cover this
    UNCOVERED = "uncovered"       # No policy covers this requirement
    UNKNOWN = "unknown"           # Not yet analyzed


@dataclass
class RequirementCoverage:
    """Coverage status for a single RT APL requirement"""
    requirement_id: str
    apl_code: str
    requirement_text: str
    status: CoverageStatus
    covering_policies: List[str]  # Policy codes that cover this
    confidence: float
    gaps: List[str]


class CorpusCoverageAnalyzer:
    """
    Analyzes whether the corpus of policies covers all RT APL requirements
    Simple keyword-based approach for MVP
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_corpus_coverage(self) -> Dict:
        """
        Main analysis: Check if corpus covers all requirements
        """
        # Get all policies and requirements from DB
        policies = self.db.query(Policy).all()
        requirements = self.db.query(AuditRequirement).all()
        
        logger.info(f"Analyzing coverage for {len(policies)} policies against {len(requirements)} RT APLs")
        
        results = {
            'total_requirements': 0,
            'covered': 0,
            'partial': 0,
            'uncovered': 0,
            'coverage_details': []
        }
        
        # For each requirement, find which policies cover it
        for requirement in requirements:
            criteria = self.db.query(AuditCriteria).filter(
                AuditCriteria.audit_requirement_id == requirement.id
            ).all()
            
            for criterion in criteria:
                coverage = self._check_requirement_coverage(
                    criterion,
                    policies,
                    requirement.apl_code
                )
                results['coverage_details'].append(coverage)
                results['total_requirements'] += 1
                
                # Update counters
                if coverage.status == CoverageStatus.COVERED:
                    results['covered'] += 1
                elif coverage.status == CoverageStatus.PARTIAL:
                    results['partial'] += 1
                else:
                    results['uncovered'] += 1
        
        # Calculate overall coverage percentage
        if results['total_requirements'] > 0:
            results['coverage_percentage'] = (
                (results['covered'] + results['partial'] * 0.5) / 
                results['total_requirements'] * 100
            )
        else:
            results['coverage_percentage'] = 0
        
        return results
    
    def _check_requirement_coverage(self, 
                                   criterion: AuditCriteria,
                                   policies: List[Policy],
                                   apl_code: str) -> RequirementCoverage:
        """
        Check if any policy in the corpus covers this requirement
        """
        coverage = RequirementCoverage(
            requirement_id=criterion.criteria_code or str(criterion.id),
            apl_code=apl_code,
            requirement_text=criterion.criteria_text[:200],
            status=CoverageStatus.UNCOVERED,
            covering_policies=[],
            confidence=0.0,
            gaps=[]
        )
        
        # Simple keyword matching for MVP
        requirement_keywords = self._extract_keywords(criterion.criteria_text)
        
        best_match_score = 0
        
        for policy in policies:
            if not policy.extracted_text:
                continue
                
            # Check for keyword matches
            match_score = self._calculate_match_score(
                requirement_keywords,
                policy.extracted_text
            )
            
            if match_score > 0.7:  # Good match
                coverage.covering_policies.append(policy.policy_code)
                coverage.status = CoverageStatus.COVERED
                best_match_score = max(best_match_score, match_score)
            elif match_score > 0.4:  # Partial match
                coverage.covering_policies.append(f"{policy.policy_code} (partial)")
                if coverage.status != CoverageStatus.COVERED:
                    coverage.status = CoverageStatus.PARTIAL
                best_match_score = max(best_match_score, match_score)
        
        coverage.confidence = best_match_score
        
        # Identify gaps
        if coverage.status != CoverageStatus.COVERED:
            missing_keywords = [kw for kw in requirement_keywords 
                              if not self._keyword_in_any_policy(kw, policies)]
            if missing_keywords:
                coverage.gaps = [f"Missing: {', '.join(missing_keywords[:3])}"]
        
        return coverage
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from requirement text"""
        # Simple approach - extract key phrases
        keywords = []
        
        important_phrases = [
            '30 calendar days', '30 days', 'timely access',
            'network certification', 'annual', 'grievance',
            'appeal', 'prior authorization', 'emergency',
            'mental health', 'complete and accurate'
        ]
        
        text_lower = text.lower()
        for phrase in important_phrases:
            if phrase in text_lower:
                keywords.append(phrase)
        
        # Also extract any numbers (timeframes, percentages)
        import re
        numbers = re.findall(r'\d+\s*(?:days?|hours?|%)', text_lower)
        keywords.extend(numbers)
        
        return keywords if keywords else [text[:50].lower()]  # Fallback to first 50 chars
    
    def _calculate_match_score(self, keywords: List[str], text: str) -> float:
        """Calculate how well text matches keywords"""
        if not keywords:
            return 0.0
            
        text_lower = text.lower()
        matches = sum(1 for kw in keywords if kw in text_lower)
        
        return matches / len(keywords)
    
    def _keyword_in_any_policy(self, keyword: str, policies: List[Policy]) -> bool:
        """Check if keyword appears in any policy"""
        for policy in policies:
            if policy.extracted_text and keyword.lower() in policy.extracted_text.lower():
                return True
        return False
    
    def get_coverage_summary(self) -> Dict:
        """Get a simplified summary for the UI"""
        results = self.analyze_corpus_coverage()
        
        # Group by RT APL
        by_rt_apl = {}
        for detail in results['coverage_details']:
            apl = detail.apl_code
            if apl not in by_rt_apl:
                by_rt_apl[apl] = {
                    'apl_code': apl,
                    'total': 0,
                    'covered': 0,
                    'partial': 0,
                    'uncovered': 0,
                    'requirements': []
                }
            
            by_rt_apl[apl]['total'] += 1
            by_rt_apl[apl]['requirements'].append({
                'id': detail.requirement_id,
                'text': detail.requirement_text,
                'status': detail.status.value,
                'policies': detail.covering_policies,
                'confidence': detail.confidence
            })
            
            if detail.status == CoverageStatus.COVERED:
                by_rt_apl[apl]['covered'] += 1
            elif detail.status == CoverageStatus.PARTIAL:
                by_rt_apl[apl]['partial'] += 1
            else:
                by_rt_apl[apl]['uncovered'] += 1
        
        return {
            'overall_coverage': results['coverage_percentage'],
            'total_requirements': results['total_requirements'],
            'covered': results['covered'],
            'partial': results['partial'],
            'uncovered': results['uncovered'],
            'by_rt_apl': list(by_rt_apl.values())
        }