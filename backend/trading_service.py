"""
Automated trading service
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import and_

from backend.models import Order, OrderStatus, OrderType, User, Position
from backend.database import get_db_session
from backend.stock_service import get_current_price

def create_order(user_id: int, ticker: str, order_type: str, price: float, quantity: float) -> Order:
    """Create a new order"""
    with get_db_session() as session:
        order = Order(
            user_id=user_id,
            ticker=ticker,
            order_type=OrderType.BUY if order_type.lower() == "buy" else OrderType.SELL,
            price=price,
            quantity=quantity,
            status=OrderStatus.PENDING
        )
        session.add(order)
        return order

def get_orders(user_id: int, status: Optional[str] = None) -> List[Order]:
    """Get orders for a user, optionally filtered by status"""
    with get_db_session() as session:
        query = session.query(Order).filter(Order.user_id == user_id)
        if status:
            query = query.filter(Order.status == OrderStatus[status.upper()])
        return query.all()

def cancel_order(user_id: int, order_id: int) -> bool:
    """Cancel a pending order"""
    with get_db_session() as session:
        order = session.query(Order).filter(
            Order.id == order_id, 
            Order.user_id == user_id,
            Order.status == OrderStatus.PENDING
        ).first()
        
        if not order:
            return False
            
        order.status = OrderStatus.CANCELLED
        return True

def check_pending_orders() -> List[Dict[str, Any]]:
    """Check all pending orders and execute them if conditions are met"""
    executed_orders = []
    
    with get_db_session() as session:
        # Get all pending orders
        pending_orders = session.query(Order).filter(Order.status == OrderStatus.PENDING).all()
        
        for order in pending_orders:
            ticker = order.ticker
            try:
                # Get current price
                current_price = get_current_price(ticker)
                
                # Check if order should be executed
                execute = False
                if order.order_type == OrderType.BUY and current_price <= order.price:
                    execute = True
                elif order.order_type == OrderType.SELL and current_price >= order.price:
                    execute = True
                    
                if execute:
                    # Update order status
                    order.status = OrderStatus.EXECUTED
                    order.executed_at = datetime.now()
                    
                    # If this is a buy order, add to portfolio
                    if order.order_type == OrderType.BUY:
                        position = Position(
                            user_id=order.user_id,
                            ticker=order.ticker,
                            shares=order.quantity,
                            entry_price=current_price,
                            purchase_date=datetime.now()
                        )
                        session.add(position)
                    
                    # If this is a sell order, update portfolio
                    elif order.order_type == OrderType.SELL:
                        positions = session.query(Position).filter(
                            Position.user_id == order.user_id,
                            Position.ticker == order.ticker
                        ).all()
                        
                        remaining_quantity = order.quantity
                        for position in positions:
                            if remaining_quantity <= 0:
                                break
                                
                            if position.shares <= remaining_quantity:
                                remaining_quantity -= position.shares
                                session.delete(position)
                            else:
                                position.shares -= remaining_quantity
                                remaining_quantity = 0
                    
                    # Add to executed orders list
                    user = session.query(User).filter(User.id == order.user_id).first()
                    executed_orders.append({
                        "username": user.username if user else "Unknown",
                        "ticker": ticker,
                        "type": order.order_type.value,
                        "price": current_price,
                        "quantity": order.quantity
                    })
                    
            except Exception as e:
                print(f"Error processing order for {ticker}: {str(e)}")
                
    return executed_orders
