from sqlalchemy import Column, String
from core.database import Base

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    token = Column(String(500), primary_key=True)