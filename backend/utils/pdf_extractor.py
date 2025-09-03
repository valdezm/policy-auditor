"""
PDF Extraction Utilities for Policy and Audit Documents
"""
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

import pdfplumber
import PyPDF2
from PyPDF2 import PdfReader
import fitz  # PyMuPDF for better text extraction

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Advanced PDF text extraction with metadata parsing"""
    
    def __init__(self):
        self.policy_pattern = re.compile(
            r'([A-Z]{2,3})\.(\d{4}[a-z]?)_.*?v(\d{8})',
            re.IGNORECASE
        )
        self.apl_pattern = re.compile(
            r'RT\s+APL\s+(\d{2}-\d{3})',
            re.IGNORECASE
        )
        
    def extract_text_from_pdf(self, file_path: str) -> Tuple[str, Dict]:
        """
        Extract text and metadata from PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        metadata = {
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'file_hash': self._calculate_file_hash(file_path),
            'extraction_date': datetime.now().isoformat(),
            'page_count': 0,
            'extraction_method': None
        }
        
        # Try multiple extraction methods for best results
        text = ""
        
        # Method 1: PyMuPDF (usually best for complex PDFs)
        try:
            text, pages = self._extract_with_pymupdf(file_path)
            metadata['page_count'] = pages
            metadata['extraction_method'] = 'pymupdf'
            if text.strip():
                return text, metadata
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {e}")
        
        # Method 2: pdfplumber (good for tables)
        try:
            text, pages = self._extract_with_pdfplumber(file_path)
            metadata['page_count'] = pages
            metadata['extraction_method'] = 'pdfplumber'
            if text.strip():
                return text, metadata
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
        
        # Method 3: PyPDF2 (fallback)
        try:
            text, pages = self._extract_with_pypdf2(file_path)
            metadata['page_count'] = pages
            metadata['extraction_method'] = 'pypdf2'
            return text, metadata
        except Exception as e:
            logger.error(f"All PDF extraction methods failed: {e}")
            raise
    
    def _extract_with_pymupdf(self, file_path: Path) -> Tuple[str, int]:
        """Extract text using PyMuPDF"""
        doc = fitz.open(str(file_path))
        text_parts = []
        
        for page_num, page in enumerate(doc, 1):
            text = page.get_text()
            if text:
                text_parts.append(f"--- Page {page_num} ---\n{text}")
        
        doc.close()
        return "\n\n".join(text_parts), len(text_parts)
    
    def _extract_with_pdfplumber(self, file_path: Path) -> Tuple[str, int]:
        """Extract text using pdfplumber"""
        text_parts = []
        
        with pdfplumber.open(str(file_path)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    text_parts.append(f"--- Page {page_num} ---\n{text}")
            
            return "\n\n".join(text_parts), len(pdf.pages)
    
    def _extract_with_pypdf2(self, file_path: Path) -> Tuple[str, int]:
        """Extract text using PyPDF2"""
        text_parts = []
        
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            num_pages = len(reader.pages)
            
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text:
                    text_parts.append(f"--- Page {page_num} ---\n{text}")
        
        return "\n\n".join(text_parts), num_pages
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def parse_policy_metadata(self, filename: str, text: str) -> Dict:
        """
        Extract policy-specific metadata from filename and text
        
        Args:
            filename: Name of the policy file
            text: Extracted text from the policy
            
        Returns:
            Dictionary of policy metadata
        """
        metadata = {
            'policy_code': None,
            'category': None,
            'subcategory': None,
            'version': None,
            'effective_date': None,
            'title': None
        }
        
        # Parse filename for policy code and version
        match = self.policy_pattern.search(filename)
        if match:
            category = match.group(1)
            subcategory = match.group(2)
            version_str = match.group(3)
            
            metadata['category'] = category
            metadata['subcategory'] = subcategory
            metadata['policy_code'] = f"{category}.{subcategory}"
            
            # Parse version date
            try:
                metadata['version'] = version_str
                metadata['effective_date'] = datetime.strptime(
                    version_str, '%Y%m%d'
                ).date().isoformat()
            except ValueError:
                pass
        
        # Extract title from text (usually in first few lines)
        lines = text.split('\n')[:20]
        for line in lines:
            if 'policy' in line.lower() and len(line) > 10:
                metadata['title'] = line.strip()
                break
        
        return metadata
    
    def parse_audit_metadata(self, filename: str, text: str) -> Dict:
        """
        Extract audit requirement metadata from filename and text
        
        Args:
            filename: Name of the audit file
            text: Extracted text from the audit
            
        Returns:
            Dictionary of audit metadata
        """
        metadata = {
            'apl_code': None,
            'title': None,
            'effective_date': None,
            'category': None
        }
        
        # Parse APL code from filename
        match = self.apl_pattern.search(filename)
        if match:
            metadata['apl_code'] = f"APL {match.group(1)}"
        
        # Extract title and other info from text
        lines = text.split('\n')[:50]
        for line in lines:
            line = line.strip()
            
            # Look for title patterns
            if 'all plan letter' in line.lower() and not metadata['title']:
                metadata['title'] = line
            
            # Look for effective date
            if 'effective' in line.lower():
                date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
                if date_match:
                    try:
                        date_obj = datetime.strptime(date_match.group(1), '%m/%d/%Y')
                        metadata['effective_date'] = date_obj.date().isoformat()
                    except ValueError:
                        pass
        
        return metadata
    
    def extract_sections(self, text: str) -> List[Dict]:
        """
        Extract structured sections from document text
        
        Args:
            text: Document text
            
        Returns:
            List of section dictionaries
        """
        sections = []
        
        # Common section patterns
        section_patterns = [
            r'^(\d+\.?\d*)\s+([A-Z][^:\n]{3,50})',  # 1.1 Section Title
            r'^([A-Z]\.)\s+([A-Z][^:\n]{3,50})',     # A. Section Title
            r'^(Section\s+\d+[:.]\s*)([^:\n]{3,50})', # Section 1: Title
            r'^(Article\s+[IVX]+[:.]\s*)([^:\n]{3,50})', # Article IV: Title
        ]
        
        combined_pattern = '|'.join(f'({p})' for p in section_patterns)
        
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            # Check if line matches a section header
            is_section = False
            for pattern in section_patterns:
                match = re.match(pattern, line.strip())
                if match:
                    # Save previous section if exists
                    if current_section:
                        current_section['content'] = '\n'.join(current_content)
                        sections.append(current_section)
                    
                    # Start new section
                    current_section = {
                        'section_number': match.group(1).strip(),
                        'section_title': match.group(2).strip(),
                        'content': ''
                    }
                    current_content = []
                    is_section = True
                    break
            
            # Add line to current section content if not a header
            if not is_section and current_section:
                current_content.append(line)
        
        # Save last section
        if current_section:
            current_section['content'] = '\n'.join(current_content)
            sections.append(current_section)
        
        return sections


class DocumentProcessor:
    """Process and prepare documents for compliance checking"""
    
    def __init__(self, extractor: Optional[PDFExtractor] = None):
        self.extractor = extractor or PDFExtractor()
    
    def process_policy_document(self, file_path: str) -> Dict:
        """
        Process a policy document and extract all relevant information
        
        Args:
            file_path: Path to policy PDF
            
        Returns:
            Dictionary containing processed policy data
        """
        # Extract text and metadata
        text, extraction_metadata = self.extractor.extract_text_from_pdf(file_path)
        
        # Parse policy-specific metadata
        policy_metadata = self.extractor.parse_policy_metadata(
            Path(file_path).name, text
        )
        
        # Extract sections
        sections = self.extractor.extract_sections(text)
        
        return {
            'file_path': file_path,
            'extracted_text': text,
            'sections': sections,
            'metadata': {
                **extraction_metadata,
                **policy_metadata
            }
        }
    
    def process_audit_document(self, file_path: str) -> Dict:
        """
        Process an audit requirement document
        
        Args:
            file_path: Path to audit PDF
            
        Returns:
            Dictionary containing processed audit data
        """
        # Extract text and metadata
        text, extraction_metadata = self.extractor.extract_text_from_pdf(file_path)
        
        # Parse audit-specific metadata
        audit_metadata = self.extractor.parse_audit_metadata(
            Path(file_path).name, text
        )
        
        # Extract audit criteria
        criteria = self._extract_audit_criteria(text)
        
        return {
            'file_path': file_path,
            'extracted_text': text,
            'criteria': criteria,
            'metadata': {
                **extraction_metadata,
                **audit_metadata
            }
        }
    
    def _extract_audit_criteria(self, text: str) -> List[Dict]:
        """
        Extract specific audit criteria from audit text
        
        Args:
            text: Audit document text
            
        Returns:
            List of audit criteria
        """
        criteria = []
        
        # Pattern for numbered requirements
        requirement_pattern = re.compile(
            r'(\d+\.?\d*)\s*([^:]{10,100}):\s*([^.]+\.)',
            re.MULTILINE
        )
        
        matches = requirement_pattern.findall(text)
        for match in matches:
            criteria.append({
                'criteria_code': match[0].strip(),
                'criteria_title': match[1].strip(),
                'criteria_text': match[2].strip()
            })
        
        # Also look for bullet points that might be criteria
        bullet_pattern = re.compile(
            r'[•·▪]\s*([^:]{10,100}):\s*([^.]+\.)',
            re.MULTILINE
        )
        
        bullet_matches = bullet_pattern.findall(text)
        for i, match in enumerate(bullet_matches):
            criteria.append({
                'criteria_code': f'B{i+1}',
                'criteria_title': match[0].strip(),
                'criteria_text': match[1].strip()
            })
        
        return criteria