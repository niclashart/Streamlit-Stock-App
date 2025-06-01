# Portfolio management functions for Streamlit Stock App
import pandas as pd
import os
from datetime import date
import yfinance as yf
import streamlit as st


def get_portfolio_file(username):
    return f"portfolio_{username}.csv"


def load_portfolio(username):
    file = get_portfolio_file(username)
    if os.path.exists(file):
        return pd.read_csv(file, parse_dates=["Kaufdatum"])
    return pd.DataFrame(columns=["Ticker", "Anteile", "Einstiegspreis", "Kaufdatum"])


def save_portfolio(df, username):
    df.to_csv(get_portfolio_file(username), index=False)


def get_price_history(tickers, start="2015-01-01"):
    data = pd.DataFrame()
    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(start=start)
            if "Close" in hist.columns:
                data[ticker] = hist["Close"]
        except Exception as e:
            st.warning(f"{ticker}: konnte nicht geladen werden ({e})")
    return data


def get_dividends(ticker):
    stock = yf.Ticker(ticker)
    try:
        dividends = stock.dividends
        return dividends[dividends.index > "2015-01-01"]
    except:
        return pd.Series()
