"""PDF processing service for document extraction and analysis."""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

try:
    import fitz  # PyMuPDF
    PDF_PROCESSING_AVAILABLE = True
except ImportError:
    PDF_PROCESSING_AVAILABLE = False
    fitz = None

from ..models.document import DocumentType

logger = logging.getLogger(__name__)


@dataclass
class PageContent:
    """Extracted content from a PDF page."""
    page_number: int
    text: str
    char_count: int


@dataclass
class DocumentSection:
    """A detected document section within a PDF."""
    document_type: Optional[DocumentType]
    page_start: int
    page_end: int
    text_preview: str  # First 500 chars
    reference_number: Optional[str]
    confidence: float  # 0.0 - 1.0
    detection_method: str  # "keyword", "ai", "manual"
    detected_fields: Dict[str, Any]


# Reference number patterns for common document types
REFERENCE_PATTERNS = {
    DocumentType.BILL_OF_LADING: [
        r'B/L\s*(?:No\.?|#|:)?\s*[:\s]*(\d{6,})',
        r'Bill\s+of\s+Lading\s*(?:No\.?|#|:)?\s*[:\s]*(\d{6,})',
        r'BL\s*(?:No\.?|#|:)?\s*[:\s]*(\d{6,})',
        r'MSKU\d+',  # Maersk container prefix
    ],
    DocumentType.CERTIFICATE_OF_ORIGIN: [
        r'(?:NACCIMA|C/O|COO)\s*(?:No\.?|#|:)?\s*[:\s]*([\w\d]+)',
        r'Certificate\s+(?:of\s+)?Origin\s*(?:No\.?|#|:)?\s*[:\s]*([\w\d]+)',
        r'FORM\s+[A-Z]\s*(?:No\.?|#|:)?\s*([\w\d]+)',
    ],
    DocumentType.PHYTOSANITARY_CERTIFICATE: [
        r'(?:FPI|PHYTO|PC)\s*(?:No\.?|#|:)?\s*[:\s]*([\w\d]+)',
        r'Phytosanitary\s*(?:Certificate)?\s*(?:No\.?|#|:)?\s*([\w\d]+)',
    ],
    DocumentType.FUMIGATION_CERTIFICATE: [
        r'(?:FUM|FC)\s*(?:No\.?|#|:)?\s*[:\s]*([\w\d]+)',
        r'Fumigation\s*(?:Certificate)?\s*(?:No\.?|#|:)?\s*([\w\d]+)',
    ],
    DocumentType.SANITARY_CERTIFICATE: [
        r'(?:VVD|VET|SC)\s*[/#]?\s*([\w\d/]+)',
        r'(?:Veterinary|Health|Sanitary)\s*(?:Certificate)?\s*(?:No\.?|#|:)?\s*([\w\d/]+)',
    ],
    DocumentType.COMMERCIAL_INVOICE: [
        r'(?:Invoice|INV)\s*(?:No\.?|#|:)?\s*[:\s]*([\w\d-]+)',
        r'(?:PI|CI)\s*(?:No\.?|#|:)?\s*[:\s]*([\w\d-]+)',
    ],
    DocumentType.QUALITY_CERTIFICATE: [
        r'(?:QC|QUALITY)\s*(?:No\.?|#|:)?\s*[:\s]*([\w\d]+)',
        r'(?:Inspection|Quality)\s*(?:Certificate)?\s*(?:No\.?|#|:)?\s*([\w\d]+)',
    ],
}

# Keywords for document type detection
DOCUMENT_KEYWORDS = {
    DocumentType.BILL_OF_LADING: [
        'bill of lading', 'b/l', 'shipper', 'consignee', 'notify party',
        'port of loading', 'port of discharge', 'ocean bill', 'carrier'
    ],
    DocumentType.CERTIFICATE_OF_ORIGIN: [
        'certificate of origin', 'country of origin', 'naccima',
        'chamber of commerce', 'preferential origin', 'form a'
    ],
    DocumentType.PHYTOSANITARY_CERTIFICATE: [
        'phytosanitary', 'plant health', 'plant protection',
        'plant quarantine', 'fao', 'ippc'
    ],
    DocumentType.FUMIGATION_CERTIFICATE: [
        'fumigation', 'fumigated', 'methyl bromide', 'pest control',
        'treatment certificate'
    ],
    DocumentType.SANITARY_CERTIFICATE: [
        'veterinary', 'health certificate', 'sanitary', 'animal health',
        'official veterinarian', 'chapter 18', 'eu health'
    ],
    DocumentType.COMMERCIAL_INVOICE: [
        'commercial invoice', 'invoice', 'pro forma', 'sold to',
        'bill to', 'unit price', 'total amount'
    ],
    DocumentType.PACKING_LIST: [
        'packing list', 'packing specification', 'net weight',
        'gross weight', 'package', 'cartons', 'pallets'
    ],
    DocumentType.QUALITY_CERTIFICATE: [
        'quality certificate', 'inspection certificate', 'grade',
        'moisture content', 'specification', 'test report'
    ],
    DocumentType.INSURANCE_CERTIFICATE: [
        'insurance', 'insured', 'coverage', 'marine insurance',
        'cargo insurance', 'policy'
    ],
    DocumentType.CUSTOMS_DECLARATION: [
        'customs', 'export declaration', 'import declaration',
        'customs declaration', 'hs code', 'tariff'
    ],
    DocumentType.CONTRACT: [
        'contract', 'agreement', 'terms and conditions', 'buyer',
        'seller', 'purchase order'
    ],
    DocumentType.EUDR_DUE_DILIGENCE: [
        'eudr', 'due diligence', 'deforestation', 'geolocation',
        'traceability', 'deforestation-free'
    ],
}


