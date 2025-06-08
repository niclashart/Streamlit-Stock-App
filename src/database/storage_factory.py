"""
Storage factory module to provide appropriate data storage manager
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config.settings import STORAGE_TYPE
from src.database.csv_manager import UserManager as CSVUserManager
from src.database.csv_manager import PortfolioManager as CSVPortfolioManager
from src.database.csv_manager import OrderManager as CSVOrderManager
from src.database.db_manager import UserDatabaseManager
from src.database.db_manager import PortfolioDatabaseManager
from src.database.db_manager import OrderDatabaseManager

class StorageFactory:
    """Factory class to create appropriate storage managers based on config"""
    
    @staticmethod
    def get_user_manager():
        """Get user manager based on storage type configuration"""
        if STORAGE_TYPE == "database":
            return UserDatabaseManager()
        else:
            return CSVUserManager()
    
    @staticmethod
    def get_portfolio_manager(username):
        """Get portfolio manager based on storage type configuration"""
        if STORAGE_TYPE == "database":
            return PortfolioDatabaseManager(username)
        else:
            return CSVPortfolioManager(username)
    
    @staticmethod
    def get_order_manager():
        """Get order manager based on storage type configuration"""
        if STORAGE_TYPE == "database":
            return OrderDatabaseManager()
        else:
            return CSVOrderManager()
