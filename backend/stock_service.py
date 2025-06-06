"""
Stock data and market information service
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import requests
import json

from backend.config import DEEPSEEK_API_KEY

def get_current_price(ticker: str) -> float:
    """Get the current price of a stock"""
    try:
        stock = yf.Ticker(ticker)
        return stock.info["regularMarketPrice"]
    except:
        return 0.0

def get_stock_history(ticker: str, period: str = "1y") -> Dict[str, List]:
    """Get historical price data for a stock"""
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period=period)
        return {
            "dates": history.index.strftime("%Y-%m-%d").tolist(),
            "prices": history["Close"].tolist(),
            "volumes": history["Volume"].tolist(),
            "high": history["High"].tolist(),
            "low": history["Low"].tolist()
        }
    except Exception as e:
        return {"error": str(e)}

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

def get_dividends(ticker: str, start_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get dividend history for a ticker"""
    try:
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365*5)).strftime("%Y-%m-%d")  # Default 5 years
            
        stock = yf.Ticker(ticker)
        dividends = stock.dividends
        
        # Filter dividends by start date
        dividends = dividends[dividends.index >= start_date]
        
        # Format the dividends
        dividend_list = []
        for date, amount in zip(dividends.index, dividends.values):
            dividend_list.append({
                "date": date.strftime("%Y-%m-%d"),
                "amount": float(amount)
            })
            
        return dividend_list
    except Exception as e:
        return []

def generate_chatbot_response(query: str, ticker: Optional[str] = None, conversation_history: List[Dict] = None) -> str:
    """Generate a response to the user's query using DeepSeek's API with conversation history"""
    try:
        if not conversation_history:
            conversation_history = []
            
        if ticker:
            # Get stock information
            stock_data = get_stock_info(ticker)
            context = f"Information about {ticker}:\n{json.dumps(stock_data, indent=2)}\n\n"
        else:
            context = "The user is asking about stocks."
        
        if DEEPSEEK_API_KEY:
            url = "https://api.deepseek.com/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            
            messages = [
                {"role": "system", "content": "You are a helpful stock market assistant. Answer questions about stocks, provide financial advice, and help with investment decisions. Keep responses concise and informative. Remember what the user has already told you and maintain context in your responses."}
            ]
            
            if conversation_history:
                messages.extend(conversation_history)
            
            messages.append({"role": "user", "content": f"{context}\n\nUser question: {query}"})
            
            payload = {
                "model": "deepseek-chat",  # Use the appropriate model name for DeepSeek
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"API Error: {response.status_code}. Please check your DeepSeek API key."
            
        else:
            if ticker:
                stock_data = get_stock_info(ticker)
                if "error" in stock_data:
                    return f"I couldn't find information about {ticker}. Please check if the ticker symbol is correct."
                
                response = f"Here's what I know about {ticker} ({stock_data['name']}):\n\n"
                response += f"Current Price: {stock_data['current_price']}\n"
                response += f"Sector: {stock_data['sector']}\n"
                response += f"Industry: {stock_data['industry']}\n"
                response += f"Market Cap: {stock_data['market_cap']}\n"
                if stock_data["pe_ratio"] != "N/A":
                    response += f"P/E Ratio: {stock_data['pe_ratio']:.2f}\n"
                if stock_data["dividend"] != "No dividend":
                    response += f"Dividend: {stock_data['dividend']}, Yield: {stock_data['dividend_yield']}\n"
                response += f"52 Week Range: {stock_data['52_week_range']}\n"
                
                if stock_data["recommendation"] != "N/A":
                    response += f"\nAnalyst Recommendation: {stock_data['recommendation']}"
                    
                if stock_data["news"]:
                    response += "\n\nRecent News:\n"
                    for news in stock_data["news"]:
                        response += f"- {news['title']}\n"
                
                return response
            else:
                return "Please set the DEEPSEEK_API_KEY in your environment to enable general questions. However, I can still provide specific stock information if you provide a ticker symbol."
    except Exception as e:
        return f"I encountered an error: {str(e)}"
