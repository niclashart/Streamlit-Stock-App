"""
User model module for handling user-related data structures and operations
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hashlib
from typing import Dict, Any, Optional
from src.database.storage_factory import StorageFactory

class User:
    """User model class"""
    
    def __init__(self, username: str, password_hash: str = None, password: str = None):
        """Initialize user with username and either password_hash or password"""
        self.username = username
        
        if password_hash:
            self.password_hash = password_hash
        elif password:
            self.password_hash = self.hash_password(password)
        else:
            raise ValueError("Either password_hash or password must be provided")
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using MD5"""
        return hashlib.md5(password.encode()).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        """Verify if the provided password matches the stored hash"""
        return self.password_hash == self.hash_password(password)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user object to dictionary"""
        return {
            "username": self.username,
            "password_hash": self.password_hash
        }


class UserService:
    """Service for user-related operations"""
    
    def __init__(self):
        self.user_manager = StorageFactory.get_user_manager()
    
    def register(self, username: str, password: str) -> bool:
        """Register a new user"""
        # Check if username already exists
        if self.user_manager.user_exists(username):
            return False
        
        # Create user and save to database
        user = User(username=username, password=password)
        return self.user_manager.add_user(username, user.password_hash)
    
    def login(self, username: str, password: str) -> bool:
        """Authenticate a user"""
        password_hash = User.hash_password(password)
        return self.user_manager.validate_user(username, password_hash)
    
    def update_password(self, username: str, new_password: str) -> bool:
        """Update user password"""
        password_hash = User.hash_password(new_password)
        return self.user_manager.update_password(username, password_hash)
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user by username"""
        df = self.user_manager.read()
        user_row = df[df["username"] == username]
        
        if user_row.empty:
            return None
        
        password_hash = user_row["password_hash"].values[0]
        return User(username=username, password_hash=password_hash)
