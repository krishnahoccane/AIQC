from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.rbac import require_role

from models.user import User
from models.Issue import Issue
import uuid
from models.issue_activity import IssueActivity
from schemas.issue_activity_schema import IssueCommentCreate
from schemas.user_schema import StaffUserResponse
from typing import List

router = APIRouter(prefix="/staff", tags=["Staff"])


# -------------------------
# GET ASSIGNED USERS
# -------------------------
@router.get("/users",response_model=List[StaffUserResponse])
def get_assigned_users(
    db: Session = Depends(get_db),
    staff=Depends(require_role(["staff"]))
):

    users = db.query(User).filter(
        User.assigned_staff_id == staff.id
    ).all()

    return users


# -------------------------
# GET ISSUES FROM USERS
# -------------------------
@router.get("/issues")
def get_staff_issues(
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    staff=Depends(require_role(["staff"]))
):

    query = db.query(Issue).filter(
        Issue.staff_id == staff.id
    )

    if status:
        query = query.filter(Issue.status == status)

    return query.all()


# -------------------------
# GET SINGLE ISSUE DETAILS
# -------------------------
@router.get("/issues/{issue_id}")
def get_issue_detail(
    issue_id: str,
    db: Session = Depends(get_db),
    staff=Depends(require_role(["staff"]))
):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if issue.staff_id != staff.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this issue"
        )

    return issue


# -------------------------
# UPDATE ISSUE STATUS
# -------------------------
VALID_TRANSITIONS = {
    "open": ["in_progress"],
    "in_progress": ["resolved"],
    "resolved": ["closed"],
    "closed": []
}


@router.patch("/issues/{issue_id}/status")
def update_issue_status(
    issue_id: str,
    new_status: str,
    db: Session = Depends(get_db),
    staff=Depends(require_role(["staff"]))
):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if issue.staff_id != staff.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to update this issue"
        )

    if new_status not in VALID_TRANSITIONS[issue.status]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from {issue.status} to {new_status}"
        )

    issue.status = new_status

    db.commit()
    db.refresh(issue)

    return issue

@router.post("/issues/{issue_id}/comment")
def add_issue_comment(
    issue_id: str,
    comment_data: IssueCommentCreate,
    db: Session = Depends(get_db),
    staff=Depends(require_role(["staff"]))
):

    issue = db.query(Issue).filter(Issue.id == issue_id).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    activity = IssueActivity(
        id=str(uuid.uuid4()),
        issue_id=issue_id,
        staff_id=staff.id,
        action="comment_added",
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

@router.get("/issues/{issue_id}/history")
def get_issue_history(
    issue_id: str,
    db: Session = Depends(get_db),
    staff=Depends(require_role(["staff"]))
):

    issue = db.query(Issue).filter(Issue.id == issue_id).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    activities = (
        db.query(IssueActivity)
        .filter(IssueActivity.issue_id == issue_id)
        .order_by(IssueActivity.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "message": "Issue activity fetched successfully",
        "count": len(activities),
        "data": activities
    }