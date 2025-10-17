from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from auth import get_current_user
import models, schemas

router = APIRouter(prefix="/operations", tags=["Operations"])


@router.get("/", response_model=list[schemas.Operation])
def get_operations(
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user),
        start_date: date | None = Query(None),
        end_date: date | None = Query(None),
):
    query = db.query(models.Operation).filter(models.Operation.user_id == current_user.id)
    if start_date:
        query = query.filter(models.Operation.date >= start_date)
    if end_date:
        query = query.filter(models.Operation.date <= end_date)
    return query.all()


@router.post("/", response_model=schemas.Operation)
def create_operation(
        op: schemas.OperationCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    new_op = models.Operation(**op.model_dump(), user_id=current_user.id)
    db.add(new_op)
    db.commit()
    db.refresh(new_op)
    return new_op


@router.get("/{operation_id}", response_model=schemas.Operation)
def get_operation(operation_id: int, db: Session = Depends(get_db),
                  current_user: models.User = Depends(get_current_user)):
    op = db.query(models.Operation).filter(models.Operation.id == operation_id,
                                           models.Operation.user_id == current_user.id).first()
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    return op


@router.put("/{operation_id}", response_model=schemas.Operation)
def update_operation(operation_id: int, updated: schemas.OperationCreate, db: Session = Depends(get_db),
                     current_user: models.User = Depends(get_current_user)):
    op = db.query(models.Operation).filter(models.Operation.id == operation_id,
                                           models.Operation.user_id == current_user.id).first()
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    for key, value in updated.model_dump().items():
        setattr(op, key, value)
    db.commit()
    db.refresh(op)
    return op


@router.delete("/{operation_id}")
def delete_operation(operation_id: int, db: Session = Depends(get_db),
                     current_user: models.User = Depends(get_current_user)):
    op = db.query(models.Operation).filter(models.Operation.id == operation_id,
                                           models.Operation.user_id == current_user.id).first()
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    db.delete(op)
    db.commit()
    return {"detail": "Operation deleted"}


@router.get("/balance/total")
def get_total_balance(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    total = db.query(func.sum(models.Operation.amount)).filter(
        models.Operation.user_id == current_user.id).scalar() or 0.0
    return {"balance": total, "currency": current_user.currency}
