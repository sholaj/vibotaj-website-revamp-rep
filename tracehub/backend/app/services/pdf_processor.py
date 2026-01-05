"""PDF processing service for document extraction and analysis."""

import re
import logging
import tempfile
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

try:
    import fitz  # PyMuPDF
    PDF_PROCESSING_AVAILABLE = True
except ImportError:
    PDF_PROCESSING_AVAILABLE = False
    fitz = None

# OCR dependencies - optional
try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    pytesseract = None
    Image = None

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    convert_from_path = None

# Check if Tesseract is actually installed and accessible
OCR_AVAILABLE = False
TESSERACT_VERSION = None


def _initialize_ocr():
    """Initialize OCR and check if Tesseract is available.

    This function handles configuration of the tesseract command path
    and verifies that OCR is functional.
    """
    global OCR_AVAILABLE, TESSERACT_VERSION

    if not PYTESSERACT_AVAILABLE:
        return

    # Try to load config for custom tesseract path
    try:
        from ..config import get_settings
        settings = get_settings()
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    except Exception:
        pass  # Config not available or tesseract_cmd not set

    try:
        TESSERACT_VERSION = pytesseract.get_tesseract_version()
        OCR_AVAILABLE = PDF2IMAGE_AVAILABLE  # Both pytesseract and pdf2image needed
    except Exception:
        # Tesseract not installed or not in PATH
        pass


# Initialize OCR on module load
_initialize_ocr()

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
    # Horn & Hoof specific documents (HS 0506/0507)
    DocumentType.EU_TRACES_CERTIFICATE: [
        r'(?:TRACES|CHED)\s*(?:No\.?|#|:)?\s*[:\s]*([\w\d\.]+)',
        r'RC\d{7}',  # EU TRACES RC number format
        r'CHED-?(?:PP?|D)?\s*[:\s]*([\w\d\.]+)',
    ],
    DocumentType.VETERINARY_HEALTH_CERTIFICATE: [
        r'(?:VHC|VET)\s*(?:No\.?|#|:)?\s*[:\s]*([\w\d/]+)',
        r'(?:Veterinary|Animal)\s+Health\s*(?:Certificate)?\s*(?:No\.?|#|:)?\s*([\w\d/]+)',
        r'NVRI\s*[:\s]*([\w\d/]+)',  # Nigerian Veterinary Research Institute
    ],
    DocumentType.EXPORT_DECLARATION: [
        r'(?:NXP|EXP|SAD)\s*(?:No\.?|#|:)?\s*[:\s]*([\w\d]+)',
        r'(?:Export)\s*(?:Declaration)?\s*(?:No\.?|#|:)?\s*([\w\d]+)',
        r'Form\s+(?:NXP|E)\s*[:\s]*([\w\d]+)',
    ],
}

