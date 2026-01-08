"""Schema verification for staging/production.

Runs lightweight checks to ensure critical columns exist after Alembic
upgrades. Exits non-zero if required columns are missing.

Checks:
- documents.file_size
- Alembic version table presence (optional)
- shipments.organization_id (informational)
"""

import os
import sys
import psycopg2


def get_db_url() -> str:
    """Build database URL from environment variables.

    Priority:
    1. DATABASE_URL
    2. POSTGRES_* variables
    Defaults:
    - host: "db" (Docker Compose service name)
    - port: 5432
    """

    url = os.getenv("DATABASE_URL")
    if url:
        return url

    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "db"))
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "tracehub"))

    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def query_bool(cur, sql: str) -> bool:
    cur.execute(sql)
    row = cur.fetchone()
    return bool(row[0]) if row else False


def main() -> int:
    db_url = get_db_url()
    try:
        conn = psycopg2.connect(db_url)
    except Exception as e:
        print(f"[SCHEMA CHECK] Failed to connect to DB: {e}")
        return 2

    missing = []
    info = {}

    try:
        with conn, conn.cursor() as cur:
            # documents.file_size must exist
            has_file_size = query_bool(
                cur,
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'documents' AND column_name = 'file_size'
                );
                """,
            )
            if not has_file_size:
                missing.append("documents.file_size")

            # Alembic version table (optional, informational)
            has_alembic = query_bool(
                cur,
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = 'alembic_version'
                );
                """,
            )
            info["alembic_version_table"] = has_alembic

            if has_alembic:
                cur.execute("SELECT version_num FROM alembic_version LIMIT 1;")
                row = cur.fetchone()
                info["alembic_version"] = row[0] if row else None

            # shipments.organization_id may be absent on older schemas
            has_org_id = query_bool(
                cur,
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'shipments' AND column_name = 'organization_id'
                );
                """,
            )
            info["shipments_has_organization_id"] = has_org_id

    finally:
        conn.close()

    print("[SCHEMA CHECK] Results:")
    for k, v in info.items():
        print(f" - {k}: {v}")

    if missing:
        print("[SCHEMA CHECK] Missing required columns:")
        for m in missing:
            print(f" - {m}")
        return 3

    print("[SCHEMA CHECK] OK: required columns present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
