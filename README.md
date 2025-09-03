# Policy Compliance Auditor - Prototype

A prototype system for validating Managed Care Plan (MCP) policies against DHCS review tool requirements.

## 🚀 Quick Start

### Test the System
```bash
# Run quick test on sample documents
./run_test.sh

# Or run directly with Python
cd backend
python main.py --test
```

## 📋 How It Works

### 1. **Relevance Detection**
The system first determines if an RT APL (review tool) applies to a policy:
- Checks for keyword overlap (network, grievance, mental health, etc.)
- Returns relevance score (0-100%)
- Skips non-applicable validations

### 2. **Requirement Extraction**
Parses RT APL PDFs to extract:
- Checklist questions ("Does the P&Ps indicate...")
- Expected keywords and phrases
- Critical values (30 days, percentages, ratios)
- APL references

### 3. **Validation**
For each requirement, the system:
- Finds relevant sections in policy
- Checks for required keywords
- Verifies critical values match
- Generates compliance score

### 4. **Reporting**
Produces a report showing:
- ✅ Compliant requirements
- ❌ Non-compliant items with gaps
- 📊 Overall compliance rate
- 🔍 Specific missing elements

## 📁 Project Structure

```
policy-auditor/
├── backend/
│   ├── core/
│   │   └── compliance_engine.py    # Main validation logic
│   ├── services/
│   │   ├── ingestion.py           # Document ingestion
│   │   └── rt_apl_parser.py       # RT APL parser
│   ├── utils/
│   │   └── pdf_extractor.py       # PDF text extraction
│   └── main.py                    # CLI interface
├── docs/
│   └── POLICY_COMPLIANCE_ARCHITECTURE.md
└── run_test.sh                    # Quick test script
```

## 🔧 Components

### SimpleComplianceEngine
- Keyword-based validation (prototype approach)
- Relevance scoring
- Gap identification

### RTAPLParser
- Extracts requirements from review tools
- Identifies critical values and timeframes
- Parses APL references

### ComplianceValidator
- Orchestrates validation process
- Generates compliance reports
- Calculates overall scores

## 📊 Sample Output

```
POLICY COMPLIANCE VALIDATION REPORT
====================================

Policy: AA.1207 vs RT APL: RT APL 23-001
Status: PARTIAL
Compliance Rate: 70%
Relevance Score: 85%

  ❌ Requirement 1a: non_compliant
     Confidence: 60%
     Missing: 30 calendar days, extension clause
     
  ✅ Requirement 1b: compliant
     Confidence: 90%
```

## 🚦 Compliance Status Levels

- **COMPLIANT**: All requirements met (>95%)
- **PARTIAL**: Most requirements met (70-95%)  
- **NON_COMPLIANT**: Significant gaps (<70%)
- **NOT_APPLICABLE**: RT APL doesn't apply to policy

## 🔄 Next Steps for Production

1. **Enhanced Validation**
   - Add semantic similarity using embeddings
   - Integrate LLM for complex requirement checking
   - Improve section finding algorithms

2. **Database Integration**
   - Store results in PostgreSQL
   - Track compliance history
   - Generate trending reports

3. **Web Interface**
   - Dashboard for compliance monitoring
   - Detailed drill-down views
   - Export capabilities

4. **AI Enhancement**
   - Use GPT-4/Claude for semantic understanding
   - Natural language explanations of gaps
   - Automated fix recommendations

## 📝 Testing

```bash
# Test specific policy category
python main.py --test --policy-filter "AA"

# Test specific RT APL
python main.py --test --rt-filter "23-001"

# Test everything (limited samples)
python main.py --test
```

## ⚡ Performance Notes

This prototype:
- Processes first 50k characters of each document
- Tests first 5 requirements per RT APL
- Uses simple keyword matching
- Suitable for quick validation testing

For production, implement:
- Full document processing
- Parallel processing
- Caching of extracted text
- Database storage

## 🛠 Dependencies

Core requirements:
- Python 3.8+
- pdfplumber
- PyPDF2
- pymupdf

Install with:
```bash
pip install -r requirements.txt
```

## 📧 Support

This is a prototype implementation. For production deployment, consider:
- Adding comprehensive error handling
- Implementing retry logic
- Setting up monitoring
- Adding authentication for API access