"""
Simplified Compliance Engine for Policy Auditing
Prototype version with basic keyword matching
"""
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"


@dataclass
class RequirementCheck:
    """Represents a single requirement from an RT APL"""
    requirement_id: str
    question_text: str
    apl_reference: str
    expected_keywords: List[str] = field(default_factory=list)
    critical_values: Dict = field(default_factory=dict)  # e.g., {"days": 30}
    section_hints: List[str] = field(default_factory=list)
    
    
@dataclass
class ValidationResult:
    """Result of validating a requirement against a policy"""
    requirement_id: str
    status: ComplianceStatus
    confidence: float
    findings: List[Dict] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)


class SimpleComplianceEngine:
    """
    Prototype compliance engine using keyword matching
    This is the simplest baseline implementation
    """
    
    def __init__(self):
        self.relevance_keywords = self._load_relevance_keywords()
        
    def _load_relevance_keywords(self) -> Dict:
        """Load keyword mappings for relevance detection"""
        return {
            'network': ['network', 'provider', 'access', 'adequacy', 'certification'],
            'grievance': ['grievance', 'appeal', 'complaint', 'dispute'],
            'mental_health': ['mental health', 'behavioral', 'psychiatric'],
            'emergency': ['emergency', 'urgent', 'crisis'],
            'quality': ['quality', 'performance', 'metrics', 'monitoring'],
            'enrollment': ['enrollment', 'eligibility', 'member'],
            'pharmacy': ['pharmacy', 'drug', 'medication', 'formulary'],
            'authorization': ['authorization', 'prior auth', 'approval'],
        }
    
    def check_relevance(self, policy_text: str, rt_apl_text: str) -> Tuple[bool, float]:
        """
        Simple relevance check based on keyword overlap
        Returns (is_relevant, confidence_score)
        """
        policy_lower = policy_text.lower()
        rt_lower = rt_apl_text.lower()
        
        # Extract topics from both documents
        policy_topics = set()
        rt_topics = set()
        
        for topic, keywords in self.relevance_keywords.items():
            # Check policy
            if any(kw in policy_lower for kw in keywords):
                policy_topics.add(topic)
            # Check RT APL
            if any(kw in rt_lower for kw in keywords):
                rt_topics.add(topic)
        
        # Calculate overlap
        if not rt_topics:
            return True, 0.5  # If no specific topic found, assume potentially relevant
        
        overlap = policy_topics & rt_topics
        if overlap:
            confidence = len(overlap) / len(rt_topics)
            return True, confidence
        
        return False, 0.0
    
    def validate_requirement(self, 
                            policy_text: str, 
                            requirement: RequirementCheck) -> ValidationResult:
        """
        Validate a single requirement against policy text
        Simple keyword-based approach for prototype
        """
        result = ValidationResult(
            requirement_id=requirement.requirement_id,
            status=ComplianceStatus.PENDING,
            confidence=0.0
        )
        
        policy_lower = policy_text.lower()
        
        # Step 1: Find relevant sections
        relevant_sections = self._find_relevant_sections(
            policy_text, 
            requirement.section_hints
        )
        
        if relevant_sections:
            result.citations = [f"Section found at position {pos}" 
                              for pos in relevant_sections]
        
        # Step 2: Check for expected keywords
        found_keywords = []
        missing_keywords = []
        
        for keyword in requirement.expected_keywords:
            if keyword.lower() in policy_lower:
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        # Step 3: Check critical values (e.g., timeframes)
        value_checks = self._check_critical_values(
            policy_text, 
            requirement.critical_values
        )
        
        # Step 4: Determine compliance status
        keyword_coverage = len(found_keywords) / len(requirement.expected_keywords) if requirement.expected_keywords else 1.0
        
        if keyword_coverage >= 0.8 and all(value_checks.values()):
            result.status = ComplianceStatus.COMPLIANT
            result.confidence = keyword_coverage
        elif keyword_coverage >= 0.5:
            result.status = ComplianceStatus.PARTIAL
            result.confidence = keyword_coverage
            result.gaps = missing_keywords
        else:
            result.status = ComplianceStatus.NON_COMPLIANT
            result.confidence = 1.0 - keyword_coverage
            result.gaps = missing_keywords
        
        # Add findings
        result.findings.append({
            'keywords_found': found_keywords,
            'keywords_missing': missing_keywords,
            'value_checks': value_checks
        })
        
        return result
    
    def _find_relevant_sections(self, text: str, section_hints: List[str]) -> List[int]:
        """Find sections in text that might be relevant"""
        positions = []
        text_lower = text.lower()
        
        for hint in section_hints:
            pos = text_lower.find(hint.lower())
            if pos != -1:
                positions.append(pos)
        
        return positions
    
    def _check_critical_values(self, text: str, critical_values: Dict) -> Dict[str, bool]:
        """Check if critical values (like timeframes) are present and correct"""
        results = {}
        
        for value_type, expected_value in critical_values.items():
            if value_type == 'days':
                # Look for day values
                pattern = r'(\d+)\s*(calendar\s*)?days?'
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                found_correct = False
                for match in matches:
                    if int(match[0]) == expected_value:
                        found_correct = True
                        break
                
                results[f'{value_type}_{expected_value}'] = found_correct
            
            elif value_type == 'percentage':
                # Look for percentage values
                pattern = r'(\d+)\s*%'
                matches = re.findall(pattern, text)
                
                found_correct = False
                for match in matches:
                    if int(match) == expected_value:
                        found_correct = True
                        break
                
                results[f'{value_type}_{expected_value}'] = found_correct
        
        return results


