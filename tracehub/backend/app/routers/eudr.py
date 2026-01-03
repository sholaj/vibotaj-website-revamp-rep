"""EUDR Router - EU Deforestation Regulation compliance endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
import io
import json

from ..database import get_db
from ..models import Shipment, Origin, Product
from ..routers.auth import get_current_user, User
from ..services.eudr import (
    validate_origin_data,
    validate_production_date,
    validate_geolocation,
    check_deforestation_risk,
    generate_due_diligence_statement,
    get_shipment_eudr_status,
    calculate_risk_score,
    RiskLevel,
    EUDRValidationStatus,
    EUDR_CUTOFF_DATE,
)
from pydantic import BaseModel, Field


router = APIRouter()


# ============================================
# Request/Response Schemas
# ============================================

class OriginVerificationRequest(BaseModel):
    """Request to verify origin data."""
    farm_plot_identifier: Optional[str] = None
    geolocation_lat: Optional[float] = Field(None, ge=-90, le=90)
    geolocation_lng: Optional[float] = Field(None, ge=-180, le=180)
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    region: Optional[str] = None
    district: Optional[str] = None
    production_start_date: Optional[date] = None
    production_end_date: Optional[date] = None
    supplier_attestation_date: Optional[date] = None
    supplier_attestation_reference: Optional[str] = None
    deforestation_free_statement: Optional[str] = None
    verification_method: Optional[str] = None


class GeolocationCheckRequest(BaseModel):
    """Request to check geolocation."""
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    country: str = Field(..., min_length=2, max_length=2)


class ProductionDateCheckRequest(BaseModel):
    """Request to check production date."""
    production_date: date


class EUDRStatusResponse(BaseModel):
    """EUDR compliance status response."""
    shipment_id: str
    shipment_reference: str
    overall_status: str
    overall_risk_level: str
    is_compliant: bool
    checklist: List[dict]
    summary: dict
    origin_validations: List[dict]
    cutoff_date: str
    assessed_at: str


class OriginValidationResponse(BaseModel):
    """Origin validation response."""
    origin_id: str
    is_valid: bool
    status: str
    risk_level: str
    risk_score: int
    checks: List[dict]
    missing_fields: List[str]
    warnings: List[str]
    errors: List[str]


class RiskAssessmentResponse(BaseModel):
    """Risk assessment response."""
    risk_level: str
    country_risk: str
    coordinates: dict
    satellite_check: dict
    recommendations: List[str]
    eudr_article: str
    assessed_at: str


# ============================================
# EUDR Status Endpoints
# ============================================

@router.get("/shipment/{shipment_id}/status", response_model=EUDRStatusResponse)
async def get_eudr_status(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get EUDR compliance status for a shipment.

    Returns comprehensive compliance status including:
    - Overall compliance status
    - Risk level assessment
    - Compliance checklist
    - Origin validation details
    """
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    status = get_shipment_eudr_status(shipment, db)
    return status


