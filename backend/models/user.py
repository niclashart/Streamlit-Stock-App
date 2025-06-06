"""
User model for authentication and identification
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from backend.models.base import Base

class User(Base):
    """User model for authentication and identification"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    portfolio_positions = relationship(
        "Position", 
        back_populates="user", 
        cascade="all, delete", 
        lazy="dynamic"
    )
    orders = relationship(
        "Order", 
        back_populates="user", 
        cascade="all, delete", 
        lazy="dynamic"
    )
