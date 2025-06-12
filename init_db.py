#!/usr/bin/env python
"""
Database initialization script to set up database tables for PostgreSQL or SQLite
"""

import os
import sys
import argparse
import sqlite3
import psycopg2
from dotenv import load_dotenv

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Load environment variables from .env file
load_dotenv()

def create_sqlite_tables():
    """
    Create SQLite database tables for the application
    """
    print("Creating SQLite database tables...")
    conn = sqlite3.connect("stock_app.db")
    cursor = conn.cursor()
    
    try:
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
        
        conn.commit()
        print("SQLite tables created successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error creating SQLite tables: {e}")
        
    finally:
        cursor.close()
        conn.close()

def create_postgres_tables():
    """
    Create PostgreSQL database tables for the application
    """
    # Get database connection details from environment variables
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5434")
    db_name = os.getenv("DB_NAME", "stock_portfolio")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        conn_string = database_url
    else:
        conn_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    print(f"Connecting to PostgreSQL database at {db_host}:{db_port}...")
    
    try:
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        ''')
        
        # Portfolios table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            ticker VARCHAR(10) NOT NULL,
            shares NUMERIC NOT NULL,
            entry_price NUMERIC NOT NULL,
            purchase_date TIMESTAMP NOT NULL,
            FOREIGN KEY (username) REFERENCES users (username),
            UNIQUE (username, ticker)
        )
        ''')
        
        # Orders table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            ticker VARCHAR(10) NOT NULL,
            order_type VARCHAR(10) NOT NULL,
            price NUMERIC NOT NULL,
            quantity NUMERIC NOT NULL,
            created_at TIMESTAMP NOT NULL,
            status VARCHAR(20) NOT NULL,
            FOREIGN KEY (username) REFERENCES users (username)
        )
        ''')
        
        conn.commit()
        print("PostgreSQL tables created successfully!")
        
    except Exception as e:
        print(f"Error creating PostgreSQL tables: {e}")
        if conn:
            conn.rollback()
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def migrate_data_from_csv():
    """
    Migrate data from CSV files to the selected database
    """
    import pandas as pd
    import sqlite3
    import os
    
    print("Migrating data from CSV files to the database...")
    
    # Determine database type
    db_type = os.getenv("STORAGE_TYPE", "csv").lower()
    if db_type != "database":
        print("Warning: Database is not set as storage type in .env file.")
        print("Setting will be: STORAGE_TYPE=database")
    
    # Connect to the database (SQLite for simplicity)
    conn = sqlite3.connect("stock_app.db")
    cursor = conn.cursor()
    
    try:
        # Migrate users
        if os.path.exists("users.csv"):
            users_df = pd.read_csv("users.csv")
            if not users_df.empty:
                print(f"Migrating {len(users_df)} users...")
                for _, row in users_df.iterrows():
                    try:
                        cursor.execute(
                            "INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)",
                            (row["username"], row["password_hash"])
                        )
                    except Exception as e:
                        print(f"Error migrating user {row['username']}: {e}")
        
        # Migrate portfolios
        portfolio_files = [f for f in os.listdir('.') if f.startswith('portfolio_') and f.endswith('.csv')]
        for pf in portfolio_files:
            try:
                username = pf.replace('portfolio_', '').replace('.csv', '')
                print(f"Migrating portfolio for {username}...")
                
                # Check if user exists in database
                cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
                if cursor.fetchone()[0] == 0:
                    print(f"Warning: User {username} not found in database, creating...")
                    cursor.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (username, "placeholder_hash")  # Use a placeholder hash
                    )
                
                # Migrate portfolio data
                portfolio_df = pd.read_csv(pf)
                if not portfolio_df.empty:
                    for _, row in portfolio_df.iterrows():
                        try:
                            # Convert date if needed
                            purchase_date = row["Kaufdatum"] if isinstance(row["Kaufdatum"], str) else str(row["Kaufdatum"])
                            
                            cursor.execute("""
                                INSERT OR REPLACE INTO portfolios 
                                (username, ticker, shares, entry_price, purchase_date) 
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                username, 
                                row["Ticker"], 
                                float(row["Anteile"]), 
                                float(row["Einstiegspreis"]), 
                                purchase_date
                            ))
                        except Exception as e:
                            print(f"Error migrating position {row['Ticker']} for {username}: {e}")
            except Exception as e:
                print(f"Error processing file {pf}: {e}")
        
        # Migrate orders
        if os.path.exists("orders.csv"):
            orders_df = pd.read_csv("orders.csv")
            if not orders_df.empty:
                print(f"Migrating {len(orders_df)} orders...")
                for _, row in orders_df.iterrows():
                    try:
                        cursor.execute("""
                            INSERT INTO orders 
                            (username, ticker, order_type, price, quantity, created_at, status) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            row["username"], 
                            row["ticker"], 
                            row["order_type"], 
                            float(row["price"]), 
                            float(row["quantity"]), 
                            row["created_at"],
                            row["status"]
                        ))
                    except Exception as e:
                        print(f"Error migrating order for {row['ticker']}: {e}")
        
        conn.commit()
        print("Data migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during data migration: {e}")
        
    finally:
        cursor.close()
        conn.close()

def main():
    """
    Main function to set up database tables
    """
    parser = argparse.ArgumentParser(description='Initialize database for Stock Portfolio App')
    parser.add_argument('--type', choices=['sqlite', 'postgres'], default='sqlite',
                        help='Database type (sqlite or postgres)')
    parser.add_argument('--migrate', action='store_true',
                        help='Migrate existing data from CSV files to the database')
    
    args = parser.parse_args()
    
    print("Initializing Stock Portfolio App database...")
    
    if args.type == 'sqlite':
        create_sqlite_tables()
    else:
        create_postgres_tables()
    
    if args.migrate:
        migrate_data_from_csv()
    
    print(f"\nDatabase initialization complete for {args.type}.")
    print("\nTo use this database with the application, update your .env file with:")
    print("STORAGE_TYPE=database")
    
    if args.type == 'sqlite':
        print("\nThe SQLite database has been created at: ./stock_app.db")
    
    print("\nYou can now run the application with: streamlit run src/main.py")

if __name__ == "__main__":
    main()
