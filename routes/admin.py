
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.user_schema import UserCreate
from services.user_service import create_user
from dependencies.rbac import require_role

router = APIRouter(prefix="/admin")

@router.post("/create-user")
def admin_create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_role(["super_admin"]))
):
    return create_user(db, user)

@router.get("/all-issues")
def get_all_issues(
    db: Session = Depends(get_db),
    admin=Depends(require_role(["super_admin"]))
):
    return db.query(Issue).all()