from pydantic import BaseModel, EmailStr


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
