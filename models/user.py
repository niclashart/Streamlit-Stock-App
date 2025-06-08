"""
User model module for handling user-related data structures
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hashlib
from typing import Dict, Any, Optional


class User:
    """User model class"""
    
    def __init__(self, username: str, password_hash: str):
        """Initialize user with username and hashed password"""
        self.username = username
        self.password_hash = password_hash
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using MD5"""
        return hashlib.md5(password.encode()).hexdigest()
    
    @classmethod
    def from_dict(cls, user_dict: Dict[str, Any]) -> 'User':
        """Create a User instance from dictionary data"""
        return cls(
            username=user_dict["username"],
            password_hash=user_dict["password_hash"]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary"""
        return {
            "username": self.username,
            "password_hash": self.password_hash
        }
    
    def verify_password(self, password: str) -> bool:
        """Verify that a provided password matches the stored hash"""
        return self.password_hash == self.hash_password(password)
