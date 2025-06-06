"""
Portfolio management service
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.models import User, Position
from backend.database import get_db_session
from backend.stock_service import get_current_price

def add_position(user_id: int, ticker: str, shares: float, entry_price: float, purchase_date: datetime) -> Position:
    """Add a new position to the user's portfolio"""
    with get_db_session() as session:
        position = Position(
            user_id=user_id,
            ticker=ticker,
            shares=shares,
            entry_price=entry_price,
            purchase_date=purchase_date
        )
        session.add(position)
        return position

def get_positions(user_id: int) -> List[Position]:
    """Get all positions for a user"""
    with get_db_session() as session:
        positions = session.query(Position).filter(Position.user_id == user_id).all()
        return positions

def get_portfolio_summary(user_id: int) -> Dict[str, Any]:
    """Get a summary of the user's portfolio with current prices and performance metrics"""
    positions = get_positions(user_id)
    if not positions:
        return {
            "total_value": 0.0,
            "total_cost": 0.0,
            "total_gain_loss": 0.0,
            "total_gain_loss_percent": 0.0,
            "positions": []
        }

    positions_data = []
    total_value = 0.0
    total_cost = 0.0
    
    for position in positions:
        current_price = get_current_price(position.ticker)
        current_value = position.shares * current_price
        cost_basis = position.shares * position.entry_price
        gain_loss = current_value - cost_basis
        gain_loss_percent = (gain_loss / cost_basis) * 100 if cost_basis > 0 else 0
        
        positions_data.append({
            "id": position.id,
            "ticker": position.ticker,
            "shares": position.shares,
            "entry_price": position.entry_price,
            "purchase_date": position.purchase_date.strftime("%Y-%m-%d"),
            "current_price": current_price,
            "current_value": current_value,
            "cost_basis": cost_basis,
            "gain_loss": gain_loss,
            "gain_loss_percent": gain_loss_percent
        })
        
        total_value += current_value
        total_cost += cost_basis
    
    return {
        "total_value": total_value,
        "total_cost": total_cost,
        "total_gain_loss": total_value - total_cost,
        "total_gain_loss_percent": ((total_value - total_cost) / total_cost) * 100 if total_cost > 0 else 0,
        "positions": positions_data
    }

def delete_position(user_id: int, position_id: int) -> bool:
    """Delete a position from the user's portfolio"""
    with get_db_session() as session:
        position = session.query(Position).filter(
            Position.id == position_id, Position.user_id == user_id
        ).first()
        if not position:
            return False
        session.delete(position)
        return True

def update_position(user_id: int, position_id: int, shares: Optional[float] = None, 
                   entry_price: Optional[float] = None) -> bool:
    """Update a position in the user's portfolio"""
    with get_db_session() as session:
        position = session.query(Position).filter(
            Position.id == position_id, Position.user_id == user_id
        ).first()
        if not position:
            return False
            
        if shares is not None:
            position.shares = shares
        if entry_price is not None:
            position.entry_price = entry_price
            
        return True
