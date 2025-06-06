"""
Stock data service for fetching market information
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import yfinance as yf
import pandas as pd
import aiohttp
import json
from fastapi import HTTPException

from backend.core.config import get_settings

settings = get_settings()

async def get_current_price(ticker: str) -> float:
    """
    Get the current price of a stock
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Current price as float
    """
    try:
        stock = yf.Ticker(ticker)
        return stock.info.get("regularMarketPrice", 0.0)
    except Exception as e:
        print(f"Error getting price for {ticker}: {str(e)}")
        return 0.0

async def get_stock_history(ticker: str, period: str = "1y") -> Dict[str, List]:
    """
    Get historical price data for a stock
    
    Args:
        ticker: Stock ticker symbol
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
    Returns:
        Dict with dates, prices, volumes, highs and lows
    """
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period=period)
        
        if history.empty:
            return {"error": f"No historical data found for {ticker}"}
            
        return {
            "dates": history.index.strftime("%Y-%m-%d").tolist(),
            "prices": history["Close"].tolist(),
            "volumes": history["Volume"].tolist(),
            "high": history["High"].tolist(),
            "low": history["Low"].tolist()
        }
    except Exception as e:
        return {"error": str(e)}

async def get_stock_info(ticker: str) -> Dict[str, Any]:
    """
    Get comprehensive stock information for a ticker
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dict with detailed stock information
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Basic info
        name = info.get('shortName', 'N/A')
        sector = info.get('sector', 'N/A') 
        industry = info.get('industry', 'N/A')
        
        # Financial info
        market_cap = info.get('marketCap', 0)
        pe_ratio = info.get('trailingPE', 'N/A')
        eps = info.get('trailingEps', 'N/A')
        dividend = info.get('dividendRate', 0)
        dividend_yield = info.get('dividendYield', 0)
        if dividend_yield:
            dividend_yield = dividend_yield * 100
            
        # Price info
        current_price = info.get('regularMarketPrice', 'N/A')
        previous_close = info.get('previousClose', 'N/A')
        open_price = info.get('regularMarketOpen', 'N/A')
        day_low = info.get('dayLow', 'N/A')
        day_high = info.get('dayHigh', 'N/A')
        fifty_two_week_low = info.get('fiftyTwoWeekLow', 'N/A')
        fifty_two_week_high = info.get('fiftyTwoWeekHigh', 'N/A')
        
        # Analyst opinions
        target_price = info.get('targetMeanPrice', 'N/A')
        recommendation = info.get('recommendationKey', 'N/A')
        
        # Get recent news
        news = stock.news[:3] if hasattr(stock, 'news') and stock.news else []
        
        # Format the information
        stock_data = {
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "industry": industry,
            "market_cap": f"${market_cap:,}" if isinstance(market_cap, (int, float)) else market_cap,
            "pe_ratio": pe_ratio,
            "eps": eps,
            "dividend": f"${dividend}" if dividend else "No dividend",
            "dividend_yield": f"{dividend_yield:.2f}%" if dividend_yield else "No dividend",
            "current_price": f"${current_price}" if current_price != 'N/A' else current_price,
            "previous_close": previous_close,
            "open": open_price,
            "day_range": f"${day_low} - ${day_high}" if day_low != 'N/A' and day_high != 'N/A' else "N/A",
            "52_week_range": f"${fifty_two_week_low} - ${fifty_two_week_high}" if fifty_two_week_low != 'N/A' and fifty_two_week_high != 'N/A' else "N/A",
            "target_price": f"${target_price}" if target_price != 'N/A' else target_price,
            "recommendation": recommendation.capitalize() if recommendation != 'N/A' else recommendation,
            "news": [{"title": item["title"], "link": item["link"]} for item in news] if news else []
        }
        
        return stock_data
    except Exception as e:
        return {"error": f"Failed to retrieve information for {ticker}: {str(e)}"}