# Keywords for document type detection (ordered by specificity - more specific first)
DOCUMENT_KEYWORDS = {
    # Veterinary Health Certificate - MUST come before SANITARY_CERTIFICATE
    # Very specific keywords for Nigerian veterinary export documents
    DocumentType.VETERINARY_HEALTH_CERTIFICATE: [
        'veterinary certificate to eu', 'veterinary officer', 'ministry of agriculture',
        'animal by-product', 'products declaration', 'crushed hooves',
        'crushed horns', 'lagos state government', 'vvd/ls', 'chapter 18',
        'health certificate', 'veterinary health', 'animal health certificate',
        'hooves and horns', 'dried horns', 'dried hooves', 'bovine',
        'slaughtered', 'slaughter house', 'ante-mortem', 'bse risk'
    ],
    # EU TRACES Certificate - for animal products entering EU
    DocumentType.EU_TRACES_CERTIFICATE: [
        'traces', 'ched', 'common health entry document', 'eu traces',
        'ched-p', 'ched-d', 'entry bip', 'border inspection post',
        'third country', 'import permit', 'rc1479592', 'eu import'
    ],
    DocumentType.BILL_OF_LADING: [
        'bill of lading', 'b/l no', 'b/l:', 'shipper', 'consignee', 'notify party',
        'port of loading', 'port of discharge', 'ocean bill', 'carrier',
        'maersk', 'msc', 'hapag', 'cma cgm', 'freight collect', 'freight prepaid',
        'container said to contain', 'shipped on board', 'multimodal transport'
    ],
    DocumentType.CERTIFICATE_OF_ORIGIN: [
        'certificate of origin', 'country of origin', 'naccima',
        'nigerian association of chambers', 'chamber of commerce',
        'preferential origin', 'form a', 'goods produced in', 'wholly produced',
        'declaration by exporter', 'origin criterion', 'goods originate'
    ],
    DocumentType.PHYTOSANITARY_CERTIFICATE: [
        'phytosanitary', 'plant health', 'plant protection',
        'plant quarantine', 'fao', 'ippc', 'naqs', 'plant inspection'
    ],
    # Fumigation Certificate - specific keywords for fumigation/quality certs
    DocumentType.FUMIGATION_CERTIFICATE: [
        'fumigation', 'fumigated', 'fumigant applied', 'methyl bromide',
        'aluminium phosphide', 'pest control', 'treatment certificate',
        'federal produce inspection', 'certificate of quality, fumigation',
        'good packaging materials', 'quality analysis of export', 'date of fumigation'
    ],
    # Sanitary Certificate - more general health/sanitary certificates
    DocumentType.SANITARY_CERTIFICATE: [
        'sanitary certificate', 'sanitary and phytosanitary', 'sps certificate',
        'food safety', 'nafdac', 'son certificate', 'health clearance'
    ],
    DocumentType.COMMERCIAL_INVOICE: [
        'commercial invoice', 'invoice no', 'pro forma', 'sold to',
        'bill to', 'unit price', 'total amount', 'payment terms',
        'incoterms', 'fob', 'cif', 'cfr'
    ],
    DocumentType.PACKING_LIST: [
        'packing list', 'packing specification', 'net weight',
        'gross weight', 'package', 'cartons', 'pallets', 'container load'
    ],
    DocumentType.QUALITY_CERTIFICATE: [
        'quality certificate', 'inspection certificate', 'grade',
        'moisture content', 'specification', 'test report', 'lab analysis'
    ],
    DocumentType.INSURANCE_CERTIFICATE: [
        'insurance', 'insured', 'coverage', 'marine insurance',
        'cargo insurance', 'policy', 'sum insured', 'underwriter'
    ],
    DocumentType.CUSTOMS_DECLARATION: [
        'customs', 'import declaration', 'customs declaration',
        'hs code', 'tariff', 'duty', 'customs clearance'
    ],
    DocumentType.EXPORT_DECLARATION: [
        'export declaration', 'nxp', 'nxp form', 'customs export',
        'single administrative document', 'sad', 'export permit',
        'export license', 'nigeria customs', 'nes'
    ],
    DocumentType.CONTRACT: [
        'contract', 'agreement', 'terms and conditions', 'buyer',
        'seller', 'purchase order', 'sales contract'
    ],
    DocumentType.EUDR_DUE_DILIGENCE: [
        'eudr', 'due diligence', 'deforestation', 'geolocation',
        'traceability', 'deforestation-free', 'eu regulation 2023/1115'
    ],
}


