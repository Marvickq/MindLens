from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

import os

from sqlalchemy import text
from sqlmodel import create_engine, SQLModel, Session
from app.config import get_settings

settings = get_settings()


def _sanitize_db_url(url: str) -> str:
    """Supabase pgbouncer URLs carry '?pgbouncer=true'. psycopg2 rejects unknown
    query parameters, and since psycopg2 does not use server-side prepared
    statements, the flag is unnecessary for transaction-mode pooling anyway."""
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() != "pgbouncer"]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


# PgBouncer-compatible engine for Supabase.
# psycopg2 doesn't use server-side prepared statements, so PgBouncer transaction mode is safe.
engine = create_engine(
    _sanitize_db_url(settings.database_url),
    echo=(settings.environment == "development"),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={"connect_timeout": 10},
)


def create_db_and_tables():
    """Create all SQLModel tables. Safe to call multiple times — skips existing tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


# Migrations 001/002 were applied manually to the existing live databases.
# They are treated as already-applied so the runner only ever applies the
# idempotent follow-up migrations (003_discrepancy_engine.sql, ...).
_ALREADY_APPLIED = {
    "001_initial_schema.sql",
    "002_rater_token_encryption.sql",
}


def apply_migrations():
    """
    Apply pending idempotent SQL migrations (files in `migrations/` beyond the
    manually-applied 001/002). Tracked in `schema_migrations` so each runs once.
    """
    migrations_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "migrations")
    )
    with Session(engine) as db:
        db.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                "name VARCHAR(255) PRIMARY KEY,"
                "applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
            )
        )
        db.commit()

        applied = {
            r[0]
            for r in db.execute(text("SELECT name FROM schema_migrations")).all()
        }
        for name in sorted(os.listdir(migrations_dir)):
            if not name.endswith(".sql") or name in _ALREADY_APPLIED:
                continue
            if name in applied:
                continue
            path = os.path.join(migrations_dir, name)
            with open(path, encoding="utf-8") as fh:
                sql = fh.read()
            db.execute(text(sql))
            db.execute(text("INSERT INTO schema_migrations (name) VALUES (:n)"), {"n": name})
            db.commit()
