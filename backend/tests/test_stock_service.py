"""
Tests for stock service
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import yfinance as yf

# Add the parent directory to the path so we can import the backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.services.stock_service import get_current_price, get_stock_info

# Mock yfinance.Ticker class
class MockTicker:
    def __init__(self, ticker):
        self.ticker = ticker
        self.info = {
            "regularMarketPrice": 150.0,
            "shortName": "Test Stock",
            "sector": "Technology",
            "industry": "Software",
            "marketCap": 1000000000,
            "trailingPE": 20.5,
            "trailingEps": 7.32,
            "dividendRate": 2.5,
            "dividendYield": 0.02,
            "previousClose": 148.0,
            "regularMarketOpen": 149.0,
            "dayLow": 147.5,
            "dayHigh": 151.5,
            "fiftyTwoWeekLow": 130.0,
            "fiftyTwoWeekHigh": 160.0,
            "targetMeanPrice": 165.0,
            "recommendationKey": "buy"
        }
        self.news = [
            {"title": "Test News 1", "link": "https://example.com/news1"},
            {"title": "Test News 2", "link": "https://example.com/news2"}
        ]


@pytest.mark.asyncio
@patch('yfinance.Ticker', MockTicker)
async def test_get_current_price():
    """Test getting the current price of a stock"""
    # Test for a valid ticker
    price = await get_current_price("AAPL")
    assert price == 150.0
    
    # Test error handling
    with patch('yfinance.Ticker', side_effect=Exception("YFinance error")):
        price = await get_current_price("AAPL")
        assert price == 0.0


@pytest.mark.asyncio
@patch('yfinance.Ticker', MockTicker)
async def test_get_stock_info():
    """Test getting stock information"""
    # Test for a valid ticker
    info = await get_stock_info("AAPL")
    
    # Verify basic structure
    assert "ticker" in info
    assert info["ticker"] == "AAPL"
    
    # Verify that important fields are present
    assert "name" in info
    assert "sector" in info
    assert "industry" in info
    assert "market_cap" in info
    assert "current_price" in info
    assert "news" in info
    
    # Test error handling
    with patch('yfinance.Ticker', side_effect=Exception("YFinance error")):
        info = await get_stock_info("AAPL")
        assert "error" in info