class ComplianceValidator:
    """
    Main validator that orchestrates the compliance checking process
    """
    
    def __init__(self):
        self.engine = SimpleComplianceEngine()
        self.results = []
    
    def validate_policy_against_rt(self, 
                                   policy_data: Dict,
                                   rt_apl_data: Dict) -> Dict:
        """
        Validate a policy against a review tool
        """
        # Check relevance first
        is_relevant, relevance_score = self.engine.check_relevance(
            policy_data.get('extracted_text', ''),
            rt_apl_data.get('extracted_text', '')
        )
        
        if not is_relevant:
            return {
                'policy': policy_data.get('policy_code', 'Unknown'),
                'rt_apl': rt_apl_data.get('apl_code', 'Unknown'),
                'status': ComplianceStatus.NOT_APPLICABLE.value,
                'relevance_score': relevance_score,
                'validations': []
            }
        
        # Process each requirement in the RT APL
        validations = []
        requirements = rt_apl_data.get('requirements', [])
        
        for req in requirements:
            requirement = RequirementCheck(
                requirement_id=req.get('id'),
                question_text=req.get('question'),
                apl_reference=req.get('reference'),
                expected_keywords=req.get('keywords', []),
                critical_values=req.get('values', {}),
                section_hints=req.get('hints', [])
            )
            
            result = self.engine.validate_requirement(
                policy_data.get('extracted_text', ''),
                requirement
            )
            
            validations.append({
                'requirement_id': result.requirement_id,
                'status': result.status.value,
                'confidence': result.confidence,
                'gaps': result.gaps,
                'citations': result.citations,
                'findings': result.findings
            })
        
        # Calculate overall compliance
        compliant_count = sum(1 for v in validations 
                             if v['status'] == ComplianceStatus.COMPLIANT.value)
        total_count = len(validations)
        
        overall_status = ComplianceStatus.COMPLIANT
        if total_count > 0:
            compliance_rate = compliant_count / total_count
            if compliance_rate >= 0.95:
                overall_status = ComplianceStatus.COMPLIANT
            elif compliance_rate >= 0.7:
                overall_status = ComplianceStatus.PARTIAL
            else:
                overall_status = ComplianceStatus.NON_COMPLIANT
        
        return {
            'policy': policy_data.get('policy_code', 'Unknown'),
            'rt_apl': rt_apl_data.get('apl_code', 'Unknown'),
            'status': overall_status.value,
            'relevance_score': relevance_score,
            'compliance_rate': compliant_count / total_count if total_count > 0 else 0,
            'validations': validations,
            'summary': {
                'total_requirements': total_count,
                'compliant': compliant_count,
                'non_compliant': total_count - compliant_count
            }
        }
    
    def generate_report(self, validation_results: List[Dict]) -> str:
        """Generate a simple text report of validation results"""
        report_lines = [
            "=" * 80,
            "POLICY COMPLIANCE VALIDATION REPORT",
            f"Generated: {datetime.now().isoformat()}",
            "=" * 80,
            ""
        ]
        
        # Summary statistics
        total = len(validation_results)
        compliant = sum(1 for r in validation_results 
                       if r['status'] == ComplianceStatus.COMPLIANT.value)
        non_compliant = sum(1 for r in validation_results 
                           if r['status'] == ComplianceStatus.NON_COMPLIANT.value)
        not_applicable = sum(1 for r in validation_results 
                            if r['status'] == ComplianceStatus.NOT_APPLICABLE.value)
        
        report_lines.extend([
            "SUMMARY",
            "-" * 40,
            f"Total Validations: {total}",
            f"Compliant: {compliant}",
            f"Non-Compliant: {non_compliant}",
            f"Not Applicable: {not_applicable}",
            ""
        ])
        
        # Detailed results
        report_lines.extend([
            "DETAILED RESULTS",
            "-" * 40,
            ""
        ])
        
        for result in validation_results:
            if result['status'] == ComplianceStatus.NOT_APPLICABLE.value:
                continue
                
            report_lines.extend([
                f"Policy: {result['policy']} vs RT APL: {result['rt_apl']}",
                f"Status: {result['status']}",
                f"Compliance Rate: {result.get('compliance_rate', 0):.1%}",
                f"Relevance Score: {result.get('relevance_score', 0):.1%}",
                ""
            ])
            
            # Show non-compliant requirements
            for validation in result.get('validations', []):
                if validation['status'] != ComplianceStatus.COMPLIANT.value:
                    report_lines.extend([
                        f"  ❌ Requirement {validation['requirement_id']}: {validation['status']}",
                        f"     Confidence: {validation['confidence']:.1%}"
                    ])
                    if validation.get('gaps'):
                        report_lines.append(f"     Missing: {', '.join(validation['gaps'])}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)