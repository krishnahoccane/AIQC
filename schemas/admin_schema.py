from pydantic import BaseModel
from typing import Optional

class UserStatusUpdate(BaseModel):
    is_active: bool


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True