from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from ..models.project import Project
from ..schemas.project import ProjectCreate


async def get_project(db: AsyncSession, project_id: str) -> Optional[Project]:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalars().first()


async def get_project_by_name(db: AsyncSession, user_id: str, name: str) -> Optional[Project]:
    result = await db.execute(
        select(Project).where(Project.user_id == user_id, Project.name == name)
    )
    return result.scalars().first()


async def get_user_projects(db: AsyncSession, user_id: str) -> List[Project]:
    result = await db.execute(select(Project).where(Project.user_id == user_id))
    return list(result.scalars().all())


async def create_project(db: AsyncSession, user_id: str, obj_in: ProjectCreate) -> Project:
    db_project = Project(
        user_id=user_id,
        name=obj_in.name,
    )
    db.add(db_project)
    await db.flush()
    return db_project
