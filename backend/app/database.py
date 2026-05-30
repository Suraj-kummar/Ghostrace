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
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings

class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass

def _make_engine():
    pass
engine = _make_engine()
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    pass

async def create_all_tables() -> None:
    pass

async def drop_all_tables() -> None:
    pass