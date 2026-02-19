from sqlalchemy.orm import Session
from models import models
import schemas.user

def get_all_users(db: Session):
    return db.query(models.User).all()

def get_user_by_id(user_id: int, db: Session):
    return db.query(models.User).filter(models.User.id == user_id).first()

def update_user_role(user: models.User, new_role: str, db: Session):
    user.role = new_role
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
