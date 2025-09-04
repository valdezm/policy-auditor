"""
Enhanced Policy Analysis Engine with Semantic Context Analysis
Works across all regulations with improved accuracy
"""
import re
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

@dataclass
class ContextualExcerpt:
    """Excerpt with contextual relevance scoring"""
    policy_code: str
    policy_title: str
    text: str
    start_pos: int
    end_pos: int
    context: str
    relevance_score: float  # 0.0 to 1.0
    matched_elements: List[str]
    surrounding_keywords: List[str]

@dataclass
class EnhancedComplianceAnalysis:
    """Enhanced analysis with better context understanding"""
    policy_code: str
    policy_title: str
    requirement_id: str
    compliance_score: float
    is_compliant: bool
    has_primary_reference: bool
    has_cross_references: bool
    missing_elements: List[str]
    found_elements: List[str]
    contextual_excerpts: List[ContextualExcerpt]
    explanation: str
    recommendations: List[str]
    confidence_level: float  # How confident we are in this analysis

class EnhancedPolicyAnalyzer:
    """
    Enhanced policy analyzer with semantic context awareness
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # Enhanced keyword patterns for better context detection
        self.context_patterns = {
            'regulatory_references': [
                r'(\d+\s+CCR\s+[\d\.]+)',  # California Code of Regulations
                r'(WIC\s+section\s+[\d\.]+)',  # Welfare and Institutions Code
                r'(Health\s+and\s+Safety\s+Code\s+[\d\.]+)',
                r'(Government\s+Code\s+[\d\.]+)'
            ],
            'apl_references': [
                r'(APL\s+\d{2}-\d{3})',  # APL XX-XXX format
                r'(All\s+Plan\s+Letter\s+\d{2}-\d{3})',
                r'(DHCS\s+APL\s+\d{2}-\d{3})'
            ],
            'compliance_verbs': [
                r'\b(must|shall|required|mandated|obligated)\b',
                r'\b(adhere|comply|conform|follow)\b',
                r'\b(ensure|verify|confirm|establish)\b'
            ],
            'process_indicators': [
                r'\b(procedure|process|method|approach)\b',
                r'\b(documentation|record|report)\b',
                r'\b(authorization|approval|recommendation)\b'
            ]
        }
        
        # Domain-specific keywords for different topic areas
        self.domain_keywords = {
            'doula_services': [
                'doula', 'birth worker', 'childbirth', 'pregnancy', 'postpartum',
                'prenatal', 'perinatal', 'labor', 'delivery', 'stillbirth',
                'miscarriage', 'abortion'
            ],
            'sanctions': [
                'sanction', 'penalty', 'violation', 'enforcement', 'corrective action',
                'probability sampling', 'harm', 'impact', 'beneficiaries'
            ],
            'quality_improvement': [
                'quality', 'improvement', 'measure', 'metric', 'performance',
                'outcome', 'indicator', 'assessment', 'evaluation'
            ],
            'network_adequacy': [
                'network', 'provider', 'access', 'availability', 'capacity',
                'geographic', 'time', 'distance', 'appointment'
            ]
        }
    
    def analyze_requirement_compliance(self, requirement_id: str) -> List[EnhancedComplianceAnalysis]:
        """
        Enhanced analysis for a specific requirement across all policies
        """
        # Get requirement details with better parsing
        requirement = self._get_requirement_details(requirement_id)
        if not requirement:
            return []
        
        # Extract semantic elements from the requirement
        semantic_elements = self._extract_semantic_elements(requirement)
        
        # Get all policies
        policies = self._get_all_policies()
        
        analyses = []
        for policy in policies:
            analysis = self._analyze_single_policy_enhanced(
                policy, requirement, semantic_elements
            )
            if analysis:
                analyses.append(analysis)
        
        # Sort by compliance score and confidence
        analyses.sort(key=lambda a: (a.compliance_score, a.confidence_level), reverse=True)
        return analyses
    
    def _get_requirement_details(self, requirement_id: str) -> Optional[Dict]:
        """Get requirement details with enhanced metadata"""
        query = text("""
            SELECT 
                ar.apl_code,
                ar.title as apl_title,
                ac.criteria_code,
                ac.criteria_text,
                ac.validation_rule,
                ar.extracted_text as apl_full_text
            FROM audit_criteria ac
            JOIN audit_requirements ar ON ar.id = ac.audit_requirement_id
            WHERE ac.id = :req_id
        """)
        
        result = self.db.execute(query, {"req_id": requirement_id}).fetchone()
        if not result:
            return None
            
        return {
            'apl_code': result.apl_code,
            'apl_title': result.apl_title,
            'criteria_code': result.criteria_code,
            'criteria_text': result.criteria_text,
            'validation_rule': result.validation_rule or "",
            'apl_full_text': result.apl_full_text or ""
        }
    
    def _extract_semantic_elements(self, requirement: Dict) -> Dict:
        """
        Extract semantic elements from requirement text for better matching
        """
        text = requirement['criteria_text']
        elements = {
            'primary_apl': requirement['apl_code'],
            'referenced_apls': [],
            'regulatory_refs': [],
            'key_concepts': [],
            'domain_context': None,
            'required_actions': [],
            'verification_methods': []
        }
        
        # Find referenced APLs (like APL 22-031 in APL 23-024 requirements)
        for pattern in self.context_patterns['apl_references']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                apl_ref = re.sub(r'\s+', ' ', match).strip()
                if apl_ref != elements['primary_apl']:
                    elements['referenced_apls'].append(apl_ref)
        
        # Find regulatory references
        for pattern in self.context_patterns['regulatory_references']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            elements['regulatory_refs'].extend(matches)
        
        # Determine domain context
        text_lower = text.lower()
        for domain, keywords in self.domain_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                elements['domain_context'] = domain
                elements['key_concepts'].extend([kw for kw in keywords if kw in text_lower])
                break
        
        # Extract required actions (what must be done)
        action_patterns = [
            r'must\s+([\w\s]+?)(?:\?|\.|\;)',
            r'shall\s+([\w\s]+?)(?:\?|\.|\;)',
            r'required\s+to\s+([\w\s]+?)(?:\?|\.|\;)'
        ]
        for pattern in action_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            elements['required_actions'].extend([m.strip() for m in matches])
        
        return elements
    
    def _get_all_policies(self) -> List:
        """Get all policies with extracted text"""
        query = text("""
            SELECT 
                policy_code,
                title,
                extracted_text
            FROM policies
            WHERE extracted_text IS NOT NULL AND LENGTH(extracted_text) > 100
        """)
        return self.db.execute(query).fetchall()
    
    def _analyze_single_policy_enhanced(self, policy, requirement: Dict, elements: Dict) -> Optional[EnhancedComplianceAnalysis]:
        """
        Enhanced single policy analysis with semantic understanding
        """
        policy_text = policy.extracted_text.lower()
        
        # Check for primary APL reference
        primary_apl = elements['primary_apl'].lower().replace("apl ", "")
        has_primary_ref = primary_apl in policy_text
        
        # Check for cross-referenced APLs
        cross_refs_found = []
        for ref_apl in elements['referenced_apls']:
            ref_clean = ref_apl.lower().replace("apl ", "")
            if ref_clean in policy_text:
                cross_refs_found.append(ref_apl)
        
        has_cross_refs = len(cross_refs_found) > 0
        
        # Find contextual excerpts with relevance scoring
        contextual_excerpts = self._find_contextual_excerpts(
            policy, elements, requirement['criteria_text']
        )
        
        # Calculate compliance elements
        found_elements, missing_elements = self._assess_compliance_elements(
            policy_text, elements, contextual_excerpts
        )
        
        # Calculate overall compliance score
        compliance_score = self._calculate_compliance_score(
            has_primary_ref, has_cross_refs, found_elements, 
            missing_elements, contextual_excerpts
        )
        
        # Determine if compliant (higher threshold for better accuracy)
        is_compliant = (
            compliance_score >= 0.8 and
            has_primary_ref and
            len(found_elements) > len(missing_elements) and
            any(excerpt.relevance_score > 0.7 for excerpt in contextual_excerpts)
        )
        
        # Generate explanation
        explanation = self._generate_enhanced_explanation(
            policy.policy_code, requirement, elements, 
            has_primary_ref, has_cross_refs, found_elements, 
            missing_elements, contextual_excerpts
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            missing_elements, elements, has_cross_refs
        )
        
        # Calculate confidence level
        confidence = self._calculate_confidence_level(
            contextual_excerpts, found_elements, missing_elements
        )
        
        return EnhancedComplianceAnalysis(
            policy_code=policy.policy_code,
            policy_title=policy.title,
            requirement_id=requirement['criteria_code'],
            compliance_score=compliance_score,
            is_compliant=is_compliant,
            has_primary_reference=has_primary_ref,
            has_cross_references=has_cross_refs,
            missing_elements=missing_elements,
            found_elements=found_elements,
            contextual_excerpts=contextual_excerpts,
            explanation=explanation,
            recommendations=recommendations,
            confidence_level=confidence
        )
    
    def _find_contextual_excerpts(self, policy, elements: Dict, requirement_text: str) -> List[ContextualExcerpt]:
        """
        Find excerpts with high contextual relevance to the requirement
        """
        excerpts = []
        policy_text = policy.extracted_text
        text_lower = policy_text.lower()
        
        # Multi-pass search for different types of matches
        search_strategies = [
            ('domain_specific', self._find_domain_excerpts),
            ('regulatory_refs', self._find_regulatory_excerpts),
            ('cross_apl_refs', self._find_cross_apl_excerpts),
            ('concept_based', self._find_concept_excerpts)
        ]
        
        for strategy_name, strategy_func in search_strategies:
            strategy_excerpts = strategy_func(policy, elements, requirement_text)
            excerpts.extend(strategy_excerpts)
        
        # Remove duplicates and overlaps
        excerpts = self._deduplicate_excerpts(excerpts)
        
        # Sort by relevance score
        excerpts.sort(key=lambda e: e.relevance_score, reverse=True)
        
        # Return top 5 most relevant excerpts
        return excerpts[:5]
    
    def _find_domain_excerpts(self, policy, elements: Dict, requirement_text: str) -> List[ContextualExcerpt]:
        """Find excerpts related to the domain context (e.g., doula services)"""
        excerpts = []
        if not elements['domain_context']:
            return excerpts
            
        domain_keywords = self.domain_keywords.get(elements['domain_context'], [])
        policy_text = policy.extracted_text
        text_lower = policy_text.lower()
        
        # Find sections that mention domain keywords
        for keyword in domain_keywords:
            if keyword in text_lower:
                # Find all occurrences
                start = 0
                while True:
                    pos = text_lower.find(keyword, start)
                    if pos == -1:
                        break
                    
                    # Extract context around the keyword
                    context_start = max(0, pos - 300)
                    context_end = min(len(policy_text), pos + 300)
                    context = policy_text[context_start:context_end]
                    
                    # Score relevance based on co-occurrence of other domain keywords
                    relevance = self._score_domain_relevance(context, domain_keywords)
                    
                    if relevance > 0.3:  # Threshold for relevance
                        excerpt = ContextualExcerpt(
                            policy_code=policy.policy_code,
                            policy_title=policy.title,
                            text=keyword,
                            start_pos=pos,
                            end_pos=pos + len(keyword),
                            context=context,
                            relevance_score=relevance,
                            matched_elements=[keyword],
                            surrounding_keywords=self._find_surrounding_keywords(
                                context, domain_keywords
                            )
                        )
                        excerpts.append(excerpt)
                    
                    start = pos + 1
        
        return excerpts
    
    def _find_regulatory_excerpts(self, policy, elements: Dict, requirement_text: str) -> List[ContextualExcerpt]:
        """Find excerpts that mention specific regulations"""
        excerpts = []
        policy_text = policy.extracted_text
        
        for reg_ref in elements['regulatory_refs']:
            # Create flexible pattern for the regulation
            reg_pattern = re.escape(reg_ref).replace(r'\ ', r'\s+')
            matches = list(re.finditer(reg_pattern, policy_text, re.IGNORECASE))
            
            for match in matches:
                context_start = max(0, match.start() - 200)
                context_end = min(len(policy_text), match.end() + 200)
                context = policy_text[context_start:context_end]
                
                # Higher relevance for regulatory references
                relevance = 0.8
                
                excerpt = ContextualExcerpt(
                    policy_code=policy.policy_code,
                    policy_title=policy.title,
                    text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    context=context,
                    relevance_score=relevance,
                    matched_elements=[reg_ref],
                    surrounding_keywords=[]
                )
                excerpts.append(excerpt)
        
        return excerpts
    
    def _find_cross_apl_excerpts(self, policy, elements: Dict, requirement_text: str) -> List[ContextualExcerpt]:
        """Find excerpts that reference cross-referenced APLs"""
        excerpts = []
        policy_text = policy.extracted_text
        
        for apl_ref in elements['referenced_apls']:
            # Look for this APL reference in the policy
            apl_clean = apl_ref.lower().replace("apl ", "")
            
            # Try different patterns
            patterns = [
                rf'\bAPL\s+{re.escape(apl_clean)}\b',
                rf'\b{re.escape(apl_ref)}\b',
                rf'All\s+Plan\s+Letter\s+{re.escape(apl_clean)}\b'
            ]
            
            for pattern in patterns:
                matches = list(re.finditer(pattern, policy_text, re.IGNORECASE))
                
                for match in matches:
                    context_start = max(0, match.start() - 250)
                    context_end = min(len(policy_text), match.end() + 250)
                    context = policy_text[context_start:context_end]
                    
                    # High relevance for cross-APL references
                    relevance = 0.9
                    
                    excerpt = ContextualExcerpt(
                        policy_code=policy.policy_code,
                        policy_title=policy.title,
                        text=match.group(0),
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=context,
                        relevance_score=relevance,
                        matched_elements=[apl_ref],
                        surrounding_keywords=[]
                    )
                    excerpts.append(excerpt)
        
        return excerpts
    
    def _find_concept_excerpts(self, policy, elements: Dict, requirement_text: str) -> List[ContextualExcerpt]:
        """Find excerpts for key concepts from the requirement"""
        excerpts = []
        policy_text = policy.extracted_text
        text_lower = policy_text.lower()
        
        for concept in elements['key_concepts']:
            if concept in text_lower:
                # Find all occurrences
                start = 0
                while True:
                    pos = text_lower.find(concept, start)
                    if pos == -1:
                        break
                    
                    context_start = max(0, pos - 200)
                    context_end = min(len(policy_text), pos + 200)
                    context = policy_text[context_start:context_end]
                    
                    # Score based on context
                    relevance = 0.5  # Base score for concept match
                    
                    excerpt = ContextualExcerpt(
                        policy_code=policy.policy_code,
                        policy_title=policy.title,
                        text=concept,
                        start_pos=pos,
                        end_pos=pos + len(concept),
                        context=context,
                        relevance_score=relevance,
                        matched_elements=[concept],
                        surrounding_keywords=[]
                    )
                    excerpts.append(excerpt)
                    
                    start = pos + 1
        
        return excerpts
    
    def _score_domain_relevance(self, context: str, domain_keywords: List[str]) -> float:
        """Score how relevant a context is to the domain"""
        context_lower = context.lower()
        matches = sum(1 for keyword in domain_keywords if keyword in context_lower)
        return min(1.0, matches / len(domain_keywords))
    
    def _find_surrounding_keywords(self, context: str, keywords: List[str]) -> List[str]:
        """Find domain keywords in the surrounding context"""
        context_lower = context.lower()
        return [kw for kw in keywords if kw in context_lower]
    
    def _deduplicate_excerpts(self, excerpts: List[ContextualExcerpt]) -> List[ContextualExcerpt]:
        """Remove overlapping excerpts"""
        if not excerpts:
            return []
        
        excerpts.sort(key=lambda e: (e.start_pos, -e.relevance_score))
        
        deduplicated = [excerpts[0]]
        for excerpt in excerpts[1:]:
            # Check if this excerpt overlaps significantly with any existing excerpt
            overlaps = False
            for existing in deduplicated:
                if (excerpt.start_pos < existing.end_pos and 
                    excerpt.end_pos > existing.start_pos):
                    # Overlaps - keep the one with higher relevance
                    if excerpt.relevance_score > existing.relevance_score:
                        deduplicated.remove(existing)
                        deduplicated.append(excerpt)
                    overlaps = True
                    break
            
            if not overlaps:
                deduplicated.append(excerpt)
        
        return deduplicated
    
    def _assess_compliance_elements(self, policy_text: str, elements: Dict, 
                                   excerpts: List[ContextualExcerpt]) -> Tuple[List[str], List[str]]:
        """Assess which compliance elements are found vs missing"""
        found = []
        missing = []
        
        # Check regulatory references
        for reg_ref in elements['regulatory_refs']:
            if any(reg_ref.lower() in policy_text for excerpt in excerpts):
                found.append(f"Regulation {reg_ref} - Referenced")
            else:
                missing.append(f"Reference to {reg_ref}")
        
        # Check cross-APL references
        for apl_ref in elements['referenced_apls']:
            apl_clean = apl_ref.lower().replace("apl ", "")
            if apl_clean in policy_text:
                found.append(f"{apl_ref} - Referenced")
            else:
                missing.append(f"Reference to {apl_ref}")
        
        # Check domain concepts
        if elements['domain_context']:
            domain_keywords = self.domain_keywords.get(elements['domain_context'], [])
            found_concepts = [kw for kw in domain_keywords if kw in policy_text]
            if found_concepts:
                found.append(f"Domain concepts: {', '.join(found_concepts[:3])}")
            else:
                missing.append(f"Domain-specific content for {elements['domain_context']}")
        
        return found, missing
    
    def _calculate_compliance_score(self, has_primary_ref: bool, has_cross_refs: bool,
                                   found_elements: List[str], missing_elements: List[str],
                                   excerpts: List[ContextualExcerpt]) -> float:
        """Calculate comprehensive compliance score"""
        score = 0.0
        
        # Primary APL reference (30%)
        if has_primary_ref:
            score += 0.3
        
        # Cross-references (20%)
        if has_cross_refs:
            score += 0.2
        
        # Found vs missing elements (30%)
        total_elements = len(found_elements) + len(missing_elements)
        if total_elements > 0:
            element_ratio = len(found_elements) / total_elements
            score += 0.3 * element_ratio
        
        # Quality of excerpts (20%)
        if excerpts:
            avg_relevance = sum(e.relevance_score for e in excerpts) / len(excerpts)
            score += 0.2 * avg_relevance
        
        return min(1.0, score)
    
    def _calculate_confidence_level(self, excerpts: List[ContextualExcerpt], 
                                   found_elements: List[str], missing_elements: List[str]) -> float:
        """Calculate confidence in the analysis"""
        confidence = 0.5  # Base confidence
        
        # High-relevance excerpts increase confidence
        if excerpts:
            high_relevance_excerpts = [e for e in excerpts if e.relevance_score > 0.7]
            confidence += 0.3 * (len(high_relevance_excerpts) / len(excerpts))
        
        # Clear found elements increase confidence
        if found_elements:
            confidence += 0.2
        
        # Many missing elements decrease confidence
        if missing_elements and len(missing_elements) > len(found_elements):
            confidence -= 0.1
        
        return max(0.1, min(1.0, confidence))
    
    def _generate_enhanced_explanation(self, policy_code: str, requirement: Dict, 
                                      elements: Dict, has_primary_ref: bool,
                                      has_cross_refs: bool, found_elements: List[str],
                                      missing_elements: List[str], 
                                      excerpts: List[ContextualExcerpt]) -> str:
        """Generate detailed explanation of the analysis"""
        explanation = f"Analysis of {policy_code}: {requirement['apl_title']}\n"
        explanation += f"Against {requirement['apl_code']} requirements:\n\n"
        
        if has_primary_ref:
            explanation += f"✓ References {requirement['apl_code']}\n\n"
        else:
            explanation += f"✗ Does NOT reference {requirement['apl_code']}\n\n"
        
        if found_elements:
            explanation += "Found elements:\n"
            for element in found_elements:
                explanation += f"  ✓ {element}\n"
            explanation += "\n"
        
        if missing_elements:
            explanation += "Missing elements:\n"
            for element in missing_elements:
                explanation += f"  ✗ {element}\n"
            explanation += "\n"
        
        if excerpts:
            explanation += "Relevant excerpts:\n\n"
            for excerpt in excerpts[:3]:  # Top 3 excerpts
                explanation += f"  From {policy_code}:\n"
                explanation += f'  "...{excerpt.context}..."\n\n'
        
        # Overall assessment
        if has_primary_ref and has_cross_refs and len(found_elements) > len(missing_elements):
            explanation += "Overall Assessment:\nThis policy appears to fully address the requirements."
        elif has_primary_ref and found_elements:
            explanation += "Overall Assessment:\nThis policy partially addresses the requirements but has some gaps."
        else:
            explanation += "Overall Assessment:\nThis policy does not adequately address the requirements."
        
        return explanation
    
    def _generate_recommendations(self, missing_elements: List[str], 
                                 elements: Dict, has_cross_refs: bool) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if missing_elements:
            recommendations.append(f"Add explicit references to: {', '.join(missing_elements)}")
        
        if elements['referenced_apls'] and not has_cross_refs:
            apl_list = ', '.join(elements['referenced_apls'])
            recommendations.append(f"Include references to related APLs: {apl_list}")
        
        if elements['domain_context']:
            recommendations.append(f"Ensure policy addresses {elements['domain_context']} specific requirements")
        
        if not recommendations:
            recommendations.append("Policy appears complete for this requirement")
        
        return recommendations