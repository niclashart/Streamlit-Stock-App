"""
Portfolio schemas
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PositionBase(BaseModel):
    """Base position schema"""
    ticker: str = Field(..., min_length=1, max_length=10)
    shares: float = Field(..., gt=0)
    entry_price: float = Field(..., gt=0)


class PositionCreate(PositionBase):
    """Position creation schema"""
    purchase_date: date


class PositionUpdate(BaseModel):
    """Position update schema"""
    shares: Optional[float] = Field(None, gt=0)
    entry_price: Optional[float] = Field(None, gt=0)


class PositionInDB(PositionBase):
    """Position in database schema"""
    id: int
    user_id: int
    purchase_date: datetime
    
    class Config:
        orm_mode = True


class PositionResponse(PositionBase):
    """Position response schema"""
    id: int
    purchase_date: date
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    cost_basis: Optional[float] = None
    gain_loss: Optional[float] = None
    gain_loss_percent: Optional[float] = None
    
    class Config:
        orm_mode = True


class PortfolioSummary(BaseModel):
    """Portfolio summary schema"""
    total_value: float
    total_cost: float
    total_gain_loss: float
    total_gain_loss_percent: float
    positions: List[PositionResponse]
