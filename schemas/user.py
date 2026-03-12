from pydantic import BaseModel

# Users
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    currency: str = "$"
    role: str = "user"

class UserOut(UserBase):
    id: int
    currency: str
    role: str

    class Config:
        orm_mode = True

class RoleUpdate(BaseModel):
    role: str