class PDFProcessor:
    """Service for processing PDF documents and extracting content."""

    # Minimum characters to consider text extraction successful (skip OCR if above this)
    MIN_TEXT_THRESHOLD = 100

    # Default OCR configuration (can be overridden by settings)
    OCR_DPI = 300  # DPI for PDF to image conversion
    OCR_TIMEOUT = 30  # Timeout per page in seconds
    OCR_LANGUAGE = "eng"  # Tesseract language
    OCR_ENABLED = True  # Whether OCR fallback is enabled

    def __init__(self):
        if not PDF_PROCESSING_AVAILABLE:
            logger.warning("PyMuPDF not installed. PDF processing will be limited.")

        # Load OCR settings from config if available
        try:
            from ..config import get_settings
            settings = get_settings()
            self.OCR_DPI = settings.ocr_dpi
            self.OCR_TIMEOUT = settings.ocr_timeout
            self.OCR_LANGUAGE = settings.ocr_language
            self.OCR_ENABLED = settings.ocr_enabled
        except Exception:
            pass  # Use defaults if config not available

        if OCR_AVAILABLE:
            logger.info(f"OCR available. Tesseract version: {TESSERACT_VERSION}")
            if not self.OCR_ENABLED:
                logger.info("OCR fallback is disabled via configuration")
        else:
            if not PYTESSERACT_AVAILABLE:
                logger.warning("pytesseract not installed. OCR will not be available.")
            elif not PDF2IMAGE_AVAILABLE:
                logger.warning("pdf2image not installed. OCR will not be available.")
            else:
                logger.warning("Tesseract not installed or not in PATH. OCR will not be available.")

    def is_available(self) -> bool:
        """Check if PDF processing is available."""
        return PDF_PROCESSING_AVAILABLE

    def is_ocr_available(self) -> bool:
        """Check if OCR processing is available."""
        return OCR_AVAILABLE

    def get_ocr_status(self) -> Dict[str, Any]:
        """Get detailed OCR availability status."""
        return {
            "available": OCR_AVAILABLE,
            "pytesseract_installed": PYTESSERACT_AVAILABLE,
            "pdf2image_installed": PDF2IMAGE_AVAILABLE,
            "tesseract_version": str(TESSERACT_VERSION) if TESSERACT_VERSION else None,
            "ocr_language": self.OCR_LANGUAGE if OCR_AVAILABLE else None,
        }

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

    def _extract_text_with_ocr_single_page(self, image) -> str:
        """Extract text from a single page image using OCR.

        Args:
            image: PIL Image object

        Returns:
            Extracted text string
        """
        if not OCR_AVAILABLE:
            return ""

        try:
            # Use pytesseract to extract text
            text = pytesseract.image_to_string(
                image,
                lang=self.OCR_LANGUAGE,
                timeout=self.OCR_TIMEOUT,
                config='--psm 1'  # Automatic page segmentation with OSD
            )
            return text.strip()
        except Exception as e:
            logger.error(f"OCR extraction failed for page: {e}")
            return ""

    def extract_text_with_ocr(self, file_path: str) -> List[PageContent]:
        """Extract text from PDF using OCR.

        Converts each PDF page to an image and uses Tesseract OCR
        to extract text. This is useful for scanned PDFs that have
        no embedded text.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of PageContent objects with OCR-extracted text
        """
        if not OCR_AVAILABLE:
            logger.warning("OCR not available. Cannot extract text from scanned PDF.")
            return []

        pages = []
        try:
            logger.info(f"Starting OCR extraction for: {file_path}")

            # Convert PDF pages to images
            images = convert_from_path(
                file_path,
                dpi=self.OCR_DPI,
                fmt='png'
            )

            logger.info(f"Converted PDF to {len(images)} images for OCR")

            for page_num, image in enumerate(images, start=1):
                logger.debug(f"Processing OCR for page {page_num}")

                # Extract text using OCR
                text = self._extract_text_with_ocr_single_page(image)

                pages.append(PageContent(
                    page_number=page_num,
                    text=text,
                    char_count=len(text)
                ))

                logger.debug(f"Page {page_num} OCR extracted {len(text)} characters")

            total_chars = sum(p.char_count for p in pages)
            logger.info(f"OCR extraction complete. Total characters: {total_chars}")

        except Exception as e:
            logger.error(f"Error during OCR extraction: {e}")

        return pages

    def _is_scanned_pdf(self, pages: List[PageContent]) -> bool:
        """Determine if a PDF is likely scanned (image-only).

        Args:
            pages: List of PageContent from normal text extraction

        Returns:
            True if the PDF appears to be scanned/image-only
        """
        if not pages:
            return True

        total_chars = sum(p.char_count for p in pages)
        return total_chars < self.MIN_TEXT_THRESHOLD

    def extract_text(self, file_path: str, use_ocr_fallback: bool = True) -> List[PageContent]:
        """Extract text content from all pages of a PDF.

        First attempts normal text extraction using PyMuPDF.
        If the PDF appears to be scanned (minimal text extracted),
        falls back to OCR if available and enabled.

        Args:
            file_path: Path to the PDF file
            use_ocr_fallback: Whether to use OCR for scanned PDFs (default: True)

        Returns:
            List of PageContent objects with extracted text
        """
        if not PDF_PROCESSING_AVAILABLE:
            return []

        pages = []
        extraction_method = "pymupdf"

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

            total_chars = sum(p.char_count for p in pages)
            logger.info(f"PyMuPDF extracted {total_chars} characters from {len(pages)} pages")

            # Check if OCR fallback is needed
            if use_ocr_fallback and self.OCR_ENABLED and self._is_scanned_pdf(pages):
                if OCR_AVAILABLE:
                    logger.info(
                        f"Document appears to be scanned (only {total_chars} chars). "
                        f"Attempting OCR extraction..."
                    )
                    ocr_pages = self.extract_text_with_ocr(file_path)

                    if ocr_pages:
                        ocr_total_chars = sum(p.char_count for p in ocr_pages)
                        # Use OCR result if it extracted more text
                        if ocr_total_chars > total_chars:
                            logger.info(
                                f"OCR extraction successful. "
                                f"Using OCR result ({ocr_total_chars} chars vs {total_chars} chars)"
                            )
                            pages = ocr_pages
                            extraction_method = "ocr"
                        else:
                            logger.info(
                                f"OCR did not improve extraction. "
                                f"Keeping original ({total_chars} chars vs OCR {ocr_total_chars} chars)"
                            )
                else:
                    logger.warning(
                        f"Document appears to be scanned (only {total_chars} chars) "
                        f"but OCR is not available. Text extraction may be incomplete."
                    )

        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")

        # Log final extraction info
        final_chars = sum(p.char_count for p in pages)
        logger.debug(f"Text extraction complete using {extraction_method}: {final_chars} total characters")

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

        # Strong document start indicators (titles/headers that indicate new document)
        doc_start_patterns = [
            r'bill of lading',
            r'certificate of origin',
            r'phytosanitary certificate',
            r'veterinary certificate',
            r'health certificate',
            r'commercial invoice',
            r'fumigation certificate',
            r'certificate of quality.*fumigation',
            r'federal ministry of industry',
            r'federal produce inspection',
            r'nigerian association of chambers',
            r'quality certificate',
            r'insurance certificate',
            r'packing list',
            r'export declaration',
            r'customs declaration',
        ]

        for i, page in enumerate(pages):
            page_num = page.page_number

            # Check if this page likely starts a new document
            if i > 0:
                # Look for strong indicators of a new document
                text_lower = page.text.lower()[:800]  # Check more text

                # Check for document start patterns
                is_new_doc = False
                for pattern in doc_start_patterns:
                    if re.search(pattern, text_lower):
                        # Verify it's near the start of the page (first 300 chars)
                        early_text = text_lower[:300]
                        if re.search(pattern, early_text):
                            is_new_doc = True
                            break

                # Also check for page 1 indicator
                if text_lower.strip().startswith('page 1') or 'page: 1' in text_lower[:100]:
                    is_new_doc = True

                if is_new_doc:
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

            # Create section - use more text for AI classification (4000 chars)
            sections.append(DocumentSection(
                document_type=doc_type,
                page_start=start_page,
                page_end=end_page,
                text_preview=section_text[:4000],  # Increased from 500 for better AI classification
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
