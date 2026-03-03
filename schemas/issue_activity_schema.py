from pydantic import BaseModel


class IssueCommentCreate(BaseModel):
    comment: str