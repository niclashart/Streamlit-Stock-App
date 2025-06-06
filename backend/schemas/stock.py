"""
Stock data schemas
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class StockHistoryResponse(BaseModel):
    """Stock history response schema"""
    ticker: str
    period: str
    data: List[Dict[str, Any]]


class StockInfoResponse(BaseModel):
    """Stock info response schema"""
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    market_cap: Optional[float] = None
    price: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    avg_volume: Optional[int] = None
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    dividend_yield: Optional[float] = None
    target_price: Optional[float] = None


class DividendResponse(BaseModel):
    """Dividend response schema"""
    ticker: str
    data: List[Dict[str, Any]]
