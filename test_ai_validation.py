#!/usr/bin/env python3
"""
Test script for AI Validation Service
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Add backend to Python path
sys.path.append('backend')

from services.ai_validator import AIValidationService

# Load environment variables
load_dotenv()

def test_ai_validation():
    """Test the AI validation service"""
    
    # Check if OpenAI API key is configured
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your-openai-api-key-here":
        print("❌ OpenAI API key not configured")
        print("Please set OPENAI_API_KEY in the .env file")
        return False
    
    print("🤖 Testing AI Validation Service...")
    
    # Sample policy text
    sample_policy = """
    CalOptima Health Policy AA.1000
    
    PURPOSE
    This policy establishes requirements for maintaining accurate member records 
    and protecting member privacy in accordance with HIPAA regulations.
    
    POLICY
    CalOptima Health maintains comprehensive member records that include:
    - Personal identification information
    - Medical history and treatment records
    - Insurance coverage details
    - Contact information
    
    All staff must protect member privacy by:
    - Using minimum necessary standards when accessing records
    - Obtaining written authorization before disclosure
    - Maintaining physical and electronic security safeguards
    
    PROCEDURE
    1. Access to member records is granted on a need-to-know basis
    2. All access is logged and monitored
    3. Records are stored in secure, encrypted systems
    4. Regular audits ensure compliance with privacy requirements
    """
    
    # Sample requirement
    sample_requirement = """
    The health plan must implement appropriate administrative, physical, and 
    technical safeguards to protect the privacy and security of protected 
    health information (PHI) as required by HIPAA Privacy Rule 45 CFR 164.530.
    """
    
    try:
        # Initialize AI service
        ai_service = AIValidationService()
        
        print("📝 Analyzing sample policy against HIPAA requirement...")
        
        # Perform validation
        result = ai_service.validate_policy_compliance(
            policy_text=sample_policy,
            requirement_text=sample_requirement,
            regulation_reference="HIPAA Privacy Rule 45 CFR 164.530",
            requirement_context={
                'key_obligations': ['administrative safeguards', 'physical safeguards', 'technical safeguards'],
                'regulation_references': ['45 CFR 164.530']
            }
        )
        
        print("\n✅ AI Analysis Complete!")
        print("=" * 50)
        print(f"Compliance Rating: {result.compliance_rating.value}")
        print(f"Confidence Level: {result.confidence_level.value}")
        print(f"Confidence Score: {result.confidence_score}%")
        print(f"Priority Level: {result.priority_level}")
        print("\n📋 Reasoning:")
        print(result.reasoning)
        
        if result.policy_strengths:
            print(f"\n💪 Policy Strengths ({len(result.policy_strengths)}):")
            for i, strength in enumerate(result.policy_strengths, 1):
                print(f"  {i}. {strength}")
        
        if result.missing_elements:
            print(f"\n❌ Missing Elements ({len(result.missing_elements)}):")
            for i, element in enumerate(result.missing_elements, 1):
                print(f"  {i}. {element}")
        
        if result.recommendations:
            print(f"\n🔧 Recommendations ({len(result.recommendations)}):")
            for i, rec in enumerate(result.recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("\n🎯 Risk Assessment:")
        print(result.risk_assessment)
        
        print("\n🏛️ Regulatory Interpretation:")
        print(result.regulatory_interpretation)
        
        if result.relevant_policy_excerpts:
            print(f"\n📄 Relevant Policy Excerpts ({len(result.relevant_policy_excerpts)}):")
            for i, excerpt in enumerate(result.relevant_policy_excerpts, 1):
                print(f"  {i}. \"{excerpt}\"")
        
        print("\n" + "=" * 50)
        print("🎉 AI Validation Service is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing AI validation: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_ai_validation()
    sys.exit(0 if success else 1)