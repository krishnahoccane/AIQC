from fastapi import Depends, HTTPException
from jose import jwt
from core.config import settings
from models.user import User
from core.database import SessionLocal


def get_current_user(token: str):
    db = SessionLocal()
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    user = db.query(User).filter(User.id == payload["sub"]).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return user


def require_role(roles: list):
    def role_checker(user=Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return role_checker