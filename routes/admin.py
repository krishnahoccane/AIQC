from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.user_schema import UserCreate
from services.user_service import create_user
from dependencies.rbac import require_role
#from dependencies.auth import oauth2_scheme

from models.user import User
from models.Issue import Issue
from fastapi import Query
from schemas.admin_schema import UserStatusUpdate,UserResponse
from typing import List


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/create-user")
def admin_create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_role(["super_admin"]))
):

    existing_user = db.query(User).filter(User.email == user.email).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )

    new_user = create_user(db, user, admin.id)

    return {
        "success": True,
        "message": "User created successfully",
        "data": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role
        }
    }

@router.get("/users",response_model=List[UserResponse])
def get_all_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    db: Session = Depends(get_db),
    admin=Depends(require_role(["super_admin"]))
):
    
    offset = (page - 1) * limit

    users = (
        db.query(User)
        .offset(offset)
        .limit(limit)
        .all()
    )

    total_users = db.query(User).count()

    return {
        "success": True,
        "message": "Users fetched successfully",
        "page": page,
        "limit": limit,
        "total_users": total_users,
        "data": users
    }


@router.patch("/users/{user_id}/status")
def update_user_status(
    user_id: str,
    status_update: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_role(["super_admin"]))
):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "super_admin":
        raise HTTPException(status_code=403, detail="Cannot modify super admin")

     # Only staff can be activated/deactivated
    if user.role != "staff":
        raise HTTPException(
            status_code=403,
            detail="Activation/deactivation allowed only for staff"
        )

    user.is_active = status_update.is_active

    db.commit()
    db.refresh(user)

    return {
        "success": True,
        "message": "Staff status updated successfully",
        "data": {
            "user_id": user.id,
            "is_active": user.is_active
        }
    }


# Delete user (only role=user can be deleted)
@router.delete("/delete-user/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    admin=Depends(require_role(["super_admin"]))
):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent deleting super admin
    if user.role == "super_admin":
        raise HTTPException(
            status_code=403,
            detail="Cannot delete super admin"
        )

    # Prevent deleting staff
    if user.role != "user":
        raise HTTPException(
            status_code=403,
            detail="Only users can be deleted"
        )

    db.delete(user)
    db.commit()

    return {
        "success": True,
        "message": "User deleted successfully",
        "data": {
            "deleted_user_id": user_id
        }
    }


# View all issues
@router.get("/all-issues")
def get_all_issues(
    db: Session = Depends(get_db),
    admin=Depends(require_role(["super_admin"]))
):

    issues = db.query(Issue).all()

    return {
        "success": True,
        "message": "Issues fetched successfully",
        "count": len(issues),
        "data": issues
    }