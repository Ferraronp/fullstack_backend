from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from fastapi import HTTPException, status
import secrets
import os
from dotenv import load_dotenv

from models.models import User
from repositories import token_repo

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(user: User) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"user_id": user.id, "role": user.role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(64)
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token_repo.save_refresh_token(db, token=token, user_id=user.id, expires_at=expires_at)
    return token


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")


def rotate_refresh_token(db: Session, old_token: str) -> tuple[User, str]:
    """Валидирует старый refresh token, отзывает его и выдаёт новый."""
    rt = token_repo.get_refresh_token(db, old_token)

    if not rt or rt.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if rt.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    token_repo.revoke_refresh_token(db, old_token)

    new_token = create_refresh_token(db, rt.user)
    return rt.user, new_token


def logout(db: Session, access_token: str, refresh_token: str) -> None:
    token_repo.revoke_access_token(db, access_token)
    token_repo.revoke_refresh_token(db, refresh_token)
