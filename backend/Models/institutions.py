from backend.db.db import Base
from sqlalchemy.orm import Mapped, mapped_column
from backend.enums import InstitutionType, InstitutionDomain, RoutingStatus
from sqlalchemy import Enum as SQLEnum, func, ForeignKey
from datetime import datetime

class Institutions(Base):
    __tablename__ = 'institutions'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()

    type: Mapped[InstitutionType] = mapped_column(
        SQLEnum(InstitutionType)
    )

    domain: Mapped[InstitutionDomain] = mapped_column(
        SQLEnum(InstitutionDomain)
    )

    district: Mapped[str] = mapped_column()
    has_incubation: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )

class Routings(Base):
    __tablename__ = 'routings'

    id: Mapped[int] = mapped_column(primary_key=True)
    problems_id: Mapped[int] = mapped_column(ForeignKey('problems.id'))
    institution_id: Mapped[int] = mapped_column(ForeignKey('institutions.id'))
    matched_reason: Mapped[str] = mapped_column()

    status: Mapped[RoutingStatus] = mapped_column(
        SQLEnum(RoutingStatus),
        default=RoutingStatus.accepted
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )


