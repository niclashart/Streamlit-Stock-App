"""
Trading API endpoints
"""
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.core.database import get_db
from backend.services.auth_service import get_current_user
from backend.services.trading_service import trading_service
from backend.schemas.auth import UserResponse as User
from backend.schemas.order import OrderCreate, OrderResponse

settings = get_settings()
router = APIRouter(prefix=f"{settings.API_PREFIX}/trading", tags=["trading"])

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new order (buy or sell)
    """
    try:
        created_order = await trading_service.create_order(
            db=db,
            user_id=current_user.id,
            ticker=order.ticker,
            order_type=order.order_type.value,
            price=order.price,
            quantity=order.quantity
        )
        return created_order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order: {str(e)}"
        )

@router.get("/orders", response_model=List[OrderResponse])
async def get_orders(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all orders for the current user with optional status filter
    """
    try:
        orders = await trading_service.get_orders(db=db, user_id=current_user.id, status=status)
        return orders
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch orders: {str(e)}"
        )

@router.delete("/orders/{order_id}", status_code=status.HTTP_200_OK)
async def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a pending order
    """
    success = await trading_service.cancel_order(db=db, user_id=current_user.id, order_id=order_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found, already executed, or does not belong to you"
        )
    
    return {"detail": "Order successfully cancelled"}

@router.get("/history", response_model=List[Dict[str, Any]])
async def get_order_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get order execution history for the current user
    """
    try:
        history = await trading_service.get_order_history(db=db, user_id=current_user.id, limit=limit)
        return history
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch order history: {str(e)}"
        )

@router.post("/check-orders", status_code=status.HTTP_200_OK)
async def check_pending_orders(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually check pending orders (admin only)
    """
    # Check if user has admin privileges (simplified check)
    if current_user.id != 1:  # Assuming user_id 1 is admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can check pending orders"
        )
    
    # Run the check in a background task
    background_tasks.add_task(trading_service.check_pending_orders, db=db)
    
    return {"detail": "Order check initiated"}
