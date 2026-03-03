from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from core.database import Base


class TokenBlacklist(Base):

    __tablename__ = "token_blacklist"

    id = Column(String(36), primary_key=True)
    token = Column(String(500), unique=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())