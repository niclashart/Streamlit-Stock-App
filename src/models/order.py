from datetime import datetime
import pandas as pd
from src.database.db import get_session, Order, User
from src.models.user import UserModel

class OrderModel:
    @staticmethod
    def load(username=None):
        """Load orders, optionally filtered by username"""
        session = get_session()
        try:
            if username:
                user_id = UserModel.get_id(username)
                if not user_id:
                    return pd.DataFrame()
                
                # Query orders by user_id
                orders = session.query(Order, User.username).join(User).filter(Order.user_id == user_id).all()
            else:
                # Query all orders
                orders = session.query(Order, User.username).join(User).all()
                
            if not orders:
                return pd.DataFrame()
                
            # Format data for DataFrame
            orders_data = []
            for order, username in orders:
                orders_data.append({
                    "username": username,
                    "ticker": order.ticker,
                    "order_type": order.order_type,
                    "price": order.price,
                    "quantity": order.quantity,
                    "created_at": order.created_at,
                    "status": order.status
                })
                
            return pd.DataFrame(orders_data)
        except Exception as e:
            print(f"Error loading orders: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    @staticmethod
    def create(username, ticker, order_type, price, quantity):
        """Create a new order"""
        session = get_session()
        try:
            user_id = UserModel.get_id(username)
            if not user_id:
                return False
                
            # Create order
            order = Order(
                user_id=user_id,
                ticker=ticker,
                order_type=order_type,
                price=float(price),
                quantity=float(quantity),
                status='pending'
            )
            
            session.add(order)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error creating order: {e}")
            return False
        finally:
            session.close()
    
    @staticmethod
    def update_status(order_id, status):
        """Update order status"""
        session = get_session()
        try:
            # Get order
            order = session.query(Order).filter_by(id=order_id).first()
            if not order:
                return False
                
            # Update status
            order.status = status
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error updating order status: {e}")
            return False
        finally:
            session.close()
    
    @staticmethod
    def delete(order_id):
        """Delete an order"""
        session = get_session()
        try:
            # Get order
            order = session.query(Order).filter_by(id=order_id).first()
            if not order:
                return False
                
            # Delete order
            session.delete(order)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error deleting order: {e}")
            return False
        finally:
            session.close()
