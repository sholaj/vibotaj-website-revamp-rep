"""Tests for shipment-level compliance aggregation (PRD-016).

Verifies the compliance decision logic: APPROVE/HOLD/REJECT based
on document states, issues, and overrides.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from uuid import uuid4
from datetime import datetime

from app.models import DocumentStatus
from app.services.compliance_aggregation import (
    get_compliance_decision,
    get_compliance_summary,
)


def make_doc(status: DocumentStatus, issues=None):
    """Helper to create a mock document with given status and issues."""
    doc = MagicMock()
    doc.id = uuid4()
    doc.status = status
    doc.issues = issues or []
    doc.document_type = MagicMock()
    doc.document_type.value = "bill_of_lading"
    return doc


def make_issue(severity="ERROR", is_overridden=False):
    """Helper to create a mock document issue."""
    issue = MagicMock()
    issue.severity = severity
    issue.is_overridden = is_overridden
    issue.rule_id = "TEST-001"
    issue.rule_name = "Test Rule"
    issue.message = "Test failure"
    issue.field = None
    issue.source_document_type = "bill_of_lading"
    issue.created_at = datetime(2026, 2, 16, 10, 0, 0)
    issue.override_reason = None
    return issue


def make_shipment(override_reason=None):
    """Helper to create a mock shipment."""
    shipment = MagicMock()
    shipment.id = uuid4()
    shipment.organization_id = uuid4()
    shipment.validation_override_reason = override_reason
    shipment.validation_override_by = "admin@vibotaj.com" if override_reason else None
    shipment.validation_override_at = datetime.utcnow() if override_reason else None
    return shipment


class TestGetComplianceDecision:
    """Tests for get_compliance_decision."""

    def test_approve_when_all_docs_compliance_ok(self):
        """APPROVE when all documents have COMPLIANCE_OK or LINKED status."""
        shipment = make_shipment()
        docs = [
            make_doc(DocumentStatus.COMPLIANCE_OK),
            make_doc(DocumentStatus.LINKED),
        ]
        db = MagicMock()

        assert get_compliance_decision(shipment, docs, db) == "APPROVE"

    def test_hold_when_no_documents(self):
        """HOLD when shipment has no documents."""
        shipment = make_shipment()
        db = MagicMock()

        assert get_compliance_decision(shipment, [], db) == "HOLD"

    def test_hold_when_docs_pending(self):
        """HOLD when some documents are still in UPLOADED/VALIDATED state."""
        shipment = make_shipment()
        docs = [
            make_doc(DocumentStatus.COMPLIANCE_OK),
            make_doc(DocumentStatus.UPLOADED),
        ]
        db = MagicMock()

        assert get_compliance_decision(shipment, docs, db) == "HOLD"

    def test_hold_when_docs_in_draft(self):
        """HOLD when some documents are still in DRAFT state."""
        shipment = make_shipment()
        docs = [make_doc(DocumentStatus.DRAFT)]
        db = MagicMock()

        assert get_compliance_decision(shipment, docs, db) == "HOLD"

    def test_reject_when_compliance_failed_with_errors(self):
        """REJECT when a document has COMPLIANCE_FAILED with unresolved errors."""
        shipment = make_shipment()
        error_issue = make_issue(severity="ERROR", is_overridden=False)
        docs = [
            make_doc(DocumentStatus.COMPLIANCE_OK),
            make_doc(DocumentStatus.COMPLIANCE_FAILED, issues=[error_issue]),
        ]
        db = MagicMock()

        assert get_compliance_decision(shipment, docs, db) == "REJECT"

    def test_hold_when_compliance_failed_but_errors_overridden(self):
        """HOLD (not REJECT) when all errors on failed doc are overridden."""
        shipment = make_shipment()
        overridden_issue = make_issue(severity="ERROR", is_overridden=True)
        docs = [
            make_doc(DocumentStatus.COMPLIANCE_FAILED, issues=[overridden_issue]),
        ]
        db = MagicMock()

        assert get_compliance_decision(shipment, docs, db) == "HOLD"

    def test_approve_when_shipment_has_override(self):
        """APPROVE when shipment has admin override, regardless of doc states."""
        shipment = make_shipment(override_reason="Admin approved manually")
        error_issue = make_issue(severity="ERROR", is_overridden=False)
        docs = [
            make_doc(DocumentStatus.COMPLIANCE_FAILED, issues=[error_issue]),
        ]
        db = MagicMock()

        assert get_compliance_decision(shipment, docs, db) == "APPROVE"

    def test_approve_with_archived_docs(self):
        """APPROVE when documents are in terminal ARCHIVED state."""
        shipment = make_shipment()
        docs = [make_doc(DocumentStatus.ARCHIVED)]
        db = MagicMock()

        assert get_compliance_decision(shipment, docs, db) == "APPROVE"


class TestGetComplianceSummary:
    """Tests for get_compliance_summary."""

    def test_summary_structure(self):
        """Summary returns expected keys."""
        shipment = make_shipment()
        docs = [make_doc(DocumentStatus.COMPLIANCE_OK)]
        db = MagicMock()
        # Mock empty results for compliance queries
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = []

        result = get_compliance_summary(shipment, docs, db)

        assert "shipment_id" in result
        assert "decision" in result
        assert "summary" in result
        assert "results" in result
        assert "override" in result
        assert result["summary"]["total_rules"] >= 0

    def test_summary_with_override(self):
        """Summary includes override info when present."""
        shipment = make_shipment(override_reason="Manual approval")
        docs = []
        db = MagicMock()
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = []

        result = get_compliance_summary(shipment, docs, db)

        assert result["override"] is not None
        assert result["override"]["reason"] == "Manual approval"
        assert result["decision"] == "APPROVE"

    def test_summary_without_override(self):
        """Summary has null override when none set."""
        shipment = make_shipment()
        docs = [make_doc(DocumentStatus.COMPLIANCE_OK)]
        db = MagicMock()
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = []

        result = get_compliance_summary(shipment, docs, db)

        assert result["override"] is None
