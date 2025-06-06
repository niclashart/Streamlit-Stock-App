"""
User repository for database operations
"""
from typing import Optional
from sqlalchemy.orm import Session

from backend.repositories.base import BaseRepository
from backend.models.user import User
from backend.schemas.auth import UserCreate, UserUpdate

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """Repository for user operations"""
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()

    def create_with_password(self, db: Session, *, obj_in: UserCreate, hashed_password: str) -> User:
        """Create user with hashed password"""
        db_obj = User(
            username=obj_in.username,
            password_hash=hashed_password
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

# Create a singleton instance
user_repository = UserRepository(User)
