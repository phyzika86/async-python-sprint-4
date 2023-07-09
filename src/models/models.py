from sqlalchemy import Boolean, Column, Integer, String, Text

from src.db.database import Base


class URL(Base):
    __tablename__ = "urls"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    key = Column(Text, unique=True, index=True)
    secret_key = Column(Text, unique=True, index=True)
    target_url = Column(Text, index=True)
    is_active = Column(Boolean, default=True)
    clicks = Column(Integer, default=0)
    is_delete = Column(Boolean, default=False)
