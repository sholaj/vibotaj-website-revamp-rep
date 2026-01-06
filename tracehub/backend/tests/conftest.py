"""
Test fixtures for TraceHub compliance tests.

These fixtures provide sample data for testing compliance rules,
especially EUDR (EU Deforestation Regulation) applicability.

Also includes shared fixtures for API testing.
"""
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationType, OrganizationStatus
from app.routers.auth import get_password_hash, get_current_active_user
from app.schemas.user import CurrentUser
from app.services.permissions import get_role_permissions


# =============================================================================
# Database Configuration for Tests
# =============================================================================

# Use PostgreSQL for testing (models use JSONB which SQLite doesn't support)
# The docker-compose.yml exposes PostgreSQL on port 5433
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://tracehub:tracehub@localhost:5433/tracehub_test"
)

engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# =============================================================================
# Shared Database Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def fresh_db_session():
    """
    Create a fresh database session for each test function.
    
    Use this when tests modify data and need isolation.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def db_session():
    """
    Create a database session that persists for the test module.
    
    More efficient for read-only tests or tests that share data.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


# =============================================================================
# Test Client Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def api_client(db_session):
    """
    Create a FastAPI test client with database override.
    
    Use this for API endpoint testing.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    del app.dependency_overrides[get_db]


# =============================================================================
# Organization Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def vibotaj_org(db_session):
    """Create the VIBOTAJ organization - platform owner."""
    org = Organization(
        name="VIBOTAJ Trading",
        slug=f"vibotaj-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.VIBOTAJ,
        status=OrganizationStatus.ACTIVE,
        contact_email="hq@vibotaj.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def hages_org(db_session):
    """Create HAGES - a German buyer organization."""
    org = Organization(
        name="HAGES GmbH",
        slug=f"hages-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.BUYER,
        status=OrganizationStatus.ACTIVE,
        contact_email="info@hages.de"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


# =============================================================================
# User Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def vibotaj_admin(db_session, vibotaj_org):
    """Create an admin user for VIBOTAJ."""
    user = User(
        email="admin@vibotaj.com",
        full_name="VIBOTAJ Admin",
        hashed_password=get_password_hash("Admin123!"),
        role=UserRole.ADMIN,
        organization_id=vibotaj_org.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="module")
def hages_admin(db_session, hages_org):
    """Create an admin user for HAGES."""
    user = User(
        email="admin@hages.de",
        full_name="HAGES Admin",
        hashed_password=get_password_hash("Hages123!"),
        role=UserRole.ADMIN,
        organization_id=hages_org.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# =============================================================================
# Authentication Helpers
# =============================================================================

def create_mock_auth(user: User) -> CurrentUser:
    """
    Create a mock CurrentUser object for testing authenticated endpoints.
    
    Usage:
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_auth(user)
    """
    permissions = [p.value for p in get_role_permissions(user.role)]
    return CurrentUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        organization_id=user.organization_id,
        permissions=permissions
    )


# =============================================================================
# Compliance Test Fixtures (Original)
# =============================================================================

@pytest.fixture
def sample_horn_hoof_shipment():
    """Sample shipment - horn/hoof product (NO EUDR).
    
    Horn and hoof products (HS 0506/0507) are NOT covered by EUDR.
    They should never require geolocation or deforestation statements.
    """
    return {
        "id": "SHIP-001",
        "hs_code": "0506.10",
        "product_type": "HORN_HOOF",
        "product_name": "Cattle Horns",
        "eudr_required": False,  # CRITICAL: Always False for 0506/0507
        "required_docs": [
            "EU_TRACES",
            "VETERINARY_HEALTH_CERT",
            "CERTIFICATE_OF_ORIGIN",
            "BILL_OF_LADING",
            "COMMERCIAL_INVOICE",
            "PACKING_LIST",
        ],
        "traces_number": "RC1479592",
        "origin_country": "Nigeria",
        "destination": "Germany",
        "buyer": "HAGES",
    }


@pytest.fixture
def sample_sweet_potato_shipment():
    """Sample shipment - sweet potato pellets (NO EUDR)."""
    return {
        "id": "SHIP-002",
        "hs_code": "0714.20",
        "product_type": "SWEET_POTATO_PELLETS",
        "product_name": "Sweet Potato Pellets",
        "eudr_required": False,
        "required_docs": [
            "PHYTOSANITARY_CERT",
            "CERTIFICATE_OF_ORIGIN",
            "QUALITY_CERT",
            "BILL_OF_LADING",
            "COMMERCIAL_INVOICE",
        ],
        "origin_country": "Nigeria",
        "destination": "Belgium",
        "buyer": "De Lochting",
    }


@pytest.fixture
def sample_cocoa_shipment():
    """Sample shipment - cocoa beans (EUDR APPLICABLE).
    
    Cocoa (HS 1801) IS covered by EUDR and requires additional documentation.
    This is for future use when VIBOTAJ expands to cocoa products.
    """
    return {
        "id": "SHIP-003",
        "hs_code": "1801.00",
        "product_type": "COCOA",
        "product_name": "Cocoa Beans",
        "eudr_required": True,  # YES - cocoa is in EUDR Annex I
        "required_docs": [
            "CERTIFICATE_OF_ORIGIN",
            "BILL_OF_LADING",
            "COMMERCIAL_INVOICE",
            "PHYTOSANITARY_CERT",
            "EUDR_STATEMENT",
            "GEOLOCATION_DATA",
            "RISK_ASSESSMENT",
        ],
        "origin_country": "Nigeria",
        "destination": "Germany",
        "geolocation": {
            "latitude": 7.3775,
            "longitude": 3.9470,
            "polygon": [],  # Farm boundary coordinates
        },
    }


@pytest.fixture
def traces_number():
    """VIBOTAJ EU TRACES number for animal products."""
    return "RC1479592"


@pytest.fixture
def eudr_applicable_hs_codes():
    """List of HS codes that require EUDR compliance.
    
    Based on EUDR Annex I:
    - 1801: Cocoa
    - 0901: Coffee
    - 1511: Palm oil
    - 4001: Rubber
    - 1201: Soybeans
    """
    return ["1801", "0901", "1511", "4001", "1201"]


@pytest.fixture
def non_eudr_hs_codes():
    """List of VIBOTAJ product HS codes that are NOT EUDR-applicable."""
    return {
        "0506": "Horn",
        "0507": "Hoof",
        "0714.20": "Sweet Potato Pellets",
        "0902.10": "Hibiscus Flowers",
        "0910.11": "Dried Ginger",
    }
