"""
Portfolio model module for handling portfolio-related data structures and operations
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
from src.database.storage_factory import StorageFactory

class Position:
    """Position model representing a stock position in a portfolio"""
    
    def __init__(self, ticker: str, shares: float, entry_price: float, 
                 purchase_date: datetime = None):
        """Initialize a position with stock ticker, shares, entry price and date"""
        self.ticker = ticker
        self.shares = shares
        self.entry_price = entry_price
        self.purchase_date = purchase_date or datetime.now()
        self.current_price: Optional[float] = None
        self.current_value: Optional[float] = None
        self.profit_loss: Optional[float] = None
        self.profit_loss_percent: Optional[float] = None
        
    def calculate_metrics(self, current_price: float) -> None:
        """Calculate position metrics based on current price"""
        self.current_price = current_price
        self.current_value = self.shares * current_price
        purchase_value = self.shares * self.entry_price
        self.profit_loss = self.current_value - purchase_value
        self.profit_loss_percent = (self.profit_loss / purchase_value) * 100 if purchase_value else 0
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary"""
        return {
            "Ticker": self.ticker,
            "Anteile": self.shares,
            "Einstiegspreis": self.entry_price,
            "Kaufdatum": self.purchase_date,
            "Aktueller Kurs": self.current_price,
            "Aktueller Wert": self.current_value,
            "Gewinn/Verlust €": self.profit_loss,
            "Gewinn/Verlust %": self.profit_loss_percent
        }


class Portfolio:
    """Portfolio model representing a collection of positions"""
    
    def __init__(self, username: str):
        """Initialize portfolio for a user"""
        self.username = username
        self.positions: List[Position] = []
        self.total_value: float = 0
        self.total_cost: float = 0
        self.total_profit_loss: float = 0
        self.total_profit_loss_percent: float = 0
        
    def add_position(self, position: Position) -> None:
        """Add a position to the portfolio"""
        # If position exists, update it
        for i, pos in enumerate(self.positions):
            if pos.ticker == position.ticker:
                self.positions[i] = position
                return
                
        # Otherwise append new position
        self.positions.append(position)
        
    def remove_position(self, ticker: str) -> bool:
        """Remove a position from portfolio by ticker"""
        original_length = len(self.positions)
        self.positions = [p for p in self.positions if p.ticker != ticker]
        return len(self.positions) < original_length
        
    def calculate_metrics(self) -> None:
        """Calculate portfolio metrics"""
        self.total_value = sum(p.current_value for p in self.positions if p.current_value is not None)
        self.total_cost = sum(p.shares * p.entry_price for p in self.positions)
        self.total_profit_loss = self.total_value - self.total_cost
        self.total_profit_loss_percent = (self.total_profit_loss / self.total_cost) * 100 if self.total_cost else 0
        
    def to_dataframe(self) -> pd.DataFrame:
        """Convert portfolio to DataFrame"""
        if not self.positions:
            return pd.DataFrame(columns=["Ticker", "Anteile", "Einstiegspreis", "Kaufdatum"])
            
        return pd.DataFrame([p.to_dict() for p in self.positions])


class PortfolioService:
    """Service for portfolio-related operations"""
    
    def __init__(self, username: str):
        """Initialize portfolio service for a user"""
        self.username = username
        self.portfolio_manager = StorageFactory.get_portfolio_manager(username)
        
    def load_portfolio(self) -> Portfolio:
        """Load portfolio from storage"""
        df = self.portfolio_manager.read()
        portfolio = Portfolio(self.username)
        
        if df.empty:
            return portfolio
            
        for _, row in df.iterrows():
            position = Position(
                ticker=row["Ticker"],
                shares=row["Anteile"],
                entry_price=row["Einstiegspreis"],
                purchase_date=row["Kaufdatum"]
            )
            portfolio.add_position(position)
            
        return portfolio
        
    def save_portfolio(self, portfolio: Portfolio) -> None:
        """Save portfolio to storage"""
        df = portfolio.to_dataframe()
        self.portfolio_manager.write(df)
        
    def add_position(self, ticker: str, shares: float, entry_price: float, 
                    purchase_date: datetime = None) -> None:
        """Add a position to the portfolio"""
        self.portfolio_manager.add_position(ticker, shares, entry_price, purchase_date)
        
    def remove_position(self, ticker: str) -> bool:
        """Remove a position from the portfolio"""
        return self.portfolio_manager.remove_position(ticker)
        
    def get_tickers(self) -> List[str]:
        """Get list of tickers in the portfolio"""
        df = self.portfolio_manager.read()
        return df["Ticker"].tolist() if not df.empty else []
