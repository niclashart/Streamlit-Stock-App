"""
Portfolio API endpoints
"""
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.core.database import get_db
from backend.services.auth_service import get_current_user
from backend.services.portfolio_service import portfolio_service
from backend.schemas.auth import UserResponse as User
from backend.schemas.portfolio import (
    PositionCreate, 
    PositionUpdate, 
    PositionResponse, 
    PortfolioSummary
)

settings = get_settings()
router = APIRouter(prefix=f"{settings.API_PREFIX}/portfolio", tags=["portfolio"])

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@router.post("/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(
    position: PositionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new position in the user's portfolio
    """
    try:
        created_position = await portfolio_service.create_position(
            db=db,
            user_id=current_user.id,
            ticker=position.ticker,
            shares=position.shares,
            entry_price=position.entry_price,
            purchase_date=position.purchase_date
        )
        return created_position
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create position: {str(e)}"
        )

@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all positions in the user's portfolio
    """
    try:
        positions = await portfolio_service.get_positions(db=db, user_id=current_user.id)
        return positions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch positions: {str(e)}"
        )

@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a summary of the user's portfolio with performance metrics
    """
    try:
        summary = await portfolio_service.get_portfolio_summary(db=db, user_id=current_user.id)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch portfolio summary: {str(e)}"
        )

@router.delete("/positions/{position_id}", status_code=status.HTTP_200_OK)
async def delete_position(
    position_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a position from the user's portfolio
    """
    success = await portfolio_service.delete_position(
        db=db, 
        user_id=current_user.id, 
        position_id=position_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found or does not belong to you"
        )
        
    return {"detail": "Position successfully deleted"}

@router.patch("/positions/{position_id}", response_model=PositionResponse)
async def update_position(
    position_id: int,
    position_update: PositionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a position in the user's portfolio
    """
    success = await portfolio_service.update_position(
        db=db,
        user_id=current_user.id,
        position_id=position_id,
        shares=position_update.shares,
        entry_price=position_update.entry_price
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found or does not belong to you"
        )
    
    # Get the updated position
    positions = await portfolio_service.get_positions(db=db, user_id=current_user.id)
    updated_position = next((p for p in positions if p.id == position_id), None)
    
    if not updated_position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Updated position not found"
        )
        
    return updated_position
