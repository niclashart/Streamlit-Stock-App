"""
Configuration management module
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5434))
DB_NAME = os.getenv("DB_NAME", "stock_portfolio")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DATABASE_URL = os.getenv("DATABASE_URL", None)

# File paths
USER_FILE = os.getenv("USER_FILE", "users.csv")
ORDERS_FILE = os.getenv("ORDERS_FILE", "orders.csv")
PORTFOLIO_FILE_TEMPLATE = os.getenv("PORTFOLIO_FILE_TEMPLATE", "portfolio_{}.csv")

# Storage settings
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "csv").lower()  # 'csv' or 'database'

# Application settings
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
