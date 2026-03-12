from sqlalchemy.orm import Session
from models.models import RefreshToken, RevokedToken
from datetime import datetime


def save_refresh_token(db: Session, token: str, user_id: int, expires_at: datetime) -> RefreshToken:
    rt = RefreshToken(token=token, user_id=user_id, expires_at=expires_at)
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt


def get_refresh_token(db: Session, token: str) -> RefreshToken | None:
    return db.query(RefreshToken).filter(RefreshToken.token == token).first()


def revoke_refresh_token(db: Session, token: str) -> None:
    rt = get_refresh_token(db, token)
    if rt:
        rt.revoked = True
        db.commit()


def revoke_all_user_refresh_tokens(db: Session, user_id: int) -> None:
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False
    ).update({"revoked": True})
    db.commit()


# Access token revocation (существующий механизм)
def is_access_token_revoked(db: Session, token: str) -> bool:
    return db.query(RevokedToken).filter(RevokedToken.token == token).first() is not None


def revoke_access_token(db: Session, token: str) -> None:
    if not is_access_token_revoked(db, token):
        db.add(RevokedToken(token=token))
        db.commit()
