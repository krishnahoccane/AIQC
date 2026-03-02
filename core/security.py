from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from core.config import settings
from jose import jwt, JWTError
from fastapi import HTTPException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def validate_password(password: str):
    if len(password) < 8:
        raise ValueError("Password too short")
    if not any(c.isupper() for c in password):
        raise ValueError("Must include uppercase")
    if not any(c.isdigit() for c in password):
        raise ValueError("Must include number")


def hash_password(password: str):
    validate_password(password)
    return pwd_context.hash(password)


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str):
    expire = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    return jwt.encode({"sub": user_id, "exp": expire, "type": "refresh"},
                      settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):

    try:

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )