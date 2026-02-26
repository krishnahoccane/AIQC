from sqlalchemy.orm import Session
from fastapi import HTTPException
from schemas.issue_schema import Issue
from models.user import User
from models.audit_log import AuditLog


VALID_TRANSITIONS = {
    "open": ["in_progress"],
    "in_progress": ["resolved"],
    "resolved": ["closed"],
    "closed": []
}


def create_issue(db: Session, user: User, data):
    if user.role != "user":
        raise HTTPException(status_code=403, detail="Only users can create issues")

    issue = Issue(
        title=data.title,
        description=data.description,
        user_id=user.id,
        staff_id=user.assigned_staff_id
    )

    db.add(issue)
    db.add(AuditLog(
        id=issue.id,
        action="Issue Created",
        performed_by=user.id
    ))
    db.commit()
    db.refresh(issue)
    return issue


def update_issue_status(db: Session, issue_id: str, staff: User, new_status: str):

    issue = db.query(Issue).filter(Issue.id == issue_id).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if issue.staff_id != staff.id:
        raise HTTPException(status_code=403, detail="Not your assigned issue")

    if new_status not in VALID_TRANSITIONS[issue.status]:
        raise HTTPException(status_code=400, detail="Invalid status transition")

    issue.status = new_status

    db.add(AuditLog(
        id=issue.id,
        action=f"Issue moved to {new_status}",
        performed_by=staff.id
    ))

    db.commit()
    db.refresh(issue)
    return issue