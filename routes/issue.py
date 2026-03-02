from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.rbac import require_role

from models.Issue import Issue
from models.user import User

from schemas.issue_schema import IssueCreate, IssueUpdateStatus
from fastapi import APIRouter


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
# STAFF VIEW ASSIGNED ISSUES
# -----------------------------
@router.get("/my-issues")
def get_staff_issues(
    db: Session = Depends(get_db),
    staff=Depends(require_role(["staff"]))
):

    issues = db.query(Issue).filter(
        Issue.staff_id == staff.id
    ).all()

    return issues


# -----------------------------
# STAFF UPDATE ISSUE STATUS
# -----------------------------
@router.patch("/{issue_id}/status")
def update_issue_status(
    issue_id: str,
    payload: IssueUpdateStatus,
    db: Session = Depends(get_db),
    staff=Depends(require_role(["staff"]))
):

    issue = db.query(Issue).filter(Issue.id == issue_id).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if issue.staff_id != staff.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to update this issue"
        )

    if payload.status not in VALID_TRANSITIONS[issue.status]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from {issue.status} to {payload.status}"
        )

    issue.status = payload.status

    db.commit()
    db.refresh(issue)

    return issue


# -----------------------------
# ADMIN VIEW ALL ISSUES
# -----------------------------
@router.get("/all")
def get_all_issues(
    db: Session = Depends(get_db),
    admin=Depends(require_role(["super_admin"]))
):

    return db.query(Issue).all()