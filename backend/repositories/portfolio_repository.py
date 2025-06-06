"""
Portfolio repository for database operations
"""
from typing import List
from sqlalchemy.orm import Session

from backend.repositories.base import BaseRepository
from backend.models.portfolio import Position
from backend.schemas.portfolio import PositionCreate, PositionUpdate

class PortfolioRepository(BaseRepository[Position, PositionCreate, PositionUpdate]):
    """Repository for portfolio operations"""
    
    def get_positions_by_user(self, db: Session, user_id: int) -> List[Position]:
        """Get all positions for a user"""
        return db.query(Position).filter(Position.user_id == user_id).all()
    
    def delete_position(self, db: Session, *, user_id: int, position_id: int) -> bool:
        """Delete a position if it belongs to the user"""
        position = db.query(Position).filter(
            Position.id == position_id, 
            Position.user_id == user_id
        ).first()
        
        if not position:
            return False
            
        db.delete(position)
        db.commit()
        return True
        
    def update_position(
        self, db: Session, *, user_id: int, position_id: int, shares=None, entry_price=None
    ) -> bool:
        """Update a position if it belongs to the user"""
        position = db.query(Position).filter(
            Position.id == position_id, 
            Position.user_id == user_id
        ).first()
        
        if not position:
            return False
            
        if shares is not None:
            position.shares = shares
        if entry_price is not None:
            position.entry_price = entry_price
            
        db.add(position)
        db.commit()
        db.refresh(position)
        return True

# Create a singleton instance
portfolio_repository = PortfolioRepository(Position)
