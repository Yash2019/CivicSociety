from backend.db.db import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, DateTime, func
from sqlalchemy import Enum as SQLEnum
from datetime import datetime
from backend.enums import SubmitterType, StatusType
from backend.Models.users_db import Users


class Problems(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(nullable=False)
    priority_score: Mapped[int] = mapped_column(nullable=True)
    submitted_by: Mapped[int] = mapped_column(ForeignKey("users.id"),
                                              nullable=True)

    submitter_type: Mapped[SubmitterType] = mapped_column(
        SQLEnum(SubmitterType),
        nullable=False
    )

    district: Mapped[str] = mapped_column(nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)

    status: Mapped[StatusType] = mapped_column(
        SQLEnum(StatusType),
        nullable=True,
        default=StatusType.submitted
    )

    duplicate_problem: Mapped[int] = mapped_column(ForeignKey("problems.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False

    )

class ProblemMedia(Base):

    __tablename__ = "problem_media"
    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"))
    file_url:Mapped[str] = mapped_column(nullable=False)
    file_type: Mapped[str] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
        
