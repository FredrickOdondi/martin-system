import logging
import re
from typing import Dict, Any, Optional
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

logger = logging.getLogger(__name__)

class DocumentIntelligenceService:
    """
    Service for extracting insights from project documents.
    Uses hybrid approach: PyMuPDF for text PDFs, Tesseract OCR for scanned PDFs.
    """
    
    def __init__(self):
        pass

    def extract_text_with_pymupdf(self, file_path: str) -> Optional[str]:
        """
        Extract text from PDF using PyMuPDF (fast, works for text-based PDFs).
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text or None if extraction fails
        """
        try:
            doc = fitz.open(file_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text += page.get_text()
            
            doc.close()
            
            # Check if we got meaningful text (not just whitespace)
            if text.strip():
                logger.info(f"✓ Extracted {len(text)} characters from {file_path} using PyMuPDF")
                return text
            else:
                logger.warning(f"PyMuPDF extracted empty text from {file_path}, may be scanned PDF")
                return None
                
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed for {file_path}: {e}")
            return None

    def extract_text_with_ocr(self, file_path: str) -> Optional[str]:
        """
        Extract text from scanned PDF using Tesseract OCR (slower but works on images).
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text or None if OCR fails
        """
        try:
            doc = fitz.open(file_path)
            text = ""
            
            # Convert each page to image and OCR
            for page_num in range(min(len(doc), 10)):  # Limit to first 10 pages for performance
                page = doc[page_num]
                
                # Render page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # OCR the image
                page_text = pytesseract.image_to_string(img)
                text += page_text + "\n"
            
            doc.close()
            
            if text.strip():
                logger.info(f"✓ OCR extracted {len(text)} characters from {file_path}")
                return text
            else:
                logger.warning(f"OCR extracted no text from {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"OCR extraction failed for {file_path}: {e}")
            return None

    async def extract_text_from_document(self, file_path: str, file_type: str) -> str:
        """
        Extract text from a document file using hybrid approach.
        
        Strategy:
        1. Try PyMuPDF first (fast, works for most PDFs)
        2. If that fails or returns empty, try OCR (slower but works on scans)
        
        Args:
            file_path: Path to document file
            file_type: MIME type of file
            
        Returns:
            Extracted text content
        """
        logger.info(f"Extracting text from {file_path} ({file_type})")
        
        # Only handle PDFs for now
        if "pdf" not in file_type.lower():
            logger.warning(f"Unsupported file type: {file_type}")
            return "Unsupported file type. Only PDFs are currently supported."
        
        # Try PyMuPDF first (fast)
        text = self.extract_text_with_pymupdf(file_path)
        
        # If PyMuPDF failed or returned empty, try OCR
        if not text or len(text.strip()) < 100:  # Less than 100 chars likely means scanned
            logger.info(f"Falling back to OCR for {file_path}")
            ocr_text = self.extract_text_with_ocr(file_path)
            if ocr_text:
                text = ocr_text
        
        # Return text or error message
        if text and text.strip():
            return text
        else:
            logger.error(f"Failed to extract any text from {file_path}")
            return "Error: Could not extract text from document."

    async def analyze_document_for_scoring(self, text: str) -> Dict[str, Any]:
        """
        Analyze text to find key scoring indicators.
        This is a basic heuristic version - will be replaced by LLM analysis.
        
        Args:
            text: Extracted document text
            
        Returns:
            Dictionary of scoring indicators
        """
        indicators = {
            "has_esia": False,
            "has_feasibility_study": False,
            "has_financial_model": False,
            "has_government_support": False,
            "irr": None
        }
        
        lower_text = text.lower()
        
        # Check for document types
        if "esia" in lower_text or "environmental and social" in lower_text or "environmental impact" in lower_text:
            indicators["has_esia"] = True
            
        if "feasibility study" in lower_text or "feasibility analysis" in lower_text:
            indicators["has_feasibility_study"] = True
            
        if "financial model" in lower_text or "irr" in lower_text or "npv" in lower_text:
            indicators["has_financial_model"] = True
        
        if "government support" in lower_text or "ministry" in lower_text or "letter of support" in lower_text:
            indicators["has_government_support"] = True
            
        # Try to extract IRR
        irr_match = re.search(r"irr.*?(\d+(?:\.\d+)?)%", lower_text)
        if irr_match:
            indicators["irr"] = float(irr_match.group(1))
            
        return indicators

