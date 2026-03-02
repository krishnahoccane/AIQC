from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.rbac import require_role

from models.user import User
from models.Issue import Issue

router = APIRouter(prefix="/staff", tags=["Staff"])


# -------------------------
# GET ASSIGNED USERS
# -------------------------
@router.get("/users")
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