import streamlit as st
import os
import json
import requests
from dotenv import load_dotenv

# Import get_yfinance_stock_info from stock_utils
from stock.stock_utils import get_yfinance_stock_info  # Corrected import path

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")


def generate_chatbot_response(query, ticker=None):
    """Generate a response to the user's query using DeepSeek's API with conversation history"""
    try:
        conversation_history = []
        if "messages" in st.session_state:
            recent_messages = st.session_state["messages"][-10:]
            for msg in recent_messages:
                conversation_history.append(
                    {"role": msg["role"], "content": msg["content"]}
                )

        context_message = ""
        if ticker:
            stock_data = get_yfinance_stock_info(ticker)
            if "error" in stock_data:
                context_message = f"Could not retrieve information for {ticker}. Error: {stock_data['error']}\n"
            else:
                context_message = f"Information about {ticker}:\n{json.dumps(stock_data, indent=2)}\n\n"
        else:
            context_message = "The user is asking about stocks generally or has not specified a ticker.\n"

        if api_key:
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            messages_payload = [
                {
                    "role": "system",
                    "content": "You are a helpful stock market assistant. Answer questions about stocks, provide financial advice, and help with investment decisions. Keep responses concise and informative. Remember what the user has already told you and maintain context in your responses.",
                }
            ]
            if conversation_history:
                messages_payload.extend(conversation_history)

            messages_payload.append(
                {"role": "user", "content": f"{context_message}User question: {query}"}
            )

            payload = {
                "model": "deepseek-chat",
                "messages": messages_payload,
                "temperature": 0.7,
                "max_tokens": 500,
            }

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"API Error: {response.status_code} - {response.text}. Please check your DeepSeek API key."
        else:
            if ticker:
                stock_data = get_yfinance_stock_info(ticker)
                if "error" in stock_data:
                    return f"I couldn't find information about {ticker}. Error: {stock_data['error']}. Please check if the ticker symbol is correct."

                response_text = f"DeepSeek API key not configured. Here's basic info for {ticker} ({stock_data.get('name', 'N/A')}):\n\n"
                response_text += (
                    f"Current Price: {stock_data.get('current_price', 'N/A')}\n"
                )
                response_text += f"Sector: {stock_data.get('sector', 'N/A')}\n"
                return response_text
            else:
                return "Please set the DEEPSEEK_API_KEY in your .env file to enable full chatbot functionality. I can only provide basic stock information if you give me a ticker symbol."
    except Exception as e:
        # Log the full exception for debugging if possible
        # For example, using: import traceback; traceback.print_exc()
        return f"I encountered an error in generate_chatbot_response: {str(e)}"
