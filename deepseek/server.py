import os
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
# Assume stock_service will be available at this URL, to be configured via env var later
STOCK_SERVICE_URL = os.getenv("STOCK_SERVICE_URL", "http://stock_service:5001")


def get_stock_info_from_service(ticker):
    """Helper function to call the stock_service API."""
    try:
        response = requests.get(f"{STOCK_SERVICE_URL}/info/{ticker}")
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling stock service for {ticker}: {e}")
        return {"error": str(e)}


@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.get_json()
    query = data.get("query")
    ticker = data.get("ticker")
    # conversation_history_data = data.get('conversation_history', []) # Future enhancement

    if not query:
        return jsonify({"error": "Query is required"}), 400

    if not DEEPSEEK_API_KEY:
        # Fallback if DeepSeek API is not configured
        if ticker:
            stock_data = get_stock_info_from_service(ticker)
            if "error" in stock_data:
                return jsonify(
                    {
                        "reply": f"DeepSeek API key not configured. I couldn't find information about {ticker}. Error: {stock_data['error']}."
                    }
                )

            response_text = f"DeepSeek API key not configured. Basic info for {ticker} ({stock_data.get('name', 'N/A')}):\\n"
            response_text += (
                f"Current Price: {stock_data.get('current_price', 'N/A')}\\n"
            )
            response_text += f"Sector: {stock_data.get('sector', 'N/A')}"
            return jsonify({"reply": response_text})
        else:
            return jsonify(
                {
                    "reply": "DeepSeek API key not configured. Please provide a ticker for basic info or configure the API key for full functionality."
                }
            )

    try:
        context_message = ""
        if ticker:
            stock_data = get_stock_info_from_service(ticker)
            if "error" in stock_data:
                context_message = f"Could not retrieve information for {ticker}. Error: {stock_data['error']}\\n"
            else:
                context_message = f"Information about {ticker}:\\n{json.dumps(stock_data, indent=2)}\\n\\n"
        else:
            context_message = "The user is asking about stocks generally or has not specified a ticker.\\n"

        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }

        # Simplified payload without direct st.session_state access
        # Conversation history would need to be passed from the frontend if desired
        messages_payload = [
            {
                "role": "system",
                "content": "You are a helpful stock market assistant. Answer questions about stocks, provide financial advice, and help with investment decisions. Keep responses concise and informative.",
            },
            {"role": "user", "content": f"{context_message}User question: {query}"},
        ]

        payload = {
            "model": "deepseek-chat",
            "messages": messages_payload,
            "temperature": 0.7,
            "max_tokens": 500,
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors

        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})

    except requests.exceptions.HTTPError as http_err:
        # Handle HTTP errors from DeepSeek API specifically
        error_details = response.text
        try:
            error_json = response.json()
            error_details = error_json.get("error", {}).get("message", response.text)
        except ValueError:  # response.json() fails if not json
            pass
        print(f"DeepSeek API HTTP error: {http_err} - Details: {error_details}")
        return (
            jsonify({"error": f"DeepSeek API Error: {http_err} - {error_details}"}),
            response.status_code,
        )
    except Exception as e:
        print(f"Error in chatbot endpoint: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
