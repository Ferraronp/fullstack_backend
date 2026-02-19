from models import models
from sqlalchemy.orm import Session
import schemas.category

def get_categories(db: Session, current_user: models.User):
    return db.query(models.Category).filter(models.Category.user_id == current_user.id).all()


def get_category(category_id: int, db: Session,
                 current_user: models.User):
    return db.query(models.Category).filter(
        models.Category.id == category_id,
        models.Category.user_id == current_user.id
    ).first()

def create_category(category: schemas.category.CategoryCreate,
        db: Session,
        current_user: models.User):
    new_category = models.Category(**category.model_dump(), user_id=current_user.id)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

def update_category(category: models.Category, updated: schemas.category.CategoryCreate, db: Session):
    for key, value in updated.model_dump().items():
        setattr(category, key, value)
    db.commit()
    db.refresh(category)
    return category

def delete_category(category: models.Category, db: Session):
    db.delete(category)
    db.commit()
