"""
Order schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class OrderTypeEnum(str, Enum):
    """Order type enum"""
    BUY = "buy"
    SELL = "sell"


class OrderStatusEnum(str, Enum):
    """Order status enum"""
    PENDING = "pending"
    EXECUTED = "executed"  
    CANCELLED = "cancelled"


class OrderBase(BaseModel):
    """Base order schema"""
    ticker: str = Field(..., min_length=1, max_length=10)
    order_type: OrderTypeEnum
    price: float = Field(..., gt=0)
    quantity: float = Field(..., gt=0)


class OrderCreate(OrderBase):
    """Order creation schema"""
    pass


class OrderUpdate(BaseModel):
    """Order update schema"""
    status: Optional[OrderStatusEnum] = None


class OrderInDB(OrderBase):
    """Order in database schema"""
    id: int
    user_id: int
    status: OrderStatusEnum
    created_at: datetime
    executed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class OrderResponse(OrderBase):
    """Order response schema"""
    id: int
    status: OrderStatusEnum
    created_at: datetime
    executed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
