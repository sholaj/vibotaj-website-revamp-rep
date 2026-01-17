"""Validation context for document rules.

The ValidationContext provides all data needed by validation rules:
- Shipment information
- Documents with their AI classification results
- Required document types based on product type
- Indexed lookups for efficient access
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from collections import defaultdict
from uuid import UUID

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from ...models import Shipment, Document, DocumentContent
    from ...models.document import DocumentType
    from ...models.shipment import ProductType


@dataclass
class DocumentClassification:
    """AI classification result for a document.

    Attributes:
        document_type: The AI-detected document type
        confidence: Confidence score (0.0 to 1.0)
        detected_fields: Fields extracted by AI
        reasoning: AI explanation for the classification
    """
    document_type: Optional["DocumentType"] = None
    confidence: float = 0.0
    detected_fields: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""


@dataclass
class DocumentWithClassification:
    """Document paired with its AI classification result.

    Used in ValidationContext to provide easy access to both
    the document record and its AI analysis.
    """
    document: "Document"
    classification: Optional[DocumentClassification] = None

    @property
    def confidence_score(self) -> float:
        """Get the confidence score from classification."""
        if self.classification:
            return self.classification.confidence
        return 0.0


@dataclass
class ValidationContext:
    """Context passed to each validation rule.

    This is the primary data structure that rules use to access
    shipment and document information. It provides:

    - Direct access to shipment and documents
    - Indexed lookups by document type
    - AI classification data for relevance checking
    - Required document types based on product type

    Example:
        context = ValidationContext.from_shipment(shipment, documents, db=db)

        # Check if BOL exists
        bols = context.documents_by_type.get(DocumentType.BILL_OF_LADING, [])

        # Check AI confidence for a document
        doc_id = str(document.id)
        if doc_id in context.classifications:
            confidence = context.classifications[doc_id].confidence_score
    """
    shipment: "Shipment"
    documents: List["Document"]
    product_type: Optional["ProductType"]
    required_document_types: List["DocumentType"]

    # Indexed for efficient lookups
    documents_by_type: Dict["DocumentType", List["Document"]] = field(default_factory=dict)
    document_count_by_type: Dict["DocumentType", int] = field(default_factory=dict)

    # AI classification data
    classifications: Dict[str, DocumentWithClassification] = field(default_factory=dict)
    ai_available: bool = False

    @classmethod
    def from_shipment(
        cls,
        shipment: "Shipment",
        documents: List["Document"],
        document_contents: Optional[Dict[str, "DocumentContent"]] = None,
        db: Optional["Session"] = None,
    ) -> "ValidationContext":
        """Factory method to create context from shipment.

        Args:
            shipment: The shipment being validated
            documents: List of documents attached to shipment
            document_contents: Pre-loaded DocumentContent records (optional)
            db: Database session for loading content if not provided

        Returns:
            ValidationContext ready for rule execution
        """
        from ...models.document import DocumentType
        from ...models.document_content import DocumentContent as DocumentContentModel
        from ..compliance import get_required_documents_by_product_type

        # Index documents by type
        docs_by_type: Dict[DocumentType, List] = defaultdict(list)
        for doc in documents:
            docs_by_type[doc.document_type].append(doc)

        # Get required document types for this product
        required_types = []
        if shipment.product_type:
            try:
                required_types = get_required_documents_by_product_type(shipment.product_type)
            except Exception:
                # If compliance service unavailable, use empty list
                required_types = []

        # Build classification data from stored results
        classifications: Dict[str, DocumentWithClassification] = {}
        ai_available = False

        # Try to check AI availability
        try:
            from ..document_classifier import document_classifier
            ai_available = document_classifier.is_ai_available()
        except Exception:
            pass

        for doc in documents:
            doc_id = str(doc.id)
            doc_with_class = DocumentWithClassification(document=doc)

            # Try to get stored classification from DocumentContent
            content = None
            if document_contents and doc_id in document_contents:
                content = document_contents[doc_id]
            elif db:
                try:
                    content = db.query(DocumentContentModel).filter(
                        DocumentContentModel.document_id == doc.id
                    ).first()
                except Exception:
                    pass

            if content and content.confidence_score is not None:
                doc_with_class.classification = DocumentClassification(
                    document_type=content.document_type if hasattr(content, 'document_type') else doc.document_type,
                    confidence=content.confidence_score or 0.0,
                    detected_fields=content.detected_fields or {},
                    reasoning=content.detected_fields.get("ai_reasoning", "") if content.detected_fields else "",
                )

            classifications[doc_id] = doc_with_class

        return cls(
            shipment=shipment,
            documents=documents,
            product_type=shipment.product_type,
            required_document_types=required_types,
            documents_by_type=dict(docs_by_type),
            document_count_by_type={k: len(v) for k, v in docs_by_type.items()},
            classifications=classifications,
            ai_available=ai_available,
        )

    def get_documents_of_type(self, doc_type: "DocumentType") -> List["Document"]:
        """Get all documents of a specific type."""
        return self.documents_by_type.get(doc_type, [])

    def has_document_type(self, doc_type: "DocumentType") -> bool:
        """Check if at least one document of this type exists."""
        return doc_type in self.documents_by_type and len(self.documents_by_type[doc_type]) > 0

    def get_classification(self, document_id: str) -> Optional[DocumentWithClassification]:
        """Get classification data for a specific document."""
        return self.classifications.get(document_id)
