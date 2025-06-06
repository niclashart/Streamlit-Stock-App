"""
Main API endpoints for the Stock Portfolio Assistant
"""
from datetime import datetime, date
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from backend.config import API_PREFIX
from backend.auth import authenticate_user, create_access_token, get_current_user, create_user
from backend.models import User
from backend.database import init_db
from backend.portfolio_service import get_portfolio_summary, add_position, get_positions, delete_position, update_position
from backend.stock_service import get_stock_history, get_stock_info, get_dividends, generate_chatbot_response
from backend.trading_service import create_order, get_orders, cancel_order, check_pending_orders

# Initialize FastAPI app
app = FastAPI(title="Stock Portfolio API", description="API for Stock Portfolio Assistant")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Schedule background task to check orders
@app.on_event("startup")
async def schedule_order_check():
    import asyncio
    
    async def periodic_order_check():
        while True:
            try:
                check_pending_orders()
            except Exception as e:
                print(f"Error checking orders: {e}")
            await asyncio.sleep(60)  # Check every minute
    
    asyncio.create_task(periodic_order_check())

# Auth models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str

# Portfolio models
class PositionCreate(BaseModel):
    ticker: str
    shares: float
    entry_price: float
    purchase_date: date

class PositionResponse(BaseModel):
    id: int
    ticker: str
    shares: float
    entry_price: float
    purchase_date: date
    current_price: Optional[float] = None
    current_value: Optional[float] = None

# Order models
class OrderCreate(BaseModel):
    ticker: str
    order_type: str  # "buy" or "sell"
    price: float
    quantity: float

class OrderResponse(BaseModel):
    id: int
    ticker: str
    order_type: str
    price: float
    quantity: float
    status: str
    created_at: datetime
    executed_at: Optional[datetime] = None

# Chat models
class ChatMessage(BaseModel):
    content: str
    role: str = "user"

class ChatRequest(BaseModel):
    message: str
    ticker: Optional[str] = None
    conversation_history: Optional[List[dict]] = None

# Authentication endpoints
@app.post(f"{API_PREFIX}/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    try:
        user = create_user(user_data.username, user_data.password)
        return {"username": user.username}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post(f"{API_PREFIX}/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get(f"{API_PREFIX}/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username}

# Portfolio endpoints
@app.get(f"{API_PREFIX}/portfolio/summary")
async def get_portfolio_summary_endpoint(current_user: User = Depends(get_current_user)):
    return get_portfolio_summary(current_user.id)

@app.post(f"{API_PREFIX}/portfolio/positions", status_code=status.HTTP_201_CREATED)
async def add_position_endpoint(position: PositionCreate, current_user: User = Depends(get_current_user)):
    new_position = add_position(
        current_user.id,
        position.ticker,
        position.shares,
        position.entry_price,
        position.purchase_date
    )
    return {"id": new_position.id, "message": "Position added successfully"}

@app.get(f"{API_PREFIX}/portfolio/positions")
async def get_positions_endpoint(current_user: User = Depends(get_current_user)):
    positions = get_positions(current_user.id)
    return positions

@app.delete(f"{API_PREFIX}/portfolio/positions/{{position_id}}")
async def delete_position_endpoint(position_id: int, current_user: User = Depends(get_current_user)):
    success = delete_position(current_user.id, position_id)
    if not success:
        raise HTTPException(status_code=404, detail="Position not found")
    return {"message": "Position deleted successfully"}

@app.patch(f"{API_PREFIX}/portfolio/positions/{{position_id}}")
async def update_position_endpoint(
    position_id: int, 
    shares: Optional[float] = None, 
    entry_price: Optional[float] = None,
    current_user: User = Depends(get_current_user)
):
    success = update_position(current_user.id, position_id, shares, entry_price)
    if not success:
        raise HTTPException(status_code=404, detail="Position not found")
    return {"message": "Position updated successfully"}

# Stock data endpoints
@app.get(f"{API_PREFIX}/stocks/{{ticker}}/history")
async def get_stock_history_endpoint(ticker: str, period: str = "1y"):
    return get_stock_history(ticker, period)

@app.get(f"{API_PREFIX}/stocks/{{ticker}}")
async def get_stock_info_endpoint(ticker: str):
    return get_stock_info(ticker)

@app.get(f"{API_PREFIX}/stocks/{{ticker}}/dividends")
async def get_dividends_endpoint(ticker: str, start_date: Optional[str] = None):
    return get_dividends(ticker, start_date)

# Trading endpoints
@app.post(f"{API_PREFIX}/trading/orders", status_code=status.HTTP_201_CREATED)
async def create_order_endpoint(order_data: OrderCreate, current_user: User = Depends(get_current_user)):
    # Validate order type
    if order_data.order_type not in ["buy", "sell"]:
        raise HTTPException(status_code=400, detail="Order type must be 'buy' or 'sell'")
    
    # If sell order, check if user has enough shares
    if order_data.order_type == "sell":
        portfolio = get_portfolio_summary(current_user.id)
        ticker_positions = [p for p in portfolio.get("positions", []) if p["ticker"] == order_data.ticker]
        
        total_shares = sum(p["shares"] for p in ticker_positions)
        if total_shares < order_data.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Not enough shares of {order_data.ticker} in portfolio. You have {total_shares} shares."
            )
    
    order = create_order(
        current_user.id,
        order_data.ticker,
        order_data.order_type,
        order_data.price,
        order_data.quantity
    )
    
    return {"id": order.id, "message": "Order created successfully"}

@app.get(f"{API_PREFIX}/trading/orders")
async def get_orders_endpoint(status: Optional[str] = None, current_user: User = Depends(get_current_user)):
    orders = get_orders(current_user.id, status)
    return orders

@app.delete(f"{API_PREFIX}/trading/orders/{{order_id}}")
async def cancel_order_endpoint(order_id: int, current_user: User = Depends(get_current_user)):
    success = cancel_order(current_user.id, order_id)
    if not success:
        raise HTTPException(status_code=404, detail="Order not found or already executed/cancelled")
    return {"message": "Order cancelled successfully"}

@app.post(f"{API_PREFIX}/trading/check-orders", status_code=status.HTTP_200_OK)
async def check_orders_endpoint(background_tasks: BackgroundTasks):
    """Manually trigger a check of pending orders"""
    background_tasks.add_task(check_pending_orders)
    return {"message": "Order check initiated"}

# Chat endpoint
@app.post(f"{API_PREFIX}/chat")
async def chat_endpoint(request: ChatRequest):
    response = generate_chatbot_response(request.message, request.ticker, request.conversation_history)
    return {
        "response": response,
        "timestamp": datetime.now().isoformat()
    }
