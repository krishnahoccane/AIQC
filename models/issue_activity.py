from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from core.database import Base

class IssueActivity(Base):

    __tablename__ = "issue_activities"

    id = Column(String(36), primary_key=True)
    issue_id = Column(String(36), ForeignKey("issues.id"))
    staff_id = Column(String(36), ForeignKey("users.id"))

    action = Column(String(255))
    comment = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())