from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


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


def create_access_token(user_id: str):
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode({"sub": user_id, "exp": expire}, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str):
    expire = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    return jwt.encode({"sub": user_id, "exp": expire, "type": "refresh"},
                      settings.SECRET_KEY, algorithm=ALGORITHM)