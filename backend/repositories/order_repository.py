"""
Order repository for database operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from backend.repositories.base import BaseRepository
from backend.models.order import Order, OrderStatus
from backend.schemas.order import OrderCreate, OrderUpdate

class OrderRepository(BaseRepository[Order, OrderCreate, OrderUpdate]):
    """Repository for order operations"""
    
    def get_orders_by_user(self, db: Session, user_id: int, status: Optional[str] = None) -> List[Order]:
        """Get all orders for a user with optional status filter"""
        query = db.query(Order).filter(Order.user_id == user_id)
        
        if status:
            query = query.filter(Order.status == status)
            
        return query.order_by(Order.created_at.desc()).all()
    
    def cancel_order(self, db: Session, *, user_id: int, order_id: int) -> bool:
        """Cancel an order if it belongs to the user and is in PENDING state"""
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == user_id,
            Order.status == OrderStatus.PENDING
        ).first()
        
        if not order:
            return False
            
        order.status = OrderStatus.CANCELLED
        db.add(order)
        db.commit()
        db.refresh(order)
        return True
    
    def get_pending_orders(self, db: Session) -> List[Order]:
        """Get all pending orders"""
        return db.query(Order).filter(Order.status == OrderStatus.PENDING).all()
    
    def execute_order(self, db: Session, *, order_id: int) -> bool:
        """Mark an order as executed"""
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.status == OrderStatus.PENDING
        ).first()
        
        if not order:
            return False
            
        order.status = OrderStatus.EXECUTED
        order.executed_at = datetime.now()
        db.add(order)
        db.commit()
        db.refresh(order)
        return True

# Create a singleton instance
order_repository = OrderRepository(Order)
