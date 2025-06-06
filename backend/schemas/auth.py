"""
Authentication schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, validator


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """User create schema"""
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """User update schema"""
    password: Optional[str] = Field(None, min_length=6)


class UserInDB(UserBase):
    """User database schema"""
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True


class UserResponse(UserBase):
    """User response schema"""
    class Config:
        orm_mode = True


class Token(BaseModel):
    """Token schema"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data schema"""
    username: Optional[str] = None
