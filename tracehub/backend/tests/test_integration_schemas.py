"""Tests for integration Pydantic schemas and database models (PRD-021)."""

import pytest
from uuid import uuid4
from pydantic import ValidationError

from app.schemas.integrations import (
    DeclarationRequest,
    DutyCalculationRequest,
    IntegrationConfigUpdate,
    IntegrationType,
    LCVerifyRequest,
    PreClearanceRequest,
    TestConnectionResponse,
)
from app.models.integration_credential import IntegrationCredential
from app.models.integration_log import IntegrationLog


class TestIntegrationType:
    """Tests for IntegrationType enum."""

    def test_customs(self):
        assert IntegrationType.CUSTOMS == "customs"

    def test_banking(self):
        assert IntegrationType.BANKING == "banking"

    def test_values(self):
        assert set(IntegrationType) == {"customs", "banking"}


class TestPreClearanceRequest:
    """Tests for PreClearanceRequest schema."""

    def test_valid(self):
        req = PreClearanceRequest(hs_code="0506", origin_country="NG")
        assert req.hs_code == "0506"
        assert req.destination_country == "DE"

    def test_custom_destination(self):
        req = PreClearanceRequest(
            hs_code="0506", origin_country="NG", destination_country="BE"
        )
        assert req.destination_country == "BE"

    def test_hs_code_too_short(self):
        with pytest.raises(ValidationError):
            PreClearanceRequest(hs_code="0", origin_country="NG")

    def test_country_code_too_long(self):
        with pytest.raises(ValidationError):
            PreClearanceRequest(hs_code="0506", origin_country="NGA")


class TestDutyCalculationRequest:
    """Tests for DutyCalculationRequest schema."""

    def test_valid(self):
        req = DutyCalculationRequest(hs_code="0506", cif_value=10000.0)
        assert req.currency == "EUR"
        assert req.quantity == 1.0

    def test_cif_must_be_positive(self):
        with pytest.raises(ValidationError):
            DutyCalculationRequest(hs_code="0506", cif_value=0)

    def test_quantity_must_be_positive(self):
        with pytest.raises(ValidationError):
            DutyCalculationRequest(hs_code="0506", cif_value=100, quantity=0)


class TestDeclarationRequest:
    """Tests for DeclarationRequest schema."""

    def test_valid(self):
        req = DeclarationRequest(
            shipment_reference="SH-001",
            hs_code="0506",
            exporter_name="VIBOTAJ",
            consignee_name="HAGES",
            cif_value=25000.0,
        )
        assert req.currency == "EUR"

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            DeclarationRequest(
                shipment_reference="SH-001",
                hs_code="0506",
                exporter_name="VIBOTAJ",
                # missing consignee_name
                cif_value=25000.0,
            )


class TestLCVerifyRequest:
    """Tests for LCVerifyRequest schema."""

    def test_valid(self):
        req = LCVerifyRequest(lc_number="LC-001", issuing_bank="GTBank")
        assert req.lc_number == "LC-001"

    def test_empty_lc_number(self):
        with pytest.raises(ValidationError):
            LCVerifyRequest(lc_number="", issuing_bank="GTBank")


class TestIntegrationConfigUpdate:
    """Tests for IntegrationConfigUpdate schema."""

    def test_valid(self):
        update = IntegrationConfigUpdate(provider="mock", is_active=True)
        assert update.config == {}

    def test_with_config(self):
        update = IntegrationConfigUpdate(
            provider="ncs",
            config={"base_url": "https://api.ncs.gov.ng"},
            is_active=True,
        )
        assert update.config["base_url"] == "https://api.ncs.gov.ng"

    def test_empty_provider(self):
        with pytest.raises(ValidationError):
            IntegrationConfigUpdate(provider="", is_active=True)


class TestTestConnectionResponse:
    """Tests for TestConnectionResponse schema."""

    def test_success(self):
        resp = TestConnectionResponse(
            integration_type="customs",
            provider="mock",
            success=True,
            message="Connection successful",
            response_time_ms=42,
        )
        assert resp.success is True

    def test_failure(self):
        resp = TestConnectionResponse(
            integration_type="banking",
            provider="mock",
            success=False,
            message="Connection failed",
        )
        assert resp.response_time_ms is None


class TestIntegrationCredentialModel:
    """Tests for IntegrationCredential SQLAlchemy model."""

    def test_table_name(self):
        assert IntegrationCredential.__tablename__ == "integration_credentials"

    def test_repr(self):
        cred = IntegrationCredential(
            organization_id=uuid4(),
            integration_type="customs",
            provider="mock",
        )
        assert "customs" in repr(cred)
        assert "mock" in repr(cred)


class TestIntegrationLogModel:
    """Tests for IntegrationLog SQLAlchemy model."""

    def test_table_name(self):
        assert IntegrationLog.__tablename__ == "integration_logs"

    def test_repr(self):
        log = IntegrationLog(
            organization_id=uuid4(),
            integration_type="banking",
            provider="mock",
            method="verify_lc",
            status="success",
        )
        assert "banking" in repr(log)
        assert "verify_lc" in repr(log)
