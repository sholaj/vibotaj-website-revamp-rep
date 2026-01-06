"""
Test fixtures for TraceHub compliance tests.

These fixtures provide sample data for testing compliance rules,
especially EUDR (EU Deforestation Regulation) applicability.

Also includes shared fixtures for API testing.

IMPORTANT: All test files should import the shared database configuration
from this file to ensure proper database connection handling in both
local development and CI/Docker environments.

Usage in test files:
    from .conftest import engine, TestingSessionLocal, Base, get_test_database_url
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

def get_test_database_url() -> str:
    """
    Determine the correct database URL for tests.

    Priority:
    1. TEST_DATABASE_URL environment variable (set by CI or docker-compose.test.yml)
    2. DATABASE_URL environment variable (when running in container)
    3. CI environment detection (GitHub Actions uses port 5432)
    4. Default localhost connection (when running tests from host machine - port 5433)

    The docker-compose.test.yml sets TEST_DATABASE_URL to point to db-test service.
    When running in the main backend container, DATABASE_URL points to the db service.
    GitHub Actions CI uses PostgreSQL service on port 5432.
    """
    # First priority: explicit test database URL
    if os.environ.get("TEST_DATABASE_URL"):
        return os.environ["TEST_DATABASE_URL"]

    # Second priority: use DATABASE_URL if we're in a container
    # (indicated by DATABASE_URL starting with db or db-test as host)
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url and ("@db:" in database_url or "@db-test:" in database_url):
        # We're in a container, use the same DB but ensure it's the test database
        # Replace the database name with tracehub_test if not already
        if "/tracehub_test" not in database_url:
            # Keep the base URL but switch to test database
            base_url = database_url.rsplit("/", 1)[0]
            return f"{base_url}/tracehub_test"
        return database_url

    # Third priority: CI environment (GitHub Actions)
    # CI uses PostgreSQL service on standard port 5432
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        return "postgresql://tracehub_test:test_password@localhost:5432/tracehub_test"

    # Default: running from host machine, connect to exposed port 5433
    return "postgresql://tracehub:tracehub@localhost:5433/tracehub_test"


# Use PostgreSQL for testing (models use JSONB which SQLite doesn't support)
TEST_DATABASE_URL = get_test_database_url()

# Create engine with pool_pre_ping to handle connection issues gracefully
engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Export for use in test files - Re-export Base from app.database
__all__ = [
    'engine',
    'TestingSessionLocal',
    'Base',
    'get_test_database_url',
    'TEST_DATABASE_URL',
]


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
