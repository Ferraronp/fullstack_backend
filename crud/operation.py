from models import models
from sqlalchemy.orm import Session
import schemas.operation
from datetime import date
from sqlalchemy import func


def get_operations(
        db: Session,
        current_user: models.User,
        start_date: date | None = None,
        end_date: date | None = None,
):
    query = db.query(models.Operation).filter(models.Operation.user_id == current_user.id)
    if start_date:
        query = query.filter(models.Operation.date >= start_date)
    if end_date:
        query = query.filter(models.Operation.date <= end_date)
    return query.all()

def create_operation(
        op: schemas.operation.OperationCreate,
        db: Session,
        current_user: models.User
):
    new_op = models.Operation(**op.model_dump(), user_id=current_user.id)
    db.add(new_op)
    db.commit()
    db.refresh(new_op)
    return new_op

def get_operation(operation_id: int, db: Session,
                  current_user: models.User):
    op = db.query(models.Operation).filter(models.Operation.id == operation_id,
                                           models.Operation.user_id == current_user.id).first()
    return op

def update_operation(op: models.Operation, updated: schemas.operation.OperationCreate, db: Session):
    for key, value in updated.model_dump().items():
        setattr(op, key, value)
    db.commit()
    db.refresh(op)

def delete_operation(op: models.Operation, db: Session):
    db.delete(op)
    db.commit()

def get_total_balance(db: Session, current_user: models.User):
    total = db.query(func.sum(models.Operation.amount)).filter(
        models.Operation.user_id == current_user.id).scalar() or 0.0
    return total
