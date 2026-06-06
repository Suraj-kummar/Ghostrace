"""
ghostrace.backend — exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Custom application exceptions for clear error handling.
"""
from __future__ import annotations

from fastapi import HTTPException, status


class ProjectNotFound(HTTPException):
    def __init__(self, project_id: str | None = None):
        detail = f"Project '{project_id}' not found" if project_id else "Project not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class SessionNotFound(HTTPException):
    def __init__(self, session_id: str | None = None):
        detail = f"Session '{session_id}' not found" if session_id else "Session not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ApiKeyNotFound(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")


class PlanLimitExceeded(HTTPException):
    def __init__(self, resource: str, limit: int, plan: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{resource} limit of {limit} reached for '{plan}' plan. Please upgrade.",
        )


class Unauthorized(HTTPException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
