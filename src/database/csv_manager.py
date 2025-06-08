"""
CSV Database Manager Module
Handles all file-based data storage operations for the application
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from datetime import datetime
from typing import Dict, List, Union, Optional, Any
from config.settings import USER_FILE, ORDERS_FILE, PORTFOLIO_FILE_TEMPLATE


class CSVManager:
    """Base class for CSV file operations"""
    def __init__(self, filename: str):
        self.filename = filename
        self._ensure_file_exists()
        
    def _ensure_file_exists(self) -> None:
        """Create the CSV file if it doesn't exist"""
        if not os.path.exists(self.filename):
            self._create_default_file()
    
    def _create_default_file(self) -> None:
        """Create a default file with columns (to be overridden by subclasses)"""
        raise NotImplementedError("Subclasses must implement this method")
    
    def read(self) -> pd.DataFrame:
        """Read the CSV file into a dataframe"""
        return pd.read_csv(self.filename)
    
    def write(self, df: pd.DataFrame) -> None:
        """Write a dataframe to the CSV file"""
        df.to_csv(self.filename, index=False)
        

class UserManager(CSVManager):
    """Handles user-related file operations"""
    def __init__(self):
        super().__init__(USER_FILE)
    
    def _create_default_file(self) -> None:
        """Create a default users file"""
        df = pd.DataFrame(columns=["username", "password_hash"])
        self.write(df)
    
    def user_exists(self, username: str) -> bool:
        """Check if a user exists"""
        df = self.read()
        return username in df["username"].values
    
    def add_user(self, username: str, password_hash: str) -> bool:
        """Add a new user"""
        if self.user_exists(username):
            return False
        
        df = self.read()
        new_user = pd.DataFrame([{
            "username": username,
            "password_hash": password_hash
        }])
        
        if df.empty:
            df = new_user
        else:
            df = pd.concat([df, new_user], ignore_index=True)
            
        self.write(df)
        return True
    
    def validate_user(self, username: str, password_hash: str) -> bool:
        """Validate user login"""
        df = self.read()
        if self.user_exists(username):
            return password_hash == df.loc[df["username"] == username, "password_hash"].values[0]
        return False
    
    def update_password(self, username: str, new_password_hash: str) -> bool:
        """Update user password"""
        df = self.read()
        if self.user_exists(username):
            df.loc[df["username"] == username, "password_hash"] = new_password_hash
            self.write(df)
            return True
        return False


class PortfolioManager(CSVManager):
    """Handles portfolio-related file operations"""
    def __init__(self, username: str):
        self.username = username
        # Generate filename based on username
        filename = PORTFOLIO_FILE_TEMPLATE.format(username)
        super().__init__(filename)
    
    def _create_default_file(self) -> None:
        """Create a default portfolio file"""
        df = pd.DataFrame(columns=["Ticker", "Anteile", "Einstiegspreis", "Kaufdatum"])
        self.write(df)
    
    def add_position(self, ticker: str, shares: float, entry_price: float, 
                    purchase_date: Optional[datetime] = None) -> None:
        """Add a new position or update existing one"""
        if purchase_date is None:
            purchase_date = datetime.now()
            
        df = self.read()
        
        # Check if ticker already exists
        if ticker in df["Ticker"].values:
            # Update existing position
            df.loc[df["Ticker"] == ticker, "Anteile"] = shares
            df.loc[df["Ticker"] == ticker, "Einstiegspreis"] = entry_price
            df.loc[df["Ticker"] == ticker, "Kaufdatum"] = purchase_date
        else:
            # Add new position
            new_position = pd.DataFrame([{
                "Ticker": ticker,
                "Anteile": shares,
                "Einstiegspreis": entry_price,
                "Kaufdatum": purchase_date
            }])
            df = pd.concat([df, new_position], ignore_index=True)
            
        self.write(df)
    
    def remove_position(self, ticker: str) -> bool:
        """Remove a position from portfolio"""
        df = self.read()
        if ticker in df["Ticker"].values:
            df = df[df["Ticker"] != ticker]
            self.write(df)
            return True
        return False


class OrderManager(CSVManager):
    """Handles order-related file operations"""
    def __init__(self):
        super().__init__(ORDERS_FILE)
    
    def _create_default_file(self) -> None:
        """Create a default orders file"""
        df = pd.DataFrame(columns=["username", "ticker", "order_type", "price", 
                                  "quantity", "created_at", "status"])
        self.write(df)
    
    def add_order(self, username: str, ticker: str, order_type: str, 
                 price: float, quantity: float) -> None:
        """Add a new order"""
        df = self.read()
        
        new_order = pd.DataFrame([{
            "username": username,
            "ticker": ticker,
            "order_type": order_type,
            "price": price,
            "quantity": quantity,
            "created_at": datetime.now(),
            "status": "pending"
        }])
        
        if df.empty:
            df = new_order
        else:
            df = pd.concat([df, new_order], ignore_index=True)
            
        self.write(df)
    
    def get_orders(self, username: Optional[str] = None) -> pd.DataFrame:
        """Get orders, optionally filtered by username"""
        df = self.read()
        
        if df.empty:
            return df
            
        if username:
            return df[df["username"] == username]
            
        return df
    
    def update_order_status(self, index: int, status: str) -> bool:
        """Update order status by index"""
        df = self.read()
        
        if index >= 0 and index < len(df):
            df.loc[index, "status"] = status
            self.write(df)
            return True
            
        return False
