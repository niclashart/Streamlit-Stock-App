"""
Authentication service
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from pydantic import ValidationError
from fastapi import Depends, HTTPException, status

from backend.core.config import settings
from backend.core.security import verify_password, get_password_hash, oauth2_scheme, create_access_token
from backend.repositories.user_repository import user_repository
from backend.core.database import get_db
from backend.models.user import User
from backend.schemas.auth import UserCreate, TokenData


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user"""
    user = user_repository.get_by_username(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user"""
    # Check if user already exists
    db_user = user_repository.get_by_username(db, username=user_data.username)
    if db_user:
        raise ValueError(f"Username '{user_data.username}' already exists")
    
    # Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # Create and return the user
    return user_repository.create_with_password(
        db=db,
        obj_in=user_data,
        hashed_password=hashed_password
    )


async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """Get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except (JWTError, ValidationError):
        raise credentials_exception
        
    # Get user from database
    user = user_repository.get_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
        
    return user
