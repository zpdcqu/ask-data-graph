from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    # Add other fields that can be updated by user or admin

class UserInDBBase(UserBase):
    id: int
    is_active: bool = True
    role: str = "user" # Default role
    created_at: datetime

    class Config:
        orm_mode = True

class User(UserInDBBase):
    pass

class UserInDB(UserInDBBase):
    hashed_password: str 