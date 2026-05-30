"""
ghostrace.backend.database
~~~~~~~~~~~~~~~~~~~~~~~~~~
Async SQLAlchemy engine + session factory.

Uses a single engine shared for the lifetime of the process.
The ``get_db`` dependency yields one AsyncSession per request and
commits/rolls back automatically.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import get_settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


def _make_engine():
    settings = get_settings()
    connect_args = {}
    # SQLite requires check_same_thread=False for async use
    if settings.database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        future=True,
        connect_args=connect_args,
    )


engine = _make_engine()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a DB session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_all_tables() -> None:
    """Create all tables (used in tests and dev; production uses Alembic)."""
    async with engine.begin() as conn:
        from .models import user, project, api_key, session, trace_event  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    """Drop all tables (used in tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
