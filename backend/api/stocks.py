"""
Stocks API endpoints
"""
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.core.database import get_db
from backend.services.auth_service import get_current_user
from backend.services.stock_service import stock_service
from backend.schemas.stock import StockInfoResponse, StockHistoryResponse, DividendResponse

settings = get_settings()
router = APIRouter(prefix=f"{settings.API_PREFIX}/stocks", tags=["stocks"])

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@router.get("/{ticker}/info", response_model=Dict[str, Any])
async def get_stock_info(ticker: str):
    """
    Get detailed information about a stock
    """
    try:
        info = await stock_service["get_stock_info"](ticker.upper())
        if "error" in info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=info["error"]
            )
        return info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stock information: {str(e)}"
        )

@router.get("/{ticker}/history", response_model=Dict[str, Any])
async def get_stock_history(
    ticker: str, 
    period: str = Query("1y", description="Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max)")
):
    """
    Get historical price data for a stock
    """
    try:
        history = await stock_service["get_stock_history"](ticker.upper(), period)
        if "error" in history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=history["error"]
            )
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stock history: {str(e)}"
        )

@router.get("/search", response_model=List[Dict[str, str]])
async def search_stocks(
    query: str = Query(..., min_length=1, description="Search query for stock tickers or names")
):
    """
    Search for stocks by name or ticker
    """
    try:
        results = await stock_service["search_stocks"](query)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search stocks: {str(e)}"
        )

@router.get("/market/overview", response_model=Dict[str, Any])
async def get_market_overview():
    """
    Get an overview of major market indices
    """
    try:
        overview = await stock_service["get_market_overview"]()
        if "error" in overview:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=overview["error"]
            )
        return overview
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve market overview: {str(e)}"
        )

@router.get("/{ticker}/analysis", response_model=Dict[str, Any])
async def get_stock_analysis(ticker: str):
    """
    Get detailed stock analysis including ratios, growth metrics, and projections
    """
    try:
        analysis = await stock_service["get_stock_analysis"](ticker.upper())
        if "error" in analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=analysis["error"]
            )
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stock analysis: {str(e)}"
        )
