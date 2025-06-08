"""
Database manager module for handling SQL database operations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3
import pandas as pd
from typing import Dict, List, Union, Optional, Any
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from src.config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DATABASE_URL

class DatabaseManager:
    """Base class for SQL database operations"""
    
    def __init__(self):
        """Initialize the database connection"""
        self.conn = None
        self._initialize_connection()
        
    def _initialize_connection(self):
        """Initialize the database connection based on environment variables"""
        # Check if we have a full DATABASE_URL (e.g., for PostgreSQL)
        if DATABASE_URL:
            self.conn = psycopg2.connect(DATABASE_URL)
        else:
            # Otherwise use SQLite
            self.conn = sqlite3.connect("stock_app.db")
            
        # Create tables if they don't exist
        self._create_tables()
    
    def _create_tables(self):
        """Create necessary database tables if they don't exist"""
        with self._get_cursor() as cursor:
            # Users table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
            ''')
            
            # Portfolios table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                ticker TEXT NOT NULL,
                shares REAL NOT NULL,
                entry_price REAL NOT NULL,
                purchase_date TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users (username),
                UNIQUE (username, ticker)
            )
            ''')
            
            # Orders table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                ticker TEXT NOT NULL,
                order_type TEXT NOT NULL,
                price REAL NOT NULL,
                quantity REAL NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users (username)
            )
            ''')
    
    @contextmanager
    def _get_cursor(self):
        """Context manager for database cursor"""
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()
            
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()


class UserDatabaseManager(DatabaseManager):
    """Manager for user-related database operations"""
    
    def read(self) -> pd.DataFrame:
        """Read all users from database
        
        Returns:
            pd.DataFrame: DataFrame with username and password_hash columns
        """
        query = "SELECT username, password_hash FROM users"
        df = pd.read_sql_query(query, self.conn)
        
        # Return empty DataFrame with correct columns if no users exist
        if df.empty:
            return pd.DataFrame(columns=["username", "password_hash"])
        return df
    
    def write(self, df: pd.DataFrame) -> None:
        """Write users DataFrame to database
        
        Args:
            df (pd.DataFrame): DataFrame with username and password_hash columns
        """
        if df.empty:
            return
            
        # Clear existing users
        with self._get_cursor() as cursor:
            cursor.execute("DELETE FROM users")
            
        # Insert all users from DataFrame
        for _, row in df.iterrows():
            # Skip attempt to add if already exists
            if not self.user_exists(row["username"]):
                self.add_user(row["username"], row["password_hash"])
    
    def user_exists(self, username: str) -> bool:
        """Check if a user exists in the database"""
        with self._get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
            return cursor.fetchone()[0] > 0
            
    def add_user(self, username: str, password_hash: str) -> bool:
        """Add a new user to the database"""
        if self.user_exists(username):
            return False
            
        with self._get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            return True
            
    def validate_user(self, username: str, password_hash: str) -> bool:
        """Validate user login"""
        with self._get_cursor() as cursor:
            cursor.execute(
                "SELECT password_hash FROM users WHERE username = ?", 
                (username,)
            )
            result = cursor.fetchone()
            return result and result[0] == password_hash
            
    def update_password(self, username: str, new_password_hash: str) -> bool:
        """Update user password"""
        if not self.user_exists(username):
            return False
            
        with self._get_cursor() as cursor:
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (new_password_hash, username)
            )
            return True
            
    def get_all_users(self) -> pd.DataFrame:
        """Get all users as a DataFrame (alias for read() for backward compatibility)"""
        return self.read()
        

class PortfolioDatabaseManager(DatabaseManager):
    """Manager for portfolio-related database operations"""
    
    def __init__(self, username: str):
        """Initialize with a specific username"""
        super().__init__()
        self.username = username
        
    def read(self) -> pd.DataFrame:
        """Read the user's portfolio from database
        
        Returns:
            pd.DataFrame: DataFrame with columns matching CSV format (Ticker, Anteile, Einstiegspreis, Kaufdatum)
        """
        query = """
            SELECT ticker as Ticker, shares as Anteile, 
                   entry_price as Einstiegspreis, purchase_date as Kaufdatum 
            FROM portfolios 
            WHERE username = ?
        """
        df = pd.read_sql_query(query, self.conn, params=(self.username,))
        
        # Ensure we have a DataFrame even if no positions exist
        if df.empty:
            return pd.DataFrame(columns=["Ticker", "Anteile", "Einstiegspreis", "Kaufdatum"])
            
        return df
        
    def write(self, df: pd.DataFrame) -> None:
        """Write portfolio DataFrame to database
        
        Args:
            df (pd.DataFrame): DataFrame with columns Ticker, Anteile, Einstiegspreis, Kaufdatum
        """
        if df.empty:
            return
            
        # First delete all existing positions for this user
        with self._get_cursor() as cursor:
            cursor.execute("DELETE FROM portfolios WHERE username = ?", (self.username,))
            
        # Then insert all positions from the DataFrame
        for _, row in df.iterrows():
            self.add_position(
                ticker=row["Ticker"],
                shares=row["Anteile"],
                entry_price=row["Einstiegspreis"],
                purchase_date=row["Kaufdatum"]
            )
        
    def add_position(self, ticker: str, shares: float, entry_price: float,
                    purchase_date: str) -> None:
        """Add or update a position in the portfolio"""
        with self._get_cursor() as cursor:
            # Check if position already exists
            cursor.execute(
                "SELECT COUNT(*) FROM portfolios WHERE username = ? AND ticker = ?",
                (self.username, ticker)
            )
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                # Update existing position
                cursor.execute(
                    """UPDATE portfolios 
                       SET shares = ?, entry_price = ?, purchase_date = ? 
                       WHERE username = ? AND ticker = ?""",
                    (shares, entry_price, purchase_date, self.username, ticker)
                )
            else:
                # Insert new position
                cursor.execute(
                    """INSERT INTO portfolios 
                       (username, ticker, shares, entry_price, purchase_date) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (self.username, ticker, shares, entry_price, purchase_date)
                )
                
    def remove_position(self, ticker: str) -> bool:
        """Remove a position from portfolio"""
        with self._get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM portfolios WHERE username = ? AND ticker = ?",
                (self.username, ticker)
            )
            return cursor.rowcount > 0
            
    def get_portfolio(self) -> pd.DataFrame:
        """Get the user's portfolio as a DataFrame (alias for read() for backward compatibility)"""
        return self.read()


class OrderDatabaseManager(DatabaseManager):
    """Manager for order-related database operations"""
    
    def read(self) -> pd.DataFrame:
        """Read all orders from database
        
        Returns:
            pd.DataFrame: DataFrame with orders data
        """
        query = """SELECT username, ticker, order_type, price, quantity, created_at, status 
                  FROM orders"""
        df = pd.read_sql_query(query, self.conn)
        
        # Return empty DataFrame with correct columns if no orders exist
        if df.empty:
            return pd.DataFrame(columns=["username", "ticker", "order_type", "price", 
                                       "quantity", "created_at", "status"])
        return df
    
    def write(self, df: pd.DataFrame) -> None:
        """Write orders DataFrame to database
        
        Args:
            df (pd.DataFrame): DataFrame with order data
        """
        if df.empty:
            return
            
        # Clear existing orders
        with self._get_cursor() as cursor:
            cursor.execute("DELETE FROM orders")
            
        # Insert all orders from DataFrame
        for _, row in df.iterrows():
            self.add_order(
                username=row["username"],
                ticker=row["ticker"],
                order_type=row["order_type"],
                price=row["price"],
                quantity=row["quantity"]
            )
    
    def add_order(self, username: str, ticker: str, order_type: str,
                 price: float, quantity: float) -> None:
        """Add a new order"""
        import datetime
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with self._get_cursor() as cursor:
            cursor.execute(
                """INSERT INTO orders 
                   (username, ticker, order_type, price, quantity, created_at, status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (username, ticker, order_type, price, quantity, created_at, "pending")
            )
            
    def get_orders(self, username: Optional[str] = None) -> pd.DataFrame:
        """Get orders, optionally filtered by username"""
        if username:
            query = "SELECT * FROM orders WHERE username = ?"
            return pd.read_sql_query(query, self.conn, params=(username,))
        else:
            query = "SELECT * FROM orders"
            return pd.read_sql_query(query, self.conn)
            
    def update_order_status(self, order_id: int, status: str) -> bool:
        """Update order status by ID"""
        with self._get_cursor() as cursor:
            cursor.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (status, order_id)
            )
            return cursor.rowcount > 0
