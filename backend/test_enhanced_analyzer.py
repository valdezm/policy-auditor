#!/usr/bin/env python3
"""
Test script for the Enhanced Policy Analyzer
Tests the analysis for APL 23-024.3 requirement specifically
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

# Set database URL
os.environ['DATABASE_URL'] = 'postgresql://postgres:password@192.168.49.29:5432/policy_auditor'

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from core.enhanced_policy_analyzer import EnhancedPolicyAnalyzer

def test_enhanced_analyzer():
    """Test the enhanced analyzer on APL 23-024.3"""
    
    # Create database connection
    engine = create_engine(os.environ['DATABASE_URL'])
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Find APL 23-024.3 requirement ID
        query = text("""
            SELECT ac.id, ac.criteria_code, ac.criteria_text
            FROM audit_criteria ac
            JOIN audit_requirements ar ON ar.id = ac.audit_requirement_id
            WHERE ar.apl_code ILIKE '%23-024%' 
            AND ac.criteria_code = '23-024.3'
        """)
        
        result = db.execute(query).fetchone()
        if not result:
            print("❌ APL 23-024.3 requirement not found")
            return
        
        requirement_id = result.id
        print(f"🔍 Testing APL 23-024.3 (ID: {requirement_id})")
        print(f"📋 Requirement: {result.criteria_text[:100]}...")
        
        # Test enhanced analyzer
        print("\n🚀 Running Enhanced Analysis...")
        enhanced_analyzer = EnhancedPolicyAnalyzer(db)
        analyses = enhanced_analyzer.analyze_requirement_compliance(requirement_id)
        
        print(f"\n📊 Results:")
        print(f"   Total policies analyzed: {len(analyses)}")
        
        # Show top analyses
        for i, analysis in enumerate(analyses[:5]):
            print(f"\n📋 Policy {i+1}: {analysis.policy_code}")
            print(f"   Compliance Score: {analysis.compliance_score:.2f}")
            print(f"   Confidence Level: {analysis.confidence_level:.2f}")
            print(f"   Is Compliant: {analysis.is_compliant}")
            print(f"   Primary Reference: {analysis.has_primary_reference}")
            print(f"   Cross References: {analysis.has_cross_references}")
            print(f"   Found Elements: {len(analysis.found_elements)}")
            print(f"   Missing Elements: {len(analysis.missing_elements)}")
            print(f"   Contextual Excerpts: {len(analysis.contextual_excerpts)}")
            
            if analysis.contextual_excerpts:
                print(f"   Top Excerpt (relevance {analysis.contextual_excerpts[0].relevance_score:.2f}):")
                excerpt = analysis.contextual_excerpts[0]
                print(f"      Text: {excerpt.text}")
                print(f"      Context: {excerpt.context[:100]}...")
        
        # Summary statistics
        compliant_count = sum(1 for a in analyses if a.is_compliant)
        high_confidence = sum(1 for a in analyses if a.confidence_level > 0.8)
        
        print(f"\n📈 Summary:")
        print(f"   Compliant Policies: {compliant_count}/{len(analyses)}")
        print(f"   High Confidence Analyses: {high_confidence}/{len(analyses)}")
        
        # Check if we found the AA.1000 issue
        aa1000_analysis = next((a for a in analyses if a.policy_code == 'AA.1000'), None)
        if aa1000_analysis:
            print(f"\n🔍 AA.1000 Analysis:")
            print(f"   Compliance Score: {aa1000_analysis.compliance_score:.2f}")
            print(f"   Confidence: {aa1000_analysis.confidence_level:.2f}")
            print(f"   Is Compliant: {aa1000_analysis.is_compliant}")
            print(f"   Contextual Excerpts: {len(aa1000_analysis.contextual_excerpts)}")
            
            if aa1000_analysis.contextual_excerpts:
                for i, excerpt in enumerate(aa1000_analysis.contextual_excerpts):
                    print(f"   Excerpt {i+1} (relevance {excerpt.relevance_score:.2f}):")
                    print(f"      Matched: {excerpt.matched_elements}")
                    print(f"      Text: {excerpt.text}")
                    print(f"      Context: {excerpt.context[:150]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_enhanced_analyzer()