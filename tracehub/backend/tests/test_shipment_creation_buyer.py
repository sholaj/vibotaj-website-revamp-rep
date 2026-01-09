"""
Tests for shipment creation with buyer_organization_id.

Phase 4: TDD Red Phase - Tests for buyer organization assignment on shipment creation.

These tests verify:
1. Shipments can be created with a buyer_organization_id
2. buyer_organization_id is optional (backward compatible)
3. Invalid/non-existent buyer_organization_id fails validation
4. buyer_organization_id must reference a BUYER-type organization
5. Response schemas include buyer organization information

TDD: These tests are written FIRST and should FAIL until implementation is complete.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from datetime import datetime
import uuid

from app.main import app
from app.database import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationType, OrganizationStatus
from app.models.shipment import Shipment, ShipmentStatus
from app.routers.auth import get_password_hash, get_current_active_user
from app.schemas.user import CurrentUser
from app.schemas.shipment import ShipmentCreate, ShipmentResponse
from app.services.permissions import get_role_permissions

# Import shared test database configuration from conftest
from .conftest import engine, TestingSessionLocal, Base


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def db_session():
    """Create test database session with clean schema."""
    # Drop and recreate schema for clean state
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def client(db_session):
    """Create test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]


@pytest.fixture(scope="module")
def org_vibotaj(db_session):
    """Create VIBOTAJ organization (exporter/platform owner)."""
    org = Organization(
        name="VIBOTAJ Global",
        slug=f"vibotaj-buyer-test-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.VIBOTAJ,
        status=OrganizationStatus.ACTIVE,
        contact_email="hq@vibotaj.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def org_hages_buyer(db_session):
    """Create HAGES buyer organization (German importer)."""
    org = Organization(
        name="HAGES GmbH",
        slug=f"hages-buyer-test-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.BUYER,
        status=OrganizationStatus.ACTIVE,
        contact_email="info@hages.de"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def org_witatrade_buyer(db_session):
    """Create Witatrade buyer organization (second buyer for testing)."""
    org = Organization(
        name="Witatrade BV",
        slug=f"witatrade-buyer-test-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.BUYER,
        status=OrganizationStatus.ACTIVE,
        contact_email="info@witatrade.nl"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def org_supplier(db_session):
    """Create a SUPPLIER-type organization (NOT a buyer)."""
    org = Organization(
        name="Nigerian Supplier Ltd",
        slug=f"supplier-test-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.SUPPLIER,
        status=OrganizationStatus.ACTIVE,
        contact_email="info@supplier.ng"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def org_logistics_agent(db_session):
    """Create a LOGISTICS_AGENT-type organization (NOT a buyer)."""
    org = Organization(
        name="Freight Forwarders Inc",
        slug=f"logistics-test-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.LOGISTICS_AGENT,
        status=OrganizationStatus.ACTIVE,
        contact_email="info@freight.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def vibotaj_admin(db_session, org_vibotaj):
    """Create admin user for VIBOTAJ (will create shipments)."""
    user = User(
        email=f"admin-buyer-test-{uuid.uuid4().hex[:6]}@vibotaj.com",
        full_name="VIBOTAJ Admin",
        hashed_password=get_password_hash("Admin123!"),
        role=UserRole.ADMIN,
        organization_id=org_vibotaj.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def mock_auth(user):
    """Create mock authentication for a user."""
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
# Test Class: Shipment Creation with Buyer Organization
# =============================================================================

class TestShipmentCreationWithBuyerOrg:
    """Tests for creating shipments with buyer_organization_id."""

    def test_create_shipment_with_buyer_org_id(
        self, client, vibotaj_admin, org_vibotaj, org_hages_buyer
    ):
        """
        Create shipment with valid buyer_organization_id.

        When VIBOTAJ creates a shipment destined for HAGES, the shipment
        should include buyer_organization_id pointing to HAGES.

        Expected: 201 Created with buyer_organization_id in response.
        """
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(vibotaj_admin)

        shipment_data = {
            "reference": f"VIBO-HAGES-{uuid.uuid4().hex[:6]}",
            "container_number": "MSKU1234567",
            "bl_number": "BL-HAGES-001",
            "vessel_name": "MAERSK SEALAND",
            "voyage_number": "V100",
            "organization_id": str(org_vibotaj.id),
            "buyer_organization_id": str(org_hages_buyer.id),  # Key field being tested
            "importer_name": "HAGES GmbH",
            "exporter_name": "VIBOTAJ Global Nigeria Ltd",
            "product_type": "horn_hoof"
        }

        response = client.post("/api/shipments", json=shipment_data)

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"
        data = response.json()

        # Verify buyer_organization_id is in response
        assert "buyer_organization_id" in data, "Response should include buyer_organization_id"
        assert data["buyer_organization_id"] == str(org_hages_buyer.id)
        assert data["reference"] == shipment_data["reference"]
        assert data["organization_id"] == str(org_vibotaj.id)

        del app.dependency_overrides[get_current_active_user]

    def test_create_shipment_without_buyer_org_id(
        self, client, vibotaj_admin, org_vibotaj
    ):
        """
        Create shipment without buyer_organization_id (optional field).

        For backward compatibility, buyer_organization_id should be optional.
        Shipments can still be created without specifying a buyer org.

        Expected: 201 Created with buyer_organization_id as null.
        """
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(vibotaj_admin)

        shipment_data = {
            "reference": f"VIBO-NOBUYER-{uuid.uuid4().hex[:6]}",
            "container_number": "TCNU7654321",
            "organization_id": str(org_vibotaj.id),
            "product_type": "horn_hoof"
            # No buyer_organization_id - should be optional
        }

        response = client.post("/api/shipments", json=shipment_data)

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"
        data = response.json()

        # buyer_organization_id should be null/None when not provided
        assert "buyer_organization_id" in data, "Response should include buyer_organization_id field"
        assert data["buyer_organization_id"] is None, "buyer_organization_id should be null when not provided"

        del app.dependency_overrides[get_current_active_user]

    def test_create_shipment_invalid_buyer_org_id_fails(
        self, client, vibotaj_admin, org_vibotaj
    ):
        """
        Create shipment with invalid UUID for buyer_organization_id.

        An invalid UUID format should be rejected by Pydantic validation.

        Expected: 400/422 Bad Request with validation error.
        """
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(vibotaj_admin)

        shipment_data = {
            "reference": f"VIBO-INVALID-{uuid.uuid4().hex[:6]}",
            "container_number": "INVU1234567",
            "organization_id": str(org_vibotaj.id),
            "buyer_organization_id": "not-a-valid-uuid",  # Invalid UUID
            "product_type": "horn_hoof"
        }

        response = client.post("/api/shipments", json=shipment_data)

        # Should fail with 400 or 422 (Pydantic validation error)
        assert response.status_code in [400, 422], \
            f"Expected 400/422 for invalid UUID, got {response.status_code}: {response.json()}"

        del app.dependency_overrides[get_current_active_user]

    def test_create_shipment_nonexistent_buyer_org_id_fails(
        self, client, vibotaj_admin, org_vibotaj
    ):
        """
        Create shipment with non-existent buyer_organization_id.

        A valid UUID that doesn't match any organization should be rejected.

        Expected: 400/404 with appropriate error message.
        """
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(vibotaj_admin)

        non_existent_id = str(uuid.uuid4())  # Valid UUID but doesn't exist

        shipment_data = {
            "reference": f"VIBO-NONEXIST-{uuid.uuid4().hex[:6]}",
            "container_number": "NXST1234567",
            "organization_id": str(org_vibotaj.id),
            "buyer_organization_id": non_existent_id,
            "product_type": "horn_hoof"
        }

        response = client.post("/api/shipments", json=shipment_data)

        # Should fail with 400 or 404
        assert response.status_code in [400, 404], \
            f"Expected 400/404 for non-existent org, got {response.status_code}: {response.json()}"

        error_detail = response.json().get("detail", "")
        assert "buyer" in error_detail.lower() or "organization" in error_detail.lower() or "not found" in error_detail.lower(), \
            f"Error message should mention buyer organization: {error_detail}"

        del app.dependency_overrides[get_current_active_user]

    def test_create_shipment_non_buyer_type_org_fails(
        self, client, vibotaj_admin, org_vibotaj, org_supplier
    ):
        """
        Create shipment with buyer_organization_id pointing to non-BUYER org type.

        buyer_organization_id should only accept organizations of type BUYER.
        Using SUPPLIER, LOGISTICS_AGENT, or VIBOTAJ should fail.

        Expected: 400 Bad Request with error about organization type.
        """
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(vibotaj_admin)

        shipment_data = {
            "reference": f"VIBO-WRONGTYPE-{uuid.uuid4().hex[:6]}",
            "container_number": "WRNG1234567",
            "organization_id": str(org_vibotaj.id),
            "buyer_organization_id": str(org_supplier.id),  # SUPPLIER, not BUYER
            "product_type": "horn_hoof"
        }

        response = client.post("/api/shipments", json=shipment_data)

        assert response.status_code == 400, \
            f"Expected 400 for non-BUYER org type, got {response.status_code}: {response.json()}"

        error_detail = response.json().get("detail", "")
        assert "buyer" in error_detail.lower() or "type" in error_detail.lower(), \
            f"Error message should mention buyer type requirement: {error_detail}"

        del app.dependency_overrides[get_current_active_user]

    def test_create_shipment_logistics_agent_type_org_fails(
        self, client, vibotaj_admin, org_vibotaj, org_logistics_agent
    ):
        """
        Create shipment with buyer_organization_id pointing to LOGISTICS_AGENT.

        LOGISTICS_AGENT organizations are not buyers and should be rejected.

        Expected: 400 Bad Request.
        """
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(vibotaj_admin)

        shipment_data = {
            "reference": f"VIBO-LOGISTICS-{uuid.uuid4().hex[:6]}",
            "container_number": "LGST1234567",
            "organization_id": str(org_vibotaj.id),
            "buyer_organization_id": str(org_logistics_agent.id),  # Not a BUYER
            "product_type": "horn_hoof"
        }

        response = client.post("/api/shipments", json=shipment_data)

        assert response.status_code == 400, \
            f"Expected 400 for LOGISTICS_AGENT org type, got {response.status_code}: {response.json()}"

        del app.dependency_overrides[get_current_active_user]

    def test_create_shipment_vibotaj_type_as_buyer_fails(
        self, client, vibotaj_admin, org_vibotaj
    ):
        """
        Create shipment with buyer_organization_id pointing to VIBOTAJ org.

        VIBOTAJ is the exporter/platform owner, not a buyer.

        Expected: 400 Bad Request.
        """
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(vibotaj_admin)

        # Create another VIBOTAJ org to use as "buyer" (should fail)
        shipment_data = {
            "reference": f"VIBO-SELFBUYER-{uuid.uuid4().hex[:6]}",
            "container_number": "SELF1234567",
            "organization_id": str(org_vibotaj.id),
            "buyer_organization_id": str(org_vibotaj.id),  # Same org as seller - invalid
            "product_type": "horn_hoof"
        }

        response = client.post("/api/shipments", json=shipment_data)

        assert response.status_code == 400, \
            f"Expected 400 for VIBOTAJ as buyer, got {response.status_code}: {response.json()}"

        del app.dependency_overrides[get_current_active_user]

    def test_created_shipment_has_buyer_org_relationship(
        self, client, db_session, vibotaj_admin, org_vibotaj, org_witatrade_buyer
    ):
        """
        Created shipment should have buyer_organization relationship loaded.

        When fetching the shipment, the buyer_organization should be accessible
        for queries and responses.

        Expected: Shipment has buyer_organization relationship populated.
        """
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(vibotaj_admin)

        shipment_ref = f"VIBO-WITA-{uuid.uuid4().hex[:6]}"
        shipment_data = {
            "reference": shipment_ref,
            "container_number": "WITA1234567",
            "bl_number": "BL-WITA-001",
            "organization_id": str(org_vibotaj.id),
            "buyer_organization_id": str(org_witatrade_buyer.id),
            "product_type": "horn_hoof"
        }

        response = client.post("/api/shipments", json=shipment_data)
        assert response.status_code == 201

        created_shipment_id = response.json()["id"]

        # Verify in database that relationship is set
        from app.models.shipment import Shipment
        from sqlalchemy.orm import joinedload

        db_shipment = (
            db_session.query(Shipment)
            .options(joinedload(Shipment.buyer_organization))
            .filter(Shipment.id == created_shipment_id)
            .first()
        )

        assert db_shipment is not None
        assert db_shipment.buyer_organization_id == org_witatrade_buyer.id
        assert db_shipment.buyer_organization is not None
        assert db_shipment.buyer_organization.name == "Witatrade BV"
        assert db_shipment.buyer_organization.type == OrganizationType.BUYER

        del app.dependency_overrides[get_current_active_user]


# =============================================================================
# Test Class: Schema Validation
# =============================================================================

class TestShipmentSchemaValidation:
    """Tests for ShipmentCreate and ShipmentResponse schema validation."""

    def test_shipment_create_schema_accepts_buyer_org_id(self):
        """
        ShipmentCreate schema should accept buyer_organization_id as UUID.

        This tests that the Pydantic schema is properly defined.
        """
        valid_data = {
            "reference": "TEST-SCHEMA-001",
            "container_number": "MSKU1234567",
            "organization_id": str(uuid.uuid4()),
            "buyer_organization_id": str(uuid.uuid4()),
            "product_type": "horn_hoof"
        }

        # Should not raise validation error
        schema = ShipmentCreate(**valid_data)
        assert schema.buyer_organization_id is not None
        assert isinstance(schema.buyer_organization_id, uuid.UUID)

    def test_shipment_create_schema_buyer_org_id_optional(self):
        """
        buyer_organization_id should be Optional in ShipmentCreate schema.

        This tests backward compatibility - existing clients should work.
        """
        valid_data = {
            "reference": "TEST-SCHEMA-002",
            "container_number": "TCNU1234567",
            "organization_id": str(uuid.uuid4()),
            "product_type": "horn_hoof"
            # No buyer_organization_id
        }

        # Should not raise validation error
        schema = ShipmentCreate(**valid_data)
        assert schema.buyer_organization_id is None

    def test_shipment_create_schema_rejects_invalid_uuid(self):
        """
        ShipmentCreate schema should reject invalid UUID for buyer_organization_id.
        """
        invalid_data = {
            "reference": "TEST-SCHEMA-003",
            "container_number": "INVU1234567",
            "organization_id": str(uuid.uuid4()),
            "buyer_organization_id": "not-a-uuid",
            "product_type": "horn_hoof"
        }

        with pytest.raises(Exception):  # Pydantic ValidationError
            ShipmentCreate(**invalid_data)


# =============================================================================
# Test Class: Response with Buyer Organization
# =============================================================================

class TestShipmentResponseWithBuyerOrg:
    """Tests for shipment response including buyer organization info."""

    def test_shipment_response_includes_buyer_org_id(
        self, client, vibotaj_admin, org_vibotaj, org_hages_buyer
    ):
        """
        ShipmentResponse should include buyer_organization_id field.

        When listing or fetching shipments, buyer_organization_id should be visible.
        """
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(vibotaj_admin)

        # Create shipment with buyer
        shipment_ref = f"VIBO-RESP-{uuid.uuid4().hex[:6]}"
        shipment_data = {
            "reference": shipment_ref,
            "container_number": "RESP1234567",
            "organization_id": str(org_vibotaj.id),
            "buyer_organization_id": str(org_hages_buyer.id),
            "product_type": "horn_hoof"
        }

        create_response = client.post("/api/shipments", json=shipment_data)
        assert create_response.status_code == 201
        shipment_id = create_response.json()["id"]

        # Fetch shipment list and verify buyer_organization_id is present
        list_response = client.get("/api/shipments")
        assert list_response.status_code == 200

        shipments = list_response.json()
        created_shipment = next(
            (s for s in shipments if s["reference"] == shipment_ref), None
        )

        assert created_shipment is not None
        assert "buyer_organization_id" in created_shipment
        assert created_shipment["buyer_organization_id"] == str(org_hages_buyer.id)

        del app.dependency_overrides[get_current_active_user]

    def test_shipment_detail_includes_buyer_organization(
        self, client, db_session, vibotaj_admin, org_vibotaj, org_hages_buyer
    ):
        """
        ShipmentDetailResponse should include buyer_organization information.

        When fetching a single shipment with buyer_organization_id,
        the detail response should include the buyer organization details.
        """
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(vibotaj_admin)

        # Create shipment with buyer
        shipment_ref = f"VIBO-DETAIL-{uuid.uuid4().hex[:6]}"
        shipment_data = {
            "reference": shipment_ref,
            "container_number": "DTIL1234567",
            "organization_id": str(org_vibotaj.id),
            "buyer_organization_id": str(org_hages_buyer.id),
            "product_type": "horn_hoof"
        }

        create_response = client.post("/api/shipments", json=shipment_data)
        assert create_response.status_code == 201
        shipment_id = create_response.json()["id"]

        # Fetch shipment detail
        detail_response = client.get(f"/api/shipments/{shipment_id}")
        assert detail_response.status_code == 200

        detail_data = detail_response.json()

        # The detail response wraps shipment in 'shipment' key
        assert "shipment" in detail_data
        shipment = detail_data["shipment"]

        # Verify buyer_organization_id is in shipment data
        assert "buyer_organization_id" in shipment
        assert shipment["buyer_organization_id"] == str(org_hages_buyer.id)

        # Optionally, detail response could include buyer_organization info
        # This depends on whether we add it to ShipmentDetailResponse
        # For now, just verify the ID is present in the shipment

        del app.dependency_overrides[get_current_active_user]

    def test_shipment_detail_without_buyer_organization(
        self, client, vibotaj_admin, org_vibotaj
    ):
        """
        ShipmentDetailResponse should handle null buyer_organization gracefully.

        Shipments without buyer_organization_id should still work correctly.
        """
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(vibotaj_admin)

        # Create shipment without buyer
        shipment_ref = f"VIBO-NOBUYER-DETAIL-{uuid.uuid4().hex[:6]}"
        shipment_data = {
            "reference": shipment_ref,
            "container_number": "NBDT1234567",
            "organization_id": str(org_vibotaj.id),
            "product_type": "horn_hoof"
            # No buyer_organization_id
        }

        create_response = client.post("/api/shipments", json=shipment_data)
        assert create_response.status_code == 201
        shipment_id = create_response.json()["id"]

        # Fetch shipment detail
        detail_response = client.get(f"/api/shipments/{shipment_id}")
        assert detail_response.status_code == 200

        detail_data = detail_response.json()
        shipment = detail_data["shipment"]

        # buyer_organization_id should be null
        assert "buyer_organization_id" in shipment
        assert shipment["buyer_organization_id"] is None

        del app.dependency_overrides[get_current_active_user]


# =============================================================================
# Test Class: Query Shipments by Buyer Organization
# =============================================================================

class TestQueryShipmentsByBuyerOrg:
    """Tests for querying shipments filtered by buyer organization."""

    @pytest.mark.skip(reason="Filter endpoint not yet implemented - Phase 5")
    def test_filter_shipments_by_buyer_org_id(
        self, client, vibotaj_admin, org_vibotaj, org_hages_buyer, org_witatrade_buyer
    ):
        """
        Should be able to filter shipments by buyer_organization_id.

        This is a future enhancement - listing shipments for a specific buyer.
        """
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(vibotaj_admin)

        # Create shipments for different buyers
        for i, buyer in enumerate([org_hages_buyer, org_witatrade_buyer]):
            shipment_data = {
                "reference": f"VIBO-FILTER-{i}-{uuid.uuid4().hex[:6]}",
                "container_number": f"FLTR{i}234567",
                "organization_id": str(org_vibotaj.id),
                "buyer_organization_id": str(buyer.id),
                "product_type": "horn_hoof"
            }
            client.post("/api/shipments", json=shipment_data)

        # Filter by HAGES buyer
        response = client.get(f"/api/shipments?buyer_organization_id={org_hages_buyer.id}")
        assert response.status_code == 200

        shipments = response.json()
        for shipment in shipments:
            assert shipment["buyer_organization_id"] == str(org_hages_buyer.id)

        del app.dependency_overrides[get_current_active_user]
