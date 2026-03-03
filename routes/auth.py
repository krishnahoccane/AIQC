from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from models.user import User
from schemas.user_schema import LoginSchema

from passlib.context import CryptContext
from core.security import create_access_token
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException



from core.security import decode_token

from dependencies.auth import get_token

from models.token_blacklist import TokenBlacklist


router = APIRouter(prefix="/auth", tags=["Auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id), "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.post("/refresh-token")
def refresh_token(
    token: str = Depends(get_token),
    db: Session = Depends(get_db)
):

    # Check if token is blacklisted
    blacklisted = db.query(TokenBlacklist).filter(
        TokenBlacklist.token == token
    ).first()

    if blacklisted:
        raise HTTPException(
            status_code=401,
            detail="Token has been logged out"
        )

    payload = decode_token(token)

    user_id = payload.get("sub")
    role = payload.get("role")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload"
        )

    new_token = create_access_token(
        data={"sub": user_id, "role": role}
    )

    return {
        "success": True,
        "message": "Token refreshed successfully",
        "data": {
            "access_token": new_token,
            "token_type": "bearer"
        }
    }


@router.post("/logout")
def logout(
    token: str = Depends(get_token),
    db: Session = Depends(get_db)
):

    existing = db.query(TokenBlacklist).filter(
        TokenBlacklist.token == token
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Token already logged out"
        )

    blacklist_entry = TokenBlacklist(
        id=str(uuid.uuid4()),
        token=token
    )

    db.add(blacklist_entry)
    db.commit()

    return {
        "success": True,
        "message": "Logged out successfully"
    }