from datetime import date
from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from schemas.category import Category


class OperationFileOut(BaseModel):
    id: int
    filename: str
    content_type: Optional[str] = None

    class Config:
        orm_mode = True


class OperationBase(BaseModel):
    date: date
    amount: float
    comment: Optional[str] = None
    category_id: Optional[int] = None

    @field_validator("amount")
    @classmethod
    def amount_not_zero(cls, v):
        if v == 0:
            raise ValueError("Amount cannot be zero")
        return v


class OperationCreate(OperationBase):
    pass


class Operation(OperationBase):
    id: int
    category: Optional[Category] = None
    files: list[OperationFileOut] = []

    class Config:
        orm_mode = True


class OperationsPage(BaseModel):
    items: list[Operation]
    total: int
    page: int
    page_size: int
    pages: int
