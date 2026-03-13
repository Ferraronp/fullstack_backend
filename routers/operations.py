from datetime import date
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from db.database import get_db
from utils.auth import get_current_user
from schemas import operation as op_schema
from models import models
from services import s3_service
import crud.operation

router = APIRouter(prefix="/operations", tags=["Operations"])


@router.get("/", response_model=op_schema.OperationsPage)
def get_operations(
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        category_id: Optional[int] = Query(None),
        comment: Optional[str] = Query(None, max_length=200),
        min_amount: Optional[float] = Query(None),
        max_amount: Optional[float] = Query(None),
        sort_by: Literal["date", "amount"] = Query("date"),
        sort_order: Literal["asc", "desc"] = Query("desc"),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
):
    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise HTTPException(status_code=422, detail="min_amount cannot be greater than max_amount")

    return crud.operation.get_operations(
        db, current_user,
        start_date=start_date, end_date=end_date,
        category_id=category_id, comment=comment,
        min_amount=min_amount, max_amount=max_amount,
        sort_by=sort_by, sort_order=sort_order,
        page=page, page_size=page_size,
    )


@router.post("/", response_model=op_schema.Operation)
def create_operation(
        op: op_schema.OperationCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    return crud.operation.create_operation(op, db, current_user)


@router.get("/balance/total")
def get_total_balance(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    total = crud.operation.get_total_balance(db, current_user)
    return {"balance": total, "currency": current_user.currency}


@router.get("/{operation_id}", response_model=op_schema.Operation)
def get_operation(operation_id: int, db: Session = Depends(get_db),
                  current_user: models.User = Depends(get_current_user)):
    op = crud.operation.get_operation(operation_id, db, current_user)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    return op


@router.put("/{operation_id}", response_model=op_schema.Operation)
def update_operation(operation_id: int, updated: op_schema.OperationCreate,
                     db: Session = Depends(get_db),
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
    # удаляем файлы из S3 перед удалением операции
    for f in op.files:
        try:
            s3_service.delete_file(f.s3_key)
        except Exception:
            pass
    crud.operation.delete_operation(op, db)


# --- файлы ---

@router.post("/{operation_id}/files", response_model=op_schema.OperationFileOut)
async def upload_file(
        operation_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user),
):
    op = crud.operation.get_operation(operation_id, db, current_user)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")

    if file.content_type not in s3_service.ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {', '.join(s3_service.ALLOWED_CONTENT_TYPES)}")

    file_bytes = await file.read()
    if len(file_bytes) > s3_service.MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {s3_service.MAX_FILE_SIZE_MB}MB")

    s3_key = s3_service.upload_file(file_bytes, file.filename, file.content_type)
    db_file = crud.operation.create_file(db, operation_id, file.filename, s3_key, file.content_type)
    return db_file


@router.get("/{operation_id}/files/{file_id}/url")
def get_file_url(
        operation_id: int,
        file_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user),
):
    op = crud.operation.get_operation(operation_id, db, current_user)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")

    f = crud.operation.get_file(db, file_id)
    if not f or f.operation_id != operation_id:
        raise HTTPException(status_code=404, detail="File not found")

    url = s3_service.get_presigned_url(f.s3_key)
    return {"url": url, "filename": f.filename, "expires_in": s3_service.PRESIGNED_URL_EXPIRES}


@router.delete("/{operation_id}/files/{file_id}")
def delete_file(
        operation_id: int,
        file_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user),
):
    op = crud.operation.get_operation(operation_id, db, current_user)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")

    f = crud.operation.get_file(db, file_id)
    if not f or f.operation_id != operation_id:
        raise HTTPException(status_code=404, detail="File not found")

    s3_service.delete_file(f.s3_key)
    crud.operation.delete_file(db, f)
    return {"detail": "File deleted"}
