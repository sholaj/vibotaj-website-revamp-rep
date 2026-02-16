"""Third-party integrations router (PRD-021).

Endpoints for customs and banking integration management,
pre-clearance checks, duty calculations, declarations,
LC verification, payment status, and forex rates.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models.integration_credential import IntegrationCredential
from ..models.integration_log import IntegrationLog
from ..schemas.integrations import (
    DeclarationRequest,
    DeclarationResponse,
    DutyCalculationRequest,
    DutyCalculationResponse,
    ForexRateResponse,
    IntegrationConfigResponse,
    IntegrationConfigUpdate,
    IntegrationLogResponse,
    IntegrationLogsListResponse,
    IntegrationsListResponse,
    IntegrationType,
    LCVerifyRequest,
    LCVerifyResponse,
    PaymentStatusResponse,
    PreClearanceRequest,
    PreClearanceResponse,
    TestConnectionResponse,
)
from ..services.banking_factory import get_banking_backend
from ..services.customs_factory import get_customs_backend

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


def _get_org_id(request: Request) -> UUID:
    """Extract organization_id from the request.

    In production, this comes from PropelAuth token.
    For dev/demo, falls back to header or default.
    """
    # Check for org_id header (dev mode)
    org_id = request.headers.get("x-organization-id")
    if org_id:
        return UUID(org_id)

    # Check for user context (PropelAuth)
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "org_id"):
        return UUID(str(user.org_id))

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": "AUTHENTICATION_REQUIRED",
            "message": "Organization context required",
        },
    )


def _log_integration_call(
    db: Session,
    org_id: UUID,
    integration_type: str,
    provider: str,
    method: str,
    request_summary: str,
    call_status: str,
    response_time_ms: int,
    error_message: Optional[str] = None,
    shipment_id: Optional[UUID] = None,
) -> None:
    """Record an integration API call in the audit log."""
    log_entry = IntegrationLog(
        organization_id=org_id,
        integration_type=integration_type,
        provider=provider,
        method=method,
        request_summary=request_summary,
        status=call_status,
        response_time_ms=response_time_ms,
        error_message=error_message,
        shipment_id=shipment_id,
    )
    db.add(log_entry)
    db.commit()


# --- Integration management ---


@router.get("", response_model=IntegrationsListResponse)
async def list_integrations(
    request: Request,
    db: Session = Depends(get_db),
) -> IntegrationsListResponse:
    """List integration configurations for the current organization."""
    org_id = _get_org_id(request)

    customs_cred = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.organization_id == org_id,
            IntegrationCredential.integration_type == "customs",
        )
        .first()
    )
    banking_cred = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.organization_id == org_id,
            IntegrationCredential.integration_type == "banking",
        )
        .first()
    )

    return IntegrationsListResponse(
        customs=(
            IntegrationConfigResponse.model_validate(customs_cred)
            if customs_cred
            else None
        ),
        banking=(
            IntegrationConfigResponse.model_validate(banking_cred)
            if banking_cred
            else None
        ),
    )


@router.put("/{integration_type}", response_model=IntegrationConfigResponse)
async def update_integration(
    integration_type: IntegrationType,
    body: IntegrationConfigUpdate,
    request: Request,
    db: Session = Depends(get_db),
) -> IntegrationConfigResponse:
    """Update integration configuration (admin only)."""
    org_id = _get_org_id(request)

    cred = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.organization_id == org_id,
            IntegrationCredential.integration_type == integration_type.value,
        )
        .first()
    )

    if cred:
        cred.provider = body.provider
        cred.config = body.config
        cred.is_active = body.is_active
        cred.updated_at = datetime.now(timezone.utc)
    else:
        cred = IntegrationCredential(
            organization_id=org_id,
            integration_type=integration_type.value,
            provider=body.provider,
            config=body.config,
            is_active=body.is_active,
        )
        db.add(cred)

    db.commit()
    db.refresh(cred)

    return IntegrationConfigResponse.model_validate(cred)


@router.post("/{integration_type}/test", response_model=TestConnectionResponse)
async def test_connection(
    integration_type: IntegrationType,
    request: Request,
    db: Session = Depends(get_db),
) -> TestConnectionResponse:
    """Test an integration connection."""
    org_id = _get_org_id(request)
    start = time.monotonic()

    if integration_type == IntegrationType.CUSTOMS:
        backend = get_customs_backend()
        available = backend.is_available()
        provider = backend.get_provider_name()
    else:
        backend = get_banking_backend()
        available = backend.is_available()
        provider = backend.get_provider_name()

    elapsed_ms = int((time.monotonic() - start) * 1000)

    # Update credential record with test result
    cred = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.organization_id == org_id,
            IntegrationCredential.integration_type == integration_type.value,
        )
        .first()
    )
    if cred:
        cred.last_tested_at = datetime.now(timezone.utc)
        cred.last_test_success = available
        db.commit()

    _log_integration_call(
        db=db,
        org_id=org_id,
        integration_type=integration_type.value,
        provider=provider,
        method="test_connection",
        request_summary=f"Test {integration_type.value} connection",
        call_status="success" if available else "error",
        response_time_ms=elapsed_ms,
    )

    return TestConnectionResponse(
        integration_type=integration_type.value,
        provider=provider,
        success=available,
        message=(
            "Connection successful"
            if available
            else "Connection failed — backend unavailable"
        ),
        response_time_ms=elapsed_ms,
    )


@router.get("/{integration_type}/logs", response_model=IntegrationLogsListResponse)
async def get_integration_logs(
    integration_type: IntegrationType,
    request: Request,
    db: Session = Depends(get_db),
    limit: int = 10,
) -> IntegrationLogsListResponse:
    """Get recent integration API call logs."""
    org_id = _get_org_id(request)

    query = (
        db.query(IntegrationLog)
        .filter(
            IntegrationLog.organization_id == org_id,
            IntegrationLog.integration_type == integration_type.value,
        )
        .order_by(IntegrationLog.created_at.desc())
    )

    total = query.count()
    logs = query.limit(min(limit, 100)).all()

    return IntegrationLogsListResponse(
        logs=[IntegrationLogResponse.model_validate(log) for log in logs],
        total=total,
    )


# --- Customs operations ---


@router.post("/customs/pre-clearance", response_model=PreClearanceResponse)
async def customs_pre_clearance(
    body: PreClearanceRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> PreClearanceResponse:
    """Run a customs pre-clearance check."""
    org_id = _get_org_id(request)

    if not settings.customs_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "CUSTOMS_DISABLED",
                "message": "Customs integration is not enabled",
            },
        )

    backend = get_customs_backend()
    start = time.monotonic()

    try:
        result = backend.check_pre_clearance(
            hs_code=body.hs_code,
            origin_country=body.origin_country,
            destination_country=body.destination_country,
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)

        _log_integration_call(
            db=db,
            org_id=org_id,
            integration_type="customs",
            provider=backend.get_provider_name(),
            method="check_pre_clearance",
            request_summary=f"Pre-clearance: HS {body.hs_code} from {body.origin_country}",
            call_status="success",
            response_time_ms=elapsed_ms,
        )

        return PreClearanceResponse(
            hs_code=result.hs_code,
            origin_country=result.origin_country,
            status=result.status.value,
            required_documents=result.required_documents,
            restrictions=result.restrictions,
            notes=result.notes,
            provider=result.provider,
        )
    except Exception as e:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        _log_integration_call(
            db=db,
            org_id=org_id,
            integration_type="customs",
            provider=backend.get_provider_name(),
            method="check_pre_clearance",
            request_summary=f"Pre-clearance: HS {body.hs_code} from {body.origin_country}",
            call_status="error",
            response_time_ms=elapsed_ms,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "CUSTOMS_API_ERROR", "message": str(e)},
        )


@router.post("/customs/duty-calc", response_model=DutyCalculationResponse)
async def customs_duty_calculation(
    body: DutyCalculationRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> DutyCalculationResponse:
    """Calculate import duties for a product."""
    org_id = _get_org_id(request)

    if not settings.customs_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "CUSTOMS_DISABLED",
                "message": "Customs integration is not enabled",
            },
        )

    backend = get_customs_backend()
    start = time.monotonic()

    try:
        result = backend.calculate_duty(
            hs_code=body.hs_code,
            cif_value=body.cif_value,
            currency=body.currency,
            quantity=body.quantity,
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)

        _log_integration_call(
            db=db,
            org_id=org_id,
            integration_type="customs",
            provider=backend.get_provider_name(),
            method="calculate_duty",
            request_summary=f"Duty calc: HS {body.hs_code} CIF {body.cif_value} {body.currency}",
            call_status="success",
            response_time_ms=elapsed_ms,
        )

        return DutyCalculationResponse(
            hs_code=result.hs_code,
            cif_value=result.cif_value,
            currency=result.currency,
            import_duty_rate=result.import_duty_rate,
            import_duty_amount=result.import_duty_amount,
            vat_rate=result.vat_rate,
            vat_amount=result.vat_amount,
            surcharges=result.surcharges,
            total_duty=result.total_duty,
            provider=result.provider,
        )
    except Exception as e:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        _log_integration_call(
            db=db,
            org_id=org_id,
            integration_type="customs",
            provider=backend.get_provider_name(),
            method="calculate_duty",
            request_summary=f"Duty calc: HS {body.hs_code}",
            call_status="error",
            response_time_ms=elapsed_ms,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "CUSTOMS_API_ERROR", "message": str(e)},
        )


@router.post("/customs/declare", response_model=DeclarationResponse)
async def customs_submit_declaration(
    body: DeclarationRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> DeclarationResponse:
    """Submit an export declaration."""
    org_id = _get_org_id(request)

    if not settings.customs_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "CUSTOMS_DISABLED",
                "message": "Customs integration is not enabled",
            },
        )

    backend = get_customs_backend()
    start = time.monotonic()

    try:
        result = backend.submit_declaration(
            shipment_reference=body.shipment_reference,
            hs_code=body.hs_code,
            exporter_name=body.exporter_name,
            consignee_name=body.consignee_name,
            cif_value=body.cif_value,
            currency=body.currency,
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)

        _log_integration_call(
            db=db,
            org_id=org_id,
            integration_type="customs",
            provider=backend.get_provider_name(),
            method="submit_declaration",
            request_summary=f"Declaration: {body.shipment_reference} HS {body.hs_code}",
            call_status="success",
            response_time_ms=elapsed_ms,
        )

        return DeclarationResponse(
            reference_number=result.reference_number,
            status=result.status.value,
            submitted_at=result.submitted_at,
            provider=result.provider,
            error=result.error,
        )
    except Exception as e:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        _log_integration_call(
            db=db,
            org_id=org_id,
            integration_type="customs",
            provider=backend.get_provider_name(),
            method="submit_declaration",
            request_summary=f"Declaration: {body.shipment_reference}",
            call_status="error",
            response_time_ms=elapsed_ms,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "CUSTOMS_API_ERROR", "message": str(e)},
        )


@router.get("/customs/declarations/{reference}", response_model=DeclarationResponse)
async def customs_declaration_status(
    reference: str,
    request: Request,
    db: Session = Depends(get_db),
) -> DeclarationResponse:
    """Get the status of a submitted declaration."""
    org_id = _get_org_id(request)

    if not settings.customs_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "CUSTOMS_DISABLED",
                "message": "Customs integration is not enabled",
            },
        )

    backend = get_customs_backend()
    start = time.monotonic()
    result = backend.get_declaration_status(reference)
    elapsed_ms = int((time.monotonic() - start) * 1000)

    _log_integration_call(
        db=db,
        org_id=org_id,
        integration_type="customs",
        provider=backend.get_provider_name(),
        method="get_declaration_status",
        request_summary=f"Declaration status: {reference}",
        call_status="success",
        response_time_ms=elapsed_ms,
    )

    return DeclarationResponse(
        reference_number=result.reference_number,
        status=result.status.value,
        submitted_at=result.submitted_at,
        provider=result.provider,
        error=result.error,
    )


# --- Banking operations ---


@router.post("/banking/verify-lc", response_model=LCVerifyResponse)
async def banking_verify_lc(
    body: LCVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> LCVerifyResponse:
    """Verify a Letter of Credit."""
    org_id = _get_org_id(request)

    if not settings.banking_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "BANKING_DISABLED",
                "message": "Banking integration is not enabled",
            },
        )

    backend = get_banking_backend()
    start = time.monotonic()

    try:
        result = backend.verify_lc(
            lc_number=body.lc_number,
            issuing_bank=body.issuing_bank,
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)

        _log_integration_call(
            db=db,
            org_id=org_id,
            integration_type="banking",
            provider=backend.get_provider_name(),
            method="verify_lc",
            request_summary=f"LC verification: {body.lc_number} from {body.issuing_bank}",
            call_status="success",
            response_time_ms=elapsed_ms,
        )

        return LCVerifyResponse(
            lc_number=result.lc_number,
            status=result.status.value,
            issuing_bank=result.issuing_bank,
            beneficiary=result.beneficiary,
            amount=result.amount,
            currency=result.currency,
            expiry_date=result.expiry_date,
            terms=result.terms,
            provider=result.provider,
            error=result.error,
        )
    except Exception as e:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        _log_integration_call(
            db=db,
            org_id=org_id,
            integration_type="banking",
            provider=backend.get_provider_name(),
            method="verify_lc",
            request_summary=f"LC verification: {body.lc_number}",
            call_status="error",
            response_time_ms=elapsed_ms,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "BANKING_API_ERROR", "message": str(e)},
        )


@router.get("/banking/payment/{reference}", response_model=PaymentStatusResponse)
async def banking_payment_status(
    reference: str,
    request: Request,
    db: Session = Depends(get_db),
) -> PaymentStatusResponse:
    """Get the status of a payment."""
    org_id = _get_org_id(request)

    if not settings.banking_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "BANKING_DISABLED",
                "message": "Banking integration is not enabled",
            },
        )

    backend = get_banking_backend()
    start = time.monotonic()

    try:
        result = backend.get_payment_status(reference)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        _log_integration_call(
            db=db,
            org_id=org_id,
            integration_type="banking",
            provider=backend.get_provider_name(),
            method="get_payment_status",
            request_summary=f"Payment status: {reference}",
            call_status="success",
            response_time_ms=elapsed_ms,
        )

        return PaymentStatusResponse(
            reference=result.reference,
            status=result.status.value,
            amount=result.amount,
            currency=result.currency,
            payer=result.payer,
            payee=result.payee,
            initiated_at=result.initiated_at,
            completed_at=result.completed_at,
            provider=result.provider,
            error=result.error,
        )
    except Exception as e:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        _log_integration_call(
            db=db,
            org_id=org_id,
            integration_type="banking",
            provider=backend.get_provider_name(),
            method="get_payment_status",
            request_summary=f"Payment status: {reference}",
            call_status="error",
            response_time_ms=elapsed_ms,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "BANKING_API_ERROR", "message": str(e)},
        )


@router.get("/banking/forex/{pair}", response_model=ForexRateResponse)
async def banking_forex_rate(
    pair: str,
    request: Request,
    db: Session = Depends(get_db),
) -> ForexRateResponse:
    """Get a forex rate (e.g., NGN-EUR)."""
    org_id = _get_org_id(request)

    if not settings.banking_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "BANKING_DISABLED",
                "message": "Banking integration is not enabled",
            },
        )

    # Parse currency pair
    parts = pair.upper().split("-")
    if len(parts) != 2 or any(len(p) != 3 for p in parts):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INVALID_CURRENCY_PAIR",
                "message": "Use format: BASE-QUOTE (e.g., NGN-EUR)",
            },
        )

    base_currency, quote_currency = parts

    backend = get_banking_backend()
    start = time.monotonic()

    try:
        result = backend.get_forex_rate(base_currency, quote_currency)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        _log_integration_call(
            db=db,
            org_id=org_id,
            integration_type="banking",
            provider=backend.get_provider_name(),
            method="get_forex_rate",
            request_summary=f"Forex rate: {pair}",
            call_status="success",
            response_time_ms=elapsed_ms,
        )

        return ForexRateResponse(
            base_currency=result.base_currency,
            quote_currency=result.quote_currency,
            buy_rate=result.buy_rate,
            sell_rate=result.sell_rate,
            mid_rate=result.mid_rate,
            timestamp=result.timestamp,
            provider=result.provider,
        )
    except Exception as e:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        _log_integration_call(
            db=db,
            org_id=org_id,
            integration_type="banking",
            provider=backend.get_provider_name(),
            method="get_forex_rate",
            request_summary=f"Forex rate: {pair}",
            call_status="error",
            response_time_ms=elapsed_ms,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "BANKING_API_ERROR", "message": str(e)},
        )


# --- Webhook receivers ---


@router.post("/webhooks/customs")
async def customs_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_webhook_signature: Optional[str] = Header(default=None),
) -> dict:
    """Receive customs status update webhooks."""
    from ..routers.webhooks import verify_webhook_signature

    body = await request.body()

    # Verify signature if configured
    if settings.webhook_secret and x_webhook_signature:
        if not verify_webhook_signature(
            body, x_webhook_signature, settings.webhook_secret
        ):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    import json

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    declaration_ref = payload.get("reference_number", "")
    new_status = payload.get("status", "")

    logger.info(
        "Customs webhook received: ref=%s status=%s",
        declaration_ref,
        new_status,
    )

    return {
        "status": "received",
        "reference_number": declaration_ref,
        "new_status": new_status,
    }


@router.post("/webhooks/banking")
async def banking_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_webhook_signature: Optional[str] = Header(default=None),
) -> dict:
    """Receive banking payment update webhooks."""
    from ..routers.webhooks import verify_webhook_signature

    body = await request.body()

    # Verify signature if configured
    if settings.webhook_secret and x_webhook_signature:
        if not verify_webhook_signature(
            body, x_webhook_signature, settings.webhook_secret
        ):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    import json

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    payment_ref = payload.get("reference", "")
    payment_status = payload.get("status", "")

    logger.info(
        "Banking webhook received: ref=%s status=%s",
        payment_ref,
        payment_status,
    )

    return {
        "status": "received",
        "reference": payment_ref,
        "payment_status": payment_status,
    }
