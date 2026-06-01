from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class ProjectBase(BaseModel):
    name: str


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: str
    user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
