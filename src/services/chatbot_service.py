"""
Chatbot service module for handling AI-based stock assistant functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import requests
from typing import Dict, List, Any, Optional
from config.settings import DEEPSEEK_API_KEY
from services.stock_service import StockService

class ChatbotService:
    """Service for AI-based chatbot interactions"""
    
    def __init__(self):
        """Initialize the chatbot service"""
        self.api_key = DEEPSEEK_API_KEY
        
    def generate_response(self, query: str, ticker: Optional[str] = None, 
                         conversation_history: List[Dict[str, str]] = None) -> str:
        """Generate a response to the user's query"""
        try:
            if conversation_history is None:
                conversation_history = []
                
            if ticker:
                # Get stock information
                stock_data = StockService.get_stock_info(ticker)
                context = f"Information about {ticker}:\n{json.dumps(stock_data, indent=2)}\n\n"
            else:
                context = "The user is asking about stocks."
            
            if self.api_key:
                url = "https://api.deepseek.com/v1/chat/completions"
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                messages = [
                    {"role": "system", "content": "You are a helpful stock market assistant. Answer questions about stocks, provide financial advice, and help with investment decisions. Keep responses concise and informative. Remember what the user has already told you and maintain context in your responses."}
                ]
                
                if conversation_history:
                    messages.extend(conversation_history)
                
                messages.append({"role": "user", "content": f"{context}\n\nUser question: {query}"})
                
                payload = {
                    "model": "deepseek-chat",
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
                    stock_data = StockService.get_stock_info(ticker)
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
    
    @staticmethod
    def extract_ticker(prompt: str) -> Optional[str]:
        """Extract a potential ticker symbol from the user's query"""
        tokens = prompt.upper().split()
        for token in tokens:
            if token.isalpha() and len(token) <= 5 and token not in ["A", "I", "THE", "AND", "OR", "FOR", "WHAT", "HOW", "WHY"]:
                # Validate ticker
                if StockService.validate_ticker(token):
                    return token
        return None
