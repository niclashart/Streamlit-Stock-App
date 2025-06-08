"""
Order model module for handling order-related data structures and operations
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
from src.database.storage_factory import StorageFactory
from src.models.portfolio import PortfolioService

class Order:
    """Order model representing a buy/sell order"""
    
    def __init__(self, username: str, ticker: str, order_type: str, price: float, 
                 quantity: float, created_at: datetime = None, status: str = 'pending',
                 order_id: Optional[int] = None):
        """Initialize an order with all necessary attributes"""
        self.username = username
        self.ticker = ticker
        self.order_type = order_type  # 'buy' or 'sell'
        self.price = price
        self.quantity = quantity
        self.created_at = created_at or datetime.now()
        self.status = status  # 'pending', 'executed', or 'cancelled'
        self.order_id = order_id
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary"""
        return {
            "username": self.username,
            "ticker": self.ticker,
            "order_type": self.order_type,
            "price": self.price,
            "quantity": self.quantity,
            "created_at": self.created_at,
            "status": self.status
        }


class OrderService:
    """Service for order-related operations"""
    
    def __init__(self):
        """Initialize order service"""
        self.order_manager = StorageFactory.get_order_manager()
        
    def create_order(self, order: Order) -> None:
        """Create a new order"""
        self.order_manager.add_order(
            username=order.username,
            ticker=order.ticker,
            order_type=order.order_type,
            price=order.price,
            quantity=order.quantity
        )
        
    def get_orders(self, username: Optional[str] = None) -> List[Order]:
        """Get all orders, optionally filtered by username"""
        df = self.order_manager.get_orders(username)
        orders = []
        
        if df.empty:
            return orders
            
        for idx, row in df.iterrows():
            order = Order(
                username=row["username"],
                ticker=row["ticker"],
                order_type=row["order_type"],
                price=row["price"],
                quantity=row["quantity"],
                created_at=row["created_at"],
                status=row["status"],
                order_id=idx
            )
            orders.append(order)
            
        return orders
        
    def get_pending_orders(self, username: Optional[str] = None) -> List[Order]:
        """Get pending orders, optionally filtered by username"""
        all_orders = self.get_orders(username)
        return [order for order in all_orders if order.status == "pending"]
        
    def cancel_order(self, username: str, index: int) -> bool:
        """Cancel a pending order"""
        user_orders = self.get_orders(username)
        pending_orders = [o for o in user_orders if o.status == "pending"]
        
        if index < len(pending_orders):
            order = pending_orders[index]
            df = self.order_manager.read()
            mask = (df["username"] == username) & (df["ticker"] == order.ticker) & \
                   (df["created_at"] == order.created_at) & (df["status"] == "pending")
            
            if mask.any():
                df.loc[mask, "status"] = "cancelled"
                self.order_manager.write(df)
                return True
        
        return False
        
    def execute_order(self, order: Order, execution_price: float) -> None:
        """Mark an order as executed and update the portfolio"""
        df = self.order_manager.read()
        
        # Find the order in the dataframe
        mask = (df["username"] == order.username) & (df["ticker"] == order.ticker) & \
               (df["created_at"] == order.created_at) & (df["status"] == "pending")
        
        if mask.any():
            # Update order status
            df.loc[mask, "status"] = "executed"
            self.order_manager.write(df)
            
            # Update the portfolio
            portfolio_service = PortfolioService(order.username)
            
            if order.order_type == "buy":
                # Add position to portfolio
                portfolio_service.add_position(
                    ticker=order.ticker,
                    shares=order.quantity,
                    entry_price=execution_price,
                    purchase_date=datetime.now()
                )
            elif order.order_type == "sell":
                # Get current portfolio
                portfolio = portfolio_service.load_portfolio()
                
                # Find positions with the ticker
                positions = [p for p in portfolio.positions if p.ticker == order.ticker]
                
                if positions:
                    position = positions[0]
                    if position.shares > order.quantity:
                        # Reduce position
                        position.shares -= order.quantity
                        portfolio.add_position(position)
                        portfolio_service.save_portfolio(portfolio)
                    else:
                        # Remove position
                        portfolio_service.remove_position(order.ticker)