@router.post("/shipment/{shipment_id}/validate")
async def validate_shipment_eudr(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run full EUDR validation on a shipment.

    This performs comprehensive validation of:
    - All origin data completeness
    - Production date compliance (post Dec 31, 2020)
    - Geolocation verification
    - Required documentation
    - Risk assessment

    Returns detailed validation results with actionable feedback.
    """
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Run full validation
    status = get_shipment_eudr_status(shipment, db)

    # Generate actionable items
    action_items = []

    for check in status["checklist"]:
        if not check["passed"]:
            action_items.append({
                "action": check["item"],
                "details": check["details"],
                "priority": "high" if check["item"] in ["Origin Data Complete", "Production Dates Valid"] else "medium"
            })

    # Add recommendations based on risk level
    risk_level = RiskLevel(status["overall_risk_level"])
    if risk_level == RiskLevel.HIGH:
        action_items.append({
            "action": "Enhanced Due Diligence Required",
            "details": "High-risk origin countries detected. Consider on-site verification and third-party audit.",
            "priority": "high"
        })
    elif risk_level == RiskLevel.MEDIUM:
        action_items.append({
            "action": "Review Origin Documentation",
            "details": "Medium-risk origin countries detected. Ensure all supplier attestations are current.",
            "priority": "medium"
        })

    return {
        "shipment_id": str(shipment_id),
        "validation_result": status,
        "action_items": action_items,
        "validated_at": datetime.utcnow().isoformat(),
        "validated_by": current_user.username
    }


@router.get("/shipment/{shipment_id}/report")
async def get_eudr_report(
    shipment_id: UUID,
    format: str = "json",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate EUDR compliance report for a shipment.

    Generates a comprehensive report including:
    - Due Diligence Statement (DDS)
    - Origin validation details
    - Risk assessments
    - Compliance checklist

    Query Parameters:
        format: Output format - 'json' or 'pdf' (default: json)
    """
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Generate due diligence statement
    dds = generate_due_diligence_statement(shipment, db)

    # Get status
    status = get_shipment_eudr_status(shipment, db)

    report = {
        "report_type": "EUDR Compliance Report",
        "generated_at": datetime.utcnow().isoformat(),
        "generated_by": current_user.username,
        "shipment": {
            "id": str(shipment.id),
            "reference": shipment.reference,
            "container_number": shipment.container_number,
            "bl_number": shipment.bl_number,
            "destination": shipment.pod_name or shipment.pod_code
        },
        "compliance_status": status,
        "due_diligence_statement": dds,
        "legal_basis": {
            "regulation": "Regulation (EU) 2023/1115",
            "title": "EU Deforestation Regulation (EUDR)",
            "cutoff_date": EUDR_CUTOFF_DATE.isoformat(),
            "applicable_articles": [
                "Article 3 - Definitions",
                "Article 4 - Prohibition",
                "Article 9 - Due Diligence",
                "Article 10 - Risk Assessment",
                "Article 11 - Risk Mitigation"
            ]
        }
    }

    if format.lower() == "pdf":
        # Generate PDF report
        pdf_content = _generate_pdf_report(report)
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=EUDR-Report-{shipment.reference}.pdf"
            }
        )

    return report


def _generate_pdf_report(report: dict) -> bytes:
    """
    Generate PDF version of EUDR report.

    For POC, returns a simple text-based PDF-like format.
    In production, use reportlab or weasyprint for proper PDF generation.
    """
    # Simple text representation for POC
    # In production, integrate with reportlab or similar
    content = f"""
EUDR COMPLIANCE REPORT
======================

Generated: {report['generated_at']}
Generated By: {report['generated_by']}

SHIPMENT DETAILS
----------------
Reference: {report['shipment']['reference']}
Container: {report['shipment']['container_number']}
B/L Number: {report['shipment']['bl_number']}
Destination: {report['shipment']['destination']}

COMPLIANCE STATUS
-----------------
Overall Status: {report['compliance_status']['overall_status'].upper()}
Risk Level: {report['compliance_status']['overall_risk_level'].upper()}
Compliant: {'YES' if report['compliance_status']['is_compliant'] else 'NO'}

COMPLIANCE CHECKLIST
--------------------
"""

    for item in report['compliance_status']['checklist']:
        status = "PASS" if item['passed'] else "FAIL"
        content += f"[{status}] {item['item']}: {item['details']}\n"

    content += f"""
DUE DILIGENCE STATEMENT
-----------------------
Statement Reference: {report['due_diligence_statement']['statement_reference']}

{report['due_diligence_statement']['declaration']['text']}

LEGAL BASIS
-----------
Regulation: {report['legal_basis']['regulation']}
Title: {report['legal_basis']['title']}
Cutoff Date: {report['legal_basis']['cutoff_date']}

END OF REPORT
"""

    return content.encode('utf-8')


# ============================================
# Origin Verification Endpoints
# ============================================

