from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..database import get_db
from ..config import get_settings
from ..api.deps import get_current_user
from ..models.user import User
from ..schemas.project import ProjectCreate, ProjectResponse
from ..schemas.api_key import ApiKeyCreate, ApiKeyResponse
from ..crud.project import get_project, get_project_by_name, get_user_projects, create_project, delete_project
from ..crud.api_key import get_project_keys, create_api_key, get_api_key_by_id, delete_api_key

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_new_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Check if project name already exists for user
    existing_project = await get_project_by_name(db, user_id=current_user.id, name=project_in.name)
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project with name '{project_in.name}' already exists.",
        )

    # 2. Check plan limits
    settings = get_settings()
    limits = settings.plan_limits.get(current_user.plan.lower(), settings.plan_limits["free"])
    max_projects = limits.get("projects", 1)

    if max_projects != -1:
        current_projects = await get_user_projects(db, user_id=current_user.id)
        if len(current_projects) >= max_projects:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project limit of {max_projects} reached for your '{current_user.plan}' plan. Please upgrade.",
            )

    project = await create_project(db, user_id=current_user.id, obj_in=project_in)
    return project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_user_projects(db, user_id=current_user.id)


@router.post("/{project_id}/keys", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_new_api_key(
    project_id: str,
    key_in: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Verify project exists and belongs to current user
    project = await get_project(db, project_id=project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # 2. Check API Key plan limits
    settings = get_settings()
    limits = settings.plan_limits.get(current_user.plan.lower(), settings.plan_limits["free"])
    max_keys = limits.get("api_keys", 1)

    if max_keys != -1:
        current_keys = await get_project_keys(db, project_id=project_id)
        if len(current_keys) >= max_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"API key limit of {max_keys} reached for project on your '{current_user.plan}' plan.",
            )

    key = await create_api_key(db, project_id=project_id, obj_in=key_in)
    return key


@router.get("/{project_id}/keys", response_model=List[ApiKeyResponse])
async def list_project_api_keys(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify project exists and belongs to current user
    project = await get_project(db, project_id=project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return await get_project_keys(db, project_id=project_id)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project(db, project_id=project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    await delete_project(db, project)


@router.delete("/{project_id}/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_api_key(
    project_id: str,
    key_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project(db, project_id=project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    api_key = await get_api_key_by_id(db, key_id=key_id)
    if not api_key or api_key.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    await delete_api_key(db, api_key)
