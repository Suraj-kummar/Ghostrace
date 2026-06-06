"""
ghostrace.backend.schemas.project — extended
Adds description field to ProjectCreate / ProjectResponse.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional human-readable project description",
    )


class ProjectResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}
