from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.user_schema import UserCreate
from services.user_service import create_user
from dependencies.rbac import require_role
#from dependencies.auth import oauth2_scheme

from models.user import User
from models.Issue import Issue

router = APIRouter(prefix="/admin", tags=["Admin"])


# Create staff or user
@router.post("/create-user")
def admin_create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_role(["super_admin"]))
):
    return create_user(db, user, admin.id)


# Delete user
@router.delete("/delete-user/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    admin=Depends(require_role(["super_admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "super_admin":
        raise HTTPException(status_code=403, detail="Cannot delete super admin")

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}


# View all issues
@router.get("/all-issues")
def get_all_issues(
    db: Session = Depends(get_db),
    admin=Depends(require_role(["super_admin"]))
):
    return db.query(Issue).all()