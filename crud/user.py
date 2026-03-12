from models import models
from sqlalchemy.orm import Session
import schemas.user
import schemas.auth

def get_user(user, db: Session):
    user = db.query(models.User).filter(models.User.username == user.username).first()
    return user

def create_user(user: schemas.user.UserCreate, db: Session, hashed: str):
    new_user = models.User(username=user.username, hashed_password=hashed, currency=user.currency, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
