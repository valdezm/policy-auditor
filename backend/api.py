"""
FastAPI backend for Policy Auditor
Serves corpus coverage data to the frontend
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict
import logging

from models.database import get_db
from models.models import Policy, AuditRequirement
from core.corpus_coverage import CorpusCoverageAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Policy Auditor API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"status": "Policy Auditor API Running"}


@app.get("/api/coverage/summary")
def get_coverage_summary(db: Session = Depends(get_db)):
    """Get corpus-wide coverage summary"""
    analyzer = CorpusCoverageAnalyzer(db)
    summary = analyzer.get_coverage_summary()
    return summary


@app.get("/api/policies")
def get_all_policies(db: Session = Depends(get_db)):
    """Get all policies with basic info"""
    policies = db.query(Policy).all()
    return [{
        "id": str(p.id),
        "code": p.policy_code,
        "title": p.title,
        "category": p.category,
        "status": p.status.value if p.status else "active",
        "effective_date": str(p.effective_date) if p.effective_date else None
    } for p in policies]


@app.get("/api/requirements")
def get_all_requirements(db: Session = Depends(get_db)):
    """Get all RT APL requirements"""
    requirements = db.query(AuditRequirement).all()
    return [{
        "id": str(r.id),
        "apl_code": r.apl_code,
        "title": r.title,
        "severity": r.severity.value if r.severity else "medium",
        "category": r.category,
        "effective_date": str(r.effective_date) if r.effective_date else None
    } for r in requirements]


@app.get("/api/coverage/details")
def get_coverage_details(db: Session = Depends(get_db)):
    """Get detailed coverage analysis"""
    analyzer = CorpusCoverageAnalyzer(db)
    results = analyzer.analyze_corpus_coverage()
    
    # Format for frontend display
    return {
        "coverage_percentage": results['coverage_percentage'],
        "stats": {
            "total": results['total_requirements'],
            "covered": results['covered'],
            "partial": results['partial'],
            "uncovered": results['uncovered']
        },
        "details": results['coverage_details'][:100]  # Limit for performance
    }


@app.post("/api/ingest/trigger")
def trigger_ingestion(db: Session = Depends(get_db)):
    """Trigger batch ingestion (for testing)"""
    try:
        from services.ingestion import PolicyIngestionService, AuditIngestionService
        
        # Quick test ingestion
        policy_service = PolicyIngestionService(db)
        audit_service = AuditIngestionService(db)
        
        # Just return counts
        policy_count = db.query(Policy).count()
        requirement_count = db.query(AuditRequirement).count()
        
        return {
            "status": "success",
            "policies_in_db": policy_count,
            "requirements_in_db": requirement_count
        }
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)