# Policy Compliance Auditor

A comprehensive system for validating Managed Care Plan (MCP) policies against DHCS review tool requirements, featuring AI-powered analysis, interactive dashboards, and detailed compliance tracking.

## 🚀 Features

### Core Capabilities
- **AI-Powered Validation**: Advanced semantic analysis using OpenAI GPT models for intelligent requirement matching
- **Interactive Dashboard**: Next.js frontend with real-time filtering and detailed compliance views
- **Corpus-Wide Analysis**: Analyze entire policy collections for comprehensive coverage insights
- **PostgreSQL Database**: Persistent storage for policies, requirements, and validation results
- **REST API**: Full-featured API for programmatic access to all system functions
- **Batch Processing**: Efficient ingestion and analysis of large document sets

### Analysis Features
- **Relevance Detection**: Smart filtering to apply only relevant requirements to each policy
- **Requirement Coverage**: Track which requirements are addressed across your policy corpus
- **Gap Analysis**: Identify missing elements and compliance issues with detailed explanations
- **Confidence Scoring**: AI-generated confidence levels for each validation result
- **Historical Tracking**: Monitor compliance trends over time

## 📋 System Architecture

### Technology Stack
- **Backend**: Python FastAPI with async support
- **Frontend**: Next.js 14 with TypeScript, shadcn/ui components
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI/ML**: OpenAI GPT-4, spaCy NLP, sentence-transformers
- **Infrastructure**: Docker Compose for containerized deployment

### Components Overview
```
policy-auditor/
├── backend/                    # Python FastAPI backend
│   ├── api/                   # REST API endpoints
│   ├── core/                  # Core validation engine
│   ├── models/                # SQLAlchemy database models
│   ├── services/              # Business logic services
│   │   ├── ai_validator.py   # AI-powered validation
│   │   ├── ingestion.py      # Document ingestion
│   │   └── rt_apl_parser.py  # Review tool parsing
│   └── utils/                 # Utility functions
├── frontend-next/             # Next.js frontend application
│   ├── app/                   # Next.js app router pages
│   ├── components/            # React components
│   └── lib/                   # Utility libraries
├── database/                  # Database migrations and seeds
└── config/                    # Configuration files
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 18+
- PostgreSQL 14+
- Docker & Docker Compose (optional)

### Environment Configuration
1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Update `.env` with your configuration:
```env
# Database Configuration
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_NAME=policy_auditor
DB_HOST=localhost
DB_PORT=5432

# AI Configuration (Required for AI validation)
OPENAI_API_KEY=your-openai-api-key

# File Paths
POLICY_PATH=/path/to/policies
AUDIT_PATH=/path/to/review-tools
```

### Quick Start with Docker
```bash
# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend python -m alembic upgrade head

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

### Manual Installation

#### Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
cd backend
alembic upgrade head

# Start the backend server
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend-next

# Install dependencies
npm install

# Start development server
npm run dev
```

## 🎯 Usage

### Web Interface
1. Open http://localhost:3000 in your browser
2. Navigate to the Requirements Dashboard to view all requirements
3. Use filters to find specific requirements by type, category, or APL
4. Click on any requirement for detailed analysis
5. View policy compliance status and AI-generated insights

### Command Line Interface
```bash
# Run full system analysis
python backend/main.py --analyze

# Test with sample documents
./run_test.sh

# Ingest new policies
python backend/ingest_all.py --path /path/to/policies

# Run AI validation on specific policy
python backend/test_ai_validation.py --policy GA.1113 --requirement REQ-001
```

### API Access
```python
import requests

# Get all requirements
response = requests.get("http://localhost:8000/api/requirements")
requirements = response.json()

# Run validation
validation_request = {
    "policy_id": "GA.1113",
    "requirement_id": "REQ-001"
}
response = requests.post("http://localhost:8000/api/validate", json=validation_request)
result = response.json()
```

## 📊 Dashboard Features

### Requirements Dashboard
- **Filter by Category**: Grievances, Network, Quality Management, etc.
- **Filter by Type**: Timeliness, Documentation, Process requirements
- **Search**: Full-text search across all requirements
- **Sort**: By ID, category, criticality, or validation status

### Requirement Detail View
- **Full Requirement Text**: Complete requirement description
- **Validation Results**: AI analysis with confidence scores
- **Related Policies**: List of policies that address this requirement
- **Gap Analysis**: Specific missing elements identified

### Coverage Analysis
- **Policy Coverage**: See which requirements each policy addresses
- **Requirement Coverage**: Track which policies cover each requirement
- **Gap Reports**: Export comprehensive gap analysis reports

## 🤖 AI Validation Service

The AI validation service provides intelligent requirement matching using GPT-4:

### Features
- **Semantic Understanding**: Goes beyond keyword matching to understand context
- **Confidence Scoring**: Provides reliability metrics for each validation
- **Detailed Explanations**: Natural language explanations of compliance status
- **Smart Suggestions**: Recommendations for addressing gaps

### Configuration
Set your OpenAI API key in `.env`:
```env
OPENAI_API_KEY=sk-your-api-key-here
```

### Usage Example
```python
from backend.services.ai_validator import AIValidator

validator = AIValidator()
result = await validator.validate_requirement(
    policy_text="Policy content here...",
    requirement="Must process grievances within 30 days"
)
print(f"Compliant: {result['is_compliant']}")
print(f"Confidence: {result['confidence']}%")
print(f"Explanation: {result['explanation']}")
```

## 🚦 Compliance Status Levels

- **COMPLIANT**: All requirements fully met (>95% confidence)
- **PARTIAL**: Most requirements met with minor gaps (70-95%)  
- **NON_COMPLIANT**: Significant gaps identified (<70%)
- **NOT_APPLICABLE**: Requirement doesn't apply to this policy type
- **PENDING**: Awaiting AI validation

## 🔄 Development Workflow

### Running Tests
```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend-next
npm test
```

### Database Migrations
```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Adding New Requirements
```bash
# Batch ingest RT APLs
python backend/batch_ingest_rt_apls.py

# Ingest specific APL
python backend/ingest_apl_23_001.py
```

## 📈 Performance Optimization

### Current Capabilities
- Processes documents up to 500k characters
- Parallel processing for batch operations
- Redis caching for frequently accessed data (optional)
- Optimized database queries with eager loading

### Scaling Considerations
- Use PostgreSQL connection pooling for high load
- Deploy multiple API workers behind a load balancer
- Consider vector databases for semantic search at scale
- Implement rate limiting for AI API calls

## 🛠 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify connection settings in .env
psql -h localhost -U postgres -d policy_auditor
```

**AI Validation Not Working**
- Verify OpenAI API key is set correctly
- Check API rate limits and quota
- Review logs in `logs/app.log`

**Frontend Build Issues**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## 📝 API Documentation

Interactive API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Key endpoints:
- `GET /api/requirements` - List all requirements
- `GET /api/policies` - List all policies
- `POST /api/validate` - Run validation
- `GET /api/coverage` - Get coverage analysis
- `POST /api/ingest` - Ingest new documents

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

This project is proprietary software. All rights reserved.

## 📧 Support

For issues, questions, or feature requests:
- Create an issue in the GitHub repository
- Contact the development team
- Check the documentation in the `docs/` folder

## 🔒 Security Notes

- Always use strong passwords for database access
- Keep API keys secure and never commit them to version control
- Use HTTPS in production environments
- Regularly update dependencies for security patches
- Implement proper authentication for production deployment