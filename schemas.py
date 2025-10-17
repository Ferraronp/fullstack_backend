from datetime import date
from pydantic import BaseModel, EmailStr
from typing import Optional


# Users
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str
    currency: str = "$"


class UserOut(UserBase):
    id: int
    currency: str

    class Config:
        orm_mode = True


# Auth
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


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
