# filepath: /home/niclas/Schreibtisch/KI/6. Semester/Mobile Applikationen/Streamlit-Stock-App/src/models/portfolio.py
import pandas as pd
from datetime import datetime
from src.database.db import get_session, Portfolio, User
from src.models.user import UserModel

class PortfolioModel:
    @staticmethod
    def load(username):
        """Load portfolio for a user"""
        session = get_session()
        try:
            user_id = UserModel.get_id(username)
            if not user_id:
                return pd.DataFrame(columns=["Ticker", "Anteile", "Einstiegspreis", "Kaufdatum"])
            
            # Query portfolio data
            portfolio_items = session.query(Portfolio).filter_by(user_id=user_id).all()
            
            if not portfolio_items:
                return pd.DataFrame(columns=["Ticker", "Anteile", "Einstiegspreis", "Kaufdatum"])
            
            portfolio_data = []
            for item in portfolio_items:
                portfolio_data.append({
                    "Ticker": item.ticker,
                    "Anteile": item.shares,
                    "Einstiegspreis": item.entry_price,
                    "Kaufdatum": item.purchase_date
                })
            
            return pd.DataFrame(portfolio_data)
        except Exception as e:
            print(f"Error loading portfolio: {e}")
            return pd.DataFrame(columns=["Ticker", "Anteile", "Einstiegspreis", "Kaufdatum"])
        finally:
            session.close()
    
    @staticmethod
    def add_position(username, ticker, shares, entry_price, purchase_date=None):
        """Add a new position to the portfolio"""
        if purchase_date is None:
            purchase_date = datetime.now().date()
            
        session = get_session()
        try:
            user_id = UserModel.get_id(username)
            if not user_id:
                return False
            
            # Check if position already exists
            existing = session.query(Portfolio).filter_by(user_id=user_id, ticker=ticker).first()
            
            if existing:
                # Update existing position
                existing.shares += float(shares)
                # Calculate new average entry price
                total_cost = (existing.entry_price * (existing.shares - float(shares))) + (float(entry_price) * float(shares))
                existing.entry_price = total_cost / existing.shares
            else:
                # Create new position
                new_position = Portfolio(
                    user_id=user_id,
                    ticker=ticker,
                    shares=float(shares),
                    entry_price=float(entry_price),
                    purchase_date=purchase_date
                )
                session.add(new_position)
                
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error adding position: {e}")
            return False
        finally:
            session.close()
    
    @staticmethod
    def update_position(username, ticker, shares, entry_price, purchase_date=None):
        """Update an existing position"""
        if purchase_date is None:
            purchase_date = datetime.now().date()
            
        session = get_session()
        try:
            user_id = UserModel.get_id(username)
            if not user_id:
                return False
            
            # Get existing position
            position = session.query(Portfolio).filter_by(user_id=user_id, ticker=ticker).first()
            
            if not position:
                return False
                
            # Update position
            position.shares = float(shares)
            position.entry_price = float(entry_price)
            position.purchase_date = purchase_date
                
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error updating position: {e}")
            return False
        finally:
            session.close()
    
    @staticmethod
    def delete_position(username, ticker):
        """Delete a position from the portfolio"""
        session = get_session()
        try:
            user_id = UserModel.get_id(username)
            if not user_id:
                return False
            
            # Find and delete position
            position = session.query(Portfolio).filter_by(user_id=user_id, ticker=ticker).first()
            
            if position:
                session.delete(position)
                session.commit()
                return True
                
            return False
        except Exception as e:
            session.rollback()
            print(f"Error deleting position: {e}")
            return False
        finally:
            session.close()