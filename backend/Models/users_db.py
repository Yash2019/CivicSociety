from backend.db.db import Base
from sqlalchemy.orm import Mapped, mapped_column

class Users(Base):
    __tablename__ = "Users"
    id: Mapped[int] = mapped_column(primary_key=True)