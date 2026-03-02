from fastapi import Depends, HTTPException
from jose import jwt
from core.config import settings
from models.user import User
from core.database import SessionLocal
from fastapi import Depends, HTTPException
#from dependencies.auth import oauth2_scheme
from core.security import decode_token
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from dependencies.auth import get_token
from core.security import decode_token
from core.database import get_db
from models.user import User


def get_current_user(token: str):
    db = SessionLocal()
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    user = db.query(User).filter(User.id == payload["sub"]).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return user

def require_role(roles: list):

    def role_checker(
        token: str = Depends(get_token),
        db: Session = Depends(get_db)
    ):

        payload = decode_token(token)

        user_id = payload.get("sub")

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Not authorized")

        return user

    return role_checker