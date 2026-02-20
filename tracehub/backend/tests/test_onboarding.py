"""Tests for PRD-024: Self-Service Onboarding Flow.

Tests cover:
- Onboarding schemas validation
- Organization creation via public signup
- Onboarding state management
- Slug generation and uniqueness
- Trial period calculation
- Multi-tenancy isolation
"""

import pytest
import uuid
from datetime import datetime, timedelta

from app.models.user import User, UserRole
from app.models.organization import (
    Organization,
    OrganizationMembership,
    OrganizationStatus,
    OrganizationType,
    OrgRole,
    MembershipStatus,
)
from app.schemas.onboarding import (
    PlanTier,
    PlanInfo,
    OnboardingState,
    OnboardingStep,
    PublicSignupRequest,
)
from app.services.onboarding import (
    generate_unique_slug,
    is_slug_available,
    calculate_trial_end,
    create_organization_with_signup,
    get_onboarding_state,
    update_onboarding_step,
    complete_onboarding,
    TRIAL_DAYS,
    ALL_ONBOARDING_STEPS,
)
from app.routers.auth import get_password_hash

from .conftest import engine, TestingSessionLocal, Base


# =============================================================================
# Module-scoped fixtures
# =============================================================================


@pytest.fixture(scope="module")
def db_session():
    """Create a database session for onboarding tests."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def test_user(db_session):
    """Create a test user for signup tests."""
    user = User(
        email=f"signup-{uuid.uuid4().hex[:6]}@test.com",
        full_name="Test Signup User",
        hashed_password=get_password_hash("TestPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="module")
def second_user(db_session):
    """Create a second test user for multi-tenancy tests."""
    user = User(
        email=f"signup2-{uuid.uuid4().hex[:6]}@test.com",
        full_name="Second Test User",
        hashed_password=get_password_hash("TestPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestOnboardingSchemas:
    """Tests for onboarding Pydantic schemas."""

    def test_plan_tier_values(self):
        """Verify all plan tiers exist."""
        assert PlanTier.FREE == "free"
        assert PlanTier.STARTER == "starter"
        assert PlanTier.PROFESSIONAL == "professional"
        assert PlanTier.ENTERPRISE == "enterprise"

    def test_onboarding_step_values(self):
        """Verify all onboarding steps exist."""
        assert OnboardingStep.PROFILE == "profile"
        assert OnboardingStep.ORGANIZATION == "organization"
        assert OnboardingStep.INVITE_TEAM == "invite_team"
        assert OnboardingStep.TOUR == "tour"

    def test_plan_info_defaults(self):
        """PlanInfo should default to free with no trial."""
        plan = PlanInfo()
        assert plan.tier == PlanTier.FREE
        assert plan.selected_at is None
        assert plan.trial_ends_at is None

    def test_onboarding_state_defaults(self):
        """OnboardingState should start empty."""
        state = OnboardingState()
        assert state.completed_steps == []
        assert state.completed_at is None
        assert state.skipped_at is None

    def test_signup_request_valid(self):
        """Valid signup request should pass validation."""
        req = PublicSignupRequest(
            org_name="Test Corp",
            org_slug="test-corp",
            org_type=OrganizationType.BUYER,
            contact_email="contact@test.com",
            plan_tier=PlanTier.STARTER,
            user_full_name="Jane Doe",
            user_email="jane@test.com",
        )
        assert req.org_slug == "test-corp"
        assert req.plan_tier == PlanTier.STARTER

    def test_signup_request_slug_no_uppercase(self):
        """Slug must be lowercase."""
        with pytest.raises(ValueError):
            PublicSignupRequest(
                org_name="Test",
                org_slug="Test-Corp",
                org_type=OrganizationType.BUYER,
                contact_email="c@t.com",
                user_full_name="Jane",
                user_email="j@t.com",
            )

    def test_signup_request_slug_no_leading_hyphen(self):
        """Slug cannot start with hyphen."""
        with pytest.raises(ValueError):
            PublicSignupRequest(
                org_name="Test",
                org_slug="-test-corp",
                org_type=OrganizationType.BUYER,
                contact_email="c@t.com",
                user_full_name="Jane",
                user_email="j@t.com",
            )

    def test_signup_request_slug_no_consecutive_hyphens(self):
        """Slug cannot contain consecutive hyphens."""
        with pytest.raises(ValueError):
            PublicSignupRequest(
                org_name="Test",
                org_slug="test--corp",
                org_type=OrganizationType.BUYER,
                contact_email="c@t.com",
                user_full_name="Jane",
                user_email="j@t.com",
            )

    def test_signup_request_org_name_min_length(self):
        """Org name must be at least 2 characters."""
        with pytest.raises(ValueError):
            PublicSignupRequest(
                org_name="X",
                org_slug="test",
                org_type=OrganizationType.BUYER,
                contact_email="c@t.com",
                user_full_name="Jane",
                user_email="j@t.com",
            )


# =============================================================================
# Slug Generation Tests
# =============================================================================


class TestSlugGeneration:
    """Tests for slug generation and availability."""

    def test_slug_available_when_no_org(self, db_session):
        """Slug should be available if no org uses it."""
        unique = f"available-slug-{uuid.uuid4().hex[:6]}"
        assert is_slug_available(db_session, unique) is True

    def test_slug_not_available_after_creation(self, db_session):
        """Slug should not be available after an org is created with it."""
        slug = f"taken-slug-{uuid.uuid4().hex[:6]}"
        org = Organization(
            name="Taken Org",
            slug=slug,
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="taken@test.com",
        )
        db_session.add(org)
        db_session.commit()

        assert is_slug_available(db_session, slug) is False

    def test_generate_unique_slug_returns_base_when_available(self, db_session):
        """Should return base slug if available."""
        base = f"unique-base-{uuid.uuid4().hex[:6]}"
        result = generate_unique_slug(db_session, base)
        assert result == base

    def test_generate_unique_slug_appends_suffix_when_taken(self, db_session):
        """Should append -1, -2, etc. when base slug is taken."""
        base = f"dup-slug-{uuid.uuid4().hex[:6]}"
        # Create org with base slug
        org = Organization(
            name="Dup Org",
            slug=base,
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="dup@test.com",
        )
        db_session.add(org)
        db_session.commit()

        result = generate_unique_slug(db_session, base)
        assert result == f"{base}-1"

    def test_generate_unique_slug_normalizes_input(self, db_session):
        """Should normalize slugs (lowercase, strip special chars)."""
        result = generate_unique_slug(db_session, "  My-Corp!  ")
        assert result == "my-corp"


# =============================================================================
# Trial Calculation Tests
# =============================================================================


class TestTrialCalculation:
    """Tests for trial period calculation."""

    def test_free_plan_no_trial(self):
        """Free plan should not have a trial period."""
        result = calculate_trial_end(PlanTier.FREE)
        assert result is None

    def test_starter_plan_has_trial(self):
        """Starter plan should get a 14-day trial."""
        before = datetime.utcnow()
        result = calculate_trial_end(PlanTier.STARTER)
        after = datetime.utcnow()

        assert result is not None
        expected_min = before + timedelta(days=TRIAL_DAYS)
        expected_max = after + timedelta(days=TRIAL_DAYS)
        assert expected_min <= result <= expected_max

    def test_professional_plan_has_trial(self):
        """Professional plan should get a trial."""
        result = calculate_trial_end(PlanTier.PROFESSIONAL)
        assert result is not None

    def test_enterprise_plan_has_trial(self):
        """Enterprise plan should get a trial."""
        result = calculate_trial_end(PlanTier.ENTERPRISE)
        assert result is not None


# =============================================================================
# Organization Creation Tests
# =============================================================================


class TestCreateOrganizationWithSignup:
    """Tests for self-service organization creation."""

    def test_create_org_with_valid_data(self, db_session, test_user):
        """Should create org with pending_setup status and admin membership."""
        slug = f"new-org-{uuid.uuid4().hex[:6]}"
        request = PublicSignupRequest(
            org_name="New Organization",
            org_slug=slug,
            org_type=OrganizationType.SUPPLIER,
            contact_email="info@neworg.com",
            plan_tier=PlanTier.STARTER,
            user_full_name=test_user.full_name,
            user_email=test_user.email,
        )

        org = create_organization_with_signup(db_session, request, test_user)

        assert org.name == "New Organization"
        assert org.slug == slug
        assert org.type == OrganizationType.SUPPLIER
        assert org.status == OrganizationStatus.PENDING_SETUP
        assert org.created_by == test_user.id

        # Check settings contain plan info
        settings = org.settings
        assert settings["plan"]["tier"] == "starter"
        assert settings["plan"]["trial_ends_at"] is not None
        assert settings["onboarding"]["completed_steps"] == []

    def test_create_org_creates_admin_membership(self, db_session, test_user):
        """Should create admin membership for the signing-up user."""
        slug = f"membership-org-{uuid.uuid4().hex[:6]}"
        request = PublicSignupRequest(
            org_name="Membership Org",
            org_slug=slug,
            org_type=OrganizationType.BUYER,
            contact_email="info@mem.com",
            plan_tier=PlanTier.FREE,
            user_full_name=test_user.full_name,
            user_email=test_user.email,
        )

        org = create_organization_with_signup(db_session, request, test_user)

        membership = (
            db_session.query(OrganizationMembership)
            .filter(
                OrganizationMembership.organization_id == org.id,
                OrganizationMembership.user_id == test_user.id,
            )
            .first()
        )

        assert membership is not None
        assert membership.org_role == OrgRole.ADMIN
        assert membership.status == MembershipStatus.ACTIVE
        assert membership.is_primary is True

    def test_create_org_duplicate_slug_raises(self, db_session, test_user):
        """Should raise ValueError if slug is already taken."""
        slug = f"dup-org-{uuid.uuid4().hex[:6]}"
        # Create first org
        request = PublicSignupRequest(
            org_name="First Org",
            org_slug=slug,
            org_type=OrganizationType.BUYER,
            contact_email="first@test.com",
            plan_tier=PlanTier.FREE,
            user_full_name=test_user.full_name,
            user_email=test_user.email,
        )
        create_organization_with_signup(db_session, request, test_user)

        # Attempt duplicate
        request2 = PublicSignupRequest(
            org_name="Second Org",
            org_slug=slug,
            org_type=OrganizationType.BUYER,
            contact_email="second@test.com",
            plan_tier=PlanTier.FREE,
            user_full_name=test_user.full_name,
            user_email=test_user.email,
        )
        with pytest.raises(ValueError, match="already taken"):
            create_organization_with_signup(db_session, request2, test_user)

    def test_create_org_free_plan_no_trial(self, db_session, test_user):
        """Free plan org should not have trial_ends_at."""
        slug = f"free-org-{uuid.uuid4().hex[:6]}"
        request = PublicSignupRequest(
            org_name="Free Org",
            org_slug=slug,
            org_type=OrganizationType.BUYER,
            contact_email="free@test.com",
            plan_tier=PlanTier.FREE,
            user_full_name=test_user.full_name,
            user_email=test_user.email,
        )

        org = create_organization_with_signup(db_session, request, test_user)
        assert org.settings["plan"]["trial_ends_at"] is None


# =============================================================================
# Onboarding State Tests
# =============================================================================


class TestOnboardingState:
    """Tests for onboarding state management."""

    @pytest.fixture(autouse=True)
    def setup_org(self, db_session, second_user):
        """Create a fresh org for each test."""
        slug = f"onboard-{uuid.uuid4().hex[:6]}"
        request = PublicSignupRequest(
            org_name="Onboarding Test Org",
            org_slug=slug,
            org_type=OrganizationType.LOGISTICS_AGENT,
            contact_email="onboard@test.com",
            plan_tier=PlanTier.PROFESSIONAL,
            user_full_name=second_user.full_name,
            user_email=second_user.email,
        )
        self.org = create_organization_with_signup(db_session, request, second_user)
        self.db = db_session

    def test_get_onboarding_state_initial(self):
        """Initial state should have no completed steps."""
        state = get_onboarding_state(self.db, self.org.id)
        assert state is not None
        assert state["status"] == OrganizationStatus.PENDING_SETUP
        assert state["onboarding"].completed_steps == []
        assert state["all_steps_completed"] is False

    def test_get_onboarding_state_nonexistent_org(self):
        """Should return None for nonexistent org."""
        state = get_onboarding_state(self.db, uuid.uuid4())
        assert state is None

    def test_update_onboarding_step(self):
        """Should mark a step as completed."""
        result = update_onboarding_step(self.db, self.org.id, OnboardingStep.PROFILE)
        assert result is not None
        assert OnboardingStep.PROFILE in result["onboarding"].completed_steps

    def test_update_onboarding_step_idempotent(self):
        """Completing the same step twice should not duplicate it."""
        update_onboarding_step(self.db, self.org.id, OnboardingStep.PROFILE)
        result = update_onboarding_step(self.db, self.org.id, OnboardingStep.PROFILE)
        count = result["onboarding"].completed_steps.count(OnboardingStep.PROFILE)
        assert count == 1

    def test_all_steps_completed_flag(self):
        """Should set all_steps_completed when all steps are done."""
        for step in ALL_ONBOARDING_STEPS:
            result = update_onboarding_step(self.db, self.org.id, step)
        assert result["all_steps_completed"] is True


# =============================================================================
# Onboarding Completion Tests
# =============================================================================


class TestOnboardingCompletion:
    """Tests for completing the onboarding flow."""

    @pytest.fixture(autouse=True)
    def setup_org(self, db_session, second_user):
        """Create a fresh org for each test."""
        slug = f"complete-{uuid.uuid4().hex[:6]}"
        request = PublicSignupRequest(
            org_name="Complete Test Org",
            org_slug=slug,
            org_type=OrganizationType.BUYER,
            contact_email="complete@test.com",
            plan_tier=PlanTier.STARTER,
            user_full_name=second_user.full_name,
            user_email=second_user.email,
        )
        self.org = create_organization_with_signup(db_session, request, second_user)
        self.db = db_session

    def test_complete_onboarding_sets_active(self):
        """Completing onboarding should set org status to active."""
        org = complete_onboarding(self.db, self.org.id)
        assert org is not None
        assert org.status == OrganizationStatus.ACTIVE
        assert org.settings["onboarding"]["completed_at"] is not None

    def test_skip_onboarding_sets_active(self):
        """Skipping onboarding should also set org status to active."""
        org = complete_onboarding(self.db, self.org.id, skip=True)
        assert org is not None
        assert org.status == OrganizationStatus.ACTIVE
        assert org.settings["onboarding"]["skipped_at"] is not None
        assert org.settings["onboarding"]["completed_at"] is None

    def test_complete_already_active_raises(self, db_session, second_user):
        """Cannot complete onboarding if org is already active."""
        slug = f"already-active-{uuid.uuid4().hex[:6]}"
        request = PublicSignupRequest(
            org_name="Already Active",
            org_slug=slug,
            org_type=OrganizationType.BUYER,
            contact_email="active@test.com",
            plan_tier=PlanTier.FREE,
            user_full_name=second_user.full_name,
            user_email=second_user.email,
        )
        org = create_organization_with_signup(db_session, request, second_user)
        complete_onboarding(db_session, org.id)

        with pytest.raises(ValueError, match="not in pending_setup"):
            complete_onboarding(db_session, org.id)

    def test_complete_nonexistent_org(self):
        """Should return None for nonexistent org."""
        result = complete_onboarding(self.db, uuid.uuid4())
        assert result is None


# =============================================================================
# Multi-Tenancy Tests
# =============================================================================


class TestOnboardingMultiTenancy:
    """Tests ensuring onboarding respects tenant isolation."""

    def test_org_a_cannot_see_org_b_onboarding(
        self, db_session, test_user, second_user
    ):
        """Each org's onboarding state is independent."""
        slug_a = f"org-a-{uuid.uuid4().hex[:6]}"
        slug_b = f"org-b-{uuid.uuid4().hex[:6]}"

        req_a = PublicSignupRequest(
            org_name="Org A",
            org_slug=slug_a,
            org_type=OrganizationType.BUYER,
            contact_email="a@test.com",
            plan_tier=PlanTier.STARTER,
            user_full_name=test_user.full_name,
            user_email=test_user.email,
        )
        req_b = PublicSignupRequest(
            org_name="Org B",
            org_slug=slug_b,
            org_type=OrganizationType.SUPPLIER,
            contact_email="b@test.com",
            plan_tier=PlanTier.FREE,
            user_full_name=second_user.full_name,
            user_email=second_user.email,
        )

        org_a = create_organization_with_signup(db_session, req_a, test_user)
        org_b = create_organization_with_signup(db_session, req_b, second_user)

        # Update org_a's onboarding
        update_onboarding_step(db_session, org_a.id, OnboardingStep.PROFILE)

        # Org B should not have that step
        state_b = get_onboarding_state(db_session, org_b.id)
        assert OnboardingStep.PROFILE not in state_b["onboarding"].completed_steps
