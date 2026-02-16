"""Tests for document transition persistence (PRD-016).

Verifies that state transitions are persisted to document_transitions
table with actor, reason, and timestamp tracking.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.models import DocumentStatus
from app.models.document_transition import DocumentTransition
from app.services.workflow import (
    persist_transition,
    transition_document,
    get_transition_history,
    TransitionResult,
)


class TestPersistTransition:
    """Tests for the persist_transition function."""

    def test_persist_transition_creates_record(self):
        """persist_transition creates a DocumentTransition record."""
        db = MagicMock()
        doc = MagicMock()
        doc.id = uuid4()
        doc.organization_id = uuid4()
        actor_id = uuid4()

        result = persist_transition(
            db=db,
            document=doc,
            from_state=DocumentStatus.DRAFT,
            to_state=DocumentStatus.UPLOADED,
            actor_id=actor_id,
            reason="File uploaded",
        )

        assert isinstance(result, DocumentTransition)
        assert result.document_id == doc.id
        assert result.from_state == "DRAFT"
        assert result.to_state == "UPLOADED"
        assert result.actor_id == actor_id
        assert result.reason == "File uploaded"
        assert result.organization_id == doc.organization_id
        db.add.assert_called_once_with(result)

    def test_persist_transition_with_metadata(self):
        """persist_transition stores metadata dict."""
        db = MagicMock()
        doc = MagicMock()
        doc.id = uuid4()
        doc.organization_id = uuid4()

        meta = {"auto_validated": True, "runner_version": "1.0"}
        result = persist_transition(
            db=db,
            document=doc,
            from_state=DocumentStatus.UPLOADED,
            to_state=DocumentStatus.VALIDATED,
            metadata=meta,
        )

        assert result.metadata == meta

    def test_persist_transition_without_actor(self):
        """persist_transition works with system transitions (no actor)."""
        db = MagicMock()
        doc = MagicMock()
        doc.id = uuid4()
        doc.organization_id = uuid4()

        result = persist_transition(
            db=db,
            document=doc,
            from_state=DocumentStatus.UPLOADED,
            to_state=DocumentStatus.VALIDATED,
        )

        assert result.actor_id is None


class TestTransitionDocumentPersistence:
    """Tests that transition_document persists when db is provided."""

    @patch("app.services.workflow.validate_document")
    def test_transition_persists_when_db_provided(self, mock_validate):
        """Successful transition is persisted when db session given."""
        db = MagicMock()
        doc = MagicMock()
        doc.id = uuid4()
        doc.status = DocumentStatus.DRAFT
        doc.organization_id = uuid4()
        user_id = uuid4()

        result = transition_document(
            document=doc,
            target_status=DocumentStatus.UPLOADED,
            user_id=user_id,
            user_email="test@vibotaj.com",
            user_role="admin",
            db=db,
        )

        assert result.success is True
        assert result.new_status == DocumentStatus.UPLOADED
        # Check that db.add was called (transition persisted)
        db.add.assert_called_once()
        added_obj = db.add.call_args[0][0]
        assert isinstance(added_obj, DocumentTransition)
        assert added_obj.from_state == "DRAFT"
        assert added_obj.to_state == "UPLOADED"

    def test_transition_not_persisted_without_db(self):
        """Transition is not persisted when no db session."""
        doc = MagicMock()
        doc.status = DocumentStatus.DRAFT
        doc.organization_id = uuid4()

        result = transition_document(
            document=doc,
            target_status=DocumentStatus.UPLOADED,
            user_role="admin",
        )

        assert result.success is True

    def test_failed_transition_not_persisted(self):
        """Failed transitions are not persisted."""
        db = MagicMock()
        doc = MagicMock()
        doc.status = DocumentStatus.DRAFT
        doc.organization_id = uuid4()

        # DRAFT -> ARCHIVED not allowed for supplier role
        result = transition_document(
            document=doc,
            target_status=DocumentStatus.ARCHIVED,
            user_role="supplier",
            db=db,
        )

        assert result.success is False
        db.add.assert_not_called()


class TestGetTransitionHistory:
    """Tests for get_transition_history function."""

    def test_returns_transition_list(self):
        """get_transition_history returns formatted list."""
        doc_id = uuid4()
        org_id = uuid4()

        mock_transition = MagicMock()
        mock_transition.id = uuid4()
        mock_transition.document_id = doc_id
        mock_transition.from_state = "DRAFT"
        mock_transition.to_state = "UPLOADED"
        mock_transition.actor_id = uuid4()
        mock_transition.reason = "File attached"
        mock_transition.metadata = {}
        mock_transition.created_at = datetime(2026, 2, 16, 10, 0, 0)

        db = MagicMock()
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.all.return_value = [mock_transition]

        history = get_transition_history(db, doc_id, org_id)

        assert len(history) == 1
        assert history[0]["from_state"] == "DRAFT"
        assert history[0]["to_state"] == "UPLOADED"
        assert history[0]["reason"] == "File attached"
        assert history[0]["document_id"] == str(doc_id)

    def test_returns_empty_for_no_transitions(self):
        """get_transition_history returns empty list when none found."""
        db = MagicMock()
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.all.return_value = []

        history = get_transition_history(db, uuid4(), uuid4())
        assert history == []
