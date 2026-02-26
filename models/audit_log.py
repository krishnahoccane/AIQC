from sqlalchemy import Column, String, DateTime
from datetime import datetime
from core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True)
    action = Column(String(255))
    performed_by = Column(String(36))
    timestamp = Column(DateTime, default=datetime.utcnow)