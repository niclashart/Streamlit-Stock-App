"""
User authentication and authorization service
"""
import hashlib
import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.database import get_db_session
from backend.models import User
from backend.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def hash_password(password: str) -> str:
    """Hash a password using MD5 (Note: Consider using a stronger algorithm in production)"""
    return hashlib.md5(password.encode()).hexdigest()

def create_user(username: str, password: str) -> User:
    """Create a new user"""
    with get_db_session() as session:
        # Check if user exists
        existing_user = session.query(User).filter(User.username == username).first()
        if existing_user:
            raise ValueError("Username already exists")
        
        # Create new user
        user = User(username=username, password_hash=hash_password(password))
        session.add(user)
        return user

def authenticate_user(username: str, password: str) -> User:
    """Authenticate a user by username and password"""
    with get_db_session() as session:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return None
        if user.password_hash != hash_password(password):
            return None
        return user

def create_access_token(data: dict) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current user from a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    with get_db_session() as session:
        user = session.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
