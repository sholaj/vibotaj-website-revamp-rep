"""EUDR Compliance Service - EU Deforestation Regulation validation and compliance."""

from datetime import date, datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from decimal import Decimal
from enum import Enum

from sqlalchemy.orm import Session

from ..models import Shipment, Product, Origin, Document, DocumentType, DocumentStatus


# EUDR cutoff date - production must be after this date
EUDR_CUTOFF_DATE = date(2020, 12, 31)


class RiskLevel(str, Enum):
    """EUDR risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class EUDRValidationStatus(str, Enum):
    """EUDR validation status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"
    INCOMPLETE = "incomplete"


# Country risk levels based on EU guidance (simplified for POC)
# Reference: European Commission deforestation risk assessments
COUNTRY_RISK_LEVELS: Dict[str, RiskLevel] = {
    # Low risk countries (mostly EU, developed nations)
    "DE": RiskLevel.LOW,
    "NL": RiskLevel.LOW,
    "FR": RiskLevel.LOW,
    "BE": RiskLevel.LOW,
    "AT": RiskLevel.LOW,
    "US": RiskLevel.LOW,
    "CA": RiskLevel.LOW,
    "AU": RiskLevel.LOW,
    "NZ": RiskLevel.LOW,
    "JP": RiskLevel.LOW,

    # Medium risk countries
    "MX": RiskLevel.MEDIUM,
    "AR": RiskLevel.MEDIUM,
    "CL": RiskLevel.MEDIUM,
    "ZA": RiskLevel.MEDIUM,
    "NG": RiskLevel.MEDIUM,
    "KE": RiskLevel.MEDIUM,
    "ET": RiskLevel.MEDIUM,
    "TZ": RiskLevel.MEDIUM,
    "GH": RiskLevel.MEDIUM,
    "CI": RiskLevel.MEDIUM,

    # High risk countries (major deforestation concerns)
    "BR": RiskLevel.HIGH,
    "ID": RiskLevel.HIGH,
    "MY": RiskLevel.HIGH,
    "CG": RiskLevel.HIGH,
    "CD": RiskLevel.HIGH,
    "PE": RiskLevel.HIGH,
    "CO": RiskLevel.HIGH,
    "BO": RiskLevel.HIGH,
    "PY": RiskLevel.HIGH,
    "VE": RiskLevel.HIGH,
}


# Country bounding boxes for basic coordinate validation (lat_min, lat_max, lng_min, lng_max)
COUNTRY_BOUNDS: Dict[str, Tuple[float, float, float, float]] = {
    "NG": (4.0, 14.0, 2.5, 15.0),       # Nigeria
    "ET": (3.0, 15.0, 33.0, 48.0),       # Ethiopia
    "KE": (-5.0, 5.0, 33.5, 42.0),       # Kenya
    "TZ": (-12.0, -1.0, 29.0, 41.0),     # Tanzania
    "ZA": (-35.0, -22.0, 16.0, 33.0),    # South Africa
    "GH": (4.5, 11.2, -3.3, 1.2),        # Ghana
    "CI": (4.3, 10.7, -8.6, -2.5),       # Cote d'Ivoire
    "BR": (-34.0, 5.3, -74.0, -32.0),    # Brazil
    "ID": (-11.0, 6.0, 95.0, 141.0),     # Indonesia
    "MY": (0.8, 7.4, 99.6, 119.3),       # Malaysia
    "DE": (47.3, 55.1, 5.9, 15.0),       # Germany
}


class EUDRValidationResult:
    """Result of EUDR validation check."""

    def __init__(self):
        self.is_valid: bool = True
        self.status: EUDRValidationStatus = EUDRValidationStatus.PENDING
        self.risk_level: RiskLevel = RiskLevel.UNKNOWN
        self.risk_score: int = 100  # Start at 100, deduct for issues
        self.checks: List[Dict[str, Any]] = []
        self.missing_fields: List[str] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def add_check(self, name: str, passed: bool, message: str, severity: str = "error"):
        """Add a validation check result."""
        self.checks.append({
            "name": name,
            "passed": passed,
            "message": message,
            "severity": severity
        })
        if not passed:
            if severity == "error":
                self.errors.append(message)
                self.is_valid = False
            elif severity == "warning":
                self.warnings.append(message)

    def add_missing_field(self, field: str, deduction: int = 10):
        """Add a missing required field."""
        self.missing_fields.append(field)
        self.risk_score = max(0, self.risk_score - deduction)
        self.is_valid = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "is_valid": self.is_valid,
            "status": self.status.value,
            "risk_level": self.risk_level.value,
            "risk_score": self.risk_score,
            "checks": self.checks,
            "missing_fields": self.missing_fields,
            "warnings": self.warnings,
            "errors": self.errors,
            "total_checks": len(self.checks),
            "passed_checks": len([c for c in self.checks if c["passed"]]),
        }


