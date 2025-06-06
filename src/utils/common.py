import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date, timedelta

def format_currency(value):
    """Format a number as currency"""
    if pd.isna(value):
        return "$0.00"
    return f"${value:,.2f}"

def format_percent(value):
    """Format a number as percentage"""
    if pd.isna(value):
        return "0.00%"
    return f"{value:,.2f}%"

def format_date(date_obj):
    """Format a date object as string"""
    if isinstance(date_obj, (date, datetime)):
        return date_obj.strftime('%Y-%m-%d')
    return str(date_obj)

def create_price_chart(ticker, price_data, title=None):
    """Create a price chart for a single ticker"""
    fig = go.Figure()
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=price_data.index, 
        y=price_data.values, 
        mode='lines',
        name=ticker,
        line=dict(color='rgb(0, 100, 180)', width=2)
    ))
    
    # Layout
    fig.update_layout(
        title=title or f"{ticker} Price History",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=500,
        template="plotly_white",
        hovermode="x unified"
    )
    
    return fig

def create_portfolio_chart(portfolio_df, price_history):
    """Create a portfolio value over time chart"""
    # Calculate daily portfolio value
    portfolio_value = pd.DataFrame(index=price_history.index)
    portfolio_value['Total'] = 0
    
    for _, row in portfolio_df.iterrows():
        ticker = row['Ticker']
        shares = row['Anteile']
        
        if ticker in price_history.columns:
            portfolio_value[ticker] = price_history[ticker] * shares
            portfolio_value['Total'] += portfolio_value[ticker]
    
    # Create chart
    fig = go.Figure()
    
    # Add total value line
    fig.add_trace(go.Scatter(
        x=portfolio_value.index, 
        y=portfolio_value['Total'], 
        mode='lines',
        name='Total Portfolio Value',
        line=dict(color='rgb(0, 100, 180)', width=3)
    ))
    
    # Layout
    fig.update_layout(
        title="Portfolio Value Over Time",
        xaxis_title="Date",
        yaxis_title="Value ($)",
        height=500,
        template="plotly_white",
        hovermode="x unified"
    )
    
    return fig

def display_error(message):
    """Display an error message"""
    st.error(f"❌ {message}")

def display_success(message):
    """Display a success message"""
    st.success(f"✅ {message}")

def display_info(message):
    """Display an info message"""
    st.info(f"ℹ️ {message}")
