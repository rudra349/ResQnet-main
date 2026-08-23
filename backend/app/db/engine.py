"""
ResQNet — Database Engine & Session
Async SQLAlchemy engine for CockroachDB (PostgreSQL-compatible).
"""
from __future__ import annotations

from typing import AsyncGenerator
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.dialects.postgresql.asyncpg import PGDialect_asyncpg

from app.config import settings

logger = logging.getLogger("resqnet.db")

# CockroachDB compatibility patches for SQLAlchemy + asyncpg
# 1. Parse CockroachDB version strings without AssertionError
_orig_get_server_version_info = PGDialect._get_server_version_info

def _safe_get_server_version_info(self, connection):
    try:
        return _orig_get_server_version_info(self, connection)
    except AssertionError:
        v = connection.exec_driver_sql("select pg_catalog.version()").scalar()
        match = re.search(r"v(\d+)\.(\d+)(?:\.(\d+))?", v or "")
        if match:
            return tuple(int(x) for x in match.groups() if x is not None)
        return (14, 0)

PGDialect._get_server_version_info = _safe_get_server_version_info

# 2. CockroachDB lacks pg_catalog.json (uses jsonb), so wrap codec registration safely
_orig_setup_json_codec = PGDialect_asyncpg.setup_asyncpg_json_codec

async def _safe_setup_asyncpg_json_codec(self, conn):
    try:
        await _orig_setup_json_codec(self, conn)
    except Exception:
        pass

PGDialect_asyncpg.setup_asyncpg_json_codec = _safe_setup_asyncpg_json_codec

# ── Engine ────────────────────────────────────────────────────────────────────
db_url = settings.database_url
if db_url.startswith("cockroachdb+asyncpg://"):
    db_url = db_url.replace("cockroachdb+asyncpg://", "postgresql+asyncpg://", 1)
elif db_url.startswith("cockroachdb://"):
    db_url = db_url.replace("cockroachdb://", "postgresql+asyncpg://", 1)

# Clean up sslmode if present in asyncpg URL
if "asyncpg" in db_url:
    for ssl_param in ["sslmode=disable", "&sslmode=disable", "?sslmode=disable"]:
        db_url = db_url.replace(ssl_param, "")
    db_url = db_url.replace("sslmode=require", "ssl=require")
    db_url = db_url.replace("sslmode=verify-full", "ssl=require")
    db_url = db_url.rstrip("?&")

engine = create_async_engine(
    db_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={
        "server_settings": {
            "application_name": "resqnet-backend",
        }
    } if "asyncpg" in db_url else {},
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ── Dependency ────────────────────────────────────────────────────────────────
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def ensure_database_exists() -> None:
    """Ensure the target database exists; if not, auto-create it via defaultdb/postgres."""
    from sqlalchemy.engine.url import make_url
    url = make_url(db_url)
    target_db = url.database
    if not target_db or target_db in ("defaultdb", "postgres"):
        return

    import asyncpg

    user = url.username or "root"
    password = url.password
    host = url.host or "localhost"
    port = url.port or 26257

    for admin_db in ["defaultdb", "postgres"]:
        try:
            conn = await asyncpg.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                database=admin_db,
            )
            try:
                await conn.execute(f'CREATE DATABASE IF NOT EXISTS "{target_db}";')
            except Exception:
                exists = await conn.fetchval(
                    "SELECT 1 FROM pg_database WHERE datname = $1", target_db
                )
                if not exists:
                    await conn.execute(f'CREATE DATABASE "{target_db}";')
            await conn.close()
            break
        except Exception:
            continue


async def create_db_and_tables() -> None:
    """Create all tables on startup. In production, use Alembic migrations."""
    try:
        await ensure_database_exists()
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
    except Exception as e:
        if "already exists" in str(e) or "DuplicateTableError" in str(e):
            pass
        elif "10061" in str(e) or "Connection refused" in str(e) or "Connect call failed" in str(e):
            logger.warning("⚠️ CockroachDB is not running. Please start CockroachDB to enable database operations.")
        else:
            logger.warning(f"⚠️ Database initialization warning: {e}")


async def init_vector_index() -> None:
    """
    CockroachDB Capability #1: Distributed Vector Indexing (C-SPANN).
    Create the CockroachDB distributed vector index (C-SPANN) on memories.embedding.
    This is idempotent — safe to call on every startup.
    """
    vector_index_sql = f"""
    CREATE VECTOR INDEX IF NOT EXISTS idx_memories_embedding
    ON memories USING CSPANN (embedding {settings.embedding_dim});
    """
    try:
        async with engine.begin() as conn:
            await conn.exec_driver_sql(vector_index_sql)
    except Exception as e:
        import logging
        logging.getLogger("resqnet").warning(
            f"Could not create VECTOR INDEX (will use sequential scan): {e}"
        )