def validate_origin_data(origin: Origin) -> EUDRValidationResult:
    """
    Validate that an origin record has all required EUDR fields.

    EUDR requires:
    - Farm/plot identification
    - Geolocation (coordinates or polygon)
    - Country
    - Production dates
    - Supplier identity
    - Due diligence statement

    Args:
        origin: Origin record to validate

    Returns:
        EUDRValidationResult with validation details
    """
    result = EUDRValidationResult()

    # Check farm/plot identifier
    farm_plot_id = origin.farm_name or origin.plot_identifier
    if not farm_plot_id:
        result.add_missing_field("farm_plot_identifier")
        result.add_check(
            "farm_plot_id",
            False,
            "Farm/plot identifier is required for EUDR compliance",
            "error"
        )
    else:
        result.add_check(
            "farm_plot_id",
            True,
            f"Farm/plot identifier present: {farm_plot_id}",
            "info"
        )

    # Check geolocation
    has_coordinates = (
        origin.latitude is not None and
        origin.longitude is not None
    )
    has_polygon = origin.geolocation_polygon is not None

    if not has_coordinates and not has_polygon:
        result.add_missing_field("geolocation")
        result.add_check(
            "geolocation",
            False,
            "Geolocation coordinates or polygon required for EUDR compliance",
            "error"
        )
    else:
        if has_coordinates:
            result.add_check(
                "geolocation",
                True,
                f"Coordinates present: ({origin.latitude}, {origin.longitude})",
                "info"
            )
        if has_polygon:
            result.add_check(
                "geolocation_polygon",
                True,
                "Plot polygon boundary defined",
                "info"
            )

    # Check country
    if not origin.country:
        result.add_missing_field("country")
        result.add_check(
            "country",
            False,
            "Country code is required for EUDR compliance",
            "error"
        )
    else:
        result.add_check(
            "country",
            True,
            f"Country code present: {origin.country}",
            "info"
        )

    # Check production dates
    if not origin.production_date and not origin.harvest_date:
        result.add_missing_field("production_date")
        result.add_check(
            "production_date",
            False,
            "Production date is required for EUDR compliance",
            "error"
        )
    else:
        prod_date = origin.harvest_date or origin.production_date
        result.add_check(
            "production_date",
            True,
            f"Production date present: {prod_date}",
            "info"
        )

    # Check supplier
    if not origin.supplier_id:
        result.add_missing_field("supplier_id")
        result.add_check(
            "supplier",
            False,
            "Supplier identification required for EUDR compliance",
            "warning"
        )
    else:
        result.add_check(
            "supplier",
            True,
            "Supplier linked to origin",
            "info"
        )

    # Check due diligence statement
    if not origin.due_diligence_statement_ref and not origin.deforestation_free_statement:
        result.add_missing_field("due_diligence_statement")
        result.add_check(
            "due_diligence",
            False,
            "Due diligence statement required for EUDR compliance",
            "error"
        )
    else:
        result.add_check(
            "due_diligence",
            True,
            "Due diligence statement present",
            "info"
        )

    # Update overall status
    if result.is_valid and len(result.missing_fields) == 0:
        result.status = EUDRValidationStatus.COMPLIANT
    elif len(result.errors) > 0:
        result.status = EUDRValidationStatus.NON_COMPLIANT
    else:
        result.status = EUDRValidationStatus.INCOMPLETE

    return result


def validate_production_date(production_date: date) -> Tuple[bool, str]:
    """
    Validate that production date is after EUDR cutoff (Dec 31, 2020).

    Args:
        production_date: Date to validate

    Returns:
        Tuple of (is_valid, message)
    """
    if production_date is None:
        return False, "Production date is required"

    if production_date <= EUDR_CUTOFF_DATE:
        return False, f"Production date {production_date} is before EUDR cutoff date ({EUDR_CUTOFF_DATE}). Products must be produced after December 31, 2020."

    return True, f"Production date {production_date} is after EUDR cutoff date"


