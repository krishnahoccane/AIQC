from pydantic import BaseModel, EmailStr

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re


ALLOWED_ROLES = {"staff", "user"}


class UserCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str
    assigned_staff_id: Optional[str] = None

    # -------- ROLE VALIDATION --------
    @field_validator("role")
    @classmethod
    def validate_role(cls, value):
        if value not in ALLOWED_ROLES:
            raise ValueError("Super admin can only create staff or user")
        return value

    # -------- PASSWORD VALIDATION --------
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value):

        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")

        if not re.search(r"[!@#$%^&*()_+\-=]", value):
            raise ValueError("Password must contain at least one special character")

        return value

    # -------- STAFF ASSIGNMENT VALIDATION --------
    @field_validator("assigned_staff_id")
    @classmethod
    def validate_staff_assignment(cls, value, info):
        role = info.data.get("role")

        if role == "user" and not value:
            raise ValueError("User must be assigned to a staff")

        if role == "staff" and value:
            raise ValueError("Staff cannot be assigned to another staff")

        return value
    
class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True