from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db.database import get_db
from utils.auth import get_current_user
from schemas import operation
from models import models
import crud.operation

router = APIRouter(prefix="/operations", tags=["Operations"])


@router.get("/", response_model=list[operation.Operation])
def get_operations(
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user),
        start_date: date | None = Query(None),
        end_date: date | None = Query(None),
):
    query = crud.operation.get_operations(db, current_user, start_date, end_date)
    return query


@router.post("/", response_model=operation.Operation)
def create_operation(
        op: operation.OperationCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    print(op.category_id)
    new_op = crud.operation.create_operation(op, db, current_user)
    return new_op


@router.get("/{operation_id}", response_model=operation.Operation)
def get_operation(operation_id: int, db: Session = Depends(get_db),
                  current_user: models.User = Depends(get_current_user)):
    op = crud.operation.get_operation(operation_id, db, current_user)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    return op


@router.put("/{operation_id}", response_model=operation.Operation)
def update_operation(operation_id: int, updated: operation.OperationCreate, db: Session = Depends(get_db),
                     current_user: models.User = Depends(get_current_user)):
    op = crud.operation.get_operation(operation_id, db, current_user)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    crud.operation.update_operation(op, updated, db)
    return op


@router.delete("/{operation_id}")
def delete_operation(operation_id: int, db: Session = Depends(get_db),
                     current_user: models.User = Depends(get_current_user)):
    op = crud.operation.get_operation(operation_id, db, current_user)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    crud.operation.delete_operation(op, db)


@router.get("/balance/total")
def get_total_balance(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    total = crud.operation.get_total_balance(db, current_user)
    return {"balance": total, "currency": current_user.currency}
