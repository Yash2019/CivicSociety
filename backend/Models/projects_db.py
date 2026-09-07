from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, DateTime, func, String, Text
from sqlalchemy import Enum as SQLEnum
from backend.db.db import Base
from backend.enums import ProjectStage, ApprovalStatus




class Projects(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    proposal_text: Mapped[str] = mapped_column(Text, nullable=False)

    stage: Mapped[ProjectStage] = mapped_column(
        SQLEnum(ProjectStage),
        default=ProjectStage.proposed,
        nullable=False
    )
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        SQLEnum(ApprovalStatus),
        default=ApprovalStatus.pending,
        nullable=False
    )
    approved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

