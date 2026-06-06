"""
ghostrace.backend.api.pagination
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Generic pagination helpers shared by list endpoints.
"""
from __future__ import annotations

from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    """Query params for paginated list endpoints."""
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=50, ge=1, le=200, description="Max records to return")


class Page(BaseModel, Generic[T]):
    """Generic paginated response envelope."""
    items: List[T]
    total: Optional[int] = None    # total matching records (if known)
    skip: int = 0
    limit: int = 50
    has_more: bool = False

    @classmethod
    def of(cls, items: List[T], *, skip: int = 0, limit: int = 50, total: Optional[int] = None) -> "Page[T]":
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(total is not None and skip + len(items) < total),
        )
