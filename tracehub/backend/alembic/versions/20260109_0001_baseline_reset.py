"""Reset baseline to match current models (POC clean slate).

This migration recreates the schema directly from SQLAlchemy models. It assumes
an empty database (or that existing data can be discarded). Downgrade drops all
TraceHub tables.
"""

from alembic import op
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision = "20260109_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Import models so metadata is populated
    from app.database import Base
    import app.models  # noqa: F401

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    from app.database import Base
    import app.models  # noqa: F401

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
