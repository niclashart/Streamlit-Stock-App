import yfinance as yf
import pandas as pd
from datetime import date, datetime


def get_price_history(tickers, start="2015-01-01"):
    data = pd.DataFrame()
    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(start=start)
            if "Close" in hist.columns:
                data[ticker] = hist["Close"]
        except Exception as e:
            # Consider logging this warning instead of printing to streamlit
            print(f"Warning: {ticker}: konnte nicht geladen werden ({e})")
    return data


def get_dividends(ticker):
    stock = yf.Ticker(ticker)
    try:
        dividends = stock.dividends
        return dividends[dividends.index > "2015-01-01"]
    except:
        return pd.Series()


def get_yfinance_stock_info(ticker):
    """Get comprehensive stock information for a ticker using yfinance"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Basic info
        name = info.get("shortName", "N/A")
        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")

        # Financial info
        market_cap = info.get("marketCap", 0)
        pe_ratio = info.get("trailingPE", "N/A")
        eps = info.get("trailingEps", "N/A")
        dividend_rate = info.get(
            "dividendRate", 0
        )  # Renamed from dividend to avoid confusion
        dividend_yield = info.get("dividendYield", 0)
        if dividend_yield and isinstance(dividend_yield, (int, float)):
            dividend_yield = dividend_yield * 100

        # Price info
        current_price = info.get("regularMarketPrice", "N/A")
        previous_close = info.get("previousClose", "N/A")
        open_price = info.get("regularMarketOpen", "N/A")
        day_low = info.get("dayLow", "N/A")
        day_high = info.get("dayHigh", "N/A")
        fifty_two_week_low = info.get("fiftyTwoWeekLow", "N/A")
        fifty_two_week_high = info.get("fiftyTwoWeekHigh", "N/A")

        # Analyst opinions
        target_price = info.get("targetMeanPrice", "N/A")
        recommendation = info.get("recommendationKey", "N/A")

        # Get recent news
        news_data = []
        if hasattr(stock, "news") and stock.news:
            for item in stock.news[:3]:  # Limit to 3 news items
                news_data.append(
                    {"title": item.get("title", "N/A"), "link": item.get("link", "N/A")}
                )

        stock_data = {
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "industry": industry,
            "market_cap": (
                f"${market_cap:,}"
                if isinstance(market_cap, (int, float))
                else market_cap
            ),
            "pe_ratio": pe_ratio,
            "eps": eps,
            "dividend_rate": f"${dividend_rate}" if dividend_rate else "No dividend",
            "dividend_yield": (
                f"{dividend_yield:.2f}%"
                if dividend_yield and isinstance(dividend_yield, (int, float))
                else "No dividend"
            ),
            "current_price": (
                f"${current_price}" if current_price != "N/A" else current_price
            ),
            "previous_close": previous_close,
            "open": open_price,
            "day_range": (
                f"${day_low} - ${day_high}"
                if day_low != "N/A" and day_high != "N/A"
                else "N/A"
            ),
            "52_week_range": (
                f"${fifty_two_week_low} - ${fifty_two_week_high}"
                if fifty_two_week_low != "N/A" and fifty_two_week_high != "N/A"
                else "N/A"
            ),
            "target_price": (
                f"${target_price}" if target_price != "N/A" else target_price
            ),
            "recommendation": (
                recommendation.capitalize()
                if recommendation != "N/A"
                else recommendation
            ),
            "news": news_data,
        }

        return stock_data
    except Exception as e:
        return {
            "error": f"Failed to retrieve yfinance information for {ticker}: {str(e)}"
        }
