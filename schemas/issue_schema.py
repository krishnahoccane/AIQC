from pydantic import BaseModel
from typing import Optional


class IssueCreate(BaseModel):
    title: str
    description: str


class IssueUpdateStatus(BaseModel):
    status: str  # validated in service


class IssueResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str
    user_id: str
    staff_id: str

    class Config:
        from_attributes = True