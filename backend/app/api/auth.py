from __future__ import annotations
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..config import get_settings
from ..schemas.user import UserCreate, UserResponse, Token, RefreshTokenRequest
from ..schemas.project import ProjectCreate
from ..schemas.api_key import ApiKeyCreate
from ..crud.user import create_user, get_user_by_email, verify_password
from ..crud.project import create_project
from ..crud.api_key import create_api_key
from ..api.deps import create_access_token, get_current_user
from ..models.user import User

router = APIRouter()

# Simple in-memory rate limiter: tracks failed login attempts per IP
_failed_attempts: dict[str, int] = {}
_MAX_ATTEMPTS = 10


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
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"

    # Soft rate limit: return 429 after too many failed attempts
    if _failed_attempts.get(client_ip, 0) >= _MAX_ATTEMPTS:
        response.headers["Retry-After"] = "300"
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again in 5 minutes.",
        )

    user = await get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        _failed_attempts[client_ip] = _failed_attempts.get(client_ip, 0) + 1
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    # Reset failed attempt counter on success
    _failed_attempts.pop(client_ip, None)

    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    response.headers["X-RateLimit-Remaining"] = str(_MAX_ATTEMPTS - _failed_attempts.get(client_ip, 0))
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
    )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Issue a new access token given a valid (unexpired) refresh token."""
    from jose import JWTError, jwt
    settings = get_settings()
    try:
        payload = jwt.decode(body.refresh_token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub", "")
        token_type: str = payload.get("type", "access")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if token_type != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")

    user = await get_user_by_email(db, email=email)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    expires = timedelta(minutes=settings.access_token_expire_minutes)
    new_token = create_access_token(data={"sub": user.email}, expires_delta=expires)
    return Token(access_token=new_token, token_type="bearer", expires_in=int(expires.total_seconds()))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user