def validate_geolocation(
    lat: Optional[Decimal],
    lng: Optional[Decimal],
    country: str
) -> EUDRValidationResult:
    """
    Validate geolocation coordinates for EUDR compliance.

    Checks:
    - Coordinates are within valid ranges
    - Coordinates fall within the stated country's boundaries (basic check)

    Args:
        lat: Latitude coordinate
        lng: Longitude coordinate
        country: ISO 2-letter country code

    Returns:
        EUDRValidationResult with validation details
    """
    result = EUDRValidationResult()

    if lat is None or lng is None:
        result.add_check(
            "coordinates_present",
            False,
            "Geolocation coordinates are missing",
            "error"
        )
        return result

    lat_float = float(lat)
    lng_float = float(lng)

    # Check valid coordinate ranges
    if not (-90 <= lat_float <= 90):
        result.add_check(
            "latitude_range",
            False,
            f"Latitude {lat_float} is outside valid range (-90 to 90)",
            "error"
        )
    else:
        result.add_check(
            "latitude_range",
            True,
            f"Latitude {lat_float} is within valid range",
            "info"
        )

    if not (-180 <= lng_float <= 180):
        result.add_check(
            "longitude_range",
            False,
            f"Longitude {lng_float} is outside valid range (-180 to 180)",
            "error"
        )
    else:
        result.add_check(
            "longitude_range",
            True,
            f"Longitude {lng_float} is within valid range",
            "info"
        )

    # Check country match (if bounds available)
    if country and country.upper() in COUNTRY_BOUNDS:
        bounds = COUNTRY_BOUNDS[country.upper()]
        lat_min, lat_max, lng_min, lng_max = bounds

        lat_ok = lat_min <= lat_float <= lat_max
        lng_ok = lng_min <= lng_float <= lng_max

        if lat_ok and lng_ok:
            result.add_check(
                "country_match",
                True,
                f"Coordinates fall within {country} boundaries",
                "info"
            )
        else:
            result.add_check(
                "country_match",
                False,
                f"Coordinates ({lat_float}, {lng_float}) appear to be outside {country} boundaries. Please verify.",
                "warning"
            )
    else:
        result.add_check(
            "country_match",
            True,
            f"Country {country} boundary check not available - manual verification required",
            "warning"
        )

    return result


def check_deforestation_risk(
    lat: Optional[Decimal],
    lng: Optional[Decimal],
    country: str
) -> Dict[str, Any]:
    """
    Check deforestation risk for given coordinates.

    Sprint 14: Now uses satellite service for AI-powered detection.
    Falls back to country-level assessment when satellite data unavailable.

    Args:
        lat: Latitude coordinate
        lng: Longitude coordinate
        country: ISO 2-letter country code

    Returns:
        Dictionary with risk assessment results including:
        - risk_level: LOW/MEDIUM/HIGH/CRITICAL
        - source: satellite or country_baseline
        - forest_loss_detected: bool (if satellite data available)
        - recommendations: list of actions
    """
    from .satellite import check_deforestation_sync

    # Use satellite service (sync wrapper)
    result = check_deforestation_sync(
        latitude=float(lat) if lat else None,
        longitude=float(lng) if lng else None,
        country=country
    )

    # Map satellite risk levels to EUDR RiskLevel enum
    risk_map = {
        "LOW": RiskLevel.LOW,
        "MEDIUM": RiskLevel.MEDIUM,
        "HIGH": RiskLevel.HIGH,
        "CRITICAL": RiskLevel.HIGH,  # Map CRITICAL to HIGH for compatibility
    }

    risk_level_str = result.get("risk_level", "MEDIUM").upper()
    eudr_risk = risk_map.get(risk_level_str, RiskLevel.MEDIUM)

    # Add EUDR-specific fields
    result["country_risk"] = result.get("risk_level", "medium")
    result["recommendations"] = result.get("recommendations", _get_risk_recommendations(eudr_risk))

    # Build satellite_check for backward compatibility
    if result.get("source") == "satellite":
        result["satellite_check"] = {
            "available": True,
            "provider": result.get("provider", "Global Forest Watch"),
            "last_checked": result.get("checked_at"),
            "forest_loss_detected": result.get("forest_loss_detected"),
            "forest_loss_hectares": result.get("forest_loss_hectares"),
            "message": "Satellite data analysis complete"
        }
    else:
        result["satellite_check"] = {
            "available": False,
            "provider": None,
            "last_checked": result.get("checked_at"),
            "forest_loss_detected": None,
            "message": result.get("fallback_reason", "Using country-level risk assessment")
        }

    return result


