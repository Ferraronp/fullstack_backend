from datetime import date
from pydantic import BaseModel
from typing import Optional


# Category
class CategoryBase(BaseModel):
    name: str
    color: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int

    class Config:
        orm_mode = True


# Operation
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
