from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional
from sqlalchemy import String, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .project import Project
    from .trace_event import TraceEvent


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tags: Mapped[Dict[str, str]] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project: Mapped[Project] = relationship("Project", back_populates="sessions")
    events: Mapped[List[TraceEvent]] = relationship(
        "TraceEvent",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="TraceEvent.sequence_number",
    )
