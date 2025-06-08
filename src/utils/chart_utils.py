"""
Utility functions for the Streamlit Stock App
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Dict, Any, List, Optional
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def format_currency(value: float) -> str:
    """Format a value as currency"""
    return f"${value:,.2f}"

def format_percentage(value: float) -> str:
    """Format a value as percentage"""
    return f"{value:.2f}%"

def calculate_portfolio_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate portfolio metrics from a portfolio dataframe"""
    if df.empty:
        return {
            "total_value": 0,
            "total_cost": 0,
            "total_profit_loss": 0,
            "total_profit_loss_percent": 0
        }
    
    # Calculate metrics
    total_value = df["Aktueller Wert"].sum()
    total_cost = df["Kaufwert"].sum()
    total_profit_loss = total_value - total_cost
    total_profit_loss_percent = (total_profit_loss / total_cost) * 100 if total_cost else 0
    
    return {
        "total_value": total_value,
        "total_cost": total_cost,
        "total_profit_loss": total_profit_loss,
        "total_profit_loss_percent": total_profit_loss_percent
    }

def create_portfolio_chart(portfolio_history: pd.DataFrame, benchmark_data: Optional[Dict[str, pd.Series]] = None) -> go.Figure:
    """Create a portfolio performance chart with optional benchmarks"""
    # Create subplot
    fig = make_subplots()
    
    # Add portfolio line
    fig.add_trace(go.Scatter(
        x=portfolio_history.index,
        y=portfolio_history["Total"],
        name="Portfolio",
        line=dict(width=3)
    ))
    
    # Add benchmarks if provided
    if benchmark_data:
        # Find first valid portfolio value for normalization
        valid_values = portfolio_history["Total"][portfolio_history["Total"] > 0]
        if not valid_values.empty:
            first_valid_value = valid_values.iloc[0]
            
            for name, benchmark in benchmark_data.items():
                if not benchmark.empty:
                    # Normalize benchmark to portfolio starting value
                    normalized = benchmark / benchmark.iloc[0] * first_valid_value
                    
                    fig.add_trace(go.Scatter(
                        x=normalized.index,
                        y=normalized,
                        name=name,
                        line=dict(dash="dot")
                    ))
    
    # Update layout
    fig.update_layout(
        title="Portfolio Performance",
        xaxis_title="Date",
        yaxis_title="Value ($)",
        height=500
    )
    
    return fig

def create_stock_chart(stock_data: pd.DataFrame, title: str = "Stock Price") -> go.Figure:
    """Create a stock price chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=stock_data.index,
        y=stock_data["Close"],
        name="Close",
        line=dict(width=2)
    ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=400
    )
    
    return fig

def create_portfolio_allocation_chart(df: pd.DataFrame) -> go.Figure:
    """Create a portfolio allocation pie chart"""
    if df.empty:
        return go.Figure()
        
    fig = go.Figure(go.Pie(
        labels=df["Ticker"],
        values=df["Aktueller Wert"],
        textinfo="label+percent",
        hole=0.3
    ))
    
    fig.update_layout(
        title="Portfolio Allocation",
        height=400
    )
    
    return fig