def _get_risk_recommendations(risk_level: RiskLevel) -> List[str]:
    """Get recommendations based on risk level."""
    recommendations = {
        RiskLevel.LOW: [
            "Standard due diligence procedures apply",
            "Maintain documentation for 5 years",
        ],
        RiskLevel.MEDIUM: [
            "Enhanced due diligence recommended",
            "Consider on-site verification",
            "Request satellite imagery verification",
            "Maintain documentation for 5 years",
        ],
        RiskLevel.HIGH: [
            "Full due diligence required",
            "On-site verification strongly recommended",
            "Independent third-party verification advised",
            "Request recent satellite imagery (within 3 months)",
            "Consider supplier audit",
            "Maintain documentation for 5 years",
        ],
        RiskLevel.UNKNOWN: [
            "Unable to assess risk level",
            "Manual verification required",
            "Contact compliance team for guidance",
        ],
    }
    return recommendations.get(risk_level, recommendations[RiskLevel.UNKNOWN])


def generate_due_diligence_statement(
    shipment: Shipment,
    db: Session
) -> Dict[str, Any]:
    """
    Generate EUDR Due Diligence Statement for a shipment.

    The DDS is a key EUDR requirement that operators must submit to EU authorities
    before placing products on the market or exporting.

    Args:
        shipment: Shipment to generate statement for
        db: Database session

    Returns:
        Dictionary containing DDS data structure
    """
    # Collect origin data from all products
    origins_data = []
    overall_risk = RiskLevel.LOW
    all_compliant = True

    for product in shipment.products:
        for origin in product.origins:
            # Validate origin
            validation = validate_origin_data(origin)

            # Check production date
            prod_date = origin.harvest_date or origin.production_date
            date_valid = True
            date_message = ""
            if prod_date:
                date_valid, date_message = validate_production_date(prod_date)
            else:
                date_valid = False
                date_message = "Production date not specified"

            # Check deforestation risk
            risk_assessment = check_deforestation_risk(
                origin.latitude,
                origin.longitude,
                origin.country
            )

            # Update overall risk (take highest)
            origin_risk = RiskLevel(risk_assessment["risk_level"])
            if origin_risk == RiskLevel.HIGH:
                overall_risk = RiskLevel.HIGH
            elif origin_risk == RiskLevel.MEDIUM and overall_risk != RiskLevel.HIGH:
                overall_risk = RiskLevel.MEDIUM

            if not validation.is_valid or not date_valid:
                all_compliant = False

            origins_data.append({
                "origin_id": str(origin.id),
                "farm_plot_id": origin.farm_name or origin.plot_identifier,
                "country": origin.country,
                "region": origin.region,
                "geolocation": {
                    "lat": float(origin.latitude) if origin.latitude else None,
                    "lng": float(origin.longitude) if origin.longitude else None,
                    "polygon": origin.geolocation_polygon
                },
                "production_date": {
                    "start": origin.production_date.isoformat() if origin.production_date else None,
                    "end": origin.harvest_date.isoformat() if origin.harvest_date else None
                },
                "cutoff_compliant": origin.eudr_cutoff_compliant,
                "production_date_valid": date_valid,
                "production_date_message": date_message,
                "risk_assessment": risk_assessment,
                "validation": validation.to_dict(),
                "supplier": {
                    "id": str(origin.supplier_id) if origin.supplier_id else None,
                    "attestation_date": origin.supplier_attestation_date.isoformat() if hasattr(origin, 'supplier_attestation_date') and origin.supplier_attestation_date else None,
                    "attestation_ref": origin.supplier_attestation_reference if hasattr(origin, 'supplier_attestation_reference') else None
                },
                "verification": {
                    "verified": origin.verified_at is not None,
                    "verified_at": origin.verified_at.isoformat() if origin.verified_at else None,
                    "verified_by": origin.verified_by,
                    "method": origin.verification_method if hasattr(origin, 'verification_method') else None
                }
            })

    # Check for EUDR Due Diligence document
    eudr_doc = None
    for doc in shipment.documents:
        if doc.document_type == DocumentType.EUDR_DUE_DILIGENCE:
            eudr_doc = {
                "id": str(doc.id),
                "name": doc.name,
                "status": doc.status.value,
                "reference": doc.reference_number,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None
            }
            break

    # Build products summary
    products_data = []
    for product in shipment.products:
        products_data.append({
            "id": str(product.id),
            "hs_code": product.hs_code,
            "description": product.description,
            "quantity_kg": float(product.quantity_net_kg) if product.quantity_net_kg else None,
            "batch_lot": product.batch_lot_number,
            "origin_count": len(product.origins)
        })

    # Generate statement reference
    statement_ref = f"DDS-{shipment.reference}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    return {
        "statement_reference": statement_ref,
        "generated_at": datetime.utcnow().isoformat(),
        "shipment": {
            "id": str(shipment.id),
            "reference": shipment.reference,
            "container_number": shipment.container_number,
            "bl_number": shipment.bl_number,
            "destination_country": shipment.pod_code[:2] if shipment.pod_code else None,
            "etd": shipment.etd.isoformat() if shipment.etd else None,
            "eta": shipment.eta.isoformat() if shipment.eta else None
        },
        "compliance_summary": {
            "overall_status": "compliant" if all_compliant else "non_compliant",
            "overall_risk_level": overall_risk.value,
            "total_origins": len(origins_data),
            "compliant_origins": len([o for o in origins_data if o["validation"]["is_valid"]]),
            "eudr_document_uploaded": eudr_doc is not None,
            "all_production_dates_valid": all(o["production_date_valid"] for o in origins_data),
            "all_geolocations_present": all(o["geolocation"]["lat"] is not None for o in origins_data)
        },
        "products": products_data,
        "origins": origins_data,
        "eudr_document": eudr_doc,
        "declaration": {
            "text": (
                "The operator declares that due diligence has been exercised in accordance with "
                "Regulation (EU) 2023/1115 (EUDR) and that, based on the information gathered, "
                "there is no or only negligible risk that the relevant products are non-compliant "
                "with the requirements of the Regulation."
            ),
            "signed_by": None,
            "signed_at": None
        },
        "legal_references": {
            "regulation": "Regulation (EU) 2023/1115",
            "articles": ["Article 4 - Prohibition", "Article 9 - Due Diligence", "Article 10 - Risk Assessment"],
            "cutoff_date": EUDR_CUTOFF_DATE.isoformat()
        }
    }


