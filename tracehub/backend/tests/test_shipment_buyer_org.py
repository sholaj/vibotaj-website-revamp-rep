"""
Tests for buyer_organization_id field on Shipment model.

TDD Phase 1: RED - These tests should FAIL initially.

This field allows VIBOTAJ (exporter) to associate a shipment with a specific
buyer organization, enabling:
- Buyer visibility: Buyers can see shipments assigned to them
- Cross-organization sharing: VIBOTAJ creates shipment, buyer can view
- Compliance tracking: Documents flow to the correct buyer

Test coverage:
1. Model field existence and type (UUID, nullable)
2. Setting buyer_organization_id to valid buyer org
3. Relationship loading (buyer_organization)
4. Index verification for query performance
5. Backward compatibility (existing shipments without field)
6. Constraint: buyer_organization must be of type BUYER
"""
import pytest
from datetime import datetime
from sqlalchemy import text, inspect
from sqlalchemy.exc import IntegrityError
import uuid

from app.models.shipment import Shipment, ShipmentStatus
from app.models.organization import Organization, OrganizationType, OrganizationStatus

# Import shared test database configuration
from .conftest import engine, TestingSessionLocal, Base


@pytest.fixture(scope="module")
def db_session():
    """Create test database session with clean schema."""
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def exporter_org(db_session):
    """Create VIBOTAJ exporter organization."""
    org = Organization(
        name="VIBOTAJ Global",
        slug=f"vibotaj-buyer-test-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.VIBOTAJ,
        status=OrganizationStatus.ACTIVE,
        contact_email="export@vibotaj.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def buyer_org_hages(db_session):
    """Create HAGES buyer organization."""
    org = Organization(
        name="HAGES GmbH",
        slug=f"hages-buyer-test-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.BUYER,
        status=OrganizationStatus.ACTIVE,
        contact_email="import@hages.de"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def buyer_org_witatrade(db_session):
    """Create Witatrade buyer organization."""
    org = Organization(
        name="Witatrade GmbH",
        slug=f"witatrade-buyer-test-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.BUYER,
        status=OrganizationStatus.ACTIVE,
        contact_email="import@witatrade.de"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def supplier_org(db_session):
    """Create a supplier organization (NOT a buyer)."""
    org = Organization(
        name="Lagos Supplier Co",
        slug=f"lagos-supplier-test-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.SUPPLIER,
        status=OrganizationStatus.ACTIVE,
        contact_email="sales@lagossupplier.ng"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


class TestBuyerOrganizationFieldExists:
    """Tests to verify the buyer_organization_id field exists on Shipment model."""

    def test_shipment_model_has_buyer_organization_id_attribute(self, db_session, exporter_org):
        """
        FAILING TEST: Shipment model should have buyer_organization_id attribute.

        This will fail because the field doesn't exist yet.
        """
        shipment = Shipment(
            reference="BUYERTEST-001",
            container_number="MSKU1234567",
            status=ShipmentStatus.DRAFT,
            organization_id=exporter_org.id
        )

        # This should NOT raise AttributeError after implementation
        assert hasattr(shipment, 'buyer_organization_id'), \
            "Shipment model should have buyer_organization_id attribute"

    def test_shipment_buyer_organization_id_column_exists_in_database(self, db_session):
        """
        FAILING TEST: Database should have buyer_organization_id column.

        Verifies the column exists at the database level.
        """
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('shipments')]

        assert 'buyer_organization_id' in columns, \
            "shipments table should have buyer_organization_id column"

    def test_shipment_buyer_organization_id_is_uuid_type(self, db_session):
        """
        FAILING TEST: buyer_organization_id should be UUID type.

        Verifies the column is the correct PostgreSQL UUID type.
        """
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('shipments')}

        assert 'buyer_organization_id' in columns, \
            "buyer_organization_id column must exist"

        # Check column type is UUID
        col_type = str(columns['buyer_organization_id']['type'])
        assert 'UUID' in col_type.upper(), \
            f"buyer_organization_id should be UUID type, got {col_type}"

    def test_shipment_buyer_organization_id_is_nullable(self, db_session, exporter_org):
        """
        FAILING TEST: buyer_organization_id should be nullable.

        Existing shipments may not have a buyer assigned yet.
        """
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('shipments')}

        assert 'buyer_organization_id' in columns, \
            "buyer_organization_id column must exist"

        assert columns['buyer_organization_id']['nullable'] is True, \
            "buyer_organization_id should be nullable for backward compatibility"


class TestBuyerOrganizationFieldAssignment:
    """Tests for assigning buyer_organization_id to shipments."""

    def test_create_shipment_with_buyer_organization_id(
        self, db_session, exporter_org, buyer_org_hages
    ):
        """
        FAILING TEST: Should create shipment with buyer_organization_id.

        VIBOTAJ creates a shipment and assigns it to HAGES buyer.
        """
        shipment = Shipment(
            reference="HAGESSHIP-001",
            container_number="MSKU2345678",
            status=ShipmentStatus.DRAFT,
            organization_id=exporter_org.id,
            buyer_organization_id=buyer_org_hages.id  # This will fail - field doesn't exist
        )
        db_session.add(shipment)
        db_session.commit()
        db_session.refresh(shipment)

        assert shipment.buyer_organization_id == buyer_org_hages.id

        # Cleanup
        db_session.delete(shipment)
        db_session.commit()

    def test_create_shipment_without_buyer_organization_id(self, db_session, exporter_org):
        """
        FAILING TEST: Should create shipment without buyer_organization_id (null).

        Backward compatibility - existing workflows don't set buyer.
        """
        shipment = Shipment(
            reference="NOBUYER-001",
            container_number="MSKU3456789",
            status=ShipmentStatus.DRAFT,
            organization_id=exporter_org.id
            # buyer_organization_id intentionally not set
        )
        db_session.add(shipment)
        db_session.commit()
        db_session.refresh(shipment)

        # Field should exist and be None
        assert hasattr(shipment, 'buyer_organization_id'), \
            "Shipment should have buyer_organization_id attribute"
        assert shipment.buyer_organization_id is None, \
            "buyer_organization_id should be None when not set"

        # Cleanup
        db_session.delete(shipment)
        db_session.commit()

    def test_update_shipment_buyer_organization_id(
        self, db_session, exporter_org, buyer_org_hages, buyer_org_witatrade
    ):
        """
        FAILING TEST: Should update buyer_organization_id on existing shipment.

        Shipment initially assigned to HAGES, then reassigned to Witatrade.
        """
        # Create shipment assigned to HAGES
        shipment = Shipment(
            reference="REASSIGN-001",
            container_number="MSKU4567890",
            status=ShipmentStatus.DRAFT,
            organization_id=exporter_org.id,
            buyer_organization_id=buyer_org_hages.id
        )
        db_session.add(shipment)
        db_session.commit()
        db_session.refresh(shipment)

        assert shipment.buyer_organization_id == buyer_org_hages.id

        # Reassign to Witatrade
        shipment.buyer_organization_id = buyer_org_witatrade.id
        db_session.commit()
        db_session.refresh(shipment)

        assert shipment.buyer_organization_id == buyer_org_witatrade.id

        # Cleanup
        db_session.delete(shipment)
        db_session.commit()

    def test_clear_buyer_organization_id(self, db_session, exporter_org, buyer_org_hages):
        """
        FAILING TEST: Should allow clearing buyer_organization_id (set to None).

        Useful when buyer assignment is revoked or changed.
        """
        shipment = Shipment(
            reference="CLEARBUYER-001",
            container_number="MSKU5678901",
            status=ShipmentStatus.DRAFT,
            organization_id=exporter_org.id,
            buyer_organization_id=buyer_org_hages.id
        )
        db_session.add(shipment)
        db_session.commit()

        # Clear buyer assignment
        shipment.buyer_organization_id = None
        db_session.commit()
        db_session.refresh(shipment)

        assert shipment.buyer_organization_id is None

        # Cleanup
        db_session.delete(shipment)
        db_session.commit()


class TestBuyerOrganizationRelationship:
    """Tests for the buyer_organization relationship on Shipment."""

    def test_shipment_has_buyer_organization_relationship(self, db_session):
        """
        FAILING TEST: Shipment should have buyer_organization relationship.

        Verifies the relationship is defined on the model.
        """
        assert hasattr(Shipment, 'buyer_organization'), \
            "Shipment model should have buyer_organization relationship"

    def test_buyer_organization_relationship_loads_correctly(
        self, db_session, exporter_org, buyer_org_hages
    ):
        """
        FAILING TEST: buyer_organization relationship should load the buyer org.

        Accessing shipment.buyer_organization should return the Organization object.
        """
        shipment = Shipment(
            reference="RELTEST-001",
            container_number="MSKU6789012",
            status=ShipmentStatus.DRAFT,
            organization_id=exporter_org.id,
            buyer_organization_id=buyer_org_hages.id
        )
        db_session.add(shipment)
        db_session.commit()
        db_session.refresh(shipment)

        # Access the relationship
        buyer = shipment.buyer_organization

        assert buyer is not None, "buyer_organization should not be None"
        assert buyer.id == buyer_org_hages.id
        assert buyer.name == "HAGES GmbH"
        assert buyer.type == OrganizationType.BUYER

        # Cleanup
        db_session.delete(shipment)
        db_session.commit()

    def test_buyer_organization_relationship_is_none_when_not_set(
        self, db_session, exporter_org
    ):
        """
        FAILING TEST: buyer_organization should be None when buyer_organization_id is None.
        """
        shipment = Shipment(
            reference="RELNULL-001",
            container_number="MSKU7890123",
            status=ShipmentStatus.DRAFT,
            organization_id=exporter_org.id
            # buyer_organization_id not set
        )
        db_session.add(shipment)
        db_session.commit()
        db_session.refresh(shipment)

        assert shipment.buyer_organization is None, \
            "buyer_organization should be None when buyer_organization_id is not set"

        # Cleanup
        db_session.delete(shipment)
        db_session.commit()


class TestBuyerOrganizationIndex:
    """Tests for buyer_organization_id index for query performance."""

    def test_buyer_organization_id_has_index(self, db_session):
        """
        FAILING TEST: buyer_organization_id should be indexed.

        Required for efficient queries when buyers fetch their shipments.
        """
        inspector = inspect(engine)
        indexes = inspector.get_indexes('shipments')

        # Look for an index containing buyer_organization_id
        buyer_org_indexes = [
            idx for idx in indexes
            if 'buyer_organization_id' in idx.get('column_names', [])
        ]

        assert len(buyer_org_indexes) > 0, \
            "buyer_organization_id should have an index for query performance"

    def test_buyer_organization_id_index_name(self, db_session):
        """
        FAILING TEST: Verify the index name follows conventions.

        Index should be named like ix_shipments_buyer_organization_id.
        """
        inspector = inspect(engine)
        indexes = inspector.get_indexes('shipments')

        index_names = [idx['name'] for idx in indexes]

        # Check for an index with buyer_organization_id in the name
        has_buyer_org_index = any(
            'buyer_organization_id' in (name or '')
            for name in index_names
        )

        assert has_buyer_org_index, \
            "Should have an index named with 'buyer_organization_id'"


class TestBuyerOrganizationForeignKey:
    """Tests for buyer_organization_id foreign key constraint."""

    def test_buyer_organization_id_references_organizations_table(self, db_session):
        """
        FAILING TEST: buyer_organization_id should reference organizations table.

        Foreign key ensures referential integrity.
        """
        inspector = inspect(engine)
        foreign_keys = inspector.get_foreign_keys('shipments')

        # Find FK for buyer_organization_id
        buyer_org_fks = [
            fk for fk in foreign_keys
            if 'buyer_organization_id' in fk.get('constrained_columns', [])
        ]

        assert len(buyer_org_fks) > 0, \
            "buyer_organization_id should have a foreign key constraint"

        fk = buyer_org_fks[0]
        assert fk['referred_table'] == 'organizations', \
            "buyer_organization_id FK should reference organizations table"

    def test_invalid_buyer_organization_id_raises_integrity_error(
        self, db_session, exporter_org
    ):
        """
        FAILING TEST: Invalid buyer_organization_id should raise IntegrityError.

        Cannot assign a non-existent organization as buyer.
        """
        fake_uuid = uuid.uuid4()  # Non-existent org ID

        shipment = Shipment(
            reference="FAKEBUYERTEST-001",
            container_number="MSKU8901234",
            status=ShipmentStatus.DRAFT,
            organization_id=exporter_org.id,
            buyer_organization_id=fake_uuid
        )

        db_session.add(shipment)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()


class TestBackwardCompatibility:
    """Tests ensuring backward compatibility with existing shipments."""

    def test_existing_shipments_without_buyer_org_remain_valid(
        self, db_session, exporter_org
    ):
        """
        FAILING TEST: Existing shipments created before this feature should work.

        No migration should break existing data.
        """
        # Simulate an "existing" shipment (created without buyer_organization_id)
        shipment = Shipment(
            reference="LEGACY-001",
            container_number="MSKU9012345",
            bl_number="BL-LEGACY-001",
            vessel_name="MSC LEGACY",
            status=ShipmentStatus.IN_TRANSIT,
            organization_id=exporter_org.id
        )
        db_session.add(shipment)
        db_session.commit()
        db_session.refresh(shipment)

        # Should be queryable without errors
        queried = db_session.query(Shipment).filter(
            Shipment.id == shipment.id
        ).first()

        assert queried is not None
        assert queried.reference == "LEGACY-001"
        assert queried.buyer_organization_id is None

        # Cleanup
        db_session.delete(shipment)
        db_session.commit()

    def test_can_query_shipments_with_null_buyer_organization_id(
        self, db_session, exporter_org
    ):
        """
        FAILING TEST: Should query shipments where buyer_organization_id IS NULL.

        Useful for finding shipments not yet assigned to a buyer.
        """
        # Create shipments - some with buyer, some without
        shipment_no_buyer = Shipment(
            reference="NULLQUERY-001",
            container_number="MSKU0123456",
            status=ShipmentStatus.DRAFT,
            organization_id=exporter_org.id
        )
        db_session.add(shipment_no_buyer)
        db_session.commit()

        # Query for shipments without buyer
        unassigned = db_session.query(Shipment).filter(
            Shipment.organization_id == exporter_org.id,
            Shipment.buyer_organization_id.is_(None)
        ).all()

        assert len(unassigned) >= 1
        refs = [s.reference for s in unassigned]
        assert "NULLQUERY-001" in refs

        # Cleanup
        db_session.delete(shipment_no_buyer)
        db_session.commit()


class TestBuyerOrganizationQueries:
    """Tests for querying shipments by buyer_organization_id."""

    def test_query_shipments_by_buyer_organization_id(
        self, db_session, exporter_org, buyer_org_hages, buyer_org_witatrade
    ):
        """
        FAILING TEST: Should query shipments for a specific buyer.

        HAGES should only see their assigned shipments.
        """
        # Create shipments for different buyers
        shipment_hages = Shipment(
            reference="HAGESQUERY-001",
            container_number="HGQS1234567",
            status=ShipmentStatus.DRAFT,
            organization_id=exporter_org.id,
            buyer_organization_id=buyer_org_hages.id
        )
        shipment_witatrade = Shipment(
            reference="WITAQUERY-001",
            container_number="WTQS1234567",
            status=ShipmentStatus.DRAFT,
            organization_id=exporter_org.id,
            buyer_organization_id=buyer_org_witatrade.id
        )
        db_session.add_all([shipment_hages, shipment_witatrade])
        db_session.commit()

        # Query for HAGES shipments only
        hages_shipments = db_session.query(Shipment).filter(
            Shipment.buyer_organization_id == buyer_org_hages.id
        ).all()

        refs = [s.reference for s in hages_shipments]
        assert "HAGESQUERY-001" in refs
        assert "WITAQUERY-001" not in refs

        # Cleanup
        db_session.delete(shipment_hages)
        db_session.delete(shipment_witatrade)
        db_session.commit()

    def test_count_shipments_by_buyer_organization(
        self, db_session, exporter_org, buyer_org_hages
    ):
        """
        FAILING TEST: Should count shipments for a buyer.

        Useful for dashboard statistics.
        """
        # Create multiple shipments for HAGES
        shipments = []
        for i in range(3):
            s = Shipment(
                reference=f"HAGESCOUNT-{i:03d}",
                container_number=f"HGCT{i:07d}",
                status=ShipmentStatus.DRAFT,
                organization_id=exporter_org.id,
                buyer_organization_id=buyer_org_hages.id
            )
            shipments.append(s)
        db_session.add_all(shipments)
        db_session.commit()

        # Count HAGES shipments
        count = db_session.query(Shipment).filter(
            Shipment.buyer_organization_id == buyer_org_hages.id
        ).count()

        assert count >= 3

        # Cleanup
        for s in shipments:
            db_session.delete(s)
        db_session.commit()


class TestOrganizationBuyerShipmentsRelationship:
    """Tests for reverse relationship - Organization.buyer_shipments."""

    def test_organization_has_buyer_shipments_relationship(self, db_session):
        """
        FAILING TEST: Organization should have buyer_shipments relationship.

        This is the reverse relationship for shipments where this org is the buyer.
        """
        assert hasattr(Organization, 'buyer_shipments'), \
            "Organization model should have buyer_shipments relationship"

    def test_buyer_organization_buyer_shipments_loads(
        self, db_session, exporter_org, buyer_org_hages
    ):
        """
        FAILING TEST: Accessing org.buyer_shipments returns assigned shipments.

        HAGES.buyer_shipments should return shipments assigned to HAGES.
        """
        shipment = Shipment(
            reference="REVERSEREL-001",
            container_number="RREL1234567",
            status=ShipmentStatus.DRAFT,
            organization_id=exporter_org.id,
            buyer_organization_id=buyer_org_hages.id
        )
        db_session.add(shipment)
        db_session.commit()
        db_session.refresh(buyer_org_hages)

        # Access reverse relationship
        buyer_shipments = buyer_org_hages.buyer_shipments

        assert len(buyer_shipments) >= 1
        refs = [s.reference for s in buyer_shipments]
        assert "REVERSEREL-001" in refs

        # Cleanup
        db_session.delete(shipment)
        db_session.commit()