async def get_market_overview() -> Dict[str, Any]:
    """
    Get an overview of major market indices
    
    Returns:
        Dict with market index information
    """
    indices = [
        "^GSPC",  # S&P 500
        "^DJI",   # Dow Jones
        "^IXIC",  # NASDAQ
        "^FTSE",  # FTSE 100
        "^N225"   # Nikkei 225
    ]
    
    results = {}
    
    try:
        for index in indices:
            stock = yf.Ticker(index)
            info = stock.info
            
            if not info:
                results[index] = {"error": "Data not available"}
                continue
            
            current = info.get('regularMarketPrice', 'N/A')
            previous = info.get('previousClose', 'N/A')
            
            if current != 'N/A' and previous != 'N/A':
                change = current - previous
                change_percent = (change / previous) * 100
            else:
                change = 'N/A'
                change_percent = 'N/A'
                
            name = info.get('shortName', index)
            
            results[index] = {
                "name": name,
                "price": current,
                "change": change,
                "change_percent": change_percent
            }
            
        return {
            "indices": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": f"Failed to retrieve market overview: {str(e)}"}

async def search_stocks(query: str) -> List[Dict[str, str]]:
    """
    Search for stocks matching the query
    
    Args:
        query: Search term
        
    Returns:
        List of matching stocks with basic information
    """
    try:
        # This is a simplified implementation - in production, you might want to use
        # a more sophisticated search API with better performance
        tickers = yf.Tickers(query)
        results = []
        
        for ticker_symbol, ticker in tickers.tickers.items():
            try:
                info = ticker.info
                if info and 'shortName' in info:
                    results.append({
                        "symbol": ticker_symbol,
                        "name": info.get('shortName', 'Unknown'),
                        "exchange": info.get('exchange', 'Unknown')
                    })
            except:
                continue
                
        return results
    except Exception as e:
        return [{"error": f"Search failed: {str(e)}"}]

async def get_stock_analysis(ticker: str) -> Dict[str, Any]:
    """
    Get detailed stock analysis including ratios, growth metrics, and projections
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dict with detailed analysis
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Basic info
        name = info.get('shortName', 'N/A')
        
        # Valuation metrics
        pe = info.get('trailingPE', 'N/A')
        forward_pe = info.get('forwardPE', 'N/A')
        peg = info.get('pegRatio', 'N/A')
        price_to_sales = info.get('priceToSalesTrailing12Months', 'N/A')
        price_to_book = info.get('priceToBook', 'N/A')
        
        # Financial health
        current_ratio = info.get('currentRatio', 'N/A')
        debt_to_equity = info.get('debtToEquity', 'N/A')
        return_on_equity = info.get('returnOnEquity', 'N/A')
        return_on_assets = info.get('returnOnAssets', 'N/A')
        
        # Growth metrics
        earnings_growth = info.get('earningsQuarterlyGrowth', 'N/A')
        revenue_growth = info.get('revenueGrowth', 'N/A')
        
        # Get earnings and revenue history
        earnings = stock.earnings
        
        return {
            "ticker": ticker,
            "name": name,
            "valuation": {
                "pe_ratio": pe,
                "forward_pe": forward_pe,
                "peg_ratio": peg,
                "price_to_sales": price_to_sales,
                "price_to_book": price_to_book
            },
            "financial_health": {
                "current_ratio": current_ratio,
                "debt_to_equity": debt_to_equity,
                "return_on_equity": return_on_equity,
                "return_on_assets": return_on_assets
            },
            "growth": {
                "earnings_growth": earnings_growth,
                "revenue_growth": revenue_growth
            },
            "earnings_history": earnings.to_dict() if not earnings.empty else {}
        }
    except Exception as e:
        return {"error": f"Failed to retrieve analysis for {ticker}: {str(e)}"}

# Stock service singleton
stock_service = {
    "get_current_price": get_current_price,
    "get_stock_history": get_stock_history,
    "get_stock_info": get_stock_info,
    "get_market_overview": get_market_overview,
    "search_stocks": search_stocks,
    "get_stock_analysis": get_stock_analysis
}
