from sqlalchemy import Column, String, Boolean, Enum, ForeignKey
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
import uuid
from AIQC.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("super_admin", "staff", "user"), nullable=False)
    is_active = Column(Boolean, default=True)
    assigned_staff_id = Column(CHAR(36), ForeignKey("users.id"), nullable=True)

    assigned_staff = relationship("User", remote_side=[id])