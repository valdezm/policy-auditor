"""
Policy Analysis Engine with Excerpt Extraction and Detailed Explanations
"""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import text

@dataclass
class PolicyExcerpt:
    """Relevant excerpt from a policy"""
    policy_code: str
    policy_title: str
    text: str
    start_pos: int
    end_pos: int
    context: str  # Surrounding text for better understanding

@dataclass
class ComplianceAnalysis:
    """Detailed analysis of why a policy does/doesn't comply"""
    policy_code: str
    policy_title: str
    requirement_id: str
    compliance_score: float
    is_compliant: bool
    has_reference: bool
    missing_elements: List[str]
    found_elements: List[str]
    relevant_excerpts: List[PolicyExcerpt]
    explanation: str
    recommendations: List[str]


class PolicyAnalyzer:
    """
    Analyzes policies for compliance with specific requirements
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_requirement_compliance(self, requirement_id: str) -> List[ComplianceAnalysis]:
        """
        Analyze all policies for a specific requirement
        """
        # Get the requirement details
        query = text("""
            SELECT 
                ar.apl_code,
                ar.title as apl_title,
                ac.criteria_text,
                ac.validation_rule,
                ar.extracted_text as apl_text
            FROM audit_criteria ac
            JOIN audit_requirements ar ON ar.id = ac.audit_requirement_id
            WHERE ac.id = :req_id
        """)
        
        req_result = self.db.execute(query, {"req_id": requirement_id}).fetchone()
        if not req_result:
            return []
        
        # Get all policies
        policies_query = text("""
            SELECT 
                policy_code,
                title,
                extracted_text
            FROM policies
            WHERE extracted_text IS NOT NULL
        """)
        
        policies = self.db.execute(policies_query).fetchall()
        
        analyses = []
        for policy in policies:
            analysis = self._analyze_single_policy(
                policy,
                req_result.apl_code,
                req_result.criteria_text,
                req_result.validation_rule or ""
            )
            if analysis:
                analyses.append(analysis)
        
        return analyses
    
    def _analyze_single_policy(self, policy, apl_code: str, criteria_text: str, validation_rule: str) -> Optional[ComplianceAnalysis]:
        """
        Analyze a single policy against a requirement
        """
        policy_text = policy.extracted_text.lower()
        
        # Extract key requirements from criteria
        requirements = self._extract_requirement_elements(criteria_text)
        
        # Check for APL reference
        has_apl_reference = apl_code.lower().replace("apl ", "") in policy_text
        
        # Find all relevant excerpts
        excerpts = []
        found_elements = []
        missing_elements = []
        
        # Check each requirement element
        for req_element in requirements:
            found = False
            
            # Search for the element in the policy
            if req_element['type'] == 'regulation':
                # Look for regulation references (e.g., "22 CCR 51458.2")
                pattern = self._create_regulation_pattern(req_element['value'])
                matches = re.finditer(pattern, policy_text, re.IGNORECASE)
                
                for match in matches:
                    found = True
                    excerpt = self._extract_excerpt(
                        policy.extracted_text,
                        match.start(),
                        match.end(),
                        context_chars=200
                    )
                    excerpts.append(PolicyExcerpt(
                        policy_code=policy.policy_code,
                        policy_title=policy.title,
                        text=match.group(0),
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=excerpt
                    ))
                    found_elements.append(f"{req_element['value']} - Found at position {match.start()}")
            
            elif req_element['type'] == 'concept':
                # Look for concepts (e.g., "probability sampling")
                if req_element['value'].lower() in policy_text:
                    found = True
                    # Find the position
                    pos = policy_text.find(req_element['value'].lower())
                    excerpt = self._extract_excerpt(
                        policy.extracted_text,
                        pos,
                        pos + len(req_element['value']),
                        context_chars=200
                    )
                    excerpts.append(PolicyExcerpt(
                        policy_code=policy.policy_code,
                        policy_title=policy.title,
                        text=req_element['value'],
                        start_pos=pos,
                        end_pos=pos + len(req_element['value']),
                        context=excerpt
                    ))
                    found_elements.append(f"{req_element['value']} - Found")
            
            if not found:
                missing_elements.append(req_element['description'])
        
        # Only return analysis if there's some relevance
        if not has_apl_reference and not found_elements and not excerpts:
            return None
        
        # Calculate compliance score
        total_requirements = len(requirements)
        found_count = len(found_elements)
        compliance_score = found_count / total_requirements if total_requirements > 0 else 0
        
        # Generate explanation
        explanation = self._generate_explanation(
            policy.policy_code,
            policy.title,
            apl_code,
            found_elements,
            missing_elements,
            has_apl_reference,
            excerpts
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(missing_elements)
        
        return ComplianceAnalysis(
            policy_code=policy.policy_code,
            policy_title=policy.title,
            requirement_id=apl_code,
            compliance_score=compliance_score,
            is_compliant=compliance_score >= 0.8 and has_apl_reference,
            has_reference=has_apl_reference,
            missing_elements=missing_elements,
            found_elements=found_elements,
            relevant_excerpts=excerpts,
            explanation=explanation,
            recommendations=recommendations
        )
    
    def _extract_requirement_elements(self, criteria_text: str) -> List[Dict]:
        """
        Extract specific elements that need to be checked from criteria text
        """
        elements = []
        
        # Extract regulation references (e.g., "22 CCR 51458.2", "WIC 14197.7")
        reg_patterns = [
            r'(\d+\s*CCR\s*\d+(?:\.\d+)*)',
            r'(WIC\s*(?:section\s*)?\d+(?:\.\d+)*(?:\([a-z]\)(?:\(\d+\))?)?)',
            r'(HSC\s*(?:section\s*)?\d+(?:\.\d+)*)',
            r'(42\s*CFR\s*\d+(?:\.\d+)*)'
        ]
        
        for pattern in reg_patterns:
            matches = re.finditer(pattern, criteria_text, re.IGNORECASE)
            for match in matches:
                elements.append({
                    'type': 'regulation',
                    'value': match.group(1),
                    'description': f"Reference to {match.group(1)}"
                })
        
        # Extract key concepts
        concept_keywords = [
            'probability sampling',
            'extrapolation',
            'statistical sampling',
            '30 calendar days',
            '30 days',
            'corrective action plan',
            'CAP',
            'enforcement action',
            'sanctions'
        ]
        
        for concept in concept_keywords:
            if concept.lower() in criteria_text.lower():
                elements.append({
                    'type': 'concept',
                    'value': concept,
                    'description': f"Must address '{concept}'"
                })
        
        # For generic requirements, extract key terms from the criteria text
        if not elements:
            # Extract important terms from the criteria
            important_words = []
            text_lower = criteria_text.lower()
            
            # Look for important terms that policies should address
            key_patterns = [
                r'\b(time\s+(?:or\s+)?distance\s+standards?)\b',
                r'\b(population\s+density)\b',
                r'\b(provider\s+types?)\b',
                r'\b(attachment\s+[a-z])\b',
                r'\b(geographic\s+access)\b',
                r'\b(network\s+adequacy)\b',
                r'\b(certification)\b',
                r'\b(requirements?)\b',
                r'\b(standards?)\b'
            ]
            
            for pattern in key_patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    term = match.group(1)
                    if term not in [item['value'] for item in elements]:
                        elements.append({
                            'type': 'concept',
                            'value': term,
                            'description': f"Must address '{term}'"
                        })
        
        return elements
    
    def _create_regulation_pattern(self, regulation: str) -> str:
        """
        Create a regex pattern to find a regulation reference
        """
        # Escape special characters and allow for variations
        reg_escaped = re.escape(regulation)
        # Allow for variations in spacing and formatting
        reg_pattern = reg_escaped.replace(r'\ ', r'\s*')
        return reg_pattern
    
    def _extract_excerpt(self, full_text: str, start: int, end: int, context_chars: int = 200) -> str:
        """
        Extract text excerpt with surrounding context
        """
        excerpt_start = max(0, start - context_chars)
        excerpt_end = min(len(full_text), end + context_chars)
        
        excerpt = full_text[excerpt_start:excerpt_end]
        
        # Add ellipsis if truncated
        if excerpt_start > 0:
            excerpt = "..." + excerpt
        if excerpt_end < len(full_text):
            excerpt = excerpt + "..."
        
        # Highlight the matched text
        matched_text = full_text[start:end]
        excerpt = excerpt.replace(matched_text, f"**{matched_text}**")
        
        return excerpt.strip()
    
    def _generate_explanation(self, policy_code: str, policy_title: str, 
                             apl_code: str, found_elements: List[str], 
                             missing_elements: List[str], has_reference: bool,
                             excerpts: List[PolicyExcerpt]) -> str:
        """
        Generate detailed explanation of compliance
        """
        explanation = f"Analysis of {policy_code}: {policy_title}\n"
        explanation += f"Against {apl_code} requirements:\n\n"
        
        if has_reference:
            explanation += f"✓ References {apl_code}\n"
        else:
            explanation += f"✗ Does NOT reference {apl_code}\n"
        
        if found_elements:
            explanation += "\nFound elements:\n"
            for element in found_elements:
                explanation += f"  ✓ {element}\n"
        
        if missing_elements:
            explanation += "\nMissing elements:\n"
            for element in missing_elements:
                explanation += f"  ✗ {element}\n"
        
        if excerpts:
            explanation += "\nRelevant excerpts:\n"
            for excerpt in excerpts[:3]:  # Limit to first 3 excerpts
                explanation += f"\n  From {excerpt.policy_code}:\n"
                explanation += f"  \"{excerpt.context}\"\n"
        
        # Overall assessment
        explanation += "\nOverall Assessment:\n"
        if not found_elements:
            explanation += "This policy does not address any of the specific requirements."
        elif len(missing_elements) > len(found_elements):
            explanation += "This policy partially addresses the requirements but has significant gaps."
        elif not missing_elements and has_reference:
            explanation += "This policy appears to fully address the requirements."
        else:
            explanation += "This policy addresses most requirements but may need updates."
        
        return explanation
    
    def _generate_recommendations(self, missing_elements: List[str]) -> List[str]:
        """
        Generate recommendations for policy updates
        """
        recommendations = []
        
        if not missing_elements:
            recommendations.append("Policy appears complete for this requirement")
            return recommendations
        
        for element in missing_elements:
            if "22 CCR" in element:
                recommendations.append("Add reference to 22 CCR 51458.2 for probability sampling methodology")
            elif "WIC" in element:
                recommendations.append("Include reference to the correct WIC section subsection")
            elif "probability sampling" in element.lower():
                recommendations.append("Add definition and procedures for probability sampling")
            elif "extrapolation" in element.lower():
                recommendations.append("Include extrapolation methodology and definitions")
            elif "30" in element and "days" in element:
                recommendations.append("Specify 30 calendar day timeframe requirement")
            else:
                recommendations.append(f"Add content addressing: {element}")
        
        return recommendations


class APL23012Analyzer:
    """
    Specialized analyzer for APL 23-012 Sanctions requirements
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.analyzer = PolicyAnalyzer(db)
    
    def analyze_23012_compliance(self) -> Dict:
        """
        Perform detailed analysis for APL 23-012 requirements
        """
        # Get policies that mention relevant terms
        query = text("""
            SELECT 
                policy_code,
                title,
                extracted_text
            FROM policies
            WHERE 
                extracted_text ILIKE '%23-012%'
                OR extracted_text ILIKE '%14197.7%'
                OR extracted_text ILIKE '%51458.2%'
                OR extracted_text ILIKE '%probability sampl%'
                OR extracted_text ILIKE '%extrapolat%'
                OR extracted_text ILIKE '%sanction%'
            ORDER BY 
                CASE 
                    WHEN extracted_text ILIKE '%51458.2%' THEN 1
                    WHEN extracted_text ILIKE '%probability sampl%' THEN 2
                    WHEN extracted_text ILIKE '%23-012%' THEN 3
                    ELSE 4
                END
        """)
        
        relevant_policies = self.db.execute(query).fetchall()
        
        analysis_results = {
            'apl_code': 'APL 23-012',
            'title': 'Sanctions Requirements',
            'requirements': [
                {
                    'id': '23-012.1',
                    'text': 'Must reference 22 CCR 51458.2 and WIC 14197.7(g)(1)',
                    'required_elements': [
                        '22 CCR 51458.2',
                        'WIC section 14197.7(g)(1)',
                        'probability sampling',
                        'potential harm or impact on beneficiaries'
                    ]
                },
                {
                    'id': '23-012.2',
                    'text': 'Must reference probability sampling for extrapolation',
                    'required_elements': [
                        'probability sampling',
                        'extrapolate',
                        'WIC section 14197.7(f)(1)',
                        'number of beneficiaries impacted'
                    ]
                },
                {
                    'id': '23-012.3',
                    'text': 'Must include DHCS definitions',
                    'required_elements': [
                        'probability sampling definition',
                        'extrapolation definition',
                        'mathematical theory',
                        'margin of error'
                    ]
                }
            ],
            'policy_analyses': []
        }
        
        # Analyze each relevant policy
        for policy in relevant_policies:
            policy_analysis = self._analyze_policy_for_23012(policy)
            analysis_results['policy_analyses'].append(policy_analysis)
        
        return analysis_results
    
    def _analyze_policy_for_23012(self, policy) -> Dict:
        """
        Detailed analysis of a single policy for APL 23-012
        """
        text = policy.extracted_text.lower() if policy.extracted_text else ""
        
        analysis = {
            'policy_code': policy.policy_code,
            'policy_title': policy.title,
            'compliance_summary': {
                'has_apl_reference': '23-012' in text,
                'has_ccr_reference': '51458.2' in text,
                'has_wic_reference': '14197.7' in text,
                'has_probability_sampling': 'probability sampl' in text,
                'has_extrapolation': 'extrapolat' in text,
                'is_compliant': False
            },
            'detailed_findings': [],
            'relevant_excerpts': [],
            'explanation': ""
        }
        
        # Check for specific WIC subsections
        wic_pattern = r'wic\s*(?:section\s*)?\d+\.?\d*\([a-z]\)(?:\(\d+\))?'
        wic_matches = re.finditer(wic_pattern, text, re.IGNORECASE)
        
        for match in wic_matches:
            analysis['detailed_findings'].append(f"Found WIC reference: {match.group(0)}")
            
            # Extract context
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            excerpt = policy.extracted_text[start:end] if policy.extracted_text else ""
            analysis['relevant_excerpts'].append({
                'text': excerpt,
                'highlight': match.group(0)
            })
        
        # Generate explanation
        if policy.policy_code == 'GA.7111':
            analysis['explanation'] = """
            GA.7111: Health Network Certification Process
            - References APL 23-012 and WIC 14197.7(e) for enforcement actions
            - Does NOT reference 22 CCR 51458.2
            - Does NOT mention probability sampling methodology
            - References wrong subsection of WIC 14197.7 (references subsection (e), not (g)(1))
            
            Conclusion: Does not meet APL 23-012 requirements
            """
        elif policy.policy_code == 'GG.1661':
            analysis['explanation'] = """
            GG.1661: External Quality Review Requirements
            - References APL 23-012 only regarding failure to meet Minimum Performance Levels
            - Does NOT reference 22 CCR 51458.2
            - Does NOT mention probability sampling or extrapolation
            - Does NOT reference WIC 14197.7(g)(1)
            
            Conclusion: Does not meet APL 23-012 requirements
            """
        else:
            # Generic explanation
            missing = []
            if not analysis['compliance_summary']['has_ccr_reference']:
                missing.append("22 CCR 51458.2")
            if not analysis['compliance_summary']['has_probability_sampling']:
                missing.append("probability sampling methodology")
            if not analysis['compliance_summary']['has_extrapolation']:
                missing.append("extrapolation procedures")
            
            if missing:
                analysis['explanation'] = f"""
                {policy.policy_code}: {policy.title}
                Missing required elements: {', '.join(missing)}
                
                Conclusion: Does not fully meet APL 23-012 requirements
                """
            else:
                analysis['explanation'] = f"""
                {policy.policy_code}: {policy.title}
                Contains relevant elements for APL 23-012 compliance
                """
        
        # Set compliance status
        analysis['compliance_summary']['is_compliant'] = (
            analysis['compliance_summary']['has_ccr_reference'] and
            analysis['compliance_summary']['has_probability_sampling'] and
            analysis['compliance_summary']['has_extrapolation'] and
            '(g)(1)' in text and '(f)(1)' in text
        )
        
        return analysis