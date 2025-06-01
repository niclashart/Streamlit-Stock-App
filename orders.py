# Order management functions for Streamlit Stock App
import pandas as pd
import os
from datetime import datetime
import yfinance as yf
import streamlit as st
from portfolio import load_portfolio, save_portfolio

ORDERS_FILE = "orders.csv"


def init_orders_file():
    if not os.path.exists(ORDERS_FILE):
        df = pd.DataFrame(
            columns=[
                "username",
                "ticker",
                "order_type",
                "price",
                "quantity",
                "created_at",
                "status",
            ]
        )
        df.to_csv(ORDERS_FILE, index=False)


def load_orders(username=None):
    if not os.path.exists(ORDERS_FILE):
        init_orders_file()
    df = pd.read_csv(ORDERS_FILE)
    if username:
        df = df[df["username"] == username]
    return df


def add_order(username, ticker, order_type, price, quantity):
    df = load_orders()
    new_order = pd.DataFrame(
        [
            {
                "username": username,
                "ticker": ticker,
                "order_type": order_type,
                "price": price,
                "quantity": quantity,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "pending",
            }
        ]
    )
    if df.empty:
        df = new_order
    else:
        df = pd.concat([df, new_order], ignore_index=True)
    df.to_csv(ORDERS_FILE, index=False)
    return True


def check_orders(current_username):
    df = load_orders()
    if df.empty or "pending" not in df["status"].values:
        return False
    pending_orders = df[df["status"] == "pending"]
    executed_orders = []
    for _, order in pending_orders.iterrows():
        ticker = order["ticker"]
        try:
            stock = yf.Ticker(ticker)
            current_price = stock.info["regularMarketPrice"]
            execute = False
            if order["order_type"] == "buy" and current_price <= order["price"]:
                execute = True
            elif order["order_type"] == "sell" and current_price >= order["price"]:
                execute = True
            if execute:
                df.loc[
                    (df["username"] == order["username"])
                    & (df["ticker"] == order["ticker"])
                    & (df["created_at"] == order["created_at"]),
                    "status",
                ] = "executed"
                # Portfolio update
                user_portfolio = load_portfolio(order["username"])
                if order["order_type"] == "buy":
                    new_position = pd.DataFrame(
                        [
                            {
                                "Ticker": ticker,
                                "Anteile": order["quantity"],
                                "Einstiegspreis": current_price,
                                "Kaufdatum": datetime.now().strftime("%Y-%m-%d"),
                            }
                        ]
                    )
                    if user_portfolio.empty:
                        user_portfolio = new_position
                    else:
                        user_portfolio = pd.concat(
                            [user_portfolio, new_position], ignore_index=True
                        )
                    save_portfolio(user_portfolio, order["username"])
                elif order["order_type"] == "sell":
                    ticker_positions = user_portfolio[
                        user_portfolio["Ticker"] == ticker
                    ]
                    if not ticker_positions.empty:
                        idx = ticker_positions.index[0]
                        if user_portfolio.loc[idx, "Anteile"] > order["quantity"]:
                            user_portfolio.loc[idx, "Anteile"] -= order["quantity"]
                        else:
                            user_portfolio = user_portfolio.drop(idx)
                        save_portfolio(user_portfolio, order["username"])
                executed_orders.append(
                    {
                        "username": order["username"],
                        "ticker": ticker,
                        "type": order["order_type"],
                        "price": current_price,
                        "quantity": order["quantity"],
                    }
                )
        except Exception as e:
            st.warning(f"Error processing order for {ticker}: {e}")
    df.to_csv(ORDERS_FILE, index=False)
    return executed_orders


def cancel_order(username, index):
    df = load_orders()
    user_orders = df[df["username"] == username]
    if index < len(user_orders):
        order_created_at = user_orders.iloc[index]["created_at"]
        df.loc[
            (df["username"] == username) & (df["created_at"] == order_created_at),
            "status",
        ] = "cancelled"
        df.to_csv(ORDERS_FILE, index=False)
        return True
    return False
