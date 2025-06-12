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
        """Create a new order
        
        The order is always created with 'pending' status.
        The trading bot will check market conditions and execute if appropriate.
        
        IMPORTANT: This method ONLY creates the order in the database.
        It does NOT execute the order or update the portfolio.
        """
        # Force the order status to be pending (even if it was set differently)
        order.status = "pending"
        
        print(f"[OrderService] Creating new {order.order_type} order for {order.ticker} at ${order.price:.2f}")
        print(f"[OrderService] Order will remain PENDING until price conditions are met")
        
        # Add the order to the database
        self.order_manager.add_order(
            username=order.username,
            ticker=order.ticker,
            order_type=order.order_type,
            price=order.price,
            quantity=order.quantity
        )
        
        print(f"[OrderService] Order saved to database with 'pending' status")
        
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
        """Mark an order as executed and update the portfolio
        
        This method is called by the trading bot when price conditions are met.
        The order stays in pending state until the target price is reached.
        
        Args:
            order: The order to execute
            execution_price: The actual price at which the order is executed
        """
        print(f"[OrderService] Attempting to execute order: {order.ticker} ({order.order_type}) at ${execution_price:.2f}")
        
        # Verify this is a pending order
        if order.status != "pending":
            print(f"[OrderService] Cannot execute order - status is {order.status}, not pending")
            return
            
        # Double check the price conditions
        from src.services.stock_service import StockService
        current_price = StockService.get_current_price(order.ticker)
        
        if current_price is None:
            print(f"[OrderService] Cannot execute order - failed to get current price")
            return
            
        # Verify the price conditions are still met
        if order.order_type == "buy" and current_price > order.price:
            print(f"[OrderService] Cannot execute buy order - current price ${current_price:.2f} > target price ${order.price:.2f}")
            return
        elif order.order_type == "sell" and current_price < order.price:
            print(f"[OrderService] Cannot execute sell order - current price ${current_price:.2f} < target price ${order.price:.2f}")
            return
            
        print(f"[OrderService] Price conditions met, executing order...")
        
        df = self.order_manager.read()
        
        # Find the order in the dataframe
        mask = (df["username"] == order.username) & (df["ticker"] == order.ticker) & \
               (df["created_at"] == order.created_at) & (df["status"] == "pending")
        
        if not mask.any():
            print(f"[OrderService] Order not found in database")
            return
            
        # Update order status
        df.loc[mask, "status"] = "executed"
        self.order_manager.write(df)
        
        print(f"[OrderService] Order status updated to 'executed'")
            
        # Update the portfolio
        portfolio_service = PortfolioService(order.username)
        
        if order.order_type == "buy":
            # Add position to portfolio - use execution_price, not the target price
            portfolio_service.add_position(
                ticker=order.ticker,
                shares=order.quantity,
                entry_price=execution_price,  # Use actual execution price
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
