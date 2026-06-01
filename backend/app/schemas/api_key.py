from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class ApiKeyBase(BaseModel):
    name: str


class ApiKeyCreate(ApiKeyBase):
    pass


class ApiKeyResponse(ApiKeyBase):
    id: str
    project_id: str
    key: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
