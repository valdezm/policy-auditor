#!/usr/bin/env python3
"""
Quick test to check if the basic system works
No database or heavy dependencies required
"""
import os
import sys
from pathlib import Path

def check_directories():
    """Check if policy and RT APL directories exist"""
    policy_dir = Path("/mnt/c/Users/markv/Downloads/PNPs")
    rt_dir = Path("/mnt/c/Users/markv/Downloads/APL RTs")
    
    print("🔍 Checking directories...")
    
    if policy_dir.exists():
        # Count PDFs in subdirectories
        pdf_count = 0
        categories = []
        for subdir in policy_dir.iterdir():
            if subdir.is_dir() and not subdir.name.startswith('_'):
                pdfs = list(subdir.glob("*.pdf"))
                pdf_count += len(pdfs)
                if pdfs:
                    categories.append(f"{subdir.name} ({len(pdfs)} files)")
        
        print(f"✅ Found policy directory with {pdf_count} PDFs")
        print(f"   Categories: {', '.join(categories[:5])}")
    else:
        print(f"❌ Policy directory not found: {policy_dir}")
    
    if rt_dir.exists():
        rt_pdfs = list(rt_dir.glob("RT APL*.pdf"))
        print(f"✅ Found RT APL directory with {len(rt_pdfs)} review tools")
        if rt_pdfs:
            print(f"   Examples: {', '.join([f.name for f in rt_pdfs[:3]])}")
    else:
        print(f"❌ RT APL directory not found: {rt_dir}")
    
    return policy_dir.exists() and rt_dir.exists()

def simple_coverage_check():
    """Simple demonstration of coverage concept"""
    print("\n📊 Simple Coverage Example:")
    print("-" * 40)
    
    # Mock data for demonstration
    requirements = [
        "Submit data within 30 calendar days",
        "Maintain network adequacy",
        "Process grievances timely",
        "Provide mental health services",
        "Emergency care access"
    ]
    
    policies = {
        "AA.1207": ["network", "30 days"],
        "GA.2005": ["grievance", "timely"],
        "EE.3001": ["emergency"],
    }
    
    print("Requirements to check:")
    for i, req in enumerate(requirements, 1):
        # Simple keyword check
        covered = False
        covering_policy = None
        
        for policy, keywords in policies.items():
            if any(kw in req.lower() for kw in keywords):
                covered = True
                covering_policy = policy
                break
        
        status = "✅" if covered else "❌"
        print(f"  {status} {req}")
        if covering_policy:
            print(f"      Covered by: {covering_policy}")
    
    covered_count = sum(1 for r in requirements 
                       if any(any(kw in r.lower() for kw in keywords) 
                             for keywords in policies.values()))
    
    print(f"\nOverall Coverage: {covered_count}/{len(requirements)} ({covered_count*100//len(requirements)}%)")

if __name__ == "__main__":
    print("=" * 50)
    print("POLICY AUDITOR - QUICK TEST")
    print("=" * 50)
    print()
    
    if check_directories():
        print("\n✅ System can access policy files!")
        simple_coverage_check()
    else:
        print("\n⚠️ Please ensure the policy directories are accessible")
        print("   Expected locations:")
        print("   - /mnt/c/Users/markv/Downloads/PNPs")
        print("   - /mnt/c/Users/markv/Downloads/APL RTs")
    
    print("\n" + "=" * 50)
    print("This is a simplified test without database dependencies")
    print("For full system, install dependencies and run ./run_system.sh")