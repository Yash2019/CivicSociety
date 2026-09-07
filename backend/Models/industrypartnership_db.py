from datetime import datetime, date
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import ForeignKey, DateTime, Date, func, String, Text, Integer, Boolean
from sqlalchemy import Enum as SQLEnum


class IndustryPartnerships(Base):
    __tablename__ = "industry_partnerships"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    industry_institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    partnership_type: Mapped[PartnershipType] = mapped_column(
        SQLEnum(PartnershipType),
        nullable=False
    )
    status: Mapped[PartnershipStatus] = mapped_column(
        SQLEnum(PartnershipStatus),
        default=PartnershipStatus.requested,
        nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())