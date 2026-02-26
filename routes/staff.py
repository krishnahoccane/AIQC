from schemas.issue_schema import Issue
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dependencies.rbac import require_role
from core.database import get_db

router = APIRouter(prefix="/admin")

@router.get("/my-issues")
def get_my_issues(
    db: Session = Depends(get_db),
    staff=Depends(require_role(["staff"]))
):
    return db.query(Issue).filter(Issue.staff_id == staff.id).all()