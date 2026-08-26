from backend.db.db import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, DateTime, func
from enum import Enum
from sqlalchemy import Enum as SQLEnum
from datetime import datetime


class SubmitterType(str, Enum):
    individual = "individual"
    commuity_org = "community_org"
    panchayati_Raj_Insitiution = "pri"
    urban_Local_Body = "ulb"
    govt_dept = "govt_dept"

class StatusType(str, Enum):
    submitted =  "submitted"
    under_review = "under_review"
    routed = "routed"
    rejected = "rejected"
    duplicate = "duplicate"


class Problems(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    priority_score: Mapped[int] = mapped_column()
    submitted_by: Mapped[int] = mapped_column(ForeignKey("users.id"))

    submiter_type: Mapped[SubmitterType] = mapped_column(
        SQLEnum(SubmitterType),
        nullable=False
    )

    district: Mapped[str] = mapped_column(nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)

    status: Mapped[StatusType] = mapped_column(
        SQLEnum(StatusType),
        nullable=False
    )

    duplicate_problem: Mapped[int] = mapped_column(ForeignKey("problems.id"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False

    )



