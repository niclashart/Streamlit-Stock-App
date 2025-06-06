"""
Portfolio models for tracking stock positions
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from backend.models.base import Base

class Position(Base):
    """Stock position model for portfolio tracking"""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ticker = Column(String, index=True)
    shares = Column(Float)
    entry_price = Column(Float)
    purchase_date = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="portfolio_positions")
