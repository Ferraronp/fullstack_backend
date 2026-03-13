from models import models
from sqlalchemy.orm import Session
from sqlalchemy import func, asc, desc
import schemas.operation
from datetime import date
from typing import Optional


SORT_FIELDS = {
    "date": models.Operation.date,
    "amount": models.Operation.amount,
}


def get_operations(
        db: Session,
        current_user: models.User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_id: Optional[int] = None,
        comment: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        sort_by: str = "date",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
):
    query = db.query(models.Operation).filter(models.Operation.user_id == current_user.id)

    if start_date:
        query = query.filter(models.Operation.date >= start_date)
    if end_date:
        query = query.filter(models.Operation.date <= end_date)
    if category_id:
        query = query.filter(models.Operation.category_id == category_id)
    if comment:
        query = query.filter(models.Operation.comment.ilike(f"%{comment}%"))
    if min_amount is not None:
        query = query.filter(models.Operation.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(models.Operation.amount <= max_amount)

    total = query.count()

    sort_col = SORT_FIELDS.get(sort_by, models.Operation.date)
    order_fn = desc if sort_order == "desc" else asc
    query = query.order_by(order_fn(sort_col))

    items = query.offset((page - 1) * page_size).limit(page_size).all()
    pages = (total + page_size - 1) // page_size

    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


def create_operation(op: schemas.operation.OperationCreate, db: Session, current_user: models.User):
    new_op = models.Operation(**op.model_dump(), user_id=current_user.id)
    db.add(new_op)
    db.commit()
    db.refresh(new_op)
    return new_op


def get_operation(operation_id: int, db: Session, current_user: models.User):
    return db.query(models.Operation).filter(
        models.Operation.id == operation_id,
        models.Operation.user_id == current_user.id
    ).first()


def update_operation(op: models.Operation, updated: schemas.operation.OperationCreate, db: Session):
    for key, value in updated.model_dump().items():
        setattr(op, key, value)
    db.commit()
    db.refresh(op)


def delete_operation(op: models.Operation, db: Session):
    db.delete(op)
    db.commit()


def get_total_balance(db: Session, current_user: models.User):
    return db.query(func.sum(models.Operation.amount)).filter(
        models.Operation.user_id == current_user.id
    ).scalar() or 0.0


# --- файлы ---

def create_file(db: Session, operation_id: int, filename: str, s3_key: str, content_type: str):
    f = models.OperationFile(
        operation_id=operation_id,
        filename=filename,
        s3_key=s3_key,
        content_type=content_type,
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def get_file(db: Session, file_id: int):
    return db.query(models.OperationFile).filter(models.OperationFile.id == file_id).first()


def delete_file(db: Session, file: models.OperationFile):
    db.delete(file)
    db.commit()
