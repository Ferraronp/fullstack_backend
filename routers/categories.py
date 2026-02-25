from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from utils.auth import get_current_user
import schemas.category
from models import models
import crud.category

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", response_model=list[schemas.category.Category])
def get_categories(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.category.get_categories(db, current_user)


@router.get("/{category_id}", response_model=schemas.category.Category)
def get_category(category_id: int, db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    category = crud.category.get_category(category_id, db, current_user)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("/", response_model=schemas.category.Category)
def create_category(
        category: schemas.category.CategoryCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    categories = crud.category.get_categories(db, current_user)
    for cat in categories:
        if cat.name == category.name:
            raise HTTPException(status_code=400, detail="Category already exists")
    new_category = crud.category.create_category(category, db, current_user)
    return new_category


@router.put("/{category_id}", response_model=schemas.category.Category)
def update_category(
        category_id: int,
        updated: schemas.category.CategoryCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    category = crud.category.get_category(category_id, db, current_user)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    crud.category.update_category(category, updated, db)
    return category


@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    category = crud.category.get_category(category_id, db, current_user)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    crud.category.delete_category(category, db)