def get_shipment_eudr_status(
    shipment: Shipment,
    db: Session
) -> Dict[str, Any]:
    """
    Get comprehensive EUDR compliance status for a shipment.

    Args:
        shipment: Shipment to check
        db: Database session

    Returns:
        Dictionary with complete EUDR status
    """
    # Collect all validations
    origin_validations = []
    all_compliant = True
    highest_risk = RiskLevel.UNKNOWN

    total_origins = 0
    compliant_origins = 0

    for product in shipment.products:
        for origin in product.origins:
            total_origins += 1
            validation = validate_origin_data(origin)

            # Validate production date
            prod_date = origin.harvest_date or origin.production_date
            if prod_date:
                date_valid, date_msg = validate_production_date(prod_date)
                validation.add_check("production_date_cutoff", date_valid, date_msg, "error" if not date_valid else "info")

            # Validate geolocation
            if origin.latitude and origin.longitude:
                geo_validation = validate_geolocation(
                    origin.latitude,
                    origin.longitude,
                    origin.country
                )
                validation.checks.extend(geo_validation.checks)
                validation.errors.extend(geo_validation.errors)
                validation.warnings.extend(geo_validation.warnings)

            # Risk assessment
            risk = check_deforestation_risk(
                origin.latitude,
                origin.longitude,
                origin.country
            )
            validation.risk_level = RiskLevel(risk["risk_level"])

            # Update highest risk
            risk_order = [RiskLevel.UNKNOWN, RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]
            if risk_order.index(validation.risk_level) > risk_order.index(highest_risk):
                highest_risk = validation.risk_level

            if validation.is_valid:
                compliant_origins += 1
            else:
                all_compliant = False

            origin_validations.append({
                "origin_id": str(origin.id),
                "farm_plot_id": origin.farm_name or origin.plot_identifier,
                "country": origin.country,
                "validation": validation.to_dict(),
                "risk": risk
            })

    # Check for EUDR document
    has_eudr_doc = any(
        doc.document_type == DocumentType.EUDR_DUE_DILIGENCE and
        doc.status in [DocumentStatus.UPLOADED, DocumentStatus.VALIDATED, DocumentStatus.COMPLIANCE_OK, DocumentStatus.LINKED]
        for doc in shipment.documents
    )

    # Build checklist
    checklist = [
        {
            "item": "Origin Data Complete",
            "passed": compliant_origins == total_origins,
            "details": f"{compliant_origins}/{total_origins} origins have complete data"
        },
        {
            "item": "Production Dates Valid",
            "passed": all(
                ov["validation"]["is_valid"] and
                any(c["name"] == "production_date_cutoff" and c["passed"] for c in ov["validation"]["checks"])
                for ov in origin_validations
            ) if origin_validations else False,
            "details": f"All products produced after {EUDR_CUTOFF_DATE}"
        },
        {
            "item": "Geolocation Verified",
            "passed": all(
                ov["validation"]["risk_score"] >= 80
                for ov in origin_validations
            ) if origin_validations else False,
            "details": "All origins have valid geolocations"
        },
        {
            "item": "EUDR Due Diligence Document",
            "passed": has_eudr_doc,
            "details": "Due diligence statement uploaded" if has_eudr_doc else "Due diligence statement required"
        },
        {
            "item": "Risk Assessment",
            "passed": highest_risk in [RiskLevel.LOW, RiskLevel.MEDIUM],
            "details": f"Overall risk level: {highest_risk.value.upper()}"
        }
    ]

    # Overall status
    overall_status = EUDRValidationStatus.COMPLIANT
    if not all_compliant or not has_eudr_doc:
        if any(not item["passed"] for item in checklist[:3]):  # Critical items
            overall_status = EUDRValidationStatus.NON_COMPLIANT
        else:
            overall_status = EUDRValidationStatus.INCOMPLETE

    return {
        "shipment_id": str(shipment.id),
        "shipment_reference": shipment.reference,
        "overall_status": overall_status.value,
        "overall_risk_level": highest_risk.value,
        "is_compliant": overall_status == EUDRValidationStatus.COMPLIANT,
        "checklist": checklist,
        "summary": {
            "total_origins": total_origins,
            "compliant_origins": compliant_origins,
            "has_eudr_document": has_eudr_doc,
            "passed_checks": len([c for c in checklist if c["passed"]]),
            "total_checks": len(checklist)
        },
        "origin_validations": origin_validations,
        "cutoff_date": EUDR_CUTOFF_DATE.isoformat(),
        "assessed_at": datetime.utcnow().isoformat()
    }


