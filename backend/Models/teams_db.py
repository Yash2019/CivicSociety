from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, func
from backend.db.db import Base
from datetime import datetime


class Teams(Base):
    __tablename__ = 'teams'

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey('problems.id'))
    institution_id: Mapped[int] = mapped_column(ForeignKey('institutions.id'))
    faculty_mentor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )

class Team_member(Base):
    __tablename__ = 'team_members'

    team_id: Mapped[int] = mapped_column(
        ForeignKey('teams.id'),
        primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'),
        primary_key=True
    )