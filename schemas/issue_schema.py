from pydantic import BaseModel,Field
from typing import Optional


class IssueCreate(BaseModel):
    title: str  = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=5)


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

class IssueCommentCreate(BaseModel):
    comment: str