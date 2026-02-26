from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from models.user import User
from models.audit_log import AuditLog
from core.security import hash_password


def create_user(db: Session, data, performed_by):

    if data.role == "super_admin":
        raise HTTPException(status_code=403, detail="Cannot create super admin")

    try:
        if data.role == "user":
            count = db.execute(
                select(func.count()).select_from(User)
                .where(User.assigned_staff_id == data.assigned_staff_id)
                .with_for_update()
            ).scalar()

            if count >= 100:
                raise HTTPException(status_code=400, detail="Staff limit reached")

        new_user = User(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
            role=data.role,
            assigned_staff_id=data.assigned_staff_id
        )

        db.add(new_user)
        db.add(AuditLog(
            id=data.email,
            action="User Created",
            performed_by=performed_by
        ))

        db.commit()
        return new_user

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate entry")