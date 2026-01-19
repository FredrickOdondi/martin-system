"""
LLM-powered document analyzer for AfCEN scoring.

Uses GitHub Models to analyze extracted document text and return structured data
for the scoring algorithm.
"""

import logging
from typing import Dict, Any, Optional
import json
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class DocumentAnalyzer:
    """
    Analyzes document content using LLM to extract structured scoring data.
    """
    
    def __init__(self):
        self.llm_client = get_llm_service()
    
    async def analyze_document(self, text: str, filename: str) -> Dict[str, Any]:
        """
        Analyze document text using LLM to extract scoring indicators.
        
        Args:
            text: Extracted document text
            filename: Original filename for context
            
        Returns:
            Dictionary with scoring indicators
        """
        # Truncate text if too long (LLM context limits)
        max_chars = 15000  # ~4000 tokens
        if len(text) > max_chars:
            logger.warning(f"Truncating document text from {len(text)} to {max_chars} characters")
            text = text[:max_chars] + "\n\n[... document truncated ...]"
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(text, filename)
        
        try:
            # Call LLM
            # Note: chat() is synchronous so we run it directly (may block briefly)
            # or we could use run_in_threadpool if needed. 
            # For now, simplistic approach as per existing patterns.
            response = self.llm_client.chat(
                prompt=prompt,
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=1000
            )
            
            # Parse JSON response
            analysis = self._parse_llm_response(response)
            
            logger.info(f"✓ LLM analysis complete for {filename}: {analysis}")
            return analysis
            
        except Exception as e:
            logger.error(f"LLM analysis failed for {filename}: {e}")
            # Fall back to heuristic analysis
            return self._fallback_heuristic_analysis(text, filename)
    
    def _build_analysis_prompt(self, text: str, filename: str) -> str:
        """Build the LLM prompt for document analysis."""
        return f"""You are analyzing a project document for investment readiness scoring.

**Document:** {filename}

**Task:** Extract the following information from the document text and return as JSON:

1. **document_type**: Identify the type (feasibility_study, esia, financial_model, government_support, technical_spec, or other)
2. **has_feasibility_study**: Boolean - Does this contain feasibility analysis?
3. **has_esia**: Boolean - Does this contain Environmental & Social Impact Assessment?
4. **has_financial_model**: Boolean - Does this contain financial projections/models?
5. **has_government_support**: Boolean - Is this a government support letter or does it mention government backing?
6. **has_permits**: Boolean - Does it mention permits, licenses, or regulatory approvals?
7. **has_site_control**: Boolean - Does it mention land access, site control, or property rights?
8. **irr_percentage**: Float or null - Extract Internal Rate of Return (IRR) if mentioned
9. **npv_value**: Float or null - Extract Net Present Value (NPV) if mentioned
10. **cross_border_impact**: Boolean - Does it mention cross-border, regional integration, or multi-country benefits?
11. **esg_compliant**: Boolean - Does it address ESG (Environmental, Social, Governance) standards?
12. **technical_viability_score**: Integer 0-10 - Rate technical feasibility if assessable
13. **confidence**: Float 0-1 - Your confidence in this analysis

**Document Text:**
```
{text}
```

**IMPORTANT:** Return ONLY valid JSON, no markdown formatting. Example:
{{
    "document_type": "feasibility_study",
    "has_feasibility_study": true,
    "has_esia": false,
    "has_financial_model": true,
    "has_government_support": false,
    "has_permits": true,
    "has_site_control": true,
    "irr_percentage": 15.2,
    "npv_value": 45000000,
    "cross_border_impact": true,
    "esg_compliant": true,
    "technical_viability_score": 8,
    "confidence": 0.85
}}"""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM JSON response."""
        try:
            # Remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            # Parse JSON
            data = json.loads(response)
            
            # Validate required fields
            required_fields = [
                "document_type", "has_feasibility_study", "has_esia",
                "has_financial_model", "has_government_support"
            ]
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing field in LLM response: {field}")
                    data[field] = False if field.startswith("has_") else None
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Raw response: {response}")
            raise
    
    def _fallback_heuristic_analysis(self, text: str, filename: str) -> Dict[str, Any]:
        """
        Fallback heuristic analysis if LLM fails.
        Uses simple keyword matching.
        """
        logger.warning(f"Using fallback heuristic analysis for {filename}")
        
        lower_text = text.lower()
        lower_filename = filename.lower()
        
        return {
            "document_type": self._guess_document_type(lower_filename, lower_text),
            "has_feasibility_study": "feasibility" in lower_text or "feasibility" in lower_filename,
            "has_esia": "esia" in lower_text or "environmental" in lower_text or "esia" in lower_filename,
            "has_financial_model": "financial" in lower_text or "irr" in lower_text or "financial" in lower_filename,
            "has_government_support": "government" in lower_text or "ministry" in lower_text or "support" in lower_filename,
            "has_permits": "permit" in lower_text or "license" in lower_text,
            "has_site_control": "land" in lower_text or "site" in lower_text,
            "irr_percentage": self._extract_irr(lower_text),
            "npv_value": None,
            "cross_border_impact": "cross-border" in lower_text or "regional" in lower_text,
            "esg_compliant": "esg" in lower_text,
            "technical_viability_score": 5,  # Neutral score
            "confidence": 0.3  # Low confidence for heuristic
        }
    
    def _guess_document_type(self, filename: str, text: str) -> str:
        """Guess document type from filename and content."""
        if "feasibility" in filename or "feasibility" in text:
            return "feasibility_study"
        elif "esia" in filename or "environmental" in text:
            return "esia"
        elif "financial" in filename or "financial model" in text:
            return "financial_model"
        elif "government" in filename or "support" in filename:
            return "government_support"
        else:
            return "other"
    
    def _extract_irr(self, text: str) -> Optional[float]:
        """Extract IRR percentage from text."""
        import re
        match = re.search(r"irr.*?(\d+(?:\.\d+)?)%", text)
        if match:
            return float(match.group(1))
        return None


# Singleton instance
_analyzer: Optional[DocumentAnalyzer] = None

def get_document_analyzer() -> DocumentAnalyzer:
    """Get or create the document analyzer singleton."""
    global _analyzer
    if _analyzer is None:
        _analyzer = DocumentAnalyzer()
    return _analyzer
