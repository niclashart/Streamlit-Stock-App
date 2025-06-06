import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime

class StockService:
    @staticmethod
    def get_price_history(tickers, start="2015-01-01"):
        """Get price history for multiple tickers"""
        data = pd.DataFrame()
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                history = stock.history(start=start)
                if not history.empty:
                    data[ticker] = history["Close"]
            except Exception as e:
                print(f"Error getting price history for {ticker}: {e}")
                
        return data
    
    @staticmethod
    def get_current_price(ticker):
        """Get current price for a ticker"""
        try:
            stock = yf.Ticker(ticker)
            todays_data = stock.history(period="1d")
            if not todays_data.empty:
                return todays_data["Close"].iloc[-1]
        except Exception as e:
            print(f"Error getting current price for {ticker}: {e}")
        
        return None
    
    @staticmethod
    def get_dividends(ticker):
        """Get dividend history for a ticker"""
        try:
            stock = yf.Ticker(ticker)
            dividends = stock.dividends
            return dividends[dividends.index > "2015-01-01"] if not dividends.empty else pd.Series()
        except Exception as e:
            print(f"Error getting dividends for {ticker}: {e}")
            return pd.Series()
    
    @staticmethod
    def get_stock_info(ticker):
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

class ChatbotService:
    @staticmethod
    def generate_response(query, ticker=None):
        """Generate a response to the user's query using your API with conversation history"""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        
        # If API key is not available or empty, provide a generic response
        if not api_key:
            if ticker:
                return f"I'm sorry, I can't provide specific information about {ticker} right now. API key is missing."
            return "I'm sorry, I can't process that request right now. API key is missing."
        
        try:
            # Here you would implement the actual API call to your AI service
            # For now, returning a placeholder response
            if ticker:
                return f"This is a placeholder response about {ticker}. In a real implementation, this would be generated by the AI service."
            return "This is a placeholder response. In a real implementation, this would be generated by the AI service."
            
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
