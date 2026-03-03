from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.rbac import require_role

from models.Issue import Issue
from models.user import User

from schemas.issue_schema import IssueCreate, IssueUpdateStatus
from fastapi import APIRouter

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.rbac import require_role

from models.Issue import Issue
from models.issue_activity import IssueActivity

from schemas.issue_schema import IssueCommentCreate


router = APIRouter(prefix="/issues", tags=["Issues"])


VALID_TRANSITIONS = {
    "open": ["in_progress"],
    "in_progress": ["resolved"],
    "resolved": ["closed"],
    "closed": []
}


# -----------------------------
# USER CREATES ISSUE
# -----------------------------
@router.post("/")
def create_issue(
    payload: IssueCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(["user"]))
):

    if not user.assigned_staff_id:
        raise HTTPException(
            status_code=400,
            detail="User is not assigned to any staff"
        )

    issue = Issue(
        title=payload.title,
        description=payload.description,
        user_id=user.id,
        staff_id=user.assigned_staff_id,
        status="open"
    )

    db.add(issue)
    db.commit()
    db.refresh(issue)

    return issue


# -----------------------------
# USER VIEW SUBMITTED ISSUES
# -----------------------------
@router.get("/my-issues")
def get_user_issues(
    db: Session = Depends(get_db),
    user=Depends(require_role(["user"]))
):

    issues = db.query(Issue).filter(
        Issue.user_id == user.id
    ).all()

    return {
        "success": True,
        "message": "User issues fetched successfully",
        "count": len(issues),
        "data": issues
    }


@router.post("/{issue_id}/comment")
def add_issue_comment(
    issue_id: str,
    comment_data: IssueCommentCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(["user"]))
):

    issue = db.query(Issue).filter(Issue.id == issue_id).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Ensure user owns the issue
    if issue.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only comment on your own issues"
        )

    activity = IssueActivity(
        id=str(uuid.uuid4()),
        issue_id=issue_id,
        staff_id=None,
        action="user_comment",
        comment=comment_data.comment
    )

    db.add(activity)
    db.commit()

    return {
        "success": True,
        "message": "Comment added successfully",
        "data": {
            "issue_id": issue_id,
            "comment": comment_data.comment
        }
    }

@router.patch("/{issue_id}/close")
def close_issue(
    issue_id: str,
    db: Session = Depends(get_db),
    user=Depends(require_role(["user"]))
):

    issue = db.query(Issue).filter(Issue.id == issue_id).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Ensure user owns the issue
    if issue.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only close your own issue"
        )

    if issue.status == "closed":
        raise HTTPException(
            status_code=400,
            detail="Issue already closed"
        )

    issue.status = "closed"

    activity = IssueActivity(
        id=str(uuid.uuid4()),
        issue_id=issue_id,
        staff_id=None,
        action="issue_closed",
        comment="Issue closed by user"
    )

    db.add(activity)
    db.commit()

    return {
        "success": True,
        "message": "Issue closed successfully",
        "data": {
            "issue_id": issue_id,
            "status": "closed"
        }
    }