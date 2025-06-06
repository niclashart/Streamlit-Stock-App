"""
Trading service for handling orders
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models.order import Order, OrderStatus, OrderType
from backend.schemas.order import OrderCreate, OrderUpdate
from backend.repositories.order_repository import order_repository
from backend.services.stock_service import get_current_price
from backend.services.portfolio_service import portfolio_service
from backend.core.config import get_settings
from backend.core.database import get_db

settings = get_settings()

class TradingService:
    """Service for trading operations"""

    async def check_pending_orders(self, db: Session) -> Dict[str, Any]:
        """
        Check all pending orders and execute them if conditions are met
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with execution results
        """
        results = {
            "executed": [],
            "errors": [],
            "success_count": 0,
            "error_count": 0
        }
        
        try:
            # Get all pending orders
            pending_orders = order_repository.get_pending_orders(db=db)
            
            # Process each order
            for order in pending_orders:
                # Get current price for the ticker
                try:
                    current_price = await get_current_price(order.ticker)
                    
                    if current_price is None or current_price == 0:
                        results["errors"].append(f"Could not get price for {order.ticker}")
                        results["error_count"] += 1
                        continue
                    
                    # Check if order conditions are met
                    if ((order.order_type == OrderType.BUY and current_price <= order.price) or 
                        (order.order_type == OrderType.SELL and current_price >= order.price)):
                        
                        # Mark order as executed
                        order_repository.execute_order(db=db, order_id=order.id)
                        
                        # If this is a buy order, create a position
                        if order.order_type == OrderType.BUY:
                            await portfolio_service.create_position(
                                db=db,
                                user_id=order.user_id,
                                ticker=order.ticker,
                                shares=order.quantity,
                                entry_price=current_price
                            )
                        # If this is a sell order, update or delete the position
                        else:
                            # TODO: Implement position update/delete logic when selling
                            pass
                            
                        results["executed"].append({
                            "order_id": order.id,
                            "ticker": order.ticker,
                            "type": order.order_type.value,
                            "price": current_price,
                            "quantity": order.quantity
                        })
                        results["success_count"] += 1
                        
                except Exception as e:
                    results["errors"].append(f"Error processing order {order.id}: {str(e)}")
                    results["error_count"] += 1
            
            return results
        except Exception as e:
            return {"error": f"Error checking orders: {str(e)}"}
    
    async def create_order(
        self, db: Session, user_id: int, ticker: str, order_type: str, 
        price: float, quantity: float
    ) -> Order:
        """
        Create a new order
        
        Args:
            db: Database session
            user_id: User ID
            ticker: Stock ticker symbol
            order_type: Type of order (BUY or SELL)
            price: Target price
            quantity: Number of shares
            
        Returns:
            Created order object
        """
        order_data = OrderCreate(
            user_id=user_id,
            ticker=ticker.upper(),
            order_type=order_type,
            price=price,
            quantity=quantity,
            status=OrderStatus.PENDING.value
        )
        
        return order_repository.create(db=db, obj_in=order_data)
    
    async def get_orders(
        self, db: Session, user_id: int, status: Optional[str] = None
    ) -> List[Order]:
        """
        Get orders for a user with optional status filter
        
        Args:
            db: Database session
            user_id: User ID
            status: Optional order status filter
            
        Returns:
            List of orders
        """
        return order_repository.get_orders_by_user(db=db, user_id=user_id, status=status)
    
    async def cancel_order(
        self, db: Session, user_id: int, order_id: int
    ) -> bool:
        """
        Cancel an order if it belongs to the user and is in PENDING state
        
        Args:
            db: Database session
            user_id: User ID
            order_id: Order ID
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        return order_repository.cancel_order(db=db, user_id=user_id, order_id=order_id)
    
    async def get_order_history(
        self, db: Session, user_id: int, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get order execution history for a user
        
        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of orders to return
            
        Returns:
            List of orders with details
        """
        orders = order_repository.get_orders_by_user(db=db, user_id=user_id)
        orders = orders[:limit]  # Limit the number of orders returned
        
        result = []
        for order in orders:
            result.append({
                "id": order.id,
                "ticker": order.ticker,
                "order_type": order.order_type.value,
                "status": order.status.value,
                "price": order.price,
                "quantity": order.quantity,
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "executed_at": order.executed_at.strftime("%Y-%m-%d %H:%M:%S") if order.executed_at else None
            })
            
        return result

# Create a singleton instance
trading_service = TradingService()
