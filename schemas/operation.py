from datetime import date
from pydantic import BaseModel, EmailStr
from typing import Optional
from schemas.category import Category


class OperationBase(BaseModel):
    date: date
    amount: float
    comment: Optional[str] = None
    category_id: Optional[int] = None


class OperationCreate(OperationBase):
    pass


class Operation(OperationBase):
    id: int
    category: Optional[Category] = None

    class Config:
        orm_mode = True
