#!/usr/bin/env python3
"""
Batch ingestion script - Load all policies and RT APLs into database
Simplified approach: Just get everything into the DB for corpus-wide analysis
"""
import os
import sys
import logging
from pathlib import Path
# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.database import Base, get_db
from services.ingestion import PolicyIngestionService, AuditIngestionService
from utils.pdf_extractor import PDFExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_all_documents():
    """Ingest all policies and RT APLs from disk"""
    
    # Paths
    POLICY_DIR = Path("/mnt/c/Users/markv/Downloads/PNPs")
    RT_APL_DIR = Path("/mnt/c/Users/markv/Downloads/APL RTs")
    
    # Database setup
    from models.database import engine, SessionLocal
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Ingest all policies
        logger.info("=" * 80)
        logger.info("STARTING BATCH INGESTION")
        logger.info("=" * 80)
        
        policy_service = PolicyIngestionService(db)
        logger.info(f"\n📁 Ingesting policies from: {POLICY_DIR}")
        policy_stats = policy_service.ingest_policy_directory(str(POLICY_DIR))
        
        logger.info(f"✅ Policies ingested:")
        logger.info(f"   Total: {policy_stats['total_files']}")
        logger.info(f"   Success: {policy_stats['successful']}")
        logger.info(f"   Failed: {policy_stats['failed']}")
        logger.info(f"   Skipped: {policy_stats['skipped']}")
        
        # 2. Ingest all RT APLs
        audit_service = AuditIngestionService(db)
        logger.info(f"\n📋 Ingesting RT APLs from: {RT_APL_DIR}")
        audit_stats = audit_service.ingest_audit_directory(str(RT_APL_DIR))
        
        logger.info(f"✅ RT APLs ingested:")
        logger.info(f"   Total: {audit_stats['total_files']}")
        logger.info(f"   Success: {audit_stats['successful']}")
        logger.info(f"   Failed: {audit_stats['failed']}")
        logger.info(f"   Skipped: {audit_stats['skipped']}")
        
        # 3. Summary
        logger.info("\n" + "=" * 80)
        logger.info("INGESTION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total policies in database: {policy_stats['successful']}")
        logger.info(f"Total RT APLs in database: {audit_stats['successful']}")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("🚀 Starting batch document ingestion...")
    ingest_all_documents()
    logger.info("✅ Done!")