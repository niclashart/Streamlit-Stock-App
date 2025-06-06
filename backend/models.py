"""
Database models for the Stock Portfolio Assistant
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class User(Base):
    """User model for authentication and identification"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    portfolio_positions = relationship("Position", back_populates="user", cascade="all, delete")
    orders = relationship("Order", back_populates="user", cascade="all, delete")
    
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
