#!/usr/bin/env python3
"""
Policy Auditor - Simple CLI Interface
Quick prototype for testing compliance validation
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict

from utils.pdf_extractor import PDFExtractor, DocumentProcessor
from services.rt_apl_parser import RTAPLParser, RequirementExtractor
from core.compliance_engine import ComplianceValidator, SimpleComplianceEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolicyAuditor:
    """Main application class for policy auditing"""
    
    def __init__(self, policy_dir: str, audit_dir: str):
        self.policy_dir = Path(policy_dir)
        self.audit_dir = Path(audit_dir)
        
        # Initialize components
        self.pdf_extractor = PDFExtractor()
        self.doc_processor = DocumentProcessor(self.pdf_extractor)
        self.rt_parser = RTAPLParser()
        self.requirement_extractor = RequirementExtractor()
        self.validator = ComplianceValidator()
        
    def run_quick_test(self, policy_pattern: str = None, rt_pattern: str = None):
        """
        Run a quick test on sample documents
        """
        print("=" * 80)
        print("POLICY COMPLIANCE AUDITOR - PROTOTYPE")
        print("=" * 80)
        print()
        
        # Get sample policy
        policies = self._get_sample_policies(policy_pattern)
        if not policies:
            print("❌ No policies found")
            return
            
        # Get sample RT APL
        rt_apls = self._get_sample_rt_apls(rt_pattern)
        if not rt_apls:
            print("❌ No RT APLs found")
            return
        
        print(f"📄 Found {len(policies)} policies")
        print(f"📋 Found {len(rt_apls)} RT APLs")
        print()
        
        # Run validation
        results = []
        for policy_path in policies[:2]:  # Test first 2 policies
            print(f"\n🔍 Processing Policy: {policy_path.name}")
            
            # Extract policy text
            try:
                policy_text, policy_meta = self.pdf_extractor.extract_text_from_pdf(str(policy_path))
                policy_data = {
                    'policy_code': policy_path.stem,
                    'extracted_text': policy_text[:50000],  # Limit for prototype
                    'metadata': policy_meta
                }
            except Exception as e:
                print(f"  ❌ Failed to extract: {e}")
                continue
            
            for rt_path in rt_apls[:2]:  # Test first 2 RT APLs
                print(f"  📊 Checking against: {rt_path.name}")
                
                # Extract RT APL
                try:
                    rt_text, rt_meta = self.pdf_extractor.extract_text_from_pdf(str(rt_path))
                    
                    # Parse requirements
                    requirements = self.requirement_extractor.extract_from_rt_apl(rt_text)
                    
                    rt_data = {
                        'apl_code': rt_path.stem,
                        'extracted_text': rt_text[:50000],
                        'requirements': requirements[:5],  # Test first 5 requirements
                        'metadata': rt_meta
                    }
                except Exception as e:
                    print(f"    ❌ Failed to extract: {e}")
                    continue
                
                # Validate
                result = self.validator.validate_policy_against_rt(policy_data, rt_data)
                results.append(result)
                
                # Show quick result
                status_icon = "✅" if result['status'] == 'compliant' else "❌"
                print(f"    {status_icon} Status: {result['status']}")
                print(f"    📈 Relevance: {result['relevance_score']:.1%}")
                if result['status'] != 'not_applicable':
                    print(f"    📊 Compliance Rate: {result.get('compliance_rate', 0):.1%}")
        
        # Generate report
        print("\n" + "=" * 80)
        print("SUMMARY REPORT")
        print("=" * 80)
        report = self.validator.generate_report(results)
        print(report)
        
        # Save results
        self._save_results(results)
        
    def _get_sample_policies(self, pattern: str = None) -> List[Path]:
        """Get sample policy files"""
        policies = []
        
        # Get policies from subdirectories
        for category_dir in self.policy_dir.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith('_'):
                pdfs = list(category_dir.glob("*.pdf"))
                if pattern:
                    pdfs = [p for p in pdfs if pattern.lower() in p.name.lower()]
                policies.extend(pdfs[:2])  # Take 2 from each category for testing
                
        return policies[:5]  # Limit to 5 total for quick test
    
    def _get_sample_rt_apls(self, pattern: str = None) -> List[Path]:
        """Get sample RT APL files"""
        rt_apls = list(self.audit_dir.glob("RT APL*.pdf"))
        
        if pattern:
            rt_apls = [r for r in rt_apls if pattern.lower() in r.name.lower()]
            
        return rt_apls[:3]  # Test with first 3
    
    def _save_results(self, results: List[Dict]):
        """Save results to JSON file"""
        output_file = Path("compliance_results.json")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {output_file}")
    
    def run_full_audit(self):
        """Run full audit (not implemented in prototype)"""
        print("Full audit not implemented in prototype")
        print("Use run_quick_test() for testing")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Policy Compliance Auditor')
    parser.add_argument(
        '--policies', 
        default='/mnt/c/Users/markv/Downloads/PNPs',
        help='Path to policies directory'
    )
    parser.add_argument(
        '--audits',
        default='/mnt/c/Users/markv/Downloads/APL RTs',
        help='Path to RT APL audits directory'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run quick test mode'
    )
    parser.add_argument(
        '--policy-filter',
        help='Filter policies by pattern'
    )
    parser.add_argument(
        '--rt-filter', 
        help='Filter RT APLs by pattern'
    )
    
    args = parser.parse_args()
    
    # Create auditor
    auditor = PolicyAuditor(args.policies, args.audits)
    
    if args.test:
        print("🚀 Running quick test...")
        auditor.run_quick_test(args.policy_filter, args.rt_filter)
    else:
        print("💡 Tip: Use --test flag for quick testing")
        auditor.run_quick_test()


if __name__ == '__main__':
    main()