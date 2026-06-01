from __future__ import annotations
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .user import User
    from .api_key import ApiKey
    from .session import Session


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_project_user_name"),
    )

    owner: Mapped[User] = relationship("User", back_populates="projects")
    api_keys: Mapped[List[ApiKey]] = relationship(
        "ApiKey",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[List[Session]] = relationship(
        "Session",
        back_populates="project",
        cascade="all, delete-orphan",
    )