def calculate_risk_score(
    origin: Origin,
    validation_result: EUDRValidationResult
) -> int:
    """
    Calculate comprehensive EUDR risk score for an origin.

    Score starts at 100 and deductions are made for:
    - Missing data (-10 points per required field)
    - High risk country (-20 points)
    - Medium risk country (-10 points)
    - Unverified supplier (-15 points)
    - Incomplete documents (-10 points)
    - Production date concerns (-25 points)

    Args:
        origin: Origin to score
        validation_result: Validation result for the origin

    Returns:
        Risk score (0-100)
    """
    score = 100

    # Deduct for missing fields
    score -= len(validation_result.missing_fields) * 10

    # Deduct for country risk
    country_risk = COUNTRY_RISK_LEVELS.get(origin.country.upper() if origin.country else "", RiskLevel.UNKNOWN)
    if country_risk == RiskLevel.HIGH:
        score -= 20
    elif country_risk == RiskLevel.MEDIUM:
        score -= 10
    elif country_risk == RiskLevel.UNKNOWN:
        score -= 15

    # Deduct for unverified
    if not origin.verified_at:
        score -= 15

    # Deduct for production date issues
    prod_date = origin.harvest_date or origin.production_date
    if prod_date:
        valid, _ = validate_production_date(prod_date)
        if not valid:
            score -= 25
    else:
        score -= 20

    # Deduct for missing due diligence
    if not origin.due_diligence_statement_ref and not origin.deforestation_free_statement:
        score -= 15

    return max(0, min(100, score))
