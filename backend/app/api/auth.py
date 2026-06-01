from __future__ import annotations
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..config import get_settings
from ..schemas.user import UserCreate, UserResponse, Token
from ..schemas.project import ProjectCreate
from ..schemas.api_key import ApiKeyCreate
from ..crud.user import create_user, get_user_by_email, verify_password
from ..crud.project import create_project
from ..crud.api_key import create_api_key
from ..api.deps import create_access_token

router = APIRouter()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # 1. Check if user already exists
    existing_user = await get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    # 2. Create user
    user = await create_user(db, user_in)

    # 3. Create default project for the new user
    project_in = ProjectCreate(name="default")
    project = await create_project(db, user_id=user.id, obj_in=project_in)

    # 4. Create default API key for the new project
    key_in = ApiKeyCreate(name="Default Key")
    await create_api_key(db, project_id=project.id, obj_in=key_in)

    return user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
