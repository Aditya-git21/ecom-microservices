from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional

# Base properties shared across schemas
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None

# Properties received on User Creation (Registration)
class UserCreate(UserBase):
    password: str

# Properties returned to the client (Hides password_hash)
class UserOut(UserBase):
    id: UUID
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schema for incoming Login credentials
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Schema representing Token responses
class Token(BaseModel):
    access_token: str
    token_type: str

# Schema data embedded inside the JWT payload
class TokenData(BaseModel):
    user_id: Optional[str] = None

