"""
CSV Database Manager Module
Handles all file-based data storage operations for the application
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os
import pandas as pd
from datetime import datetime


class CSVManager:
    """Base class for CSV file operations"""
    def __init__(self, filename):
        self.filename = filename
        self._ensure_file_exists()
        
    def _ensure_file_exists(self):
        """Create the CSV file if it doesn't exist"""
        if not os.path.exists(self.filename):
            self._create_default_file()
            
    def _create_default_file(self):
        """Create a default file structure - to be implemented by subclasses"""
        pass
    
    def read(self):
        """Read data from CSV file"""
        return pd.read_csv(self.filename)
    
    def write(self, df):
        """Write dataframe to CSV file"""
        df.to_csv(self.filename, index=False)


class UserManager(CSVManager):
    """Manager for user data stored in CSV"""
    def __init__(self, filename="users.csv"):
        super().__init__(filename)
        
    def _create_default_file(self):
        """Create default users file"""
        df = pd.DataFrame(columns=["username", "password_hash"])
        df.to_csv(self.filename, index=False)
        
    def add_user(self, username, password_hash):
        """Add a new user to the CSV file"""
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
        
    def get_user(self, username):
        """Get user by username"""
        df = self.read()
        if username in df["username"].values:
            return df[df["username"] == username].iloc[0].to_dict()
        return None
        
    def update_password(self, username, password_hash):
        """Update a user's password hash"""
        df = self.read()
        if username in df["username"].values:
            df.loc[df["username"] == username, "password_hash"] = password_hash
            self.write(df)
            return True
        return False


class OrderManager(CSVManager):
    """Manager for order data stored in CSV"""
    def __init__(self, filename="orders.csv"):
        super().__init__(filename)
        
    def _create_default_file(self):
        """Create default orders file"""
        df = pd.DataFrame(columns=["username", "ticker", "order_type", "price", "quantity", "created_at", "status"])
        df.to_csv(self.filename, index=False)
        
    def add_order(self, username, ticker, order_type, price, quantity):
        """Add a new order"""
        df = self.read()
        new_order = pd.DataFrame([{
            "username": username,
            "ticker": ticker,
            "order_type": order_type,
            "price": price,
            "quantity": quantity,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending"
        }])
        if df.empty:
            df = new_order
        else:
            df = pd.concat([df, new_order], ignore_index=True)
        self.write(df)
        return True
        
    def get_orders(self, username=None, status=None):
        """Get orders filtered by username and/or status"""
        df = self.read()
        if username:
            df = df[df["username"] == username]
        if status:
            df = df[df["status"] == status]
        return df
        
    def update_order_status(self, username, created_at, new_status):
        """Update order status"""
        df = self.read()
        df.loc[(df["username"] == username) & 
               (df["created_at"] == created_at), "status"] = new_status
        self.write(df)
        return True


class PortfolioManager(CSVManager):
    """Manager for portfolio data stored in CSV"""
    def __init__(self, username):
        self.username = username
        super().__init__(f"portfolio_{username}.csv")
        
    def _create_default_file(self):
        """Create default portfolio file"""
        df = pd.DataFrame(columns=["Ticker", "Anteile", "Einstiegspreis", "Kaufdatum"])
        df.to_csv(self.filename, index=False)
        
    def add_position(self, ticker, shares, price, purchase_date):
        """Add a new position to the portfolio"""
        df = self.read()
        new_position = pd.DataFrame([{
            "Ticker": ticker,
            "Anteile": shares,
            "Einstiegspreis": price,
            "Kaufdatum": purchase_date
        }])
        if df.empty:
            df = new_position
        else:
            df = pd.concat([df, new_position], ignore_index=True)
        self.write(df)
        return True
        
    def remove_shares(self, ticker, shares):
        """Remove shares of a specific ticker from portfolio"""
        df = self.read()
        ticker_positions = df[df["Ticker"] == ticker]
        
        if not ticker_positions.empty:
            idx = ticker_positions.index[0]
            if df.loc[idx, "Anteile"] > shares:
                df.loc[idx, "Anteile"] -= shares
                self.write(df)
            else:
                df = df.drop(idx)
                self.write(df)
            return True
        return False
