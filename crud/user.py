from models import models
from sqlalchemy.orm import Session
import schemas.user
import schemas.auth

def get_user(user: schemas.user.UserCreate, db: Session):
    user = db.query(models.User).filter(models.User.email == user.email).first()
    return user

def create_user(user: schemas.user.UserCreate, db: Session, hashed: str):
    new_user = models.User(email=user.email, hashed_password=hashed, currency=user.currency)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