@router.post("/origin/{origin_id}/verify", response_model=OriginValidationResponse)
async def verify_origin(
    origin_id: UUID,
    verification: Optional[OriginVerificationRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify origin data for EUDR compliance.

    If verification data is provided, updates the origin record first.
    Then runs full EUDR validation on the origin.
    """
    origin = db.query(Origin).filter(Origin.id == origin_id).first()
    if not origin:
        raise HTTPException(status_code=404, detail="Origin not found")

    # Update origin if verification data provided
    if verification:
        if verification.farm_plot_identifier is not None:
            origin.farm_plot_identifier = verification.farm_plot_identifier
        if verification.geolocation_lat is not None:
            origin.geolocation_lat = Decimal(str(verification.geolocation_lat))
        if verification.geolocation_lng is not None:
            origin.geolocation_lng = Decimal(str(verification.geolocation_lng))
        if verification.country is not None:
            origin.country = verification.country.upper()
        if verification.region is not None:
            origin.region = verification.region
        if verification.district is not None:
            origin.district = verification.district
        if verification.production_start_date is not None:
            origin.production_start_date = verification.production_start_date
        if verification.production_end_date is not None:
            origin.production_end_date = verification.production_end_date
        if verification.deforestation_free_statement is not None:
            origin.deforestation_free_statement = verification.deforestation_free_statement
        if verification.supplier_attestation_date is not None:
            origin.supplier_attestation_date = verification.supplier_attestation_date
        if verification.supplier_attestation_reference is not None:
            origin.supplier_attestation_reference = verification.supplier_attestation_reference
        if verification.verification_method is not None:
            origin.verification_method = verification.verification_method

        # Mark as verified
        origin.verified_at = datetime.utcnow()
        origin.verified_by = current_user.username

        db.commit()
        db.refresh(origin)

    # Run validation
    validation = validate_origin_data(origin)

    # Calculate risk score
    risk_score = calculate_risk_score(origin, validation)
    validation.risk_score = risk_score

    # Add production date check
    prod_date = origin.production_end_date or origin.production_start_date
    if prod_date:
        date_valid, date_msg = validate_production_date(prod_date)
        validation.add_check("production_date_cutoff", date_valid, date_msg)

    # Add geolocation check
    if origin.geolocation_lat and origin.geolocation_lng:
        geo_result = validate_geolocation(
            origin.geolocation_lat,
            origin.geolocation_lng,
            origin.country
        )
        validation.checks.extend(geo_result.checks)

    # Get risk level
    risk_assessment = check_deforestation_risk(
        origin.geolocation_lat,
        origin.geolocation_lng,
        origin.country
    )
    validation.risk_level = RiskLevel(risk_assessment["risk_level"])

    return OriginValidationResponse(
        origin_id=str(origin.id),
        is_valid=validation.is_valid,
        status=validation.status.value,
        risk_level=validation.risk_level.value,
        risk_score=validation.risk_score,
        checks=validation.checks,
        missing_fields=validation.missing_fields,
        warnings=validation.warnings,
        errors=validation.errors
    )


@router.get("/origin/{origin_id}/risk", response_model=RiskAssessmentResponse)
async def get_origin_risk(
    origin_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get deforestation risk assessment for an origin."""
    origin = db.query(Origin).filter(Origin.id == origin_id).first()
    if not origin:
        raise HTTPException(status_code=404, detail="Origin not found")

    risk = check_deforestation_risk(
        origin.geolocation_lat,
        origin.geolocation_lng,
        origin.country
    )

    return risk


# ============================================
# Validation Utility Endpoints
# ============================================

@router.post("/check/geolocation")
async def check_geolocation(
    request: GeolocationCheckRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Check if geolocation coordinates are valid and within country boundaries.

    Useful for validating coordinates before saving to an origin record.
    """
    result = validate_geolocation(
        Decimal(str(request.lat)),
        Decimal(str(request.lng)),
        request.country
    )

    risk = check_deforestation_risk(
        Decimal(str(request.lat)),
        Decimal(str(request.lng)),
        request.country
    )

    return {
        "coordinates": {
            "lat": request.lat,
            "lng": request.lng
        },
        "country": request.country,
        "validation": result.to_dict(),
        "risk_assessment": risk
    }


@router.post("/check/production-date")
async def check_production_date(
    request: ProductionDateCheckRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Check if production date meets EUDR requirements.

    Production date must be after December 31, 2020.
    """
    is_valid, message = validate_production_date(request.production_date)

    return {
        "production_date": request.production_date.isoformat(),
        "cutoff_date": EUDR_CUTOFF_DATE.isoformat(),
        "is_valid": is_valid,
        "message": message,
        "days_after_cutoff": (request.production_date - EUDR_CUTOFF_DATE).days if is_valid else None
    }


@router.get("/countries/risk-levels")
async def get_country_risk_levels(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of countries with their EUDR risk levels.

    Risk levels are based on EU Commission assessments:
    - low: Low deforestation risk
    - medium: Medium deforestation risk
    - high: High deforestation risk
    - unknown: Not yet assessed
    """
    from ..services.eudr import COUNTRY_RISK_LEVELS

    return {
        "risk_levels": {
            code: level.value for code, level in COUNTRY_RISK_LEVELS.items()
        },
        "risk_categories": {
            "low": [code for code, level in COUNTRY_RISK_LEVELS.items() if level == RiskLevel.LOW],
            "medium": [code for code, level in COUNTRY_RISK_LEVELS.items() if level == RiskLevel.MEDIUM],
            "high": [code for code, level in COUNTRY_RISK_LEVELS.items() if level == RiskLevel.HIGH]
        },
        "source": "EU Commission Country Benchmarking (simplified for POC)",
        "last_updated": "2024-01-01"
    }


@router.get("/regulation/info")
async def get_regulation_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get information about the EUDR regulation.

    Provides key dates, requirements, and compliance checklist.
    """
    return {
        "regulation": {
            "name": "EU Deforestation Regulation",
            "official_name": "Regulation (EU) 2023/1115",
            "short_name": "EUDR",
            "entry_into_force": "2023-06-29",
            "applicable_from_large_operators": "2024-12-30",
            "applicable_from_sme": "2025-06-30"
        },
        "key_dates": {
            "cutoff_date": EUDR_CUTOFF_DATE.isoformat(),
            "cutoff_description": "Products must be produced on land that was not deforested after this date"
        },
        "covered_commodities": [
            {"name": "Cattle", "hs_codes": ["0102"]},
            {"name": "Cocoa", "hs_codes": ["1801", "1802", "1803", "1804", "1805", "1806"]},
            {"name": "Coffee", "hs_codes": ["0901"]},
            {"name": "Palm Oil", "hs_codes": ["1511", "1513"]},
            {"name": "Rubber", "hs_codes": ["4001", "4002", "4003", "4004", "4005", "4011"]},
            {"name": "Soya", "hs_codes": ["1201", "1507", "2304"]},
            {"name": "Wood", "hs_codes": ["4401", "4403", "4406", "4407", "4408", "4409", "4410", "4411", "4412", "4413", "4414", "4415", "4418", "9403"]}
        ],
        "requirements": {
            "geolocation": "Precise geographic coordinates (lat/lng) or polygon for each production plot",
            "production_date": f"Production must be after {EUDR_CUTOFF_DATE.isoformat()}",
            "due_diligence": "Operators must exercise due diligence before placing products on the market",
            "traceability": "Full chain of custody documentation from source to export"
        },
        "compliance_checklist": [
            "Origin farm/plot identification",
            "Geolocation coordinates for production area",
            "Production date verification (post cutoff)",
            "Supplier due diligence attestation",
            "Deforestation-free declaration",
            "Complete documentation chain"
        ]
    }
