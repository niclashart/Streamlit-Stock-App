"""
Portfolio service for managing user stock positions
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.repositories.portfolio_repository import portfolio_repository
from backend.models.portfolio import Position
from backend.schemas.portfolio import PositionCreate, PositionUpdate
from backend.services.stock_service import get_current_price, get_stock_info

class PortfolioService:
    """Portfolio service for managing user positions"""
    
    async def create_position(
        self, db: Session, user_id: int, ticker: str, shares: float, 
        entry_price: float, purchase_date: Optional[datetime] = None
    ) -> Position:
        """
        Create a new position in the user's portfolio
        
        Args:
            db: Database session
            user_id: User ID
            ticker: Stock ticker symbol
            shares: Number of shares
            entry_price: Price per share at entry
            purchase_date: Optional date of purchase (defaults to now)
            
        Returns:
            Created position
        """
        # Verify the ticker is valid
        stock_info = await get_stock_info(ticker)
        if "error" in stock_info:
            raise ValueError(f"Invalid ticker symbol: {ticker}")
        
        position_data = PositionCreate(
            user_id=user_id,
            ticker=ticker.upper(),
            shares=shares,
            entry_price=entry_price,
            purchase_date=purchase_date or datetime.now()
        )
        
        return portfolio_repository.create(db=db, obj_in=position_data)
    
    async def get_positions(self, db: Session, user_id: int) -> List[Position]:
        """
        Get all positions for a user
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of positions
        """
        return portfolio_repository.get_positions_by_user(db=db, user_id=user_id)
        
    async def get_portfolio_summary(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Get a summary of the user's portfolio with current prices and performance metrics
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Portfolio summary including positions and performance metrics
        """
        positions = await self.get_positions(db=db, user_id=user_id)
        
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
            current_price = await get_current_price(position.ticker)
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
    
    async def delete_position(self, db: Session, user_id: int, position_id: int) -> bool:
        """
        Delete a position from the user's portfolio
        
        Args:
            db: Database session
            user_id: User ID
            position_id: Position ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        return portfolio_repository.delete_position(db=db, user_id=user_id, position_id=position_id)
    
    async def update_position(
        self, db: Session, user_id: int, position_id: int, 
        shares: Optional[float] = None, entry_price: Optional[float] = None
    ) -> bool:
        """
        Update a position in the user's portfolio
        
        Args:
            db: Database session
            user_id: User ID
            position_id: Position ID
            shares: Optional new number of shares
            entry_price: Optional new entry price
            
        Returns:
            True if updated successfully, False otherwise
        """
        return portfolio_repository.update_position(
            db=db, 
            user_id=user_id, 
            position_id=position_id, 
            shares=shares, 
            entry_price=entry_price
        )

# Create a singleton instance
portfolio_service = PortfolioService()
