"""
Stock service module for fetching and processing stock data from yfinance
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import yfinance as yf
from datetime import datetime

class StockService:
    """Service for retrieving and analyzing stock data"""
    
    @staticmethod
    def get_stock_info(ticker: str) -> Dict[str, Any]:
        """Get comprehensive stock information for a ticker"""
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
            
    @staticmethod
    def get_current_price(ticker: str) -> Optional[float]:
        """Get current price for a ticker"""
        try:
            stock = yf.Ticker(ticker)
            return stock.info.get("regularMarketPrice")
        except:
            return None
            
    @staticmethod
    def get_price_history(tickers: List[str], start: str = "2015-01-01") -> pd.DataFrame:
        """Get historical prices for a list of tickers"""
        data = pd.DataFrame()
        for ticker in tickers:
            try:
                hist = yf.Ticker(ticker).history(start=start)
                if "Close" in hist.columns:
                    data[ticker] = hist["Close"]
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
        return data
        
    @staticmethod
    def get_dividends(ticker: str) -> pd.Series:
        """Get dividend history for a ticker"""
        stock = yf.Ticker(ticker)
        try:
            dividends = stock.dividends
            return dividends[dividends.index > "2015-01-01"]
        except:
            return pd.Series()
            
    @staticmethod
    def check_market_conditions() -> Dict[str, Any]:
        """Get overall market conditions using major indices"""
        try:
            indices = {
                "S&P 500": "^GSPC",
                "Nasdaq": "^IXIC",
                "Dow Jones": "^DJI",
                "Russell 2000": "^RUT"
            }
            
            result = {}
            for name, ticker in indices.items():
                index = yf.Ticker(ticker)
                info = index.info
                current = info.get("regularMarketPrice", 0)
                previous = info.get("previousClose", 0)
                change = current - previous
                change_percent = (change / previous * 100) if previous else 0
                
                result[name] = {
                    "price": current,
                    "change": change,
                    "change_percent": change_percent
                }
                
            return result
        except Exception as e:
            return {"error": f"Failed to retrieve market conditions: {str(e)}"}
            
    @staticmethod
    def validate_ticker(ticker: str) -> bool:
        """Validate if a ticker exists"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return "regularMarketPrice" in info
        except:
            return False
