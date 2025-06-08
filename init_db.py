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
    print("Data migration functionality will be implemented in a future update.")
    print("Currently, you'll need to manually register and add portfolio positions.")

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
