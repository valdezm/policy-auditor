"""
RT APL (Review Tool) Parser
Extracts structured requirements from DHCS review tool PDFs
"""
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RTAPLRequirement:
    """Structured requirement from RT APL"""
    id: str
    question: str
    reference: str
    page_reference: str = ""
    keywords: List[str] = field(default_factory=list)
    values: Dict = field(default_factory=dict)
    hints: List[str] = field(default_factory=list)
    compliance_type: str = "must_state"  # must_state, must_do, must_have


class RTAPLParser:
    """
    Parser for RT APL submission review forms
    Extracts checklist questions and requirements
    """
    
    def __init__(self):
        # Patterns for parsing RT APL documents
        self.question_pattern = re.compile(
            r'(\d+[a-z]?)\)\s*(.+?)(?:\?|$)',
            re.MULTILINE | re.DOTALL
        )
        
        self.reference_pattern = re.compile(
            r'\(Reference:\s*APL\s*(\d+-\d+),\s*page\s*(\d+)\)',
            re.IGNORECASE
        )
        
        self.yes_no_pattern = re.compile(
            r'(?:Yes|No)\s*(?:Citation:|$)',
            re.IGNORECASE
        )
        
        # Keywords that indicate requirements
        self.requirement_indicators = [
            'must', 'shall', 'required', 'will', 'ensure',
            'indicate', 'maintain', 'provide', 'submit'
        ]
        
        # Time/value patterns
        self.time_pattern = re.compile(r'(\d+)\s*(calendar\s*)?(days?|months?|years?)')
        self.percentage_pattern = re.compile(r'(\d+)\s*%')
        
    def parse_rt_apl(self, text: str) -> Dict:
        """
        Parse an RT APL document into structured requirements
        """
        # Extract basic metadata
        metadata = self._extract_metadata(text)
        
        # Extract requirements/questions
        requirements = self._extract_requirements(text)
        
        # Extract categories/topics
        topics = self._extract_topics(text)
        
        return {
            'apl_code': metadata.get('apl_code'),
            'title': metadata.get('title'),
            'topics': topics,
            'requirements': requirements,
            'metadata': metadata
        }
    
    def _extract_metadata(self, text: str) -> Dict:
        """Extract RT APL metadata"""
        metadata = {}
        
        # Extract APL code (e.g., APL 23-001)
        apl_match = re.search(r'APL\s*(\d{2}-\d{3})', text, re.IGNORECASE)
        if apl_match:
            metadata['apl_code'] = f"APL {apl_match.group(1)}"
        
        # Extract submission item/title
        title_match = re.search(
            r'SUBMISSION ITEM:\s*(.+?)(?:\n|$)',
            text, re.IGNORECASE
        )
        if title_match:
            metadata['title'] = title_match.group(1).strip()
        
        # Extract references section
        ref_match = re.search(
            r'REFERENCES:\s*(.+?)(?:\n\n|$)',
            text, re.IGNORECASE | re.DOTALL
        )
        if ref_match:
            metadata['references'] = ref_match.group(1).strip()
        
        return metadata
    
    def _extract_requirements(self, text: str) -> List[Dict]:
        """Extract structured requirements from RT APL text"""
        requirements = []
        
        # Split text into questions
        # Pattern: number + ) + question text ending with ?
        sections = re.split(r'(\d+[a-z]?\))', text)
        
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                question_num = sections[i].strip(')')
                question_text = sections[i + 1]
                
                # Clean up question text
                question_text = self._clean_question_text(question_text)
                
                if not question_text:
                    continue
                
                # Extract the actual question
                question = self._extract_question(question_text)
                
                if question:
                    # Extract reference
                    reference = self._extract_reference(question_text)
                    
                    # Extract keywords
                    keywords = self._extract_keywords(question)
                    
                    # Extract critical values
                    values = self._extract_values(question)
                    
                    # Extract section hints
                    hints = self._extract_section_hints(question)
                    
                    # Determine compliance type
                    compliance_type = self._determine_compliance_type(question)
                    
                    requirements.append({
                        'id': question_num,
                        'question': question,
                        'reference': reference.get('apl', ''),
                        'page_reference': reference.get('page', ''),
                        'keywords': keywords,
                        'values': values,
                        'hints': hints,
                        'compliance_type': compliance_type
                    })
        
        return requirements
    
    def _clean_question_text(self, text: str) -> str:
        """Clean up question text"""
        # Remove Yes/No checkboxes
        text = self.yes_no_pattern.sub('', text)
        
        # Remove citation lines
        text = re.sub(r'Citation:.*?(?:\n|$)', '', text, flags=re.IGNORECASE)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _extract_question(self, text: str) -> str:
        """Extract the actual question from text"""
        # Look for text starting with "Does" or "With regard to"
        patterns = [
            r'(Does\s+.+?\?)',
            r'(With regard to.+?Does.+?\?)',
            r'([A-Z].+?\?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                question = match.group(1)
                # Clean up the question
                question = ' '.join(question.split())
                return question.strip()
        
        # If no question mark found, take first sentence
        sentences = text.split('.')
        if sentences:
            return sentences[0].strip()
        
        return text[:500] if len(text) > 500 else text
    
    def _extract_reference(self, text: str) -> Dict:
        """Extract APL reference and page number"""
        match = self.reference_pattern.search(text)
        if match:
            return {
                'apl': f"APL {match.group(1)}",
                'page': match.group(2)
            }
        return {}
    
    def _extract_keywords(self, question: str) -> List[str]:
        """Extract important keywords from question"""
        keywords = []
        question_lower = question.lower()
        
        # Predefined important terms for compliance
        important_terms = [
            'network certification', 'annual', '30 calendar days',
            'complete and accurate', 'timely access', 'provider',
            'member', 'grievance', 'appeal', 'authorization',
            'emergency', 'urgent care', 'mental health', 'pharmacy',
            'quality', 'monitoring', 'corrective action', 'cap',
            'subcontractor', 'fqhc', 'rhc', 'telehealth'
        ]
        
        for term in important_terms:
            if term in question_lower:
                keywords.append(term)
        
        # Extract requirement verbs
        for indicator in self.requirement_indicators:
            if indicator in question_lower:
                # Find the phrase after the indicator
                pattern = f'{indicator}\\s+([\\w\\s]+?)(?:\\.|,|;|$)'
                matches = re.findall(pattern, question_lower)
                for match in matches:
                    phrase = match.strip()
                    if len(phrase) < 50:  # Reasonable length
                        keywords.append(phrase)
        
        return list(set(keywords))  # Remove duplicates
    
    def _extract_values(self, question: str) -> Dict:
        """Extract critical values like timeframes and percentages"""
        values = {}
        
        # Extract time values
        time_matches = self.time_pattern.findall(question)
        for match in time_matches:
            number = int(match[0])
            unit = match[2].rstrip('s')  # Remove plural
            
            if 'day' in unit:
                values['days'] = number
            elif 'month' in unit:
                values['months'] = number
            elif 'year' in unit:
                values['years'] = number
        
        # Extract percentages
        percent_matches = self.percentage_pattern.findall(question)
        if percent_matches:
            values['percentage'] = int(percent_matches[0])
        
        # Extract ratios (e.g., "1:2000")
        ratio_pattern = re.compile(r'(\d+):(\d+)')
        ratio_matches = ratio_pattern.findall(question)
        if ratio_matches:
            values['ratio'] = f"{ratio_matches[0][0]}:{ratio_matches[0][1]}"
        
        return values
    
    def _extract_section_hints(self, question: str) -> List[str]:
        """Extract hints about which policy sections to check"""
        hints = []
        
        # Look for section references
        section_patterns = [
            r'annual network certification',
            r'network provider',
            r'timely access',
            r'grievance',
            r'mental health',
            r'emergency',
            r'quality',
            r'member services',
            r'corrective action',
            r'telehealth',
            r'alternative access'
        ]
        
        question_lower = question.lower()
        for pattern in section_patterns:
            if pattern in question_lower:
                hints.append(pattern)
        
        return hints
    
    def _determine_compliance_type(self, question: str) -> str:
        """Determine the type of compliance check needed"""
        question_lower = question.lower()
        
        if 'indicate' in question_lower or 'state' in question_lower:
            return 'must_state'
        elif 'submit' in question_lower or 'provide' in question_lower:
            return 'must_do'
        elif 'maintain' in question_lower or 'have' in question_lower:
            return 'must_have'
        elif 'ensure' in question_lower:
            return 'must_ensure'
        
        return 'must_state'  # Default
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics covered by the RT APL"""
        topics = []
        
        # Look for "With regard to" sections
        regard_pattern = re.compile(
            r'With regard to (.+?):', 
            re.IGNORECASE
        )
        
        matches = regard_pattern.findall(text)
        for match in matches:
            topic = match.strip().lower()
            if topic not in topics:
                topics.append(topic)
        
        # Also check the title/submission item
        title_keywords = [
            'network', 'grievance', 'quality', 'mental health',
            'pharmacy', 'emergency', 'enrollment', 'authorization'
        ]
        
        text_lower = text.lower()
        for keyword in title_keywords:
            if keyword in text_lower[:1000]:  # Check first part
                if keyword not in topics:
                    topics.append(keyword)
        
        return topics


class RequirementExtractor:
    """
    Simplified requirement extractor for quick prototype
    """
    
    def extract_from_rt_apl(self, rt_apl_text: str) -> List[Dict]:
        """
        Quick extraction of requirements from RT APL text
        Returns list of requirement dictionaries
        """
        requirements = []
        
        # Simple pattern to find questions
        # Look for patterns like "1) Does the P&Ps..."
        pattern = re.compile(
            r'(\d+[a-z]?\))\s*(.*?Does.*?\?)',
            re.IGNORECASE | re.DOTALL
        )
        
        matches = pattern.findall(rt_apl_text)
        
        for match in matches:
            req_id = match[0].strip(')')
            question = ' '.join(match[1].split())  # Clean whitespace
            
            # Extract some basic keywords
            keywords = []
            key_phrases = [
                '30 calendar days', 'complete and accurate',
                'network', 'provider', 'member', 'timely access'
            ]
            
            for phrase in key_phrases:
                if phrase.lower() in question.lower():
                    keywords.append(phrase)
            
            requirements.append({
                'id': req_id,
                'question': question[:500],  # Limit length
                'keywords': keywords,
                'reference': self._extract_apl_reference(question)
            })
        
        return requirements
    
    def _extract_apl_reference(self, text: str) -> str:
        """Extract APL reference from question text"""
        ref_match = re.search(r'APL\s*(\d{2}-\d{3})', text, re.IGNORECASE)
        if ref_match:
            return f"APL {ref_match.group(1)}"
        return ""