#!/bin/bash

echo "🚀 Policy Compliance Auditor - Quick Test"
echo "=========================================="
echo ""

# Navigate to backend directory
cd backend

# Install basic dependencies if needed
echo "📦 Checking dependencies..."
pip install -q pdfplumber PyPDF2 pymupdf 2>/dev/null

# Run the test
echo ""
echo "🔍 Running compliance check on sample documents..."
echo ""

python main.py \
    --policies "/mnt/c/Users/markv/Downloads/PNPs" \
    --audits "/mnt/c/Users/markv/Downloads/APL RTs" \
    --test \
    --policy-filter "AA.1" \
    --rt-filter "23-001"

echo ""
echo "✅ Test complete!"