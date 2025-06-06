"""
Order models for automated trading
"""
from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship

from backend.models.base import Base

class OrderStatus(enum.Enum):
    """Enum for order status"""
    PENDING = "pending"
    EXECUTED = "executed"  
    CANCELLED = "cancelled"

class OrderType(enum.Enum):
    """Enum for order type"""
    BUY = "buy"
    SELL = "sell"

class Order(Base):
    """Order model for automated trading"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ticker = Column(String, index=True)
    order_type = Column(SQLEnum(OrderType))
    price = Column(Float)
    quantity = Column(Float)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    created_at = Column(DateTime, default=datetime.now)
    executed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="orders")
