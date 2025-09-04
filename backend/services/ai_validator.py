"""
AI Validation Service for Policy Compliance Analysis
Uses OpenAI GPT-4 to validate policy compliance against regulatory requirements
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ComplianceRating(str, Enum):
    FULLY_COMPLIANT = "fully_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant" 
    NON_COMPLIANT = "non_compliant"
    UNCLEAR = "unclear"
    NOT_APPLICABLE = "not_applicable"


class ConfidenceLevel(str, Enum):
    HIGH = "high"      # 80-100%
    MEDIUM = "medium"  # 50-79%
    LOW = "low"        # 0-49%


@dataclass
class AIValidationResult:
    """Structured result from AI validation"""
    compliance_rating: ComplianceRating
    confidence_level: ConfidenceLevel
    confidence_score: float  # 0-100
    reasoning: str
    specific_findings: List[str]
    missing_elements: List[str]
    policy_strengths: List[str]
    recommendations: List[str]
    relevant_policy_excerpts: List[str]
    regulatory_interpretation: str
    risk_assessment: str
    priority_level: str  # "high", "medium", "low"


class AIValidationService:
    """Service for validating policy compliance using OpenAI GPT-4"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI validation service
        
        Args:
            api_key: OpenAI API key. If not provided, will use environment variable
        """
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
        
        self.model = "gpt-4o"  # Latest GPT-4 model
        self.max_tokens = 4000
        self.temperature = 0.1  # Low temperature for consistent, factual responses
        
    def validate_policy_compliance(
        self,
        policy_text: str,
        requirement_text: str,
        regulation_reference: str,
        requirement_context: Optional[Dict] = None
    ) -> AIValidationResult:
        """
        Validate if a policy complies with a specific regulatory requirement
        
        Args:
            policy_text: The full text of the policy document
            requirement_text: The specific regulatory requirement text
            regulation_reference: Reference to the regulation (e.g., "APL 23-012 Section 4.2")
            requirement_context: Additional context about the requirement
            
        Returns:
            AIValidationResult: Structured validation result
        """
        try:
            prompt = self._build_validation_prompt(
                policy_text, requirement_text, regulation_reference, requirement_context
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "validate_compliance",
                        "description": "Validate policy compliance against regulatory requirements",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "compliance_rating": {
                                    "type": "string",
                                    "enum": ["fully_compliant", "partially_compliant", "non_compliant", "unclear", "not_applicable"],
                                    "description": "Overall compliance rating"
                                },
                                "confidence_score": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 100,
                                    "description": "Confidence score (0-100)"
                                },
                                "reasoning": {
                                    "type": "string",
                                    "description": "Detailed reasoning for the compliance assessment"
                                },
                                "specific_findings": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of specific compliance findings"
                                },
                                "missing_elements": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Elements missing from the policy"
                                },
                                "policy_strengths": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Strengths found in the policy"
                                },
                                "recommendations": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Specific recommendations for improvement"
                                },
                                "relevant_policy_excerpts": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Relevant excerpts from the policy"
                                },
                                "regulatory_interpretation": {
                                    "type": "string",
                                    "description": "Interpretation of the regulatory requirement"
                                },
                                "risk_assessment": {
                                    "type": "string",
                                    "description": "Risk assessment if non-compliant"
                                },
                                "priority_level": {
                                    "type": "string",
                                    "enum": ["high", "medium", "low"],
                                    "description": "Priority level for addressing issues"
                                }
                            },
                            "required": [
                                "compliance_rating", "confidence_score", "reasoning", 
                                "specific_findings", "missing_elements", "policy_strengths",
                                "recommendations", "relevant_policy_excerpts", 
                                "regulatory_interpretation", "risk_assessment", "priority_level"
                            ]
                        }
                    }
                }],
                tool_choice={"type": "function", "function": {"name": "validate_compliance"}}
            )
            
            # Parse the function call response
            function_args = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
            
            return AIValidationResult(
                compliance_rating=ComplianceRating(function_args["compliance_rating"]),
                confidence_level=self._score_to_confidence_level(function_args["confidence_score"]),
                confidence_score=function_args["confidence_score"],
                reasoning=function_args["reasoning"],
                specific_findings=function_args["specific_findings"],
                missing_elements=function_args["missing_elements"],
                policy_strengths=function_args["policy_strengths"],
                recommendations=function_args["recommendations"],
                relevant_policy_excerpts=function_args["relevant_policy_excerpts"],
                regulatory_interpretation=function_args["regulatory_interpretation"],
                risk_assessment=function_args["risk_assessment"],
                priority_level=function_args["priority_level"]
            )
            
        except Exception as e:
            logger.error(f"AI validation failed: {str(e)}")
            # Return a fallback result indicating the validation failed
            return AIValidationResult(
                compliance_rating=ComplianceRating.UNCLEAR,
                confidence_level=ConfidenceLevel.LOW,
                confidence_score=0.0,
                reasoning=f"AI validation failed: {str(e)}",
                specific_findings=[],
                missing_elements=[],
                policy_strengths=[],
                recommendations=["Manual review required due to AI validation failure"],
                relevant_policy_excerpts=[],
                regulatory_interpretation="Could not be determined",
                risk_assessment="Unknown due to validation failure",
                priority_level="high"
            )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI model"""
        return """You are a regulatory compliance expert specializing in healthcare policy analysis. 
        Your role is to assess whether policy documents comply with specific regulatory requirements.
        
        Key responsibilities:
        1. Analyze policy text against regulatory requirements with high precision
        2. Identify specific compliance gaps and strengths
        3. Provide actionable recommendations
        4. Assess risk levels for non-compliance
        5. Extract relevant policy excerpts that support your analysis
        
        Guidelines:
        - Be thorough and precise in your analysis
        - Consider both explicit and implicit compliance elements
        - Focus on actionable insights
        - Assess confidence based on clarity and completeness of evidence
        - Consider the practical implementation aspects of requirements
        - Identify potential ambiguities that may need clarification
        
        Always provide structured, evidence-based assessments."""
    
    def _build_validation_prompt(
        self,
        policy_text: str,
        requirement_text: str, 
        regulation_reference: str,
        requirement_context: Optional[Dict] = None
    ) -> str:
        """Build the validation prompt for the AI model"""
        
        context_info = ""
        if requirement_context:
            context_info = f"""
            
Additional Requirement Context:
- Key Obligations: {requirement_context.get('key_obligations', [])}
- Timeframes: {requirement_context.get('timeframes', [])}
- Definitions: {requirement_context.get('definitions', [])}
- Related Regulations: {requirement_context.get('regulation_references', [])}
"""
        
        prompt = f"""Please analyze the following policy document for compliance with the specified regulatory requirement.

REGULATORY REQUIREMENT:
Reference: {regulation_reference}
Text: {requirement_text}
{context_info}

POLICY DOCUMENT TO ANALYZE:
{policy_text[:8000]}  # Truncate to fit in context window

ANALYSIS REQUIRED:
1. Determine overall compliance rating
2. Assess confidence level (0-100) based on clarity of evidence
3. Provide detailed reasoning for your assessment
4. Identify specific findings (both compliant and non-compliant elements)
5. List missing elements that should be addressed
6. Highlight policy strengths related to this requirement
7. Provide specific, actionable recommendations
8. Extract relevant policy excerpts that support your analysis
9. Interpret the regulatory requirement in context
10. Assess compliance risks and their severity
11. Assign priority level for addressing any issues

Focus on being precise, thorough, and actionable in your analysis."""

        return prompt
    
    def _score_to_confidence_level(self, score: float) -> ConfidenceLevel:
        """Convert numerical confidence score to confidence level"""
        if score >= 80:
            return ConfidenceLevel.HIGH
        elif score >= 50:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def batch_validate(
        self,
        policy_text: str,
        requirements: List[Tuple[str, str, str, Optional[Dict]]]
    ) -> List[AIValidationResult]:
        """
        Validate a policy against multiple requirements
        
        Args:
            policy_text: The policy document text
            requirements: List of tuples (requirement_text, regulation_reference, requirement_id, context)
            
        Returns:
            List of AIValidationResult objects
        """
        results = []
        
        for req_text, reg_ref, req_id, context in requirements:
            try:
                result = self.validate_policy_compliance(
                    policy_text, req_text, reg_ref, context
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Batch validation failed for requirement {req_id}: {str(e)}")
                # Add a failed result
                results.append(AIValidationResult(
                    compliance_rating=ComplianceRating.UNCLEAR,
                    confidence_level=ConfidenceLevel.LOW,
                    confidence_score=0.0,
                    reasoning=f"Validation failed: {str(e)}",
                    specific_findings=[],
                    missing_elements=[],
                    policy_strengths=[],
                    recommendations=["Manual review required"],
                    relevant_policy_excerpts=[],
                    regulatory_interpretation="Could not be determined",
                    risk_assessment="Unknown",
                    priority_level="high"
                ))
        
        return results