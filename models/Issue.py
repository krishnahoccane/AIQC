from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from core.database import Base


class Issue(Base):
    __tablename__ = "issues"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    status = Column(
        Enum("open", "in_progress", "resolved", "closed"),
        default="open",
        nullable=False
    )

    user_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False)
    staff_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])
    staff = relationship("User", foreign_keys=[staff_id])

