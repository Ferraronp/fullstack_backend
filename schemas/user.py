from pydantic import BaseModel, EmailStr

# Users
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    currency: str = "$"
    role: str = "user"  # optional, default user

class UserOut(UserBase):
    id: int
    currency: str
    role: str

    class Config:
        orm_mode = True

class RoleUpdate(BaseModel):
    role: str
