"""
Database connection pool — async (asyncpg) with sync fallback (psycopg2 pool).

Provides:
    get_db()           — FastAPI dependency for async sessions
    get_sync_conn()    — Context manager for sync psycopg2 connections
    engine             — SQLAlchemy async engine (lifespan managed)
"""

import os
import re
from contextlib import contextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# --- Connection URL ---
_raw_db_url = os.getenv("DATABASE_URL", "")
if "channel_binding=" in _raw_db_url:
    _raw_db_url = re.sub(r"[&?]channel_binding=[^&]*", "", _raw_db_url)
DATABASE_URL = _raw_db_url

# Build async URL from sync URL if needed
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    ASYNC_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
else:
    ASYNC_URL = DATABASE_URL

# --- Async Engine & Session Factory ---
engine = create_async_engine(
    ASYNC_URL,
    pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """FastAPI dependency: yields an async database session."""
    async with AsyncSessionLocal() as session:
        yield session


# --- Sync connection pool (backward compat during migration) ---
_sync_pool = None


def _get_sync_pool():
    """Lazy-init a psycopg2 ThreadedConnectionPool from the same DATABASE_URL."""
    global _sync_pool
    if _sync_pool is None:
        import psycopg2
        from psycopg2 import pool
        _sync_pool = pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            dsn=DATABASE_URL,
        )
    return _sync_pool


@contextmanager
def get_sync_conn():
    """Context manager: borrow/return a sync psycopg2 connection from the pool."""
    p = _get_sync_pool()
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)