class PDFProcessor:
    """Service for processing PDF documents and extracting content."""

    def __init__(self):
        if not PDF_PROCESSING_AVAILABLE:
            logger.warning("PyMuPDF not installed. PDF processing will be limited.")

    def is_available(self) -> bool:
        """Check if PDF processing is available."""
        return PDF_PROCESSING_AVAILABLE

    def get_page_count(self, file_path: str) -> int:
        """Get the number of pages in a PDF."""
        if not PDF_PROCESSING_AVAILABLE:
            return 0

        try:
            doc = fitz.open(file_path)
            count = len(doc)
            doc.close()
            return count
        except Exception as e:
            logger.error(f"Error getting page count: {e}")
            return 0

    def extract_text(self, file_path: str) -> List[PageContent]:
        """Extract text content from all pages of a PDF."""
        if not PDF_PROCESSING_AVAILABLE:
            return []

        pages = []
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                pages.append(PageContent(
                    page_number=page_num + 1,  # 1-indexed
                    text=text,
                    char_count=len(text)
                ))
            doc.close()
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")

        return pages

    def extract_reference_number(self, text: str, doc_type: DocumentType) -> Optional[str]:
        """Extract reference number from text based on document type."""
        patterns = REFERENCE_PATTERNS.get(doc_type, [])

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Return the captured group if exists, otherwise full match
                return match.group(1) if match.lastindex else match.group(0)

        return None

    def detect_document_type_by_keywords(self, text: str) -> List[Tuple[DocumentType, float]]:
        """Detect document type based on keyword matching.

        Returns list of (DocumentType, confidence) tuples sorted by confidence.
        """
        text_lower = text.lower()
        scores = {}

        for doc_type, keywords in DOCUMENT_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                # Confidence based on percentage of keywords matched
                confidence = min(matches / len(keywords), 1.0)
                # Boost confidence if multiple keywords match
                if matches >= 3:
                    confidence = min(confidence + 0.2, 1.0)
                scores[doc_type] = confidence

        # Sort by confidence descending
        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_types

    def detect_document_boundaries(self, pages: List[PageContent]) -> List[Tuple[int, int]]:
        """Detect where different documents start and end within a PDF.

        Returns list of (start_page, end_page) tuples.
        """
        if not pages:
            return []

        boundaries = []
        current_start = 1

        for i, page in enumerate(pages):
            page_num = page.page_number

            # Check if this page likely starts a new document
            if i > 0:
                # Look for strong indicators of a new document
                text_lower = page.text.lower()[:500]

                new_doc_indicators = [
                    'bill of lading' in text_lower,
                    'certificate of origin' in text_lower,
                    'phytosanitary certificate' in text_lower,
                    'veterinary certificate' in text_lower,
                    'health certificate' in text_lower,
                    'commercial invoice' in text_lower,
                    text_lower.strip().startswith('page 1'),
                ]

                if any(new_doc_indicators):
                    # End previous section
                    if current_start < page_num:
                        boundaries.append((current_start, page_num - 1))
                    current_start = page_num

        # Add final section
        if pages:
            boundaries.append((current_start, pages[-1].page_number))

        return boundaries

    def analyze_pdf(self, file_path: str) -> List[DocumentSection]:
        """Analyze a PDF and detect all documents within it.

        This is the main method for processing combined PDFs.
        """
        if not PDF_PROCESSING_AVAILABLE:
            return []

        # Extract text from all pages
        pages = self.extract_text(file_path)
        if not pages:
            return []

        # Detect document boundaries
        boundaries = self.detect_document_boundaries(pages)

        sections = []
        for start_page, end_page in boundaries:
            # Combine text from all pages in this section
            section_text = ""
            for page in pages:
                if start_page <= page.page_number <= end_page:
                    section_text += page.text + "\n"

            # Detect document type
            type_scores = self.detect_document_type_by_keywords(section_text)

            if type_scores:
                doc_type, confidence = type_scores[0]
            else:
                doc_type = DocumentType.OTHER
                confidence = 0.0

            # Extract reference number
            ref_number = self.extract_reference_number(section_text, doc_type) if doc_type else None

            # Create section
            sections.append(DocumentSection(
                document_type=doc_type,
                page_start=start_page,
                page_end=end_page,
                text_preview=section_text[:500],
                reference_number=ref_number,
                confidence=confidence,
                detection_method="keyword",
                detected_fields={
                    "page_count": end_page - start_page + 1,
                    "char_count": len(section_text),
                    "alternative_types": [
                        {"type": t.value, "confidence": c}
                        for t, c in type_scores[1:4]  # Include top 3 alternatives
                    ] if len(type_scores) > 1 else []
                }
            ))

        return sections


# Global instance
pdf_processor = PDFProcessor()
