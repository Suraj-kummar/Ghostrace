from __future__ import annotations
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from ..models.api_key import ApiKey
from ..schemas.api_key import ApiKeyCreate


from sqlalchemy.orm import joinedload


def generate_key_string() -> str:
    return f"gr_{secrets.token_hex(20)}"


async def get_api_key_by_value(db: AsyncSession, key_value: str) -> Optional[ApiKey]:
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.key == key_value, ApiKey.is_active == True)
        .options(joinedload(ApiKey.project))
    )
    return result.scalars().first()


async def get_project_keys(db: AsyncSession, project_id: str) -> List[ApiKey]:
    result = await db.execute(select(ApiKey).where(ApiKey.project_id == project_id))
    return list(result.scalars().all())


async def create_api_key(db: AsyncSession, project_id: str, obj_in: ApiKeyCreate) -> ApiKey:
    db_key = ApiKey(
        project_id=project_id,
        key=generate_key_string(),
        name=obj_in.name,
    )
    db.add(db_key)
    await db.flush()
    return db_key
