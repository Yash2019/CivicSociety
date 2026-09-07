from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, DateTime, func, Text, Integer
from backend.db.db import Base


class ProjectOutcomes(Base):
    __tablename__ = "project_outcomes"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), unique=True, nullable=False)
    patents_filed: Mapped[int] = mapped_column(Integer, default=0)
    startups_created: Mapped[int] = mapped_column(Integer, default=0)
    ip_generated: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())